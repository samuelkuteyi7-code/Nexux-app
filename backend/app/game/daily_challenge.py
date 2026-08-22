"""
Daily Challenge - Section 15 Game Layer.

One challenge per UTC calendar day, the same challenge for every
user that day (deterministic rotation by day-of-year - simple and
requires no per-user randomness/seeding). Progress is computed
against decisions actually made *today*, using each Decision row's
state_delta (already stored) and created_at timestamp - no new
per-decision bookkeeping needed.
"""

from datetime import date

DAILY_TEMPLATES = [
    {
        "key": "make_1_decision_today",
        "title": "Show Up Today",
        "description": "Make at least 1 decision today.",
        "reward_xp": 75,
        "compute": lambda ctx: (ctx["decisions_today_count"], 1),
    },
    {
        "key": "make_2_decisions_today",
        "title": "Keep Moving",
        "description": "Make 2 decisions today.",
        "reward_xp": 100,
        "compute": lambda ctx: (ctx["decisions_today_count"], 2),
    },
    {
        "key": "gain_10_skill_today",
        "title": "Sharpen Up",
        "description": "Gain 10 total skill points today.",
        "reward_xp": 100,
        "compute": lambda ctx: (ctx["skill_gain_today"], 10),
    },
    {
        "key": "gain_100_money_today",
        "title": "Earn Today",
        "description": "Gain 100 money today.",
        "reward_xp": 100,
        "compute": lambda ctx: (ctx["money_gain_today"], 100),
    },
]


def todays_template(today: date) -> dict:
    index = today.timetuple().tm_yday % len(DAILY_TEMPLATES)
    return DAILY_TEMPLATES[index]


def build_daily_context(decisions_today: list[dict]) -> dict:
    """
    decisions_today: list of Decision.state_delta dicts (already the
    engine's applied-delta audit trail) for decisions made today.
    """
    skill_gain = 0
    money_gain = 0
    for delta in decisions_today:
        for _, v in delta.get("skills", {}).items():
            if v > 0:
                skill_gain += v
        money_delta = delta.get("resources", {}).get("money", 0)
        if money_delta > 0:
            money_gain += money_delta

    return {
        "decisions_today_count": len(decisions_today),
        "skill_gain_today": skill_gain,
        "money_gain_today": money_gain,
    }


def compute_daily_status(template: dict, context: dict) -> dict:
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
