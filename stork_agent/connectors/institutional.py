from __future__ import annotations

from datetime import date

from stork_agent.connectors.base import BaseConnector
from stork_agent.models import PaperItem
from stork_agent.models import UserProfile


class WebOfScienceConnector(BaseConnector):
    name = "web_of_science"

    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        self.warnings.append("Web of Science connector is a skeleton. Use Clarivate Starter/Expanded API keys; access depends on institutional subscription.")
        return []


class ElsevierConnector(BaseConnector):
    name = "elsevier"

    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        self.warnings.append("Elsevier connector is a skeleton for Scopus Search API / ScienceDirect API with API key and institution token.")
        return []


class IEEEConnector(BaseConnector):
    name = "ieee"

    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        self.warnings.append("IEEE connector is a skeleton for Metadata Search API with API key.")
        return []


class AlertEmailConnector(BaseConnector):
    name = "alert_email"

    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        self.warnings.append("Alert email connector skeleton for WoS/Scopus/IEEE/ScienceDirect alert emails.")
        return []


class OpenURLResolver:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url

    def resolve(self, doi: str | None) -> str | None:
        if not self.base_url or not doi:
            return None
        return f"{self.base_url.rstrip('/')}?doi={doi}"

