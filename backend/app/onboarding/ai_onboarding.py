"""
Conversational onboarding - Section 2-5 of NEXUS_Conversation_to_Game_System:
"The conversation becomes the character-creation system." The user talks
naturally; NEXUS extracts a structured User World Model from it; that
model becomes the profile/goal that generates their world.

This is stateless on the backend by design - the frontend keeps the
running conversation and sends the whole history each turn. There's
no profile yet at this point (this happens BEFORE profile creation),
so there's nothing meaningful to persist server-side until the user
confirms and a profile actually gets created.

Every turn asks Claude for strict JSON (same pattern as
app/simulation/ai_narrative.py) rather than free text with a hidden
marker - much harder for parsing to silently break.
"""

import json
import os

from anthropic import Anthropic

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """You are NEXUS's onboarding conversation. Your job is to get \
to know a new user the way a thoughtful friend would - not a form. Ask about \
their background, what they're interested in, what they want to achieve, and \
any real constraints or uncertainty they have (time, money, indecision between \
paths, etc). Ask ONE natural follow-up question at a time. Keep replies warm \
and short (1-3 sentences).

Once you have a reasonable picture - usually after 2-4 user replies covering \
at least their background/interests AND a goal - stop asking questions and \
set ready_to_build to true.

Respond with ONLY valid JSON, no other text, in this exact shape:
{
  "reply": "<what to say to the user right now - a question, or a closing summary line if ready>",
  "ready_to_build": <true or false>,
  "user_world_model": null OR {
    "education_or_background": "<short phrase>",
    "interests": ["<interest>", ...],
    "primary_goal": "<a single clear sentence describing their main goal>",
    "background_summary": "<1-2 sentence summary covering constraints/uncertainty/context>"
  }
}

user_world_model MUST be null while ready_to_build is false. Once
ready_to_build is true, user_world_model MUST be fully populated."""


def generate_onboarding_turn(history: list[dict], new_message: str) -> dict | None:
    """
    history: list of {"role": "user"|"assistant", "content": str}, oldest first.
    Returns the parsed dict (reply / ready_to_build / user_world_model),
    or None if the API key is missing or the call/parse fails - the
    caller should fall back to the manual goal-form in that case.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    client = Anthropic(api_key=api_key)
    messages = history + [{"role": "user", "content": new_message}]

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        raw_text = "".join(block.text for block in response.content if block.type == "text")
        parsed = json.loads(raw_text)

        if "reply" not in parsed or "ready_to_build" not in parsed:
            return None
        if parsed["ready_to_build"] and not parsed.get("user_world_model"):
            return None

        return parsed
    except Exception:
        return None
