"""
AI Layer - Section 6 & 10 of the Master Spec.

Responsibility: conversation, narrative, character flavor, and
*proposing* possible situations/effects. Does NOT apply numbers
directly - engine.py does that.

Uses simple templates so the app runs with zero external dependencies.
Swap generate_situation to call a real AI API later - keep the
function signature the same.
"""

import random

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
    return random.choice(SITUATION_TEMPLATES)
