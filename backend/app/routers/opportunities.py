from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.opportunities.job_apis import fetch_remotive, fetch_arbeitnow
from app.opportunities.matching import build_profile_keywords, compute_match_pct

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("/jobs", response_model=list[schemas.OpportunityOut])
def get_matched_jobs(
    query: str = "",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Standalone from the simulation (spec section 13) - only reads
    UserProfile (interests/goal) and the latest World's skills for
    matching context. Never reads or writes Decision/GameProfile data.

    Pulls REAL listings from Remotive + Arbeitnow (both free, keyless
    public feeds). If both are unreachable, returns an empty list -
    never fabricated results.
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
    skills = world.state.get("skills", {}) if world else {}

    search_query = query.strip() or profile.goal
    jobs = fetch_remotive(search_query) + fetch_arbeitnow(search_query)

    profile_keywords = build_profile_keywords(profile.interests or [], profile.goal, skills)
    results = []
    for job in jobs:
        match_pct = compute_match_pct(profile_keywords, job)
        results.append(schemas.OpportunityOut(
            title=job["title"],
            company=job["company"],
            location=job["location"],
            url=job["url"],
            source=job["source"],
            match_pct=match_pct,
            tags=job.get("tags", [])[:5],
            posted_at=job.get("posted_at"),
        ))

    results.sort(key=lambda r: r.match_pct, reverse=True)
    return results[:20]
