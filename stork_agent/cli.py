from __future__ import annotations

import argparse
import os
from datetime import date
from datetime import timedelta
from pathlib import Path

from stork_agent.config import load_profiles
from stork_agent.config import write_default_profiles
from stork_agent.connectors import CONNECTORS
from stork_agent.pipeline import run_daily


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "init-config":
        created = write_default_profiles(Path(args.path))
        print(f"Created {args.path}" if created else f"{args.path} already exists")
        return 0
    if args.command == "run-daily":
        run_daily(dry_run=args.dry_run, profile_name=args.profile, output_dir=Path(args.output_dir), db_path=Path(args.db))
        return 0
    if args.command == "test-source":
        return test_source(args.source)
    return 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="auto-stork literature recommendation agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_config = subparsers.add_parser("init-config")
    init_config.add_argument("--path", default="config/profiles.yml")

    run_daily_parser = subparsers.add_parser("run-daily")
    run_daily_parser.add_argument("--dry-run", action="store_true")
    run_daily_parser.add_argument("--profile")
    run_daily_parser.add_argument("--output-dir", default="docs/stork")
    run_daily_parser.add_argument("--db", default="data/stork_agent.sqlite3")

    test_source_parser = subparsers.add_parser("test-source")
    test_source_parser.add_argument("source", choices=sorted(CONNECTORS))
    return parser.parse_args(argv)


def test_source(source_name: str) -> int:
    profile = load_profiles()[0]
    connector = CONNECTORS[source_name](dict(os.environ))
    health = connector.healthcheck()
    print(f"{health['name']}: {health['status']} - {health['message']}")
    since = date.today() - timedelta(days=min(profile.lookback_days, 7))
    try:
        papers = connector.fetch(profile, since, min(profile.daily_limit, 5))
    except Exception as exc:
        print(f"Fetch failed: {exc}")
        return 0
    print(f"Fetched {len(papers)} paper(s).")
    for paper in papers[:5]:
        print(f"- {paper.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
