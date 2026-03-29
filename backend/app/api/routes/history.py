from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

from ...core.leveling import calculate_level_from_score
from ...database import get_db
from ...dependencies import get_current_user
from ...models.user import User
from ...models.identification_history import IdentificationHistory
from ...schemas.identification_history import (
    IdentificationHistoryCreate,
    IdentificationHistoryResponse,
    UserStatsResponse,
)

router = APIRouter(prefix="/users/me/history", tags=["identification history"])


@router.post("", response_model=IdentificationHistoryResponse)
def create_identification(
    history_data: IdentificationHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Enregistrer une nouvelle identification de champignon
    
    Met à jour automatiquement le scoring et autres stats du joueur
    """
    # Créer l'entrée d'historique
    history_entry = IdentificationHistory(
        user_id=current_user.id,
        champignon=history_data.champignon,
        score=history_data.score,
        heure=history_data.heure,
        localisation=history_data.localisation,
        latitude=history_data.latitude,
        longitude=history_data.longitude,
        notes=history_data.notes,
        date=datetime.now(timezone.utc),
    )
    db.add(history_entry)

    # Mettre à jour le scoring de l'utilisateur
    current_user.scoring += history_data.score

    # Mettre à jour le streak (si score >= 50, on incrémente, sinon on réinitialise)
    if history_data.score >= 50:
        current_user.streak += 1
    else:
        current_user.streak = 0

    # Mettre à jour automatiquement le niveau avec des seuils progressifs.
    current_user.niveau = calculate_level_from_score(current_user.scoring)

    db.commit()
    db.refresh(history_entry)
    db.refresh(current_user)

    return IdentificationHistoryResponse.model_validate(history_entry)


@router.get("", response_model=list[IdentificationHistoryResponse])
def get_user_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Obtenir l'historique d'identification paginé
    
    Query parameters:
    - skip: nombre d'entrées à sauter (pagination)
    - limit: nombre maximum d'entrées à retourner (max 100)
    """
    history = (
        db.query(IdentificationHistory)
        .filter(IdentificationHistory.user_id == current_user.id)
        .order_by(IdentificationHistory.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [IdentificationHistoryResponse.model_validate(entry) for entry in history]


@router.get("/stats", response_model=UserStatsResponse)
def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtenir les statistiques de l'utilisateur
    """
    # Compter le nombre total d'identifications
    total_identifications = (
        db.query(func.count(IdentificationHistory.id))
        .filter(IdentificationHistory.user_id == current_user.id)
        .scalar()
    )

    # Obtenir la dernière identification
    last_identification = (
        db.query(IdentificationHistory)
        .filter(IdentificationHistory.user_id == current_user.id)
        .order_by(IdentificationHistory.date.desc())
        .first()
    )

    return UserStatsResponse(
        scoring_total=current_user.scoring,
        streak_actuel=current_user.streak,
        niveau=current_user.niveau,
        total_identifications=total_identifications,
        derniere_identification=last_identification.date if last_identification else None,
    )


@router.delete("/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_identification(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Supprimer une entrée d'historique (action irréversible)
    
    Recalcule les stats de l'utilisateur après suppression
    """
    # Récupérer l'entrée
    history_entry = (
        db.query(IdentificationHistory)
        .filter(
            IdentificationHistory.id == history_id,
            IdentificationHistory.user_id == current_user.id,
        )
        .first()
    )

    if not history_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entrée d'historique non trouvée",
        )

    # Soustraire le score
    current_user.scoring = max(0, current_user.scoring - history_entry.score)

    # Recalculer automatiquement le niveau avec des seuils progressifs.
    current_user.niveau = calculate_level_from_score(current_user.scoring)

    # Supprimer l'entrée
    db.delete(history_entry)
    db.commit()
    db.refresh(current_user)
