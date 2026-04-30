from __future__ import annotations

import argparse
import email
import imaplib
import os
import sys
from datetime import date
from pathlib import Path

from stork_mailer.config import load_search_config
from stork_mailer.mailbox import extract_message_content
from stork_mailer.mailbox import ImapClient
from stork_mailer.models import dedupe_by_title
from stork_mailer.parser import parse_stork_digest_items
from stork_mailer.report import render_markdown, write_report
from stork_mailer.sources import SourceError
from stork_mailer.sources import fetch_openalex_items
from stork_mailer.sources import fetch_semantic_scholar_items


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report_date = date.fromisoformat(args.date) if args.date else date.today()
    config = load_search_config(Path(args.config))
    enabled_sources = parse_sources(args.sources) or config.sources

    if args.sample:
        content = load_sample_content(Path(args.sample))
        items = parse_stork_digest_items(content)
        grouped = {"Stork Email": items}
        if args.dry_run:
            print(render_markdown(grouped, report_date) if items else "No matching articles.")
            return 0
        path = write_report(grouped, report_date, Path(args.output_dir))
        print(f"Wrote {path}" if path else "No matching articles; report not written.")
        return 0

    grouped_results: dict[str, list] = {}
    stork_messages = []

    if "stork" in enabled_sources:
        grouped_results["Stork Email"] = collect_stork_items(args)

    if "openalex" in enabled_sources:
        grouped_results["OpenAlex"] = collect_source(
            "OpenAlex",
            lambda: fetch_openalex_items(
                config,
                api_key=os.environ.get("OPENALEX_API_KEY"),
                mailto=os.environ.get("OPENALEX_MAILTO"),
                today=report_date,
            ),
        )

    if "semantic_scholar" in enabled_sources:
        grouped_results["Semantic Scholar"] = collect_source(
            "Semantic Scholar",
            lambda: fetch_semantic_scholar_items(
                config,
                api_key=os.environ.get("SEMANTIC_SCHOLAR_API_KEY"),
                today=report_date,
            ),
        )

    grouped_results = dedupe_grouped_results(grouped_results)

    if args.dry_run:
        total = sum(len(items) for items in grouped_results.values())
        print(render_markdown(grouped_results, report_date) if total else "No matching articles.")
        return 0

    path = write_report(grouped_results, report_date, Path(args.output_dir))
    print(f"Wrote {path}" if path else "No matching articles; report not written.")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect and filter Stork daily email digests.")
    parser.add_argument("--sample", help="Parse a local .html/.txt sample instead of connecting to IMAP.")
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing files or marking mail read.")
    parser.add_argument("--date", help="Report date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--output-dir", default="docs/stork", help="Directory for generated Markdown reports.")
    parser.add_argument("--config", default="config/search.yml", help="Search configuration YAML path.")
    parser.add_argument(
        "--sources",
        help="Comma-separated sources to run. Defaults to config sources. Values: stork,openalex,semantic_scholar.",
    )
    parser.add_argument("--mailbox", default="INBOX", help="IMAP mailbox to scan.")
    parser.add_argument("--lookback-days", type=int, default=7, help="How many recent days of email to inspect.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum Stork messages to parse.")
    parser.add_argument("--from-filter", default="stork", help="Substring that identifies Stork sender addresses.")
    parser.add_argument("--subject-filter", default="stork", help="Substring that identifies Stork subjects.")
    return parser.parse_args(argv)


def load_sample_content(path: Path) -> str:
    if path.suffix.lower() == ".eml":
        message = email.message_from_bytes(path.read_bytes())
        return extract_message_content(message)
    return path.read_text(encoding="utf-8")


def parse_sources(value: str | None) -> tuple[str, ...] | None:
    if not value:
        return None
    return tuple(part.strip() for part in value.split(",") if part.strip())


def collect_source(name: str, fetcher):
    try:
        return dedupe_by_title(fetcher())
    except SourceError as exc:
        print(f"Warning: skipped {name}: {exc}", file=sys.stderr)
        return []


def collect_stork_items(args: argparse.Namespace):
    username = os.environ.get("MAIL_USERNAME")
    auth_code = os.environ.get("MAIL_AUTH_CODE")
    if not username or not auth_code:
        print("Warning: skipped Stork Email: MAIL_USERNAME or MAIL_AUTH_CODE is missing.", file=sys.stderr)
        return []

    host = os.environ.get("IMAP_HOST", "imap.163.com")
    port = int(os.environ.get("IMAP_PORT", "993"))

    try:
        with ImapClient(host, port, username, auth_code) as client:
            messages = client.fetch_recent_stork_messages(
                mailbox=args.mailbox,
                lookback_days=args.lookback_days,
                limit=args.limit,
                from_filter=args.from_filter,
                subject_filter=args.subject_filter,
                readonly=args.dry_run,
            )
            items = []
            for message in messages:
                items.extend(parse_stork_digest_items(message.content))

            if not args.dry_run and messages:
                client.mark_seen([message.uid for message in messages])
            return dedupe_by_title(items)
    except (imaplib.IMAP4.error, OSError, RuntimeError) as exc:
        print(f"Warning: skipped Stork Email: {exc}", file=sys.stderr)
        return []


def dedupe_grouped_results(grouped_results: dict[str, list]) -> dict[str, list]:
    deduped = dedupe_by_title(
        [item for items in grouped_results.values() for item in items]
    )
    regrouped: dict[str, list] = {}
    for item in deduped:
        source = "Multiple Sources" if " / " in item.source else item.source
        regrouped.setdefault(source, []).append(item)
    return regrouped


if __name__ == "__main__":
    raise SystemExit(main())
