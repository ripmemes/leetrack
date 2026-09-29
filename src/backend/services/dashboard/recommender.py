"""In-memory recommendation engine.

Two modes:
  - "interview": weights NeetCode-150 core topics heavily.
  - "weakness": surfaces the user's least-practiced topic categories.

All computation is in-process; nothing is written to the database.
The global problem catalog is pre-vectorised once at module load.
"""
from __future__ import annotations

import dataclasses
from typing import Any, Literal

from services.dashboard.schemas import PublicProfile, Recommendation

RecommendMode = Literal["interview", "weakness"]

# ── NeetCode-150 topic priority list (interview mode) ────────────────────────

_INTERVIEW_PRIORITY: dict[str, int] = {
    "array": 10,
    "two-pointers": 9,
    "sliding-window": 9,
    "stack": 8,
    "binary-search": 8,
    "linked-list": 8,
    "tree": 8,
    "trie": 7,
    "heap-priority-queue": 7,
    "backtracking": 7,
    "graph": 7,
    "dynamic-programming": 9,
    "greedy": 7,
    "intervals": 6,
    "bit-manipulation": 6,
    "math": 5,
    "hash-table": 8,
    "string": 7,
    "sorting": 6,
}

# Difficulty acceptance-rate bands (approximations for ZPD scoring)
# _DIFFICULTY_BASE_ACCEPTANCE = {
#     "Easy": 0.65,
#     "Medium": 0.45,
#     "Hard": 0.25,
# }

_STARTER_SLUGS = {
    "two-sum",
    "valid-palindrome",
    "contains-duplicate",
    "valid-anagram",
    "best-time-to-buy-and-sell-stock",
    "reverse-linked-list",
    "binary-search",
    "climbing-stairs",
}

# ── catalog helpers ───────────────────────────────────────────────────────────

def _topic_slugs(problem: dict[str, Any]) -> list[str]:
    return [t.get("slug", "") for t in problem.get("topicTags", [])]


def _acceptance_rate(problem: dict[str, Any]) -> float:
    raw = problem.get("acRate", 0.0)
    return float(raw) / 100.0 if raw > 1 else float(raw)


# ── scoring ───────────────────────────────────────────────────────────────────

def _topic_need_score(
    topic_slugs: list[str],
    solved_by_topic: dict[str, int],
    mode: RecommendMode,
) -> float:
    """Returns how much the user needs to practice the given topics."""
    if not topic_slugs:
        return 0.0

    scores: list[float] = []
    for slug in topic_slugs:
        solved = solved_by_topic.get(slug, 0)
        if mode == "interview":
            priority = _INTERVIEW_PRIORITY.get(slug, 3)
            # Low solved + high interview priority → high need
            need = priority * (1.0 / (1.0 + solved * 0.1))
        else:  # weakness
            # Purely inverse of how much the user has solved in this topic
            need = 1.0 / (1.0 + solved * 0.15)
        scores.append(need)
    return max(scores)


def _difficulty_fit_score(
    difficulty: str,
    solved_stats_dict: dict[str, int],
) -> float:
    """Returns a score reflecting how appropriate the difficulty is (ZPD).

    Target the difficulty one step above user's comfortable zone.
    """
    easy_count = solved_stats_dict.get("easy", 0)
    med_count = solved_stats_dict.get("medium", 0)

    if difficulty == "easy":
        # Recommend Easy only to beginners
        return 1.0 if easy_count < 20 else 0.3
    if difficulty == "medium":
        # Sweet spot: user has some Easy but not many Mediums
        if easy_count >= 5:
            return 1.0 if med_count < 80 else 0.6
        return 0.4
    if difficulty == "hard":
        return 1.0 if med_count >= 50 else 0.2
    return 0.5


def _score_problem(
    problem: dict[str, Any],
    solved_by_topic: dict[str, int],
    solved_stats_dict: dict[str, int],
    mode: RecommendMode,
) -> float:
    topics = _topic_slugs(problem)
    difficulty = problem.get("difficulty", "Medium")
    acceptance = _acceptance_rate(problem)

    w_topic = 0.55
    w_diff = 0.30
    w_quality = 0.15

    topic_score = _topic_need_score(topics, solved_by_topic, mode)
    diff_score = _difficulty_fit_score(difficulty, solved_stats_dict)
    # Higher acceptance = more approachable; combined with acceptance rate floor
    quality_score = min(acceptance * 1.5, 1.0)

    return w_topic * topic_score + w_diff * diff_score + w_quality * quality_score


# ── public API ────────────────────────────────────────────────────────────────

def recommend(
    profile: PublicProfile,
    catalog: list[dict[str, Any]],
    mode: RecommendMode = "interview",
    top_n: int = 5,
) -> list[Recommendation]:
    """Ranks and returns the top N recommended problems.

    Args:
        profile: The user's current PublicProfile (or PrivateProfile).
        catalog: List of LeetCode problem dicts from the catalog cache.
        mode: "interview" weights core interview topics; "weakness" targets gaps.
        top_n: Number of recommendations to return.

    Returns:
        Ordered list of Recommendation objects (best first).
    """
    if profile.is_new_user:
        starter_candidates = [
            p for p in catalog
            if p.get("difficulty") == "Easy" and _acceptance_rate(p) >= 0.50
        ]
        starter_candidates.sort(
            key=lambda p: (
                1 if p.get("titleSlug") in _STARTER_SLUGS else 0,
                _acceptance_rate(p),
            ),
            reverse=True,
        )
        results: list[Recommendation] = []
        for problem in starter_candidates[:top_n]:
            topics = [t.get("name", t.get("slug", "")) for t in problem.get("topicTags", [])]
            results.append(
                Recommendation(
                    title=problem.get("title", ""),
                    title_slug=problem.get("titleSlug", ""),
                    difficulty=problem.get("difficulty", "Easy"),
                    topics=topics,
                    acceptance_rate=round(_acceptance_rate(problem) * 100, 1),
                    rationale="Great starter problem for beginners.",
                )
            )
        return results

    solved_slugs: set[str] = {s.title_slug for s in profile.recent_submissions}
    solved_by_topic: dict[str, int] = {t.slug: t.solved for t in profile.topic_stats}
    solved_stats_dict = dataclasses.asdict(profile.solved_stats)

    candidates = [p for p in catalog if p.get("titleSlug") not in solved_slugs]

    scored = [
        (
            _score_problem(p, solved_by_topic, solved_stats_dict, mode),
            p,
        )
        for p in candidates
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    results: list[Recommendation] = []
    for score, problem in scored[:top_n]:
        topics = [t.get("name", t.get("slug", "")) for t in problem.get("topicTags", [])]
        difficulty = problem.get("difficulty", "")
        acceptance = _acceptance_rate(problem)
        rationale = _build_rationale(problem, solved_by_topic, mode)

        results.append(
            Recommendation(
                title=problem.get("title", ""),
                title_slug=problem.get("titleSlug", ""),
                difficulty=difficulty,
                topics=topics,
                acceptance_rate=round(acceptance * 100, 1),
                rationale=rationale,
            )
        )
    return results


def _build_rationale(
    problem: dict[str, Any],
    solved_by_topic: dict[str, int],
    mode: RecommendMode,
) -> str:
    topics = _topic_slugs(problem)
    if not topics:
        return "Popular interview problem."

    weakest = min(topics, key=lambda s: solved_by_topic.get(s, 0))
    solved_count = solved_by_topic.get(weakest, 0)

    if mode == "interview":
        priority = _INTERVIEW_PRIORITY.get(weakest, 0)
        if priority >= 8:
            return f"Core interview topic: {weakest.replace('-', ' ')} ({solved_count} solved)."
        return f"Topic: {weakest.replace('-', ' ')}"
    else:
        return f"Weakest area: {weakest.replace('-', ' ')} : {solved_count} solved."
