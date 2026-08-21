"""
XP / Level curve - Section 15 Game Layer.

Levels get progressively more expensive: level N costs
(500 + (N-1)*250) XP to clear. This is intentionally simple and
transparent - a player can predict how much further they have to go.

XP itself is never stored per-level - only total lifetime XP is
stored on GameProfile.xp. Level and progress-into-level are always
*derived* from that single number, so there's no way for level and
XP to drift out of sync.
"""

BASE_LEVEL_COST = 500
LEVEL_COST_STEP = 250


def cost_for_level(level: int) -> int:
    """XP required to go from `level` to `level + 1`."""
    return BASE_LEVEL_COST + (level - 1) * LEVEL_COST_STEP


def compute_level(total_xp: int) -> dict:
    """
    Given lifetime XP, derive current level and progress into it.
    """
    level = 1
    remaining = total_xp
    while remaining >= cost_for_level(level):
        remaining -= cost_for_level(level)
        level += 1

    xp_for_next = cost_for_level(level)
    progress_pct = int((remaining / xp_for_next) * 100) if xp_for_next else 0

    return {
        "level": level,
        "xp_total": total_xp,
        "xp_into_level": remaining,
        "xp_for_next_level": xp_for_next,
        "progress_pct": progress_pct,
    }


def xp_for_decision(state_delta: dict) -> int:
    """
    Award XP for a committed decision. Base amount for participating,
    plus a bonus for positive growth - so decisions that build skills
    or resources earn more, but no decision earns zero.

    Deliberately does NOT penalize negative deltas - the point is to
    reward engaging with the simulation, not to punish setbacks that
    were part of a reasonable choice.
    """
    base = 25
    growth_bonus = 0
    for bucket in ("skills", "resources"):
        for _, delta in state_delta.get(bucket, {}).items():
            if delta > 0:
                growth_bonus += delta * 5
    return base + growth_bonus
