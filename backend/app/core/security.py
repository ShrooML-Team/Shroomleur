from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

# Configuration du contexte de hachage (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hacher un mot de passe"""
    # bcrypt ne supporte que 72 bytes maximum (limiter correctement)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Tronquer les bytes, pas les caractères
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifier un mot de passe contre un hash"""
    # bcrypt ne supporte que 72 bytes maximum (limiter correctement)
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        plain_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Créer un JWT token
    
    Args:
        data: Données à encoder dans le JWT
        expires_delta: Durée de validité du token (par défaut: ACCESS_TOKEN_EXPIRE_MINUTES)
    
    Returns:
        Token JWT encodé
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Décoder et vérifier un JWT token
    
    Args:
        token: Token JWT à décoder
    
    Returns:
        Données du token ou None si invalide/expiré
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None
