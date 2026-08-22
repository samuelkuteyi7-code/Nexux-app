from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.chat.ai_chat import generate_chat_reply

router = APIRouter(prefix="/chat", tags=["chat"])


def _get_profile_and_skills(current_user: models.User, db: Session):
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
    return profile, skills


@router.get("/", response_model=list[schemas.ChatMessageOut])
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    profile, _skills = _get_profile_and_skills(current_user, db)
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.profile_id == profile.id)
        .order_by(models.ChatMessage.created_at)
        .all()
    )


@router.post("/", response_model=schemas.ChatSendResponse)
def send_chat_message(
    payload: schemas.ChatSendRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    profile, skills = _get_profile_and_skills(current_user, db)

    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    prior_messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.profile_id == profile.id)
        .order_by(models.ChatMessage.created_at)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in prior_messages]

    reply_text = generate_chat_reply(profile.goal, skills, history, payload.message)
    if reply_text is None:
        reply_text = (
            "NEXUS AI chat isn't fully configured yet - the server needs an "
            "ANTHROPIC_API_KEY set to have real conversations. Everything else "
            "in the app still works."
        )

    user_msg = models.ChatMessage(profile_id=profile.id, role="user", content=payload.message)
    assistant_msg = models.ChatMessage(profile_id=profile.id, role="assistant", content=reply_text)
    db.add(user_msg)
    db.add(assistant_msg)
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    return schemas.ChatSendResponse(user_message=user_msg, assistant_message=assistant_msg)
