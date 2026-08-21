from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.game.leveling import compute_level
from app.game.streak import next_streak

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


def _get_current_profile(current_user: models.User, db: Session) -> models.UserProfile:
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No profile yet for this account")
    return profile


def _build_out(game_profile: models.GameProfile) -> schemas.GameProfileOut:
    level_info = compute_level(game_profile.xp)
    return schemas.GameProfileOut(**level_info, streak_count=game_profile.streak_count)


@router.get("/me", response_model=schemas.GameProfileOut)
def get_my_game_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Read-only - does not affect the streak. Use POST /game/checkin for that."""
    profile = _get_current_profile(current_user, db)
    game_profile = get_or_create_game_profile(profile.id, db)
    return _build_out(game_profile)


@router.post("/checkin", response_model=schemas.GameProfileOut)
def checkin(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Call this once when the app opens (or returns to the foreground).
    Idempotent for the same UTC calendar day - calling it multiple
    times today does not inflate the streak.
    """
    profile = _get_current_profile(current_user, db)
    game_profile = get_or_create_game_profile(profile.id, db)

    today = datetime.now(timezone.utc).date()
    game_profile.streak_count = next_streak(game_profile.last_checkin_date, today, game_profile.streak_count)
    game_profile.last_checkin_date = today

    db.commit()
    db.refresh(game_profile)
    return _build_out(game_profile)
