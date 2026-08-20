"""
Real AI narrative generation - Section 6 & 10 of the Master Spec.

Calls the Claude API to generate a personalized situation for the
user's goal/skills, in the same shape narrative.py's templates use,
so nothing else in the app has to change.

CORE PRINCIPLE (unchanged from narrative.py): this module only
proposes a situation + effect numbers. It never touches World.state
directly - engine.apply_decision() remains the only place real
numbers change. If the AI proposes wild numbers, engine.py's clamp()
still protects the simulation.

Requires the ANTHROPIC_API_KEY environment variable. If it's not
set, or the call fails for any reason, the caller should fall back
to the templates in narrative.py - see generate_situation() there.
"""

import json
import os

from anthropic import Anthropic

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """You generate a single short scenario for a life-simulation \
app called NEXUS. The user has a stated goal and current skills. Invent one \
realistic, specific situation relevant to their goal, with exactly two \
options to choose between.

Respond with ONLY valid JSON, no other text, in this exact shape:
{
  "situation": "<1-2 sentence description of what's happening>",
  "options": {
    "<short_option_key_1>": {
      "skills": {"<skill_name>": <integer delta, can be negative>},
      "resources": {"money": <integer delta>, "energy": <integer delta>},
      "log_entry": "<1 sentence describing what happened after choosing this>"
    },
    "<short_option_key_2>": {
      "skills": {...},
      "resources": {...},
      "log_entry": "..."
    }
  }
}

Option keys should be short lowercase_with_underscores, like "accept_offer" \
or "decline". Keep skill/resource deltas realistic and modest (skills: -10 \
to +10, money: -500 to +500, energy: -30 to +20)."""


def generate_situation_ai(goal: str, skills: dict) -> dict | None:
    """
    Returns a situation dict in the same shape as narrative.py's templates,
    or None if the API key is missing or the call/parse fails - callers
    should fall back to templates in that case.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    client = Anthropic(api_key=api_key)

    skills_desc = ", ".join(f"{k}: {v}" for k, v in skills.items()) or "none yet"
    user_prompt = f"User's goal: {goal}\nCurrent skills: {skills_desc}"

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw_text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        parsed = json.loads(raw_text)

        if "situation" not in parsed or "options" not in parsed:
            return None
        if len(parsed["options"]) < 2:
            return None

        return parsed
    except Exception:
        return None
