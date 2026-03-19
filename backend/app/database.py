from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from .core.config import settings

# Créer l'engine de base de données
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,  # Test la connexion avant d'utiliser
    pool_size=10,
    max_overflow=20,
)

# Créer la session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour tous les modèles
Base = declarative_base()


def get_db():
    """
    Dependency injection pour obtenir une session de base de données
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialiser la base de données - créer toutes les tables"""
    Base.metadata.create_all(bind=engine)

    # Compatibilité schéma: create_all ne modifie pas les tables existantes.
    # Si la base existe déjà, on ajoute manuellement la colonne manquante.
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "description_index" not in user_columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN description_index INTEGER DEFAULT 0")
            )
