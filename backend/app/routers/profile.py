from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("/", response_model=schemas.ProfileOut)
def create_profile(
    payload: schemas.ProfileCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Profile already exists for this account")

    profile = models.UserProfile(**payload.model_dump(), user_id=current_user.id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me", response_model=schemas.ProfileOut)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No profile yet for this account")
    return profile
