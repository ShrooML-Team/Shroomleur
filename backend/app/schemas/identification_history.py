from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class IdentificationHistoryCreate(BaseModel):
    """Schéma pour créer une entrée d'historique d'identification"""
    champignon: str
    score: float = Field(..., ge=0, le=100)
    heure: Optional[str] = None
    localisation: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


class IdentificationHistoryResponse(BaseModel):
    """Schéma pour répondre avec un historique d'identification"""
    id: int
    user_id: int
    champignon: str
    score: float
    date: datetime
    heure: Optional[str]
    localisation: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """Schéma pour les statistiques de l'utilisateur"""
    scoring_total: float
    streak_actuel: int
    niveau: int
    total_identifications: int
    derniere_identification: Optional[datetime]
