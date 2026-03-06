from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...dependencies import get_current_user
from ...models.user import User, UserItem
from ...schemas.user import (
    UserResponse,
    UserUpdate,
    UserPublicResponse,
    UserItemResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Obtenir le profil de l'utilisateur connecté
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mettre à jour le profil de l'utilisateur connecté
    
    Peut mettre à jour: description, champignon_prefere, photo_profil
    """
    if user_update.description is not None:
        current_user.description = user_update.description

    if user_update.champignon_prefere is not None:
        current_user.champignon_prefere = user_update.champignon_prefere

    if user_update.photo_profil is not None:
        current_user.photo_profil = user_update.photo_profil

    db.commit()
    db.refresh(current_user)

    return UserResponse.model_validate(current_user)


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

    return UserPublicResponse.model_validate(user)


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
