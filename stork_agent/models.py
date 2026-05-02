from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date


@dataclass(frozen=True)
class SearchQuery:
    text: str
    category: str | None = None


@dataclass(frozen=True)
class UserProfile:
    name: str
    keywords: tuple[str, ...]
    exclude_keywords: tuple[str, ...] = ()
    sources: tuple[str, ...] = ("stork_email", "openalex", "semantic_scholar")
    lookback_days: int = 7
    daily_limit: int = 20
    min_score: float = 0.0
    focus_authors: tuple[str, ...] = ()
    focus_venues: tuple[str, ...] = ()
    strict_api_keys: bool = False


@dataclass(frozen=True)
class PaperItem:
    title: str
    authors: tuple[str, ...] = ()
    abstract: str | None = None
    year: int | None = None
    publication_date: str | None = None
    venue: str | None = None
    doi: str | None = None
    url: str | None = None
    source: str = "Unknown"
    source_ids: dict[str, str] = field(default_factory=dict)
    keywords: tuple[str, ...] = ()
    matched_queries: tuple[str, ...] = ()
    citation_count: int | None = None
    open_access_url: str | None = None
    recommendation_score: float = 0.0
    recommendation_reason: str = ""
    innovation_summary: str = ""


@dataclass(frozen=True)
class SourceResult:
    source: str
    papers: list[PaperItem]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class DigestItem:
    paper: PaperItem
    first_seen: date
    is_new: bool = True


def with_updates(item: PaperItem, **changes) -> PaperItem:
    return replace(item, **changes)

