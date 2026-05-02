from __future__ import annotations

from typing import Any

from stork_agent.connectors.base import BaseConnector
from stork_agent.http import get_json
from stork_agent.models import PaperItem
from stork_agent.models import UserProfile
from stork_agent.summarizer import summarize_innovation


class CrossrefConnector(BaseConnector):
    name = "crossref"
    url = "https://api.crossref.org/works"

    def fetch(self, profile: UserProfile, since, limit: int) -> list[PaperItem]:
        papers: list[PaperItem] = []
        for query in profile.keywords:
            data = get_json(self.url, params={"query.title": query, "rows": str(limit)})
            for item in data.get("message", {}).get("items", []):
                papers.append(crossref_to_paper(item, query))
        return papers


def crossref_to_paper(item: dict[str, Any], query: str) -> PaperItem:
    title = (item.get("title") or ["Untitled"])[0]
    abstract = item.get("abstract")
    year = extract_year(item)
    return PaperItem(
        title=title,
        authors=tuple(format_author(author) for author in item.get("author", [])),
        abstract=abstract,
        year=year,
        venue=(item.get("container-title") or [None])[0],
        doi=item.get("DOI"),
        url=item.get("URL"),
        source="Crossref",
        source_ids={"crossref": item.get("DOI", "")},
        matched_queries=(query,),
        citation_count=item.get("is-referenced-by-count"),
        innovation_summary=summarize_innovation(title, abstract),
    )


def extract_year(item: dict[str, Any]) -> int | None:
    parts = item.get("published-print") or item.get("published-online") or item.get("created") or {}
    date_parts = parts.get("date-parts") or []
    return date_parts[0][0] if date_parts and date_parts[0] else None


def format_author(author: dict[str, Any]) -> str:
    return " ".join(part for part in (author.get("given"), author.get("family")) if part)

