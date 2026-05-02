from __future__ import annotations

import difflib
import re
from dataclasses import replace

from stork_agent.models import PaperItem


def dedupe_papers(papers: list[PaperItem], title_threshold: float = 0.94) -> list[PaperItem]:
    merged: list[PaperItem] = []
    for paper in papers:
        match_index = find_match(merged, paper, title_threshold)
        if match_index is None:
            merged.append(paper)
        else:
            merged[match_index] = merge_papers(merged[match_index], paper)
    return merged


def find_match(existing: list[PaperItem], paper: PaperItem, title_threshold: float) -> int | None:
    doi = normalize_doi(paper.doi)
    title = normalize_title(paper.title)
    for index, candidate in enumerate(existing):
        if doi and doi == normalize_doi(candidate.doi):
            return index
        if shared_source_id(candidate, paper):
            return index
        if title and difflib.SequenceMatcher(a=normalize_title(candidate.title), b=title).ratio() >= title_threshold:
            return index
    return None


def merge_papers(primary: PaperItem, secondary: PaperItem) -> PaperItem:
    sources = tuple(dict.fromkeys(primary.source.split(" / ") + secondary.source.split(" / ")))
    source_ids = dict(primary.source_ids)
    source_ids.update(secondary.source_ids)
    return replace(
        primary,
        source="Multiple Sources" if len(sources) > 1 else sources[0],
        authors=primary.authors or secondary.authors,
        abstract=primary.abstract or secondary.abstract,
        year=primary.year or secondary.year,
        publication_date=primary.publication_date or secondary.publication_date,
        venue=primary.venue or secondary.venue,
        doi=primary.doi or secondary.doi,
        url=primary.url or secondary.url,
        source_ids=source_ids,
        keywords=tuple(dict.fromkeys(primary.keywords + secondary.keywords)),
        matched_queries=tuple(dict.fromkeys(primary.matched_queries + secondary.matched_queries)),
        citation_count=primary.citation_count or secondary.citation_count,
        open_access_url=primary.open_access_url or secondary.open_access_url,
        innovation_summary=primary.innovation_summary or secondary.innovation_summary,
    )


def shared_source_id(left: PaperItem, right: PaperItem) -> bool:
    return any(key in right.source_ids and right.source_ids[key] == value for key, value in left.source_ids.items())


def normalize_doi(doi: str | None) -> str:
    if not doi:
        return ""
    return doi.lower().removeprefix("https://doi.org/").removeprefix("http://doi.org/").strip()


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()

