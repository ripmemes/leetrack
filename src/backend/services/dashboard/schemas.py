"""Typed data contracts shared across dashboard services.

These are transient — never persisted to the database.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SolvedStats:
    easy: int = 0
    medium: int = 0
    hard: int = 0

    @property
    def total(self) -> int:
        return self.easy + self.medium + self.hard


@dataclass
class TopicStat:
    slug: str
    name: str
    solved: int


@dataclass
class RecentSubmission:
    title: str
    title_slug: str
    timestamp: str  # unix epoch string as returned by LC


@dataclass
class ContestInfo:
    rating: float
    ranking: int
    attended: int


@dataclass
class PublicProfile:
    """Data available without a session cookie (public GraphQL queries)."""
    handle: str
    real_name: str
    avatar_url: str
    ranking: int
    solved_stats: SolvedStats
    topic_stats: list[TopicStat] = field(default_factory=list)
    contest_info: ContestInfo | None = None
    recent_submissions: list[RecentSubmission] = field(default_factory=list)
    calendar: dict = field(default_factory=dict)  # {dateStr: submissionCount}
    
    @property
    def is_new_user(self) -> bool:
        return self.solved_stats.total == 0

    @property
    def has_recent_activity(self) -> bool:
        return len(self.recent_submissions) > 0

    @property
    def is_inactive(self) -> bool:
        return self.solved_stats.total > 0 and len(self.recent_submissions) == 0


@dataclass
class PrivateProfile(PublicProfile):
    """Extended profile requiring a valid LEETCODE_SESSION cookie."""
    # Slots for private data (e.g. full submission history). Currently mirrors
    # PublicProfile; the distinction lives in which GraphQL queries are run.
    pass


@dataclass
class Recommendation:
    title: str
    title_slug: str
    difficulty: str
    topics: list[str]
    acceptance_rate: float
    rationale: str  # human-readable explanation shown in the UI
