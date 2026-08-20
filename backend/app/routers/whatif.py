from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.routers.world import _get_owned_world
from app.simulation.engine import project_whatif

router = APIRouter(prefix="/whatif", tags=["whatif"])


@router.post("/", response_model=schemas.WhatIfOut)
def explore_whatif(
    payload: schemas.WhatIfRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Section 11: What If? Scenario Engine. Projects a hypothetical
    outcome WITHOUT touching the real world state.
    """
    world = _get_owned_world(payload.world_id, current_user, db)

    projected_state = project_whatif(world.state, payload.hypothetical_effects, payload.steps)

    branch = models.WhatIfBranch(
        world_id=world.id,
        question=payload.question,
        assumptions=payload.assumptions,
        projected_state=projected_state,
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.get("/world/{world_id}", response_model=list[schemas.WhatIfOut])
def get_whatif_history(
    world_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_owned_world(world_id, current_user, db)  # ownership check
    return (
        db.query(models.WhatIfBranch)
        .filter(models.WhatIfBranch.world_id == world_id)
        .order_by(models.WhatIfBranch.created_at)
        .all()
    )
