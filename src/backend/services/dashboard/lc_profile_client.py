"""LeetCode GraphQL client for user profile data.

Public queries: only need a username.
Private queries: require a LEETCODE_SESSION cookie in the header.

Session cookies are NEVER stored — they are passed per-request and may be
briefly cached in Redis with a short TTL.
"""
from __future__ import annotations

from typing import Any

import requests

from services.dashboard.schemas import (
    ContestInfo,
    PrivateProfile,
    PublicProfile,
    RecentSubmission,
    SolvedStats,
    TopicStat,
)

_LC_GRAPHQL = "https://leetcode.com/graphql"
_TIMEOUT = 10

# ── shared helpers ──────────────────────────────────────────────────────────

def _post(query: str, variables: dict, session_cookie: str | None = None) -> dict[str, Any]:
    """Executes a LeetCode GraphQL POST.

    Args:
        query: GraphQL query string.
        variables: Query variables dict.
        session_cookie: LEETCODE_SESSION value. Included in Cookie header when provided.

    Returns:
        Parsed JSON response dict.

    Raises:
        RuntimeError: On non-2xx responses or network errors.
    """
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com",
    }
    if session_cookie:
        headers["Cookie"] = f"LEETCODE_SESSION={session_cookie}"

    try:
        resp = requests.post(
            _LC_GRAPHQL,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"LeetCode request error: {exc}") from exc

    if not resp.ok:
        raise RuntimeError(f"LeetCode API returned {resp.status_code}")

    return resp.json()


# ── public queries ───────────────────────────────────────────────────────────

_PUBLIC_PROFILE_QUERY = """
query publicProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      realName
      userAvatar
      ranking
    }
    submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
    }
    tagProblemCounts {
      advanced { tagName tagSlug problemsSolved }
      intermediate { tagName tagSlug problemsSolved }
      fundamental { tagName tagSlug problemsSolved }
    }
  }
  userContestRanking(username: $username) {
    rating
    globalRanking
    attendedContestsCount
  }
}
"""

_RECENT_AC_QUERY = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    title
    titleSlug
    timestamp
  }
}
"""

_CALENDAR_QUERY = """
query userCalendar($username: String!, $year: Int) {
  matchedUser(username: $username) {
    userCalendar(year: $year) {
      submissionCalendar
    }
  }
}
"""


def fetch_public_profile(handle: str) -> PublicProfile:
    """Fetches a user's public profile data (no auth required).

    Args:
        handle: LeetCode username.

    Returns:
        Populated PublicProfile dataclass.
    """
    data = _post(_PUBLIC_PROFILE_QUERY, {"username": handle})
    return _parse_public_profile(handle, data)


def fetch_recent_submissions(handle: str, limit: int = 20) -> list[RecentSubmission]:
    """Fetches recent accepted submissions (public endpoint).

    Args:
        handle: LeetCode username.
        limit: Max number of submissions to fetch.

    Returns:
        List of RecentSubmission objects.
    """
    data = _post(_RECENT_AC_QUERY, {"username": handle, "limit": limit})
    raw_list = data.get("data", {}).get("recentAcSubmissionList") or []
    return [
        RecentSubmission(
            title=s["title"],
            title_slug=s["titleSlug"],
            timestamp=s["timestamp"],
        )
        for s in raw_list
    ]


def fetch_calendar(handle: str, year: int | None = None) -> dict:
    """Fetches the submission calendar heatmap data (public endpoint).

    Args:
        handle: LeetCode username.
        year: Calendar year. Defaults to current year (LC default).

    Returns:
        Dict mapping date strings to submission counts.
    """
    variables: dict[str, Any] = {"username": handle}
    if year is not None:
        variables["year"] = year

    data = _post(_CALENDAR_QUERY, variables)
    raw = (
        data.get("data", {})
        .get("matchedUser", {})
        .get("userCalendar", {})
        .get("submissionCalendar", "{}")
    )
    import json
    return json.loads(raw) if isinstance(raw, str) else {}


# ── private queries ──────────────────────────────────────────────────────────

_FULL_PROFILE_QUERY = """
query fullProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile { realName userAvatar ranking }
    submitStatsGlobal {
      acSubmissionNum { difficulty count }
    }
    tagProblemCounts {
      advanced { tagName tagSlug problemsSolved }
      intermediate { tagName tagSlug problemsSolved }
      fundamental { tagName tagSlug problemsSolved }
    }
  }
  userContestRanking(username: $username) {
    rating
    globalRanking
    attendedContestsCount
  }
}
"""


def fetch_private_profile(handle: str, session_cookie: str) -> PrivateProfile:
    """Fetches profile data using a LEETCODE_SESSION cookie for private data.

    Args:
        handle: LeetCode username.
        session_cookie: Value of LEETCODE_SESSION cookie. Never stored.

    Returns:
        Populated PrivateProfile dataclass.
    """
    data = _post(_FULL_PROFILE_QUERY, {"username": handle}, session_cookie=session_cookie)
    public = _parse_public_profile(handle, data)
    return PrivateProfile(
        handle=public.handle,
        real_name=public.real_name,
        avatar_url=public.avatar_url,
        ranking=public.ranking,
        solved_stats=public.solved_stats,
        topic_stats=public.topic_stats,
        contest_info=public.contest_info,
        recent_submissions=public.recent_submissions,
        calendar=public.calendar,
    )


# ── parsing helpers ───────────────────────────────────────────────────────────

def _parse_public_profile(handle: str, data: dict) -> PublicProfile:
    user = data.get("data", {}).get("matchedUser") or {}
    profile = user.get("profile") or {}

    # solved counts
    ac_nums = user.get("submitStatsGlobal", {}).get("acSubmissionNum") or []
    counts = {s["difficulty"]: s["count"] for s in ac_nums}
    solved = SolvedStats(
        easy=counts.get("Easy", 0),
        medium=counts.get("Medium", 0),
        hard=counts.get("Hard", 0),
    )

    # topic stats (flatten all categories)
    tag_groups = user.get("tagProblemCounts") or {}
    topics: list[TopicStat] = []
    for group in ("fundamental", "intermediate", "advanced"):
        for tag in tag_groups.get(group) or []:
            if tag["problemsSolved"] > 0:
                topics.append(
                    TopicStat(
                        slug=tag["tagSlug"],
                        name=tag["tagName"],
                        solved=tag["problemsSolved"],
                    )
                )

    # contest info
    contest_raw = data.get("data", {}).get("userContestRanking")
    contest = None
    if contest_raw:
        contest = ContestInfo(
            rating=contest_raw.get("rating", 0.0),
            ranking=contest_raw.get("globalRanking", 0),
            attended=contest_raw.get("attendedContestsCount", 0),
        )

    return PublicProfile(
        handle=handle,
        real_name=profile.get("realName", ""),
        avatar_url=profile.get("userAvatar", ""),
        ranking=profile.get("ranking", 0),
        solved_stats=solved,
        topic_stats=topics,
        contest_info=contest,
    )
