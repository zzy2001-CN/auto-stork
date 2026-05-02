from __future__ import annotations

from datetime import date
from typing import Any

from stork_agent.connectors.base import BaseConnector
from stork_agent.http import get_json
from stork_agent.models import PaperItem
from stork_agent.models import UserProfile
from stork_agent.summarizer import summarize_innovation


class SemanticScholarConnector(BaseConnector):
    name = "semantic_scholar"
    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    def validate_config(self, profile: UserProfile | None = None) -> None:
        if not self.env.get("SEMANTIC_SCHOLAR_API_KEY"):
            self.warnings.append("SEMANTIC_SCHOLAR_API_KEY is not set; using unauthenticated access.")

    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        self.validate_config(profile)
        headers = {"x-api-key": self.env["SEMANTIC_SCHOLAR_API_KEY"]} if self.env.get("SEMANTIC_SCHOLAR_API_KEY") else None
        papers: list[PaperItem] = []
        for query in profile.keywords:
            data = get_json(
                self.url,
                params={"query": query, "limit": str(limit), "fields": "title,abstract,venue,year,externalIds,url,publicationDate,citationCount,authors"},
                headers=headers,
            )
            for raw in data.get("data", []):
                if is_recent(raw, since):
                    papers.append(semantic_to_paper(raw, query))
        return papers


def semantic_to_paper(raw: dict[str, Any], query: str) -> PaperItem:
    external = raw.get("externalIds") or {}
    title = raw.get("title") or "Untitled"
    abstract = raw.get("abstract")
    return PaperItem(
        title=title,
        authors=tuple(author.get("name") for author in raw.get("authors", []) if author.get("name")),
        abstract=abstract,
        year=raw.get("year"),
        publication_date=raw.get("publicationDate"),
        venue=raw.get("venue"),
        doi=external.get("DOI"),
        url=raw.get("url"),
        source="Semantic Scholar",
        source_ids={"semantic_scholar": raw.get("paperId", "")} if raw.get("paperId") else {},
        matched_queries=(query,),
        citation_count=raw.get("citationCount"),
        innovation_summary=summarize_innovation(title, abstract),
    )


def is_recent(raw: dict[str, Any], since: date) -> bool:
    if raw.get("publicationDate"):
        try:
            return date.fromisoformat(raw["publicationDate"]) >= since
        except ValueError:
            return True
    return raw.get("year") is None or int(raw["year"]) >= since.year

