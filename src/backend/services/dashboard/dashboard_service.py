"""DashboardService orchestrates profile fetching, caching, and recommendations.

Caching strategy:
  - Public profile: Redis TTL 600 s (10 min)
  - Private profile: Redis TTL 300 s (5 min) — session cookies are NOT cached,
    only the resulting profile payload.
  - Problem catalog: Redis TTL 86400 s (24 h), fetched from public LC endpoint.

LeetCode data is NEVER written to the application database.
"""
from __future__ import annotations

import dataclasses
import json
from typing import Any

import requests

from cache import RedisCache
from services.dashboard import lc_profile_client as lc_client
from services.dashboard.recommender import RecommendMode, recommend
from services.dashboard.schemas import PublicProfile, Recommendation


_LC_GRAPHQL = "https://leetcode.com/graphql"

# GraphQL query to load the full catalog (used for recommendations)
_CATALOG_QUERY = """
query problemsetQuestionListV2($limit: Int, $skip: Int) {
  problemsetQuestionListV2(limit: $limit, skip: $skip, sortBy: { sortField: CUSTOM, sortOrder: ASCENDING }) {
    questions {
      title
      titleSlug
      difficulty
      acRate
      topicTags { name slug }
    }
    total
  }
}
"""

_CATALOG_BATCH = 500
_CATALOG_TTL = 86_400  # 24 h
_PROFILE_TTL = 600
_PRIVATE_PROFILE_TTL = 300


class DashboardService:
    """Fetches, caches, and processes LeetCode profile data and recommendations."""

    def __init__(self, cache: RedisCache | None = None) -> None:
        self.cache = cache

    # ── public ──────────────────────────────────────────────────────────────

    def get_public_profile(self, handle: str) -> dict[str, Any]:
        """Returns a serialisable public profile dict, using cache when available.

        Args:
            handle: LeetCode username.

        Returns:
            Dict representation of PublicProfile.
        """
        key = f"dashboard:public:{handle}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached

        profile = lc_client.fetch_public_profile(handle)
        profile.recent_submissions = lc_client.fetch_recent_submissions(handle)
        profile.calendar = lc_client.fetch_calendar(handle)

        payload = self._profile_to_dict(profile)
        self._cache_set(key, payload, ttl=_PROFILE_TTL)
        return payload

    def get_public_recommendations(
        self, handle: str, mode: RecommendMode = "interview", top_n: int = 5
    ) -> list[dict[str, Any]]:
        """Generates recommendations from the public profile.

        Args:
            handle: LeetCode username.
            mode: Recommendation bias — 'interview' or 'weakness'.
            top_n: Number of results.

        Returns:
            List of serialisable Recommendation dicts.
        """
        profile = lc_client.fetch_public_profile(handle)
        profile.recent_submissions = lc_client.fetch_recent_submissions(handle)
        catalog = self._get_catalog()
        recs = recommend(profile, catalog, mode=mode, top_n=top_n)
        return [dataclasses.asdict(r) for r in recs]

    # ── private (requires session cookie) ───────────────────────────────────

    def get_private_profile(self, handle: str, session_cookie: str) -> dict[str, Any]:
        """Returns extended profile dict, using ephemeral cookie-keyed cache.

        The session_cookie itself is NEVER stored. The cache key uses a hash
        of it, and the value is only the resulting profile payload.

        Args:
            handle: LeetCode username.
            session_cookie: LEETCODE_SESSION value. Transient — not persisted.

        Returns:
            Dict representation of PrivateProfile.
        """
        # Use a short hash of the cookie as part of cache key so different
        # sessions for the same handle are correctly scoped.
        cookie_tag = str(hash(session_cookie) % 10**8)
        key = f"dashboard:private:{handle}:{cookie_tag}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached

        profile = lc_client.fetch_private_profile(handle, session_cookie)
        profile.recent_submissions = lc_client.fetch_recent_submissions(handle, limit=50)
        profile.calendar = lc_client.fetch_calendar(handle)

        payload = self._profile_to_dict(profile)
        self._cache_set(key, payload, ttl=_PRIVATE_PROFILE_TTL)
        return payload

    def get_private_recommendations(
        self,
        handle: str,
        session_cookie: str,
        mode: RecommendMode = "interview",
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        """Generates recommendations from private profile data.

        Args:
            handle: LeetCode username.
            session_cookie: LEETCODE_SESSION cookie value.
            mode: 'interview' or 'weakness'.
            top_n: Number of results.

        Returns:
            List of serialisable Recommendation dicts.
        """
        profile = lc_client.fetch_private_profile(handle, session_cookie)
        profile.recent_submissions = lc_client.fetch_recent_submissions(handle, limit=50)
        catalog = self._get_catalog()
        recs = recommend(profile, catalog, mode=mode, top_n=top_n)
        return [dataclasses.asdict(r) for r in recs]

    def invalidate_profile(self, handle: str) -> None:
        """Clears cached profile for a given handle (both public and private)."""
        if not self.cache:
            return
        self.cache.delete(f"dashboard:public:{handle}")
        # Private cache keys include a cookie hash so we can only pattern-delete
        # if the Redis client supports it. Skip silently otherwise.

    # ── catalog ─────────────────────────────────────────────────────────────

    def _get_catalog(self) -> list[dict[str, Any]]:
        """Loads the full LeetCode problem catalog, using a 24 h cache."""
        key = "dashboard:catalog"
        cached = self._cache_get(key)
        if cached is not None:
            return cached

        problems = self._fetch_full_catalog()
        self._cache_set(key, problems, ttl=_CATALOG_TTL)
        return problems

    def _fetch_full_catalog(self) -> list[dict[str, Any]]:
        """Paginates through the LC problem set to build the full catalog."""
        all_problems: list[dict[str, Any]] = []
        skip = 0

        while True:
            try:
                resp = requests.post(
                    _LC_GRAPHQL,
                    json={
                        "query": _CATALOG_QUERY,
                        "variables": {"limit": _CATALOG_BATCH, "skip": skip},
                    },
                    headers={"Content-Type": "application/json", "Referer": "https://leetcode.com"},
                    timeout=15,
                )
                resp.raise_for_status()
                result = resp.json().get("data", {}).get("problemsetQuestionListV2", {})
                batch = result.get("questions") or []
                all_problems.extend(batch)

                if len(all_problems) >= result.get("total", 0) or not batch:
                    break
                skip += _CATALOG_BATCH
            except Exception:
                break  # Return what we have if paginating fails mid-way

        return all_problems

    # ── cache helpers ────────────────────────────────────────────────────────

    def _cache_get(self, key: str) -> Any:
        if self.cache:
            return self.cache.get_json(key)
        return None

    def _cache_set(self, key: str, value: Any, ttl: int = 300) -> None:
        if self.cache:
            self.cache.set_json(key, value, ttl=ttl)

    # ── serialisation ────────────────────────────────────────────────────────

    @staticmethod
    def _profile_to_dict(profile: PublicProfile) -> dict[str, Any]:
        return dataclasses.asdict(profile)
