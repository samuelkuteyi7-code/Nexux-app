"""
Real-World Opportunity Engine - Section 11 & 12 of the spec:
"The system can surface relevant jobs, internships, scholarships,
competitions, freelance work and other legitimate opportunities."

Deliberately standalone from the simulation (per spec section 13) -
this module never touches World/Decision/GameProfile data at all.

MVP SCOPE, stated honestly: this pulls REAL live listings from two
free, no-API-key job feeds (Remotive for remote jobs, Arbeitnow for
a broader board). Scholarships/competitions/freelance work don't have
an equivalent free, keyless public feed, so they are NOT included
here rather than being faked - that's future work, not a shortcut
taken silently.
"""

from datetime import datetime, timezone

import httpx

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"
REQUEST_TIMEOUT = 8.0


def fetch_remotive(query: str) -> list[dict]:
    """Real remote-job listings from remotive.com. Returns [] on any failure."""
    try:
        resp = httpx.get(REMOTIVE_URL, params={"search": query, "limit": 20}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        jobs = resp.json().get("jobs", [])
        results = []
        for j in jobs:
            posted_at = None
            raw_date = j.get("publication_date")
            if raw_date:
                try:
                    posted_at = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S").replace(
                        tzinfo=timezone.utc
                    ).isoformat()
                except ValueError:
                    posted_at = None

            results.append({
                "title": j.get("title", ""),
                "company": j.get("company_name", ""),
                "location": j.get("candidate_required_location", "Remote"),
                "url": j.get("url", ""),
                "description": (j.get("description") or "")[:600],
                "tags": j.get("tags", []) or [],
                "source": "Remotive",
                "posted_at": posted_at,
            })
        return results
    except Exception:
        return []


def fetch_arbeitnow(query: str) -> list[dict]:
    """Real job-board listings from arbeitnow.com. Filters by query client-side
    since the public endpoint doesn't take a search param. Returns [] on failure."""
    try:
        resp = httpx.get(ARBEITNOW_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        jobs = resp.json().get("data", [])
        query_lower = query.lower()
        results = []
        for j in jobs:
            title = j.get("title", "")
            desc = j.get("description", "") or ""
            if query_lower and query_lower not in (title + desc).lower():
                continue

            posted_at = None
            raw_ts = j.get("created_at")
            if raw_ts:
                try:
                    posted_at = datetime.fromtimestamp(raw_ts, tz=timezone.utc).isoformat()
                except (ValueError, OSError, TypeError):
                    posted_at = None

            results.append({
                "title": title,
                "company": j.get("company_name", ""),
                "location": "Remote" if j.get("remote") else (j.get("location") or "Not specified"),
                "url": j.get("url", ""),
                "description": desc[:600],
                "tags": j.get("tags", []) or [],
                "source": "Arbeitnow",
                "posted_at": posted_at,
            })
        return results[:20]
    except Exception:
        return []
