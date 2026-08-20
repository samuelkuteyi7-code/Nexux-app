from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.simulation.engine import new_world_state
from app.simulation.narrative import generate_situation

router = APIRouter(prefix="/world", tags=["world"])


def _get_owned_world(world_id: int, current_user: models.User, db: Session) -> models.World:
    """Fetch a world and verify it belongs to current_user, or raise."""
    world = db.get(models.World, world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.owner.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your world")
    return world


@router.post("/generate/{profile_id}", response_model=schemas.WorldOut)
def generate_world(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Section 8: generate a constrained personalized world for a profile.
    MVP keeps this to one active goal and a starting state - no full
    economy or character roster yet.
    """
    profile = db.get(models.UserProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your profile")

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
def get_world(
    world_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _get_owned_world(world_id, current_user, db)


@router.get("/{world_id}/situation")
def get_next_situation(
    world_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Returns a new situation with options for the user to choose from."""
    world = _get_owned_world(world_id, current_user, db)
    return generate_situation(world.goal, world.state.get("skills", {}))
