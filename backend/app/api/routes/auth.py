from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import requests

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
    access_token = create_access_token(data={"sub": user.id})

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
    access_token = create_access_token(data={"sub": user.id})

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
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration Google OAuth manquante",
        )

    try:
        # Échanger le code contre un access_token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": request.code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
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
        jwt_token = create_access_token(data={"sub": user.id})

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
    access_token = create_access_token(data={"sub": current_user.id})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(current_user),
    )



