from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.database import get_db
from app import models, schemas
from app.simulation.engine import apply_decision

router = APIRouter(prefix="/decision", tags=["decision"])


@router.post("/", response_model=schemas.DecisionOut)
def make_decision(payload: schemas.DecisionChoice, db: Session = Depends(get_db)):
    world = db.get(models.World, payload.world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    new_state, delta = apply_decision(world.state, payload.option_effects)
    world.state = new_state
    flag_modified(world, "state")

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
    return decision


@router.get("/world/{world_id}", response_model=list[schemas.DecisionOut])
def get_decision_history(world_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Decision)
        .filter(models.Decision.world_id == world_id)
        .order_by(models.Decision.created_at)
        .all()
    )
