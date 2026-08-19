from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.simulation.engine import project_whatif

router = APIRouter(prefix="/whatif", tags=["whatif"])


@router.post("/", response_model=schemas.WhatIfOut)
def explore_whatif(payload: schemas.WhatIfRequest, db: Session = Depends(get_db)):
    world = db.get(models.World, payload.world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

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
def get_whatif_history(world_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.WhatIfBranch)
        .filter(models.WhatIfBranch.world_id == world_id)
        .order_by(models.WhatIfBranch.created_at)
        .all()
    )
