from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.leveling import calculate_level_from_score
from ...database import get_db
from ...dependencies import get_current_user
from ...models.user import User, UserItem
from ...schemas.user import (
    UserPhotoUploadResponse,
    UserResponse,
    UserUpdate,
    UserPublicResponse,
    UserItemResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


PROFILE_PHOTO_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
PROFILE_PHOTO_ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
PROFILE_PHOTO_MAX_SIZE_BYTES = 5 * 1024 * 1024


def _calculate_user_rank(db: Session, user_score: float) -> int:
    higher_scores_count = db.query(func.count(User.id)).filter(User.scoring > user_score).scalar() or 0
    return int(higher_scores_count) + 1


def _build_user_response(db: Session, user: User) -> UserResponse:
    rank = _calculate_user_rank(db, user.scoring)
    
    user_data = {
        'id': user.id,
        'identifiant': user.identifiant,
        'email': user.email,
        'photo_profil': user.photo_profil,
        'champignon_prefere': user.champignon_prefere,
        'description_index': user.description_index,
        'scoring': user.scoring,
        'streak': user.streak,
        'niveau': user.niveau,
        'rang': rank,
        'created_at': user.created_at,
        'is_active': user.is_active,
        'items': user.items if hasattr(user, 'items') else []
    }
    return UserResponse(**user_data)


def _build_user_public_response(db: Session, user: User) -> UserPublicResponse:
    rank = _calculate_user_rank(db, user.scoring)
    
    user_data = {
        'id': user.id,
        'identifiant': user.identifiant,
        'photo_profil': user.photo_profil,
        'champignon_prefere': user.champignon_prefere,
        'description_index': user.description_index,
        'scoring': user.scoring,
        'streak': user.streak,
        'niveau': user.niveau,
        'rang': rank
    }
    return UserPublicResponse(**user_data)


def _profile_photo_directory() -> Path:
    return Path(settings.UPLOAD_DIR) / settings.PROFILE_PHOTO_SUBDIR


def _extract_relative_upload_path(photo_url: str | None) -> str | None:
    if not photo_url:
        return None

    marker = f"/{settings.PROFILE_PHOTO_SUBDIR}/"
    uploads_marker = "/uploads"
    uploads_index = photo_url.find(uploads_marker)

    if uploads_index == -1:
        return None

    relative_path = photo_url[uploads_index + len("/uploads/"):]
    if marker.strip("/") not in relative_path:
        return None

    return relative_path


def _delete_previous_profile_photo(photo_url: str | None) -> None:
    relative_path = _extract_relative_upload_path(photo_url)
    if not relative_path:
        return

    file_path = Path(settings.UPLOAD_DIR) / relative_path
    try:
        file_path.resolve().relative_to(Path(settings.UPLOAD_DIR).resolve())
    except ValueError:
        return

    if file_path.exists():
        file_path.unlink()


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtenir le profil de l'utilisateur connecté
    """
    return _build_user_response(db, current_user)


@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mettre à jour le profil de l'utilisateur connecté
    
    Peut mettre à jour: email, champignon_prefere, photo_profil, scoring
    """
    if user_update.email is not None:
        existing_user = (
            db.query(User)
            .filter(User.email == user_update.email, User.id != current_user.id)
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email déjà utilisé",
            )

        current_user.email = user_update.email

    if user_update.champignon_prefere is not None:
        current_user.champignon_prefere = user_update.champignon_prefere

    if user_update.description_index is not None:
        current_user.description_index = user_update.description_index

    if user_update.photo_profil is not None:
        current_user.photo_profil = user_update.photo_profil

    if user_update.scoring is not None:
        current_user.scoring = max(0, user_update.scoring)
        current_user.niveau = calculate_level_from_score(current_user.scoring)

    db.commit()
    db.refresh(current_user)

    return _build_user_response(db, current_user)


@router.post("/me/photo", response_model=UserPhotoUploadResponse)
async def upload_current_user_profile_photo(
    request: Request,
    photo: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Uploader une nouvelle photo de profil pour l'utilisateur connecté."""
    if photo.content_type not in PROFILE_PHOTO_ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format d'image non supporté",
        )

    extension = PROFILE_PHOTO_ALLOWED_CONTENT_TYPES[photo.content_type]
    if extension not in PROFILE_PHOTO_ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extension d'image non supportée",
        )

    content = await photo.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier image vide",
        )

    if len(content) > PROFILE_PHOTO_MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image trop volumineuse (5 Mo max)",
        )

    profile_photo_dir = _profile_photo_directory()
    profile_photo_dir.mkdir(parents=True, exist_ok=True)

    filename = f"user_{current_user.id}_{uuid4().hex}{extension}"
    file_path = profile_photo_dir / filename
    file_path.write_bytes(content)

    _delete_previous_profile_photo(current_user.photo_profil)

    relative_path = f"{settings.PROFILE_PHOTO_SUBDIR}/{filename}"
    base_url = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else str(request.base_url).rstrip("/")
    photo_url = base_url + f"/uploads/{relative_path}"

    current_user.photo_profil = photo_url
    db.commit()
    db.refresh(current_user)

    return UserPhotoUploadResponse(photo_profil=photo_url)


@router.get("/me/photo/download")
def download_current_user_profile_photo(
    current_user: User = Depends(get_current_user),
):
    """Télécharger la photo de profil courante de l'utilisateur connecté."""
    if not current_user.photo_profil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune photo de profil enregistrée",
        )

    relative_path = _extract_relative_upload_path(current_user.photo_profil)
    if not relative_path:
        return RedirectResponse(current_user.photo_profil)

    file_path = Path(settings.UPLOAD_DIR) / relative_path
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier photo introuvable",
        )

    return FileResponse(file_path, filename=file_path.name)


@router.get("/top-ranking", response_model=list[UserPublicResponse])
def get_top_ranking_users(limit: int = 20, db: Session = Depends(get_db)):
    """
    Obtenir le classement des meilleurs joueurs triés par score
    """
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La limite doit être supérieure à 0",
        )
    
    if limit > 100:
        limit = 100

    top_users = (
        db.query(User)
        .filter(User.is_active == True)
        .order_by(User.scoring.desc())
        .limit(limit)
        .all()
    )

    return [_build_user_public_response(db, user) for user in top_users]


@router.get("/{user_id}", response_model=UserPublicResponse)
def get_user_public_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Obtenir le profil public d'un utilisateur (statistiques visibles)
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé",
        )

    return _build_user_public_response(db, user)


@router.get("/me/items", response_model=list[UserItemResponse])
def get_current_user_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtenir l'inventaire (items) de l'utilisateur connecté
    """
    items = db.query(UserItem).filter(UserItem.user_id == current_user.id).all()
    return [UserItemResponse.model_validate(item) for item in items]


@router.post("/me/items/{item_name}")
def add_user_item(
    item_name: str,
    quantity: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ajouter un item à l'inventaire de l'utilisateur
    """
    # Vérifier si l'item existe déjà
    existing_item = (
        db.query(UserItem)
        .filter(
            UserItem.user_id == current_user.id,
            UserItem.item_name == item_name,
        )
        .first()
    )

    if existing_item:
        existing_item.quantity += quantity
        db.commit()
        db.refresh(existing_item)
        return UserItemResponse.model_validate(existing_item)

    # Créer un nouvel item
    new_item = UserItem(
        user_id=current_user.id,
        item_name=item_name,
        quantity=quantity,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return UserItemResponse.model_validate(new_item)
