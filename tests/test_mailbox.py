import pytest

from stork_mailer.mailbox import ImapClient
from stork_mailer.mailbox import unique_mailbox_candidates


class FakeConnection:
    def __init__(self) -> None:
        self.calls = []

    def select(self, mailbox: str, readonly: bool = False):
        self.calls.append((mailbox, readonly))
        if mailbox == '"INBOX"':
            return "OK", [b"1"]
        return "NO", [b"no such mailbox"]


class AlwaysFailConnection:
    def select(self, mailbox: str, readonly: bool = False):
        return "NO", [b"no such mailbox"]


def test_unique_mailbox_candidates_dedupes_inbox() -> None:
    assert unique_mailbox_candidates("INBOX") == ["INBOX", '"INBOX"']


def test_select_mailbox_tries_quoted_inbox_fallback() -> None:
    client = ImapClient("imap.example.com", 993, "user", "code")
    fake = FakeConnection()
    client.connection = fake

    client.select_mailbox("INBOX", readonly=True)

    assert fake.calls == [("INBOX", True), ('"INBOX"', True)]


def test_select_mailbox_raises_clear_error() -> None:
    client = ImapClient("imap.example.com", 993, "user", "code")
    client.connection = AlwaysFailConnection()

    with pytest.raises(RuntimeError, match="Unable to select IMAP mailbox"):
        client.select_mailbox("Archive")
