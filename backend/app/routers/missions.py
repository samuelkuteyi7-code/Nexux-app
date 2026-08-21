from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.game.missions import MISSION_TEMPLATES, compute_mission_status
from app.game.leveling import compute_level
from app.routers.game import get_or_create_game_profile, _build_out

router = APIRouter(prefix="/missions", tags=["missions"])


def _get_context(current_user: models.User, db: Session) -> tuple[models.UserProfile, models.World, dict, models.GameProfile]:
    """
    Gathers everything mission progress needs to check against: the
    user's profile, their most recent world (MVP = one world per
    profile, but this is future-proof if that changes), a decision
    count, and their game profile for level/XP.
    """
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

    decision_count = db.query(models.Decision).filter(models.Decision.world_id == world.id).count()
    game_profile = get_or_create_game_profile(profile.id, db)
    level_info = compute_level(game_profile.xp)

    context = {
        "skills": world.state.get("skills", {}),
        "resources": world.state.get("resources", {}),
        "decision_count": decision_count,
        "level": level_info["level"],
    }
    return profile, world, context, game_profile


@router.get("/", response_model=list[schemas.MissionOut])
def list_missions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    profile, _world, context, _game_profile = _get_context(current_user, db)

    claimed_keys = {
        c.mission_key
        for c in db.query(models.MissionClaim).filter(models.MissionClaim.profile_id == profile.id).all()
    }

    results = []
    for template in MISSION_TEMPLATES:
        status = compute_mission_status(template, context)
        status["claimed"] = status["key"] in claimed_keys
        results.append(status)
    return results


@router.post("/{mission_key}/claim", response_model=schemas.MissionClaimResult)
def claim_mission(
    mission_key: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    profile, _world, context, game_profile = _get_context(current_user, db)

    template = next((t for t in MISSION_TEMPLATES if t["key"] == mission_key), None)
    if not template:
        raise HTTPException(status_code=404, detail="No such mission")

    status = compute_mission_status(template, context)
    if not status["completed"]:
        raise HTTPException(status_code=400, detail="Mission not completed yet")

    already_claimed = (
        db.query(models.MissionClaim)
        .filter(models.MissionClaim.profile_id == profile.id, models.MissionClaim.mission_key == mission_key)
        .first()
    )
    if already_claimed:
        raise HTTPException(status_code=409, detail="Mission already claimed")

    claim = models.MissionClaim(profile_id=profile.id, mission_key=mission_key)
    db.add(claim)
    game_profile.xp += template["reward_xp"]
    db.commit()
    db.refresh(game_profile)

    status["claimed"] = True
    return schemas.MissionClaimResult(mission=status, game=_build_out(game_profile))
