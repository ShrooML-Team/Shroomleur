from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import requests
from urllib.parse import urlencode
from pydantic import BaseModel
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from ...database import get_db
from ...dependencies import get_current_user
from ...core.config import settings
from ...core.security import hash_password, verify_password, create_access_token
from ...models.user import User
from ...schemas.user import (
    UserCreate,
    UserLogin,
    TokenResponse,
    UserResponse,
    GoogleLoginRequest,
    GoogleTokenRequest,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=TokenResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Enregistrer un nouvel utilisateur avec identifiant et mot de passe
    """
    # Vérifier que l'identifiant n'existe pas déjà
    existing_user = db.query(User).filter(User.identifiant == user_data.identifiant).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identifiant déjà utilisé",
        )

    # Vérifier que l'email n'existe pas déjà
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        # Si le compte existe mais a été créé via Google (pas de mot de passe),
        # on lui ajoute le mot de passe pour lier les deux méthodes de connexion
        if existing_email.google_id and not existing_email.mot_de_passe:
            existing_email.mot_de_passe = hash_password(user_data.mot_de_passe)
            if user_data.champignon_prefere:
                existing_email.champignon_prefere = user_data.champignon_prefere
            db.commit()
            db.refresh(existing_email)
            access_token = create_access_token(data={"sub": str(existing_email.id)})
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user=UserResponse.model_validate(existing_email),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email déjà utilisé",
        )

    # Créer le nouvel utilisateur
    user = User(
        identifiant=user_data.identifiant,
        email=user_data.email,
        mot_de_passe=hash_password(user_data.mot_de_passe),
        champignon_prefere=user_data.champignon_prefere,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Générer un token d'accès
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Se connecter avec identifiant et mot de passe
    """
    user = db.query(User).filter(User.identifiant == credentials.identifiant).first()

    if not user or not user.mot_de_passe:
        if user and user.google_id and not user.mot_de_passe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce compte utilise uniquement Google. Connectez-vous via Google ou inscrivez-vous avec votre email pour ajouter un mot de passe.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
        )

    if not verify_password(credentials.mot_de_passe, user.mot_de_passe):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé",
        )

    # Générer un token d'accès
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/google", response_model=TokenResponse)
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Authentification via Google OAuth 2.0
    
    Échange le code d'autorisation contre un token et récupère les infos utilisateur
    
    Body parameters:
    - code: Code d'autorisation de Google
    - redirect_uri: URI de redirection (optionnel)
    - platform: "web" ou "android" (défaut: "web")
    """
    # Sélectionner les clés en fonction de la plateforme
    if request.platform == "android":
        client_id = settings.GOOGLE_CLIENT_ID_ANDROID
        client_secret = settings.GOOGLE_CLIENT_SECRET_ANDROID
    else:
        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_CLIENT_SECRET

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration Google OAuth manquante pour la plateforme {request.platform}",
        )

    try:
        # Échanger le code contre un access_token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": request.code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": request.redirect_uri or settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        token_response = response.json()

        # Récupérer les informations utilisateur
        access_token = token_response["access_token"]
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}

        userinfo_response = requests.get(userinfo_url, headers=headers)
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()

        google_id = userinfo.get("id")
        email = userinfo.get("email")
        name = userinfo.get("name", email.split("@")[0])
        picture = userinfo.get("picture")

        # Chercher l'utilisateur par google_id
        user = db.query(User).filter(User.google_id == google_id).first()

        if not user:
            # Chercher par email en cas de premier login
            user = db.query(User).filter(User.email == email).first()

            if not user:
                # Créer un nouvel utilisateur
                user = User(
                    identifiant=name.replace(" ", "_").lower(),
                    email=email,
                    google_id=google_id,
                    photo_profil=picture,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                # Associer le google_id si utilisateur existe avec cet email
                user.google_id = google_id
                if not user.photo_profil:
                    user.photo_profil = picture
                db.commit()
                db.refresh(user)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte désactivé",
            )

        # Générer un token d'accès
        jwt_token = create_access_token(data={"sub": str(user.id)})

        return TokenResponse(
            access_token=jwt_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de l'authentification Google: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Rafraîchir le token d'accès
    """
    # Générer un nouveau token
    access_token = create_access_token(data={"sub": str(current_user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(current_user),
    )


class GoogleAuthUrlResponse(BaseModel):
    """Réponse avec l'URL d'authentification Google"""
    auth_url: str


@router.get("/google/url", response_model=GoogleAuthUrlResponse)
def get_google_auth_url(redirect_uri: str = Query(None)):
    """
    Obtenir l'URL d'authentification Google
    
    Utilisé pour initier le flow OAuth avec Google.
    
    Query parameters:
    - redirect_uri: URI de redirection personnalisée (optionnel, par défaut depuis config)
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration Google OAuth manquante",
        )

    auth_params = {
        "response_type": "code",
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri or settings.GOOGLE_REDIRECT_URI,
        "scope": "openid email profile",
        "access_type": "offline",
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(auth_params)}"

    return GoogleAuthUrlResponse(auth_url=auth_url)


@router.get("/google/callback", response_model=TokenResponse)
def google_callback(code: str = Query(...), state: str = Query(None), platform: str = Query("web"), db: Session = Depends(get_db)):
    """
    Callback endpoint pour Google OAuth 2.0
    
    Google redirige ici après que l'utilisateur autorise l'application.
    Échange le code contre un token et crée/met à jour l'utilisateur.
    
    Query parameters:
    - code: Code d'autorisation de Google (obligatoire)
    - state: État CSRF (optionnel)
    - platform: "web" ou "android" (optionnel, défaut: "web")
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code d'autorisation manquant",
        )

    # Créer la requête Google Login avec le code
    google_request = GoogleLoginRequest(code=code, redirect_uri=settings.GOOGLE_REDIRECT_URI, platform=platform)
    
    # Réutiliser la logique de google_login
    return google_login(google_request, db)


@router.post("/google/idtoken", response_model=TokenResponse)
def google_idtoken_login(request: GoogleTokenRequest, db: Session = Depends(get_db)):
    """
    Authentification via Google ID Token (Android Google Sign-In)
    
    Reçoit un ID Token du Google Sign-In SDK Android et le valide.
    Crée ou met à jour l'utilisateur en fonction de google_id.
    
    Body parameters:
    - idToken: ID Token du Google Sign-In SDK
    - platform: "android" (défaut)
    """
    if not settings.GOOGLE_CLIENT_ID_ANDROID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration Google OAuth Android manquante",
        )

    try:
        # Valider l'ID Token avec la clé publique de Google
        idinfo = id_token.verify_oauth2_token(
            request.idToken,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID_ANDROID
        )

        google_id = idinfo.get("sub")
        email = idinfo.get("email")
        name = idinfo.get("name", email.split("@")[0])
        picture = idinfo.get("picture")

        # Chercher l'utilisateur par google_id
        user = db.query(User).filter(User.google_id == google_id).first()

        if not user:
            # Chercher par email en cas de premier login
            user = db.query(User).filter(User.email == email).first()

            if not user:
                # Créer un nouvel utilisateur
                user = User(
                    identifiant=name.replace(" ", "_").lower(),
                    email=email,
                    google_id=google_id,
                    photo_profil=picture,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                # Associer le google_id si utilisateur existe avec cet email
                user.google_id = google_id
                if not user.photo_profil:
                    user.photo_profil = picture
                db.commit()
                db.refresh(user)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte désactivé",
            )

        # Générer un token d'accès
        jwt_token = create_access_token(data={"sub": str(user.id)})

        return TokenResponse(
            access_token=jwt_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"ID Token invalide: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}",
        )





