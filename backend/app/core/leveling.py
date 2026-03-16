"""Règles de progression de niveau basées sur des seuils croissants."""

BASE_POINTS_PER_LEVEL = 100.0
POINTS_INCREMENT_PER_LEVEL = 50.0


def points_required_for_next_level(current_level: int) -> float:
    """Points requis pour passer du niveau courant au suivant."""
    safe_level = max(1, current_level)
    return BASE_POINTS_PER_LEVEL + (safe_level - 1) * POINTS_INCREMENT_PER_LEVEL


def calculate_level_from_score(scoring: float) -> int:
    """Calcule automatiquement le niveau à partir du score total.

    Exemples avec la progression par défaut:
    - niveau 1 -> 2: 100 points
    - niveau 2 -> 3: 150 points
    - niveau 3 -> 4: 200 points
    """
    remaining_score = max(0.0, float(scoring))
    level = 1
    required = points_required_for_next_level(level)

    while remaining_score >= required:
        remaining_score -= required
        level += 1
        required = points_required_for_next_level(level)

    return level
