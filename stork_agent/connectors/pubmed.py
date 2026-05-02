from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from datetime import date

from stork_agent.connectors.base import BaseConnector
from stork_agent.http import get_text
from stork_agent.models import PaperItem
from stork_agent.models import UserProfile
from stork_agent.summarizer import summarize_innovation


class PubMedConnector(BaseConnector):
    name = "pubmed"
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        papers: list[PaperItem] = []
        for query in profile.keywords:
            ids = self.search_ids(query, since, limit)
            if ids:
                papers.extend(pubmed_xml_to_papers(self.fetch_details(ids), query))
        return papers

    def search_ids(self, query: str, since: date, limit: int) -> list[str]:
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "xml",
            "retmax": str(limit),
            "mindate": since.isoformat(),
            "datetype": "pdat",
            "tool": "auto-stork",
        }
        add_ncbi_params(params, self.env)
        root = ET.fromstring(get_text(self.search_url, params=params))
        return [node.text for node in root.findall(".//Id") if node.text]

    def fetch_details(self, ids: list[str]) -> str:
        params = {"db": "pubmed", "id": ",".join(ids), "retmode": "xml", "tool": "auto-stork"}
        add_ncbi_params(params, self.env)
        return get_text(self.fetch_url, params=params)


def add_ncbi_params(params: dict[str, str], env: dict[str, str]) -> None:
    email = env.get("NCBI_EMAIL") or os.environ.get("NCBI_EMAIL")
    api_key = env.get("NCBI_API_KEY") or os.environ.get("NCBI_API_KEY")
    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key


def pubmed_xml_to_papers(xml_text: str, query: str) -> list[PaperItem]:
    root = ET.fromstring(xml_text)
    papers: list[PaperItem] = []
    for article in root.findall(".//PubmedArticle"):
        pmid = text(article, ".//PMID")
        title = text(article, ".//ArticleTitle") or "Untitled"
        abstract = " ".join(node.text or "" for node in article.findall(".//AbstractText")).strip() or None
        journal = text(article, ".//Journal/Title")
        year_text = text(article, ".//PubDate/Year")
        year = int(year_text) if year_text and year_text.isdigit() else None
        doi = None
        for node in article.findall(".//ArticleId"):
            if node.attrib.get("IdType") == "doi":
                doi = node.text
        papers.append(
            PaperItem(
                title=title,
                abstract=abstract,
                year=year,
                venue=journal,
                doi=doi,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                source="PubMed",
                source_ids={"pmid": pmid} if pmid else {},
                matched_queries=(query,),
                innovation_summary=summarize_innovation(title, abstract),
            )
        )
    return papers


def text(root: ET.Element, path: str) -> str | None:
    node = root.find(path)
    return "".join(node.itertext()).strip() if node is not None else None

