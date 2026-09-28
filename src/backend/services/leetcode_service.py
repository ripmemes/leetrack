from typing import Any
import requests

from cache import RedisCache


class LeetCodeService:
    """Service responsible for querying LeetCode GraphQL endpoints and caching responses."""

    LEETCODE_URL = "https://leetcode.com/graphql"

    def __init__(self, cache: RedisCache | None = None) -> None:
        """Initializes LeetCodeService with an optional Redis cache instance.

        Args:
            cache: RedisCache wrapper instance.
        """
        self.cache = cache

    def get_daily_challenge(self) -> dict[str, Any]:
        """Fetches the active daily coding challenge.

        Returns:
            Dictionary containing date, question title, and link.

        Raises:
            RuntimeError: If upstream LeetCode request fails.
        """
        cache_key = "leetcode:daily"
        if self.cache:
            cached = self.cache.get_json(cache_key)
            if cached is not None:
                return cached

        query = """
        query questionOfToday {
            activeDailyCodingChallengeQuestion {
                date
                link
                question {
                    title
                }
            }
        }
        """
        response = requests.post(
            self.LEETCODE_URL,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if not response.ok:
            raise RuntimeError(f"LeetCode daily request failed with {response.status_code}")

        data = response.json()["data"]["activeDailyCodingChallengeQuestion"]
        if self.cache:
            self.cache.set_json(cache_key, data, ttl=600)
        return data

    def get_upcoming_contests(self) -> list[dict[str, Any]]:
        """Fetches upcoming contests from LeetCode.

        Returns:
            List of upcoming contest dictionaries.

        Raises:
            RuntimeError: If upstream LeetCode request fails.
        """
        cache_key = "leetcode:contest"
        if self.cache:
            cached = self.cache.get_json(cache_key)
            if cached is not None:
                return cached

        query = """
        query upcomingContests {
            upcomingContests {
                title
                titleSlug
                startTime
                duration
                __typename
            }
        }
        """
        response = requests.post(
            self.LEETCODE_URL,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if not response.ok:
            raise RuntimeError(f"LeetCode contest request failed with {response.status_code}")

        data = response.json()["data"]["upcomingContests"]
        if self.cache:
            self.cache.set_json(cache_key, data, ttl=600)
        return data

    def get_problems(
        self,
        skip: int = 0,
        limit: int = 15,
        difficulties: list[str] | None = None,
        languages: list[str] | None = None,
        topics: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetches filtered problems list from LeetCode.

        Args:
            skip: Number of questions to skip.
            limit: Number of questions to return.
            difficulties: List of problem difficulties (e.g. EASY, MEDIUM).
            languages: List of language slugs.
            topics: List of topic slugs.

        Returns:
            Dictionary containing question list and pagination info.
        """
        diff_list = difficulties or []
        lang_list = languages or []
        topic_list = topics or []

        cache_key = (
            f"leetcode:problems:skip={skip}:limit={limit}:"
            f"diff={','.join(diff_list)}:lang={','.join(lang_list)}:top={','.join(topic_list)}"
        )
        if self.cache:
            cached = self.cache.get_json(cache_key)
            if cached is not None:
                return cached

        filters: dict[str, Any] = {
            "filterCombineType": "ALL",
            "difficultyFilter": {"difficulties": [d.upper() for d in diff_list], "operator": "IS"},
            "languageFilter": {"languageSlugs": [l.lower() for l in lang_list], "operator": "IS"},
            "topicFilter": {"topicSlugs": [t.lower() for t in topic_list], "operator": "IS"},
        }
        variables = {
            "categorySlug": "all-code-essentials",
            "filters": filters,
            "filtersV2": filters,
            "limit": limit,
            "skip": skip,
            "searchKeyword": "",
            "sortBy": {"sortField": "CUSTOM", "sortOrder": "ASCENDING"},
        }
        query = """
        query problemsetQuestionListV2($filters: QuestionFilterInput, $limit: Int, $skip: Int, $sortBy: QuestionSortByInput, $categorySlug: String, $searchKeyword: String) {
          problemsetQuestionListV2(
            filters: $filters
            limit: $limit
            skip: $skip
            sortBy: $sortBy
            categorySlug: $categorySlug
            searchKeyword: $searchKeyword
          ) {
            questions {
              questionFrontendId
              title
              difficulty
            }
            hasMore
          }
        }
        """
        response = requests.post(
            self.LEETCODE_URL,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()["data"]["problemsetQuestionListV2"]

        if self.cache:
            self.cache.set_json(cache_key, data, ttl=600)
        return data
