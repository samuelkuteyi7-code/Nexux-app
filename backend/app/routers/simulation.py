from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.routers.world import _get_owned_world
from app.routers.game import get_or_create_game_profile
from app.simulation.engine import apply_decision
from app.game.leveling import xp_for_decision

router = APIRouter(prefix="/decision", tags=["decision"])


@router.post("/", response_model=schemas.DecisionOut)
def make_decision(
    payload: schemas.DecisionChoice,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Commit a decision to a world. This is the only place real world
    state changes - going through the simulation engine's fixed rules,
    never directly from AI output. Also the only place XP is awarded -
    every committed decision earns something, per app/game/leveling.py.
    """
    world = _get_owned_world(payload.world_id, current_user, db)

    new_state, delta = apply_decision(world.state, payload.option_effects)
    world.state = new_state
    flag_modified(world, "state")

    xp_earned = xp_for_decision(delta)
    game_profile = get_or_create_game_profile(world.owner.id, db)
    game_profile.xp += xp_earned

    decision = models.Decision(
        world_id=world.id,
        situation=payload.situation,
        choice=payload.choice_key,
        consequence=payload.option_effects.get("log_entry", ""),
        state_delta=delta,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)

    result = schemas.DecisionOut.model_validate(decision)
    result.xp_earned = xp_earned
    return result


@router.get("/world/{world_id}", response_model=list[schemas.DecisionOut])
def get_decision_history(
    world_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_owned_world(world_id, current_user, db)  # ownership check
    return (
        db.query(models.Decision)
        .filter(models.Decision.world_id == world_id)
        .order_by(models.Decision.created_at)
        .all()
    )
