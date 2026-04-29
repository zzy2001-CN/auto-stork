from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import requests
from requests import RequestException

from stork_mailer.config import SearchConfig
from stork_mailer.models import LiteratureItem
from stork_mailer.parser import summarize_innovation


OPENALEX_WORKS_URL = "https://api.openalex.org/works"
SEMANTIC_SCHOLAR_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


class SourceError(RuntimeError):
    pass


def fetch_openalex_items(
    config: SearchConfig,
    api_key: str | None = None,
    mailto: str | None = None,
    today: date | None = None,
) -> list[LiteratureItem]:
    today = today or date.today()
    from_date = today - timedelta(days=config.lookback_days)
    items: list[LiteratureItem] = []

    for query in config.queries:
        params = {
            "search": query,
            "filter": f"from_publication_date:{from_date.isoformat()}",
            "per-page": str(config.per_query_limit),
            "sort": "publication_date:desc",
            "select": "id,doi,title,display_name,publication_year,publication_date,abstract_inverted_index,primary_location",
        }
        if api_key:
            params["api_key"] = api_key
        if mailto:
            params["mailto"] = mailto

        data = request_json(OPENALEX_WORKS_URL, params=params)
        for work in data.get("results", []):
            item = openalex_work_to_item(work, query, config.include_keywords)
            if item is not None:
                items.append(item)

    return items


def fetch_semantic_scholar_items(
    config: SearchConfig,
    api_key: str | None = None,
    today: date | None = None,
) -> list[LiteratureItem]:
    today = today or date.today()
    from_date = today - timedelta(days=config.lookback_days)
    items: list[LiteratureItem] = []
    headers = {"x-api-key": api_key} if api_key else None

    for query in config.queries:
        params = {
            "query": query,
            "limit": str(config.per_query_limit),
            "fields": "title,abstract,venue,year,externalIds,url,publicationDate",
        }
        data = request_json(SEMANTIC_SCHOLAR_SEARCH_URL, params=params, headers=headers)
        for paper in data.get("data", []):
            if not is_recent_semantic_paper(paper, from_date):
                continue
            item = semantic_paper_to_item(paper, query, config.include_keywords)
            if item is not None:
                items.append(item)

    return items


def request_json(
    url: str,
    params: dict[str, str],
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
    except RequestException as exc:
        raise SourceError(f"Request failed for {url}: {exc}") from exc
    if response.status_code == 429:
        raise SourceError(f"Rate limited by {url}")
    if response.status_code >= 400:
        raise SourceError(f"Request failed for {url}: HTTP {response.status_code}")
    return response.json()


def openalex_work_to_item(
    work: dict[str, Any],
    query: str,
    include_keywords: tuple[str, ...],
) -> LiteratureItem | None:
    title = work.get("title") or work.get("display_name")
    if not title:
        return None

    abstract = abstract_from_inverted_index(work.get("abstract_inverted_index"))
    venue = extract_openalex_venue(work)
    haystack = " ".join(value for value in (title, abstract, venue) if value)
    matched = match_keywords(haystack, include_keywords)
    if not matched:
        return None

    return LiteratureItem(
        title=title,
        source="OpenAlex",
        venue=venue,
        year=work.get("publication_year"),
        doi=normalize_doi(work.get("doi")),
        abstract=abstract,
        url=work.get("doi") or work.get("id"),
        quartile="Unknown",
        innovation=summarize_innovation(abstract or title),
        matched_keywords=tuple(dict.fromkeys((query,) + matched)),
    )


def semantic_paper_to_item(
    paper: dict[str, Any],
    query: str,
    include_keywords: tuple[str, ...],
) -> LiteratureItem | None:
    title = paper.get("title")
    if not title:
        return None

    abstract = paper.get("abstract")
    venue = paper.get("venue")
    haystack = " ".join(value for value in (title, abstract, venue) if value)
    matched = match_keywords(haystack, include_keywords)
    if not matched:
        return None

    external_ids = paper.get("externalIds") or {}
    return LiteratureItem(
        title=title,
        source="Semantic Scholar",
        venue=venue,
        year=paper.get("year"),
        doi=normalize_doi(external_ids.get("DOI")),
        abstract=abstract,
        url=paper.get("url"),
        quartile="Unknown",
        innovation=summarize_innovation(abstract or title),
        matched_keywords=tuple(dict.fromkeys((query,) + matched)),
    )


def abstract_from_inverted_index(index: dict[str, list[int]] | None) -> str | None:
    if not index:
        return None

    positioned: list[tuple[int, str]] = []
    for word, positions in index.items():
        positioned.extend((position, word) for position in positions)
    positioned.sort()
    return " ".join(word for _, word in positioned)


def extract_openalex_venue(work: dict[str, Any]) -> str | None:
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    return source.get("display_name")


def is_recent_semantic_paper(paper: dict[str, Any], from_date: date) -> bool:
    publication_date = paper.get("publicationDate")
    if publication_date:
        try:
            return date.fromisoformat(publication_date) >= from_date
        except ValueError:
            return True

    year = paper.get("year")
    return year is None or int(year) >= from_date.year


def match_keywords(text: str, include_keywords: tuple[str, ...]) -> tuple[str, ...]:
    lower = text.lower()
    return tuple(keyword for keyword in include_keywords if keyword.lower() in lower)


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    return value.removeprefix("https://doi.org/").removeprefix("http://doi.org/")
