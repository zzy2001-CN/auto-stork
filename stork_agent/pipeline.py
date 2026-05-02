from __future__ import annotations

import os
import sys
from datetime import date
from datetime import timedelta
from pathlib import Path

from stork_agent.config import load_profiles
from stork_agent.connectors import CONNECTORS
from stork_agent.deduper import dedupe_papers
from stork_agent.models import PaperItem
from stork_agent.models import UserProfile
from stork_agent.ranker import rank_papers
from stork_agent.report.html import write_html
from stork_agent.report.markdown import write_markdown
from stork_agent.storage.sqlite import SQLiteStore
from stork_agent.storage.sqlite import paper_key


def run_daily(
    *,
    dry_run: bool = False,
    profile_name: str | None = None,
    output_dir: Path = Path("docs/stork"),
    db_path: Path = Path("data/stork_agent.sqlite3"),
    today: date | None = None,
) -> list[PaperItem]:
    today = today or date.today()
    profile = select_profile(load_profiles(), profile_name)
    since = today - timedelta(days=profile.lookback_days)
    papers = collect_profile_papers(profile, since)
    papers = dedupe_papers(papers)
    papers = rank_papers(papers, profile, today)
    papers = [paper for paper in papers if paper.recommendation_score >= profile.min_score]
    papers = papers[: profile.daily_limit]

    store = SQLiteStore(db_path)
    try:
        seen = store.seen_keys()
        new_papers = [paper for paper in papers if paper_key(paper.doi, paper.title) not in seen]
        if dry_run:
            print(f"Dry run: {len(new_papers)} new recommendation(s).")
            for paper in new_papers:
                print(f"- [{paper.recommendation_score}] {paper.title} ({paper.source})")
            return new_papers
        store.save_papers(new_papers)
        store.save_daily_run(today.isoformat(), profile.name, len(new_papers))
        write_markdown(new_papers, profile, today, output_dir)
        write_html(new_papers, profile, today, output_dir)
        return new_papers
    finally:
        store.close()


def collect_profile_papers(profile: UserProfile, since: date) -> list[PaperItem]:
    env = dict(os.environ)
    papers: list[PaperItem] = []
    for source_name in profile.sources:
        connector_cls = CONNECTORS.get(source_name)
        if not connector_cls:
            print(f"Warning: unknown source {source_name}; skipped.", file=sys.stderr)
            continue
        connector = connector_cls(env)
        try:
            fetched = connector.fetch(profile, since, profile.daily_limit)
        except Exception as exc:
            print(f"Warning: skipped {source_name}: {exc}", file=sys.stderr)
            fetched = []
        for warning in connector.warnings:
            print(f"Warning: {source_name}: {warning}", file=sys.stderr)
        papers.extend(filter_excluded(fetched, profile))
    return papers


def filter_excluded(papers: list[PaperItem], profile: UserProfile) -> list[PaperItem]:
    excluded = tuple(keyword.lower() for keyword in profile.exclude_keywords)
    if not excluded:
        return papers
    kept = []
    for paper in papers:
        haystack = " ".join(value for value in (paper.title, paper.abstract, paper.venue) if value).lower()
        if not any(keyword in haystack for keyword in excluded):
            kept.append(paper)
    return kept


def select_profile(profiles: list[UserProfile], name: str | None) -> UserProfile:
    if name is None:
        return profiles[0]
    for profile in profiles:
        if profile.name == name:
            return profile
    raise ValueError(f"Unknown profile: {name}")

