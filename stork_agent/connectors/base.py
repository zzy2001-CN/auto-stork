from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from datetime import date

from stork_agent.models import PaperItem
from stork_agent.models import UserProfile


class ConnectorConfigError(RuntimeError):
    pass


class ConnectorFetchError(RuntimeError):
    pass


class BaseConnector(ABC):
    name = "base"

    def __init__(self, env: dict[str, str] | None = None) -> None:
        self.env = env or {}
        self.warnings: list[str] = []

    @property
    def enabled(self) -> bool:
        return True

    def validate_config(self, profile: UserProfile | None = None) -> None:
        return None

    @abstractmethod
    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        raise NotImplementedError

    def healthcheck(self) -> dict[str, str]:
        try:
            self.validate_config()
        except Exception as exc:
            return {"name": self.name, "status": "warning", "message": str(exc)}
        return {"name": self.name, "status": "ok", "message": "configured"}

