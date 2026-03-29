from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from ..database import Base


class User(Base):
    """Modèle utilisateur"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    identifiant = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    mot_de_passe = Column(String(255), nullable=True)  # Nullable pour OAuth-only users
    photo_profil = Column(String(500), nullable=True)
    champignon_prefere = Column(String(255), nullable=True)
    description_index = Column(Integer, default=0, nullable=True)  # Index de la description choisie (0-14)
    
    # Statistiques du joueur
    scoring = Column(Float, default=0.0)
    streak = Column(Integer, default=0)
    niveau = Column(Integer, default=1)
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_active = Column(Boolean, default=True)
    
    # OAuth
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    
    # Relations
    items = relationship("UserItem", back_populates="user", cascade="all, delete-orphan")
    identification_history = relationship(
        "IdentificationHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User(id={self.id}, identifiant={self.identifiant}, email={self.email})>"


class UserItem(Base):
    """Modèle pour les items du joueur (inventaire)"""
    __tablename__ = "user_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_name = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1)
    
    # Métadonnées
    acquired_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relations
    user = relationship("User", back_populates="items")

    def __repr__(self):
        return f"<UserItem(id={self.id}, user_id={self.user_id}, item_name={self.item_name})>"
