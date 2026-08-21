from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.game.leveling import compute_level

router = APIRouter(prefix="/game", tags=["game"])


def get_or_create_game_profile(profile_id: int, db: Session) -> models.GameProfile:
    """
    Self-healing lookup: creates a GameProfile the first time anything
    needs one, rather than requiring it to exist from profile-creation
    time. This means the game layer can be added without a data
    migration for accounts created before it existed.
    """
    game_profile = db.query(models.GameProfile).filter(models.GameProfile.profile_id == profile_id).first()
    if not game_profile:
        game_profile = models.GameProfile(profile_id=profile_id, xp=0)
        db.add(game_profile)
        db.commit()
        db.refresh(game_profile)
    return game_profile


@router.get("/me", response_model=schemas.GameProfileOut)
def get_my_game_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No profile yet for this account")

    game_profile = get_or_create_game_profile(profile.id, db)
    return compute_level(game_profile.xp)
