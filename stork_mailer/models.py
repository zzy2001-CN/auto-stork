from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class LiteratureItem:
    title: str
    source: str
    quartile: str = "Unknown"
    innovation: str = "Pending manual review"
    venue: str | None = None
    year: int | None = None
    doi: str | None = None
    abstract: str | None = None
    url: str | None = None
    matched_keywords: tuple[str, ...] = ()


def dedupe_by_title(items: list[LiteratureItem]) -> list[LiteratureItem]:
    seen: dict[str, LiteratureItem] = {}
    order: list[str] = []

    for item in items:
        key = normalize_title(item.title)
        if not key:
            continue
        if key not in seen:
            seen[key] = item
            order.append(key)
            continue

        seen[key] = merge_items(seen[key], item)

    return [seen[key] for key in order]


def normalize_title(title: str) -> str:
    return " ".join(title.split()).strip()


def merge_items(primary: LiteratureItem, secondary: LiteratureItem) -> LiteratureItem:
    sources = tuple(dict.fromkeys(primary.source.split(" / ") + secondary.source.split(" / ")))
    keywords = tuple(dict.fromkeys(primary.matched_keywords + secondary.matched_keywords))
    return replace(
        primary,
        source=" / ".join(sources),
        quartile=primary.quartile if primary.quartile != "Unknown" else secondary.quartile,
        innovation=primary.innovation
        if primary.innovation != "Pending manual review"
        else secondary.innovation,
        venue=primary.venue or secondary.venue,
        year=primary.year or secondary.year,
        doi=primary.doi or secondary.doi,
        abstract=primary.abstract or secondary.abstract,
        url=primary.url or secondary.url,
        matched_keywords=keywords,
    )

