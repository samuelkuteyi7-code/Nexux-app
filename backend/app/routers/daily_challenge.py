from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.game.daily_challenge import todays_template, build_daily_context, compute_daily_status
from app.routers.game import get_or_create_game_profile, _build_out

router = APIRouter(prefix="/daily-challenge", tags=["daily-challenge"])


def _get_today_status(current_user: models.User, db: Session):
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No profile yet for this account")

    world = (
        db.query(models.World)
        .filter(models.World.user_id == profile.id)
        .order_by(models.World.created_at.desc())
        .first()
    )
    if not world:
        raise HTTPException(status_code=404, detail="No world yet for this account")

    today = datetime.now(timezone.utc).date()
    today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)

    decisions_today = (
        db.query(models.Decision)
        .filter(models.Decision.world_id == world.id, models.Decision.created_at >= today_start)
        .all()
    )
    context = build_daily_context([d.state_delta for d in decisions_today])
    template = todays_template(today)
    status = compute_daily_status(template, context)

    claim = (
        db.query(models.DailyChallengeClaim)
        .filter(
            models.DailyChallengeClaim.profile_id == profile.id,
            models.DailyChallengeClaim.challenge_date == today,
        )
        .first()
    )
    status["claimed"] = claim is not None
    return profile, today, template, status


@router.get("/", response_model=schemas.DailyChallengeOut)
def get_daily_challenge(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _profile, _today, _template, status = _get_today_status(current_user, db)
    return status


@router.post("/claim", response_model=schemas.DailyChallengeClaimResult)
def claim_daily_challenge(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    profile, today, template, status = _get_today_status(current_user, db)

    if not status["completed"]:
        raise HTTPException(status_code=400, detail="Today's challenge is not completed yet")
    if status["claimed"]:
        raise HTTPException(status_code=409, detail="Already claimed today's challenge")

    claim = models.DailyChallengeClaim(profile_id=profile.id, challenge_date=today, challenge_key=template["key"])
    db.add(claim)

    game_profile = get_or_create_game_profile(profile.id, db)
    game_profile.xp += template["reward_xp"]
    db.commit()
    db.refresh(game_profile)

    status["claimed"] = True
    return schemas.DailyChallengeClaimResult(challenge=status, game=_build_out(game_profile))
