from __future__ import annotations

import imaplib
from datetime import date

from stork_agent.connectors.base import BaseConnector
from stork_agent.models import PaperItem
from stork_agent.models import UserProfile
from stork_agent.summarizer import summarize_innovation
from stork_mailer.mailbox import ImapClient
from stork_mailer.parser import parse_stork_digest


class StorkEmailConnector(BaseConnector):
    name = "stork_email"

    def validate_config(self, profile: UserProfile | None = None) -> None:
        if not self.env.get("MAIL_USERNAME") or not self.env.get("MAIL_AUTH_CODE"):
            raise RuntimeError("MAIL_USERNAME and MAIL_AUTH_CODE are required for Stork email.")

    def fetch(self, profile: UserProfile, since: date, limit: int) -> list[PaperItem]:
        try:
            self.validate_config(profile)
            with ImapClient(
                self.env.get("IMAP_HOST", "imap.163.com"),
                int(self.env.get("IMAP_PORT", "993")),
                self.env["MAIL_USERNAME"],
                self.env["MAIL_AUTH_CODE"],
            ) as client:
                messages = client.fetch_recent_stork_messages(lookback_days=profile.lookback_days, limit=limit)
                papers: list[PaperItem] = []
                for message in messages:
                    for article in parse_stork_digest(message.content):
                        papers.append(
                            PaperItem(
                                title=article.title,
                                abstract=article.abstract,
                                venue=article.journal,
                                doi=article.doi,
                                source="Stork Email",
                                source_ids={"stork_email": article.doi or article.title},
                                matched_queries=profile.keywords,
                                keywords=tuple(keyword for keyword in profile.keywords if keyword.lower() in article.title.lower()),
                                innovation_summary=summarize_innovation(article.title, article.abstract) if article.abstract else article.innovation,
                            )
                        )
                if messages:
                    client.mark_seen([message.uid for message in messages])
                return papers
        except (RuntimeError, imaplib.IMAP4.error, OSError) as exc:
            self.warnings.append(str(exc))
            return []

