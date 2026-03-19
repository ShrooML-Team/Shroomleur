from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Configuration de l application"""

    # Application
    APP_NAME: str = "Shroomleur API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Base de donnees
    DATABASE_URL: str = "postgresql://shroomleur:shroomleur@localhost:5432/shroomleur"
    DATABASE_ECHO: bool = False

    # JWT/Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Google OAuth - Web
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    # Google OAuth - Android
    GOOGLE_CLIENT_ID_ANDROID: str = ""
    GOOGLE_CLIENT_SECRET_ANDROID: str = ""

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]

    # Uploads
    UPLOAD_DIR: str = str(Path("/app/uploads"))
    PROFILE_PHOTO_SUBDIR: str = "profiles"
    # URL publique de base pour construire les URLs des photos uploadees.
    # Ex: "https://shroomleur.shrooml.duckdns.org"
    # A definir si le serveur est derriere un reverse proxy (Nginx, Cloudflare, Caddy...).
    # Sans cette valeur, request.base_url peut retourner une URL http:// interne bloquee par Android 9+.
    PUBLIC_BASE_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
