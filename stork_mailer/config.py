from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path("config/search.yml")


@dataclass(frozen=True)
class SearchConfig:
    queries: tuple[str, ...]
    lookback_days: int = 7
    per_query_limit: int = 20
    include_keywords: tuple[str, ...] = ()
    sources: tuple[str, ...] = ("stork", "openalex", "semantic_scholar")


DEFAULT_QUERIES = (
    "semi-supervised medical image segmentation",
    "weakly supervised medical image segmentation",
    "scribble supervised segmentation",
    "pseudo-label medical image segmentation",
)

DEFAULT_INCLUDE_KEYWORDS = (
    "semi-supervised",
    "semisupervised",
    "semi supervised",
    "weakly supervised",
    "scribble",
    "pseudo-label",
    "pseudo label",
    "medical image segmentation",
    "medical image",
    "segmentation",
    "mri",
    "ct",
    "ultrasound",
)


def load_search_config(path: Path = DEFAULT_CONFIG_PATH) -> SearchConfig:
    if not path.exists():
        return SearchConfig(
            queries=DEFAULT_QUERIES,
            include_keywords=DEFAULT_INCLUDE_KEYWORDS,
        )

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return parse_search_config(raw)


def parse_search_config(raw: dict[str, Any]) -> SearchConfig:
    return SearchConfig(
        queries=tuple(raw.get("queries") or DEFAULT_QUERIES),
        lookback_days=int(raw.get("lookback_days", 7)),
        per_query_limit=int(raw.get("per_query_limit", 20)),
        include_keywords=tuple(raw.get("include_keywords") or DEFAULT_INCLUDE_KEYWORDS),
        sources=tuple(raw.get("sources") or ("stork", "openalex", "semantic_scholar")),
    )

