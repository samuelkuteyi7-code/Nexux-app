from fastapi import APIRouter, Depends, HTTPException

from app import models, schemas
from app.auth import get_current_user
from app.onboarding.ai_onboarding import generate_onboarding_turn

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/chat", response_model=schemas.OnboardingChatResponse)
def onboarding_chat(
    payload: schemas.OnboardingChatRequest,
    current_user: models.User = Depends(get_current_user),
):
    """
    Stateless conversational turn - see ai_onboarding.py. Requires
    login (so it can't be used as a free public AI proxy) but not a
    profile, since the whole point is this runs BEFORE one exists.
    """
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    history = [{"role": m.role, "content": m.content} for m in payload.history]
    result = generate_onboarding_turn(history, payload.message)

    if result is None:
        return schemas.OnboardingChatResponse(
            reply=(
                "Conversational onboarding isn't available right now "
                "(the server needs an ANTHROPIC_API_KEY, or something went "
                "wrong). You can still set up your world with the quick form instead."
            ),
            ready_to_build=False,
            user_world_model=None,
            ai_available=False,
        )

    return schemas.OnboardingChatResponse(
        reply=result["reply"],
        ready_to_build=result["ready_to_build"],
        user_world_model=result.get("user_world_model"),
        ai_available=True,
    )
