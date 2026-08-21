"""
Missions - Section 15 Game Layer.

Mission *definitions* are static Python data, not a database table -
there's no admin/CMS need for the MVP, and keeping them in code means
progress can be computed directly against real simulation/game data
with no separate "mission progress" table to keep in sync.

What IS stored in the database (see MissionClaim in models.py) is
only the fact that a user has claimed a completed mission's reward -
that's the one piece of state that can't be derived from anything
else, since claiming is a one-time action.

Each template's `compute` function takes a `context` dict:
    {
        "skills": dict,       # world.state["skills"]
        "resources": dict,    # world.state["resources"]
        "decision_count": int,
        "level": int,
    }
and returns (current_value, target_value).
"""

MISSION_TEMPLATES = [
    {
        "key": "make_3_decisions",
        "title": "Get Moving",
        "description": "Make 3 decisions in your world.",
        "reward_xp": 100,
        "compute": lambda ctx: (ctx["decision_count"], 3),
    },
    {
        "key": "make_10_decisions",
        "title": "Stay Consistent",
        "description": "Make 10 decisions in your world.",
        "reward_xp": 250,
        "compute": lambda ctx: (ctx["decision_count"], 10),
    },
    {
        "key": "reach_level_3",
        "title": "Level Up",
        "description": "Reach Level 3.",
        "reward_xp": 150,
        "compute": lambda ctx: (ctx["level"], 3),
    },
    {
        "key": "reach_level_5",
        "title": "Rising Star",
        "description": "Reach Level 5.",
        "reward_xp": 300,
        "compute": lambda ctx: (ctx["level"], 5),
    },
    {
        "key": "any_skill_25",
        "title": "Sharpen a Skill",
        "description": "Get any single skill to 25.",
        "reward_xp": 150,
        "compute": lambda ctx: (max(ctx["skills"].values(), default=0), 25),
    },
    {
        "key": "save_1500_money",
        "title": "Build Your Savings",
        "description": "Reach 1,500 money.",
        "reward_xp": 150,
        "compute": lambda ctx: (ctx["resources"].get("money", 0), 1500),
    },
]


def compute_mission_status(template: dict, context: dict) -> dict:
    current, target = template["compute"](context)
    current = max(0, current)
    progress_pct = min(100, int((current / target) * 100)) if target else 0
    return {
        "key": template["key"],
        "title": template["title"],
        "description": template["description"],
        "reward_xp": template["reward_xp"],
        "current": current,
        "target": target,
        "progress_pct": progress_pct,
        "completed": current >= target,
    }
