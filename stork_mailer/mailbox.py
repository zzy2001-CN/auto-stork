from __future__ import annotations

import email
import imaplib
from dataclasses import dataclass
from datetime import date, timedelta
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime


@dataclass(frozen=True)
class MailMessage:
    uid: bytes
    subject: str
    sender: str
    sent_at: str | None
    content: str


class ImapClient:
    def __init__(self, host: str, port: int, username: str, auth_code: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.auth_code = auth_code
        self.connection: imaplib.IMAP4_SSL | None = None

    def __enter__(self) -> "ImapClient":
        self.connection = imaplib.IMAP4_SSL(self.host, self.port)
        self.connection.login(self.username, self.auth_code)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.connection is None:
            return
        try:
            self.connection.logout()
        finally:
            self.connection = None

    def fetch_recent_stork_messages(
        self,
        mailbox: str = "INBOX",
        lookback_days: int = 7,
        limit: int = 10,
        from_filter: str = "stork",
        subject_filter: str = "stork",
    ) -> list[MailMessage]:
        conn = self._connection()
        conn.select(mailbox)
        since = (date.today() - timedelta(days=lookback_days)).strftime("%d-%b-%Y")
        status, data = conn.uid("SEARCH", None, "SINCE", since)
        if status != "OK" or not data:
            return []

        uids = data[0].split()
        messages: list[MailMessage] = []
        for uid in reversed(uids):
            status, fetched = conn.uid("FETCH", uid, "(BODY.PEEK[])")
            if status != "OK" or not fetched:
                continue
            raw = next((item[1] for item in fetched if isinstance(item, tuple)), None)
            if not raw:
                continue
            message = parse_email_message(uid, raw)
            if is_stork_message(message, from_filter, subject_filter):
                messages.append(message)
            if len(messages) >= limit:
                break
        return list(reversed(messages))

    def mark_seen(self, uids: list[bytes]) -> None:
        if not uids:
            return
        conn = self._connection()
        for uid in uids:
            conn.uid("STORE", uid, "+FLAGS", "(\\Seen)")

    def _connection(self) -> imaplib.IMAP4_SSL:
        if self.connection is None:
            raise RuntimeError("IMAP connection is not open")
        return self.connection


def parse_email_message(uid: bytes, raw: bytes) -> MailMessage:
    message = email.message_from_bytes(raw)
    subject = decode_mime_header(message.get("Subject", ""))
    sender = decode_mime_header(message.get("From", ""))
    sent_at = parse_sent_at(message)
    return MailMessage(
        uid=uid,
        subject=subject,
        sender=sender,
        sent_at=sent_at,
        content=extract_message_content(message),
    )


def is_stork_message(message: MailMessage, from_filter: str, subject_filter: str) -> bool:
    sender = message.sender.lower()
    subject = message.subject.lower()
    return from_filter.lower() in sender or subject_filter.lower() in subject


def extract_message_content(message: Message) -> str:
    html_part: str | None = None
    text_part: str | None = None

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()
            if disposition == "attachment":
                continue
            payload = decode_part(part)
            if not payload:
                continue
            if content_type == "text/html" and html_part is None:
                html_part = payload
            elif content_type == "text/plain" and text_part is None:
                text_part = payload
    else:
        payload = decode_part(message)
        if message.get_content_type() == "text/html":
            html_part = payload
        else:
            text_part = payload

    return html_part or text_part or ""


def decode_part(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        raw = part.get_payload()
        return raw if isinstance(raw, str) else ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def decode_mime_header(value: str) -> str:
    chunks = []
    for chunk, charset in decode_header(value):
        if isinstance(chunk, bytes):
            chunks.append(chunk.decode(charset or "utf-8", errors="replace"))
        else:
            chunks.append(chunk)
    return "".join(chunks).strip()


def parse_sent_at(message: Message) -> str | None:
    value = message.get("Date")
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError):
        return value

