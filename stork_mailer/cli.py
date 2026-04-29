from __future__ import annotations

import argparse
import email
import os
import sys
from datetime import date
from pathlib import Path

from stork_mailer.mailbox import extract_message_content
from stork_mailer.mailbox import ImapClient
from stork_mailer.parser import parse_stork_digest
from stork_mailer.report import render_markdown, write_report


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report_date = date.fromisoformat(args.date) if args.date else date.today()

    if args.sample:
        content = load_sample_content(Path(args.sample))
        articles = parse_stork_digest(content)
        if args.dry_run:
            print(render_markdown(articles, report_date) if articles else "No matching articles.")
            return 0
        path = write_report(articles, report_date, Path(args.output_dir))
        print(f"Wrote {path}" if path else "No matching articles; report not written.")
        return 0

    username = os.environ.get("MAIL_USERNAME")
    auth_code = os.environ.get("MAIL_AUTH_CODE")
    if not username or not auth_code:
        print("MAIL_USERNAME and MAIL_AUTH_CODE are required.", file=sys.stderr)
        return 2

    host = os.environ.get("IMAP_HOST", "imap.163.com")
    port = int(os.environ.get("IMAP_PORT", "993"))

    with ImapClient(host, port, username, auth_code) as client:
        messages = client.fetch_recent_stork_messages(
            mailbox=args.mailbox,
            lookback_days=args.lookback_days,
            limit=args.limit,
            from_filter=args.from_filter,
            subject_filter=args.subject_filter,
            readonly=args.dry_run,
        )
        articles = []
        for message in messages:
            articles.extend(parse_stork_digest(message.content))

        if args.dry_run:
            print(render_markdown(articles, report_date) if articles else "No matching articles.")
            return 0

        path = write_report(articles, report_date, Path(args.output_dir))
        if messages:
            client.mark_seen([message.uid for message in messages])
        print(f"Wrote {path}" if path else "No matching articles; report not written.")
        return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect and filter Stork daily email digests.")
    parser.add_argument("--sample", help="Parse a local .html/.txt sample instead of connecting to IMAP.")
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing files or marking mail read.")
    parser.add_argument("--date", help="Report date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--output-dir", default="docs/stork", help="Directory for generated Markdown reports.")
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


if __name__ == "__main__":
    raise SystemExit(main())
