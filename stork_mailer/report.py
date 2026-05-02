from __future__ import annotations

from datetime import date
from pathlib import Path

from stork_agent.models import PaperItem
from stork_agent.models import UserProfile
from stork_agent.report.markdown import render_markdown as render_agent_markdown
from stork_agent.report.markdown import write_markdown
from stork_mailer.models import LiteratureItem
from stork_mailer.parser import Article
from stork_mailer.parser import article_to_item


def render_markdown(results, report_date: date) -> str:
    papers = [legacy_to_paper(item) for item in flatten(results)]
    return render_agent_markdown(papers, UserProfile(name="legacy", keywords=()), report_date)


def write_report(results, report_date: date, output_dir: Path) -> Path | None:
    papers = [legacy_to_paper(item) for item in flatten(results)]
    return write_markdown(papers, UserProfile(name="legacy", keywords=()), report_date, output_dir)


def flatten(results) -> list:
    if isinstance(results, dict):
        return [item for items in results.values() for item in items]
    return list(results)


def legacy_to_paper(item) -> PaperItem:
    if isinstance(item, Article):
        item = article_to_item(item)
    if isinstance(item, LiteratureItem):
        return PaperItem(
            title=item.title,
            abstract=item.abstract,
            year=item.year,
            venue=item.venue,
            doi=item.doi,
            url=item.url,
            source=item.source,
            matched_queries=item.matched_keywords,
            innovation_summary=item.innovation,
        )
    return item
