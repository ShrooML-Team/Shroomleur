from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    """Schéma pour créer un utilisateur (inscription locale)"""
    identifiant: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    mot_de_passe: str = Field(..., min_length=8, max_length=72, description="Maximum 72 caractères (limitation bcrypt)")
    champignon_prefere: Optional[str] = None


class UserLogin(BaseModel):
    """Schéma pour se connecter"""
    identifiant: str
    mot_de_passe: str


class UserUpdate(BaseModel):
    """Schéma pour mettre à jour le profil utilisateur"""
    email: Optional[EmailStr] = None
    description: Optional[str] = None
    champignon_prefere: Optional[str] = None
    photo_profil: Optional[str] = None
    scoring: Optional[float] = None


class UserPhotoUploadResponse(BaseModel):
    """Réponse après upload de la photo de profil"""
    photo_profil: str


class UserItemResponse(BaseModel):
    """Schéma pour les items du joueur"""
    id: int
    item_name: str
    quantity: int
    acquired_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Schéma pour la réponse utilisateur (profil complet, authentifié)"""
    id: int
    identifiant: str
    email: str
    photo_profil: Optional[str]
    description: Optional[str]
    champignon_prefere: Optional[str]
    scoring: float
    streak: int
    niveau: int
    rang: int
    created_at: datetime
    is_active: bool
    items: List[UserItemResponse] = []

    class Config:
        from_attributes = True


class UserPublicResponse(BaseModel):
    """Schéma pour la réponse utilisateur (profil public)"""
    id: int
    identifiant: str
    photo_profil: Optional[str]
    scoring: float
    streak: int
    niveau: int
    rang: int


class TokenResponse(BaseModel):
    """Schéma pour la réponse d'authentification"""
    access_token: str
    token_type: str
    user: UserResponse


class GoogleLoginRequest(BaseModel):
    """Schéma pour la requête Google OAuth"""
    code: str
    redirect_uri: Optional[str] = None
    platform: str = "web"  # "web" ou "android"


class GoogleTokenRequest(BaseModel):
    """Schéma pour la requête Google ID Token (Android Google Sign-In)"""
    idToken: str
    platform: str = "android"


class GoogleLoginResponse(BaseModel):
    """Schéma pour la réponse de login Google"""
    access_token: str
    token_type: str
    user: UserResponse
