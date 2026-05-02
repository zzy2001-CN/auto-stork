from __future__ import annotations

from datetime import date
from typing import Any

from stork_agent.connectors.base import BaseConnector
from stork_agent.http import get_json
from stork_agent.models import PaperItem
from stork_agent.models import UserProfile
from stork_agent.summarizer import summarize_innovation


class OpenAlexConnector(BaseConnector):
    name = "openalex"
    url = "https://api.openalex.org/works"

    def validate_config(self, profile: UserProfile | None = None) -> None:
        if not self.env.get("OPENALEX_API_KEY"):
            message = "OPENALEX_API_KEY is not set; using unauthenticated OpenAlex access."
            self.warnings.append(message)
            if profile and profile.strict_api_keys:
                raise RuntimeError(message)

    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        self.validate_config(profile)
        papers: list[PaperItem] = []
        for query in profile.keywords:
            params = {
                "search": query,
                "filter": f"from_publication_date:{since.isoformat()}",
                "per-page": str(limit),
                "sort": "publication_date:desc",
                "select": "id,doi,title,display_name,publication_year,publication_date,cited_by_count,abstract_inverted_index,primary_location,authorships,open_access",
            }
            if self.env.get("OPENALEX_API_KEY"):
                params["api_key"] = self.env["OPENALEX_API_KEY"]
            data = get_json(self.url, params=params)
            for work in data.get("results", []):
                item = openalex_to_paper(work, query)
                if item:
                    papers.append(item)
        return papers


def openalex_to_paper(work: dict[str, Any], query: str) -> PaperItem | None:
    title = work.get("title") or work.get("display_name")
    if not title:
        return None
    abstract = abstract_from_inverted_index(work.get("abstract_inverted_index"))
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    open_access = work.get("open_access") or {}
    authors = tuple(
        author.get("author", {}).get("display_name")
        for author in work.get("authorships", [])
        if author.get("author", {}).get("display_name")
    )
    return PaperItem(
        title=title,
        authors=authors,
        abstract=abstract,
        year=work.get("publication_year"),
        publication_date=work.get("publication_date"),
        venue=source.get("display_name"),
        doi=normalize_doi(work.get("doi")),
        url=work.get("doi") or work.get("id"),
        source="OpenAlex",
        source_ids={"openalex": work.get("id", "")},
        matched_queries=(query,),
        citation_count=work.get("cited_by_count"),
        open_access_url=open_access.get("oa_url"),
        innovation_summary=summarize_innovation(title, abstract),
    )


def abstract_from_inverted_index(index: dict[str, list[int]] | None) -> str | None:
    if not index:
        return None
    positioned: list[tuple[int, str]] = []
    for word, positions in index.items():
        positioned.extend((position, word) for position in positions)
    return " ".join(word for _, word in sorted(positioned))


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    return value.removeprefix("https://doi.org/").removeprefix("http://doi.org/")

