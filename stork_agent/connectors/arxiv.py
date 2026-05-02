from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date

from stork_agent.connectors.base import BaseConnector
from stork_agent.http import get_text
from stork_agent.models import PaperItem
from stork_agent.models import UserProfile
from stork_agent.summarizer import summarize_innovation


ATOM = "{http://www.w3.org/2005/Atom}"


class ArxivConnector(BaseConnector):
    name = "arxiv"
    url = "https://export.arxiv.org/api/query"

    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        papers: list[PaperItem] = []
        for query in profile.keywords:
            xml_text = get_text(
                self.url,
                params={"search_query": f"all:{query}", "start": "0", "max_results": str(limit), "sortBy": "submittedDate", "sortOrder": "descending"},
            )
            papers.extend(arxiv_atom_to_papers(xml_text, query, since))
        return papers


def arxiv_atom_to_papers(xml_text: str, query: str, since: date) -> list[PaperItem]:
    root = ET.fromstring(xml_text)
    papers: list[PaperItem] = []
    for entry in root.findall(f"{ATOM}entry"):
        published = node_text(entry, f"{ATOM}published")
        if published:
            try:
                if date.fromisoformat(published[:10]) < since:
                    continue
            except ValueError:
                pass
        title = normalize(node_text(entry, f"{ATOM}title") or "Untitled")
        abstract = normalize(node_text(entry, f"{ATOM}summary") or "") or None
        arxiv_id = node_text(entry, f"{ATOM}id")
        authors = tuple(normalize(author.findtext(f"{ATOM}name") or "") for author in entry.findall(f"{ATOM}author"))
        papers.append(
            PaperItem(
                title=title,
                authors=tuple(author for author in authors if author),
                abstract=abstract,
                year=int(published[:4]) if published else None,
                publication_date=published[:10] if published else None,
                url=arxiv_id,
                source="arXiv",
                source_ids={"arxiv": arxiv_id or ""},
                matched_queries=(query,),
                innovation_summary=summarize_innovation(title, abstract),
            )
        )
    return papers


def node_text(root: ET.Element, path: str) -> str | None:
    node = root.find(path)
    return node.text if node is not None else None


def normalize(value: str) -> str:
    return " ".join(value.split())

