"""
NEXUS AI - the general assistant chat, separate from the situation
flow (Section 6: "AI Engine: Conversation, characters, narrative,
scenario assistance and explanations").

Unlike narrative.py (which generates structured JSON situations),
this is free-form conversation - the AI is a mentor/sounding board
the user can talk to about their goal, decisions, or anything else.
It never changes World.state itself; it's purely conversational.

Requires ANTHROPIC_API_KEY. If missing or the call fails, returns
None so the caller can show a clear, honest message instead of
crashing or inventing a fake reply.
"""

import os

from anthropic import Anthropic

MODEL = "claude-sonnet-5"
MAX_HISTORY_MESSAGES = 20  # keep token usage bounded on long conversations


def build_system_prompt(goal: str, skills: dict) -> str:
    skills_desc = ", ".join(f"{k}: {v}" for k, v in skills.items()) or "none developed yet"
    return f"""You are NEXUS AI, a supportive, direct mentor inside the NEXUS app. \
The user is working toward this goal: {goal}. Their current skills: {skills_desc}.

Help them think through decisions, plans, and doubts related to their goal and \
simulated world. Keep replies conversational and concise (2-4 short paragraphs \
at most). Be encouraging but honest - don't just validate everything; give real \
perspective when it's useful. You are not the same system as the situation cards \
in their simulation - you're a free-form conversation partner."""


def generate_chat_reply(goal: str, skills: dict, history: list[dict], new_message: str) -> str | None:
    """
    history: list of {"role": "user"|"assistant", "content": str}, oldest first.
    Returns the assistant's reply text, or None on any failure.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    client = Anthropic(api_key=api_key)
    trimmed_history = history[-MAX_HISTORY_MESSAGES:]
    messages = trimmed_history + [{"role": "user", "content": new_message}]

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=600,
            system=build_system_prompt(goal, skills),
            messages=messages,
        )
        return "".join(block.text for block in response.content if block.type == "text").strip() or None
    except Exception:
        return None
