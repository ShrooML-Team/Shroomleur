from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from ..database import Base


class IdentificationHistory(Base):
    """Modèle pour l'historique d'identification des champignons"""
    __tablename__ = "identification_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Identification
    champignon = Column(String(255), nullable=False)
    score = Column(Float, nullable=False)
    
    # Localisation et timing
    date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    heure = Column(String(8), nullable=True)  # Format HH:MM:SS
    localisation = Column(String(500), nullable=True)  # Texte libre ou coords
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Métadonnées
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relations
    user = relationship("User", back_populates="identification_history")

    def __repr__(self):
        return f"<IdentificationHistory(id={self.id}, user_id={self.user_id}, champignon={self.champignon}, score={self.score})>"
