"""
AI Layer - Section 6 & 10 of the Master Spec.

Responsibility: conversation, narrative, character flavor, and
*proposing* possible situations/effects. It does NOT apply numbers
directly to world state - engine.py does that.

Tries a real Claude API call first (see ai_narrative.py). If no
ANTHROPIC_API_KEY is set, or the call fails for any reason, falls
back to the templates below - the app always keeps working either
way.
"""

import random

from app.simulation.ai_narrative import generate_situation_ai

SITUATION_TEMPLATES = [
    {
        "situation": "You've been offered a part-time internship that overlaps with your coursework.",
        "options": {
            "accept": {
                "skills": {"coding": 5},
                "resources": {"money": 300, "energy": -15},
                "log_entry": "You took the internship and learned fast, but it cost you energy and study time.",
            },
            "decline": {
                "skills": {},
                "resources": {"energy": 5},
                "log_entry": "You declined the internship to focus on your studies.",
            },
        },
    },
    {
        "situation": "A friend proposes starting a small side project together.",
        "options": {
            "join": {
                "skills": {"networking": 4, "coding": 2},
                "resources": {"money": -50, "energy": -10},
                "log_entry": "You joined the side project. It's early, but you're building something.",
            },
            "pass": {
                "skills": {},
                "resources": {},
                "log_entry": "You passed on the project to keep your schedule light.",
            },
        },
    },
    {
        "situation": "Your savings take an unexpected hit from a surprise expense.",
        "options": {
            "cut_costs": {
                "skills": {},
                "resources": {"money": -100, "energy": -5},
                "log_entry": "You tightened your budget to absorb the expense.",
            },
            "take_freelance_gig": {
                "skills": {"coding": 3},
                "resources": {"money": 50, "energy": -20},
                "log_entry": "You picked up a quick freelance gig to cover the gap.",
            },
        },
    },
]


def generate_situation(goal: str, skills: dict) -> dict:
    """
    Return a situation with named options and their (proposed) effects.
    Tries a real, personalized AI-generated situation first; falls back
    to templates if no API key is set or the call fails. Either way,
    the returned shape is identical and engine.apply_decision() still
    owns every real numeric change.
    """
    ai_situation = generate_situation_ai(goal, skills)
    if ai_situation is not None:
        return ai_situation
    return random.choice(SITUATION_TEMPLATES)
