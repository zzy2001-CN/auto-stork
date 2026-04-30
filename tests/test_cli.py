from argparse import Namespace

from stork_mailer.cli import collect_stork_items


def test_collect_stork_items_skips_missing_credentials(monkeypatch) -> None:
    monkeypatch.delenv("MAIL_USERNAME", raising=False)
    monkeypatch.delenv("MAIL_AUTH_CODE", raising=False)

    items = collect_stork_items(
        Namespace(
            mailbox="INBOX",
            lookback_days=7,
            limit=10,
            from_filter="stork",
            subject_filter="stork",
            dry_run=True,
        )
    )

    assert items == []
