from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from stork_agent.connectors.base import BaseConnector
from stork_agent.models import PaperItem
from stork_agent.models import UserProfile
from stork_agent.summarizer import summarize_innovation


DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s<>)\"']+", re.IGNORECASE)
TITLE_RE = re.compile(r"^(?:title|paper|article|题目)\s*[:：]\s*(.+)$", re.IGNORECASE | re.MULTILINE)
VENUE_RE = re.compile(r"^(?:journal|source|venue|期刊|来源)\s*[:：]\s*(.+)$", re.IGNORECASE | re.MULTILINE)
ABSTRACT_RE = re.compile(r"^(?:abstract|summary|摘要)\s*[:：]\s*(.+?)(?=\n[A-Za-z\u4e00-\u9fff ]{2,20}\s*[:：]|\Z)", re.IGNORECASE | re.MULTILINE | re.DOTALL)


class WebOfScienceConnector(BaseConnector):
    name = "web_of_science"
    starter_url = "https://api.clarivate.com/apis/wos-starter/v1/documents"
    expanded_url = "https://api.clarivate.com/apis/wos/v1/documents"

    def validate_config(self, profile: UserProfile | None = None) -> None:
        api_type = self.api_type()
        if api_type not in {"starter", "expanded"}:
            raise RuntimeError("WOS_API_TYPE must be 'starter' or 'expanded'.")
        if not self.env.get("WOS_API_KEY"):
            raise RuntimeError("WOS_API_KEY is not set; Web of Science access depends on Clarivate and institutional subscription.")

    def healthcheck(self) -> dict[str, str]:
        api_type = self.api_type()
        configured = bool(self.env.get("WOS_API_KEY"))
        status = "ok" if configured and api_type in {"starter", "expanded"} else "warning"
        return {
            "name": self.name,
            "status": status,
            "message": f"type={api_type}; key={'configured' if configured else 'missing'}; access depends on institutional subscription",
        }

    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        try:
            self.validate_config(profile)
        except RuntimeError as exc:
            self.warnings.append(str(exc))
            return []
        self.warnings.append("Web of Science API fetch is reserved; configure official Clarivate API access before enabling real requests.")
        return []

    def api_type(self) -> str:
        return self.env.get("WOS_API_TYPE", "starter").lower()

    def endpoint(self) -> str:
        return self.expanded_url if self.api_type() == "expanded" else self.starter_url


class ElsevierConnector(BaseConnector):
    name = "elsevier"
    scopus_search_url = "https://api.elsevier.com/content/search/scopus"
    science_direct_url = "https://api.elsevier.com/content/search/sciencedirect"

    def validate_config(self, profile: UserProfile | None = None) -> None:
        if not self.env.get("ELSEVIER_API_KEY"):
            raise RuntimeError("ELSEVIER_API_KEY is not set; Scopus/ScienceDirect access requires official Elsevier API permission.")

    def healthcheck(self) -> dict[str, str]:
        configured = bool(self.env.get("ELSEVIER_API_KEY"))
        inst = "configured" if self.env.get("ELSEVIER_INST_TOKEN") else "missing"
        return {
            "name": self.name,
            "status": "ok" if configured else "warning",
            "message": f"api_key={'configured' if configured else 'missing'}; institution_token={inst}",
        }

    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        try:
            self.validate_config(profile)
        except RuntimeError as exc:
            self.warnings.append(str(exc))
            return []
        self.warnings.append("Elsevier API fetch is reserved for official Scopus/ScienceDirect API access.")
        return []

    def build_scopus_query(self, profile: UserProfile) -> dict[str, str]:
        return {"query": " OR ".join(profile.keywords)}


class IEEEConnector(BaseConnector):
    name = "ieee"
    metadata_search_url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"

    def validate_config(self, profile: UserProfile | None = None) -> None:
        if not self.env.get("IEEE_API_KEY"):
            raise RuntimeError("IEEE_API_KEY is not set; IEEE Metadata Search API requires official API access.")

    def healthcheck(self) -> dict[str, str]:
        configured = bool(self.env.get("IEEE_API_KEY"))
        return {
            "name": self.name,
            "status": "ok" if configured else "warning",
            "message": f"api_key={'configured' if configured else 'missing'}",
        }

    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        try:
            self.validate_config(profile)
        except RuntimeError as exc:
            self.warnings.append(str(exc))
            return []
        self.warnings.append("IEEE API fetch is reserved for official Metadata Search API access.")
        return []

    def build_metadata_query(self, profile: UserProfile, limit: int) -> dict[str, str]:
        return {"querytext": " OR ".join(profile.keywords), "max_records": str(limit)}


class AlertEmailConnector(BaseConnector):
    name = "alert_email"

    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        sample_path = self.env.get("ALERT_EMAIL_SAMPLE_PATH")
        if not sample_path:
            self.warnings.append("Alert Email connector parses user-received alert emails only; set ALERT_EMAIL_SAMPLE_PATH for local parsing.")
            return []
        path = Path(sample_path)
        if not path.exists():
            self.warnings.append(f"Alert email sample does not exist: {path}")
            return []
        return parse_alert_email(path.read_text(encoding="utf-8"), source_hint=detect_alert_source(path.name))[:limit]


class OpenURLResolver:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url

    def resolve(self, doi: str | None) -> str | None:
        if not self.base_url or not doi:
            return None
        return f"{self.base_url.rstrip('/')}?{urlencode({'doi': doi})}"


def parse_alert_email(content: str, source_hint: str | None = None) -> list[PaperItem]:
    text = html_to_text(content)
    blocks = split_blocks(text)
    papers = [paper for block in blocks if (paper := parse_alert_block(block, source_hint))]
    if papers:
        return papers
    single = parse_alert_block(text, source_hint)
    return [single] if single else []


def parse_alert_block(block: str, source_hint: str | None = None) -> PaperItem | None:
    doi_match = DOI_RE.search(block)
    title_match = TITLE_RE.search(block)
    title = clean(title_match.group(1)) if title_match else infer_title(block)
    if not title:
        return None
    venue_match = VENUE_RE.search(block)
    abstract_match = ABSTRACT_RE.search(block)
    url_match = URL_RE.search(block)
    doi = doi_match.group(0).rstrip(".") if doi_match else None
    abstract = clean(abstract_match.group(1)) if abstract_match else None
    source = source_hint or detect_alert_source(block) or "Alert Email"
    return PaperItem(
        title=title,
        abstract=abstract,
        venue=clean(venue_match.group(1)) if venue_match else None,
        doi=doi,
        url=url_match.group(0).rstrip(".,") if url_match else None,
        source=source,
        source_ids={source.lower().replace(" ", "_"): doi or title},
        innovation_summary=summarize_innovation(title, abstract),
    )


def detect_alert_source(text: str) -> str | None:
    lower = text.lower()
    if "web of science" in lower or "clarivate" in lower:
        return "Web of Science Alert"
    if "scopus" in lower or "science direct" in lower or "sciencedirect" in lower:
        return "Elsevier Alert"
    if "ieee" in lower:
        return "IEEE Alert"
    return None


def html_to_text(content: str) -> str:
    if "<" in content and ">" in content:
        return BeautifulSoup(content, "html.parser").get_text("\n")
    return content


def split_blocks(text: str) -> list[str]:
    return [block.strip() for block in re.split(r"\n\s*(?:-{3,}|={3,}|\d+[.)、]\s+)\s*", text) if len(block.strip()) > 40]


def infer_title(block: str) -> str | None:
    for line in block.splitlines():
        value = clean(line)
        if len(value) > 8 and not DOI_RE.search(value) and not value.lower().startswith(("abstract", "journal", "source", "url")):
            return value
    return None


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
