from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.simulation.engine import new_world_state
from app.simulation.narrative import generate_situation

router = APIRouter(prefix="/world", tags=["world"])


@router.post("/generate/{profile_id}", response_model=schemas.WorldOut)
def generate_world(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(models.UserProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    world = models.World(
        user_id=profile.id,
        goal=profile.goal,
        state=new_world_state(),
    )
    db.add(world)
    db.commit()
    db.refresh(world)
    return world


@router.get("/{world_id}", response_model=schemas.WorldOut)
def get_world(world_id: int, db: Session = Depends(get_db)):
    world = db.get(models.World, world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world


@router.get("/{world_id}/situation")
def get_next_situation(world_id: int, db: Session = Depends(get_db)):
    world = db.get(models.World, world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return generate_situation(world.goal, world.state.get("skills", {}))
