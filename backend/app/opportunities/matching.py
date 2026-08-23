"""
Matches real job listings against the user's actual profile data
(interests, goal, skills) - Section 11: "Matching: Opportunities can
be matched against the user's actual qualifications and interests."

Deliberately simple and transparent: keyword overlap between the
user's real profile terms and each listing's real title/description/
tags. No black-box scoring - the percentage is directly explainable
by which words matched.
"""

import re


def _extract_words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


STOPWORDS = {
    "a", "an", "the", "and", "or", "to", "of", "in", "for", "with", "on",
    "my", "i", "want", "become", "build", "get", "make", "learn", "is", "am",
}


def build_profile_keywords(interests: list[str], goal: str, skills: dict) -> set[str]:
    words = set()
    for interest in interests:
        words |= _extract_words(interest)
    words |= _extract_words(goal)
    for skill_name in skills.keys():
        words |= _extract_words(skill_name)
    return words - STOPWORDS


def compute_match_pct(profile_keywords: set[str], job: dict) -> int:
    job_text = f"{job.get('title', '')} {job.get('description', '')} {' '.join(job.get('tags', []))}"
    job_words = _extract_words(job_text) - STOPWORDS
    if not profile_keywords or not job_words:
        return 0

    overlap = profile_keywords & job_words
    pct = int((len(overlap) / len(profile_keywords)) * 100)
    return min(100, pct)
