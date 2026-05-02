from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from stork_agent.models import SearchQuery
from stork_agent.models import UserProfile


PROFILES_PATH = Path("config/profiles.yml")
LEGACY_SEARCH_PATH = Path("config/search.yml")


DEFAULT_KEYWORDS = (
    "semi-supervised medical image segmentation",
    "weakly supervised medical image segmentation",
    "scribble supervised segmentation",
    "pseudo-label medical image segmentation",
)


def load_profiles(path: Path = PROFILES_PATH) -> list[UserProfile]:
    if path.exists():
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        profiles = raw.get("profiles", raw if isinstance(raw, list) else [])
        return [parse_profile(profile) for profile in profiles] or [default_profile()]
    if LEGACY_SEARCH_PATH.exists():
        return [legacy_search_to_profile(LEGACY_SEARCH_PATH)]
    return [default_profile()]


def parse_profile(raw: dict[str, Any]) -> UserProfile:
    return UserProfile(
        name=str(raw.get("name", "default")),
        keywords=tuple(raw.get("keywords") or DEFAULT_KEYWORDS),
        exclude_keywords=tuple(raw.get("exclude_keywords") or ()),
        sources=tuple(raw.get("sources") or ("stork_email", "openalex", "semantic_scholar")),
        lookback_days=int(raw.get("lookback_days", 7)),
        daily_limit=int(raw.get("daily_limit", 20)),
        min_score=float(raw.get("min_score", 0.0)),
        focus_authors=tuple(raw.get("focus_authors") or ()),
        focus_venues=tuple(raw.get("focus_venues") or ()),
        strict_api_keys=bool(raw.get("strict_api_keys", False)),
    )


def default_profile() -> UserProfile:
    return UserProfile(name="default", keywords=DEFAULT_KEYWORDS)


def legacy_search_to_profile(path: Path) -> UserProfile:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sources = tuple("stork_email" if source == "stork" else source for source in raw.get("sources", ()))
    return UserProfile(
        name="default",
        keywords=tuple(raw.get("queries") or DEFAULT_KEYWORDS),
        sources=sources or ("stork_email", "openalex", "semantic_scholar"),
        lookback_days=int(raw.get("lookback_days", 7)),
        daily_limit=int(raw.get("per_query_limit", 20)),
    )


def profile_queries(profile: UserProfile) -> list[SearchQuery]:
    return [SearchQuery(text=keyword) for keyword in profile.keywords]


def write_default_profiles(path: Path = PROFILES_PATH) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "profiles": [
            {
                "name": "default",
                "keywords": list(DEFAULT_KEYWORDS),
                "exclude_keywords": [],
                "sources": ["stork_email", "openalex", "semantic_scholar", "pubmed", "arxiv"],
                "lookback_days": 7,
                "daily_limit": 20,
                "min_score": 0.0,
                "focus_authors": [],
                "focus_venues": [],
                "strict_api_keys": False,
            }
        ]
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return True

