from __future__ import annotations

import json
import sqlite3
from dataclasses import fields
from datetime import datetime
from pathlib import Path

from stork_agent.models import PaperItem


SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  doi TEXT,
  source_ids TEXT NOT NULL,
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL,
  payload TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi) WHERE doi IS NOT NULL AND doi != '';
CREATE TABLE IF NOT EXISTS daily_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_date TEXT NOT NULL,
  profile TEXT NOT NULL,
  paper_count INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS user_feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  paper_key TEXT NOT NULL,
  feedback TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""


class SQLiteStore:
    def __init__(self, path: Path = Path("data/stork_agent.sqlite3")) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def seen_keys(self) -> set[str]:
        rows = self.conn.execute("SELECT doi, title FROM papers").fetchall()
        return {paper_key(doi, title) for doi, title in rows}

    def save_papers(self, papers: list[PaperItem]) -> None:
        now = datetime.utcnow().isoformat()
        for paper in papers:
            existing = self.conn.execute("SELECT id FROM papers WHERE title = ? OR (doi IS NOT NULL AND doi != '' AND doi = ?)", (paper.title, paper.doi)).fetchone()
            payload = json.dumps(paper.__dict__, ensure_ascii=False, default=str)
            if existing:
                self.conn.execute("UPDATE papers SET last_seen = ?, payload = ? WHERE id = ?", (now, payload, existing[0]))
            else:
                self.conn.execute(
                    "INSERT INTO papers(title, doi, source_ids, first_seen, last_seen, payload) VALUES (?, ?, ?, ?, ?, ?)",
                    (paper.title, paper.doi, json.dumps(paper.source_ids), now, now, payload),
                )
        self.conn.commit()

    def save_daily_run(self, run_date: str, profile: str, paper_count: int) -> None:
        self.conn.execute(
            "INSERT INTO daily_runs(run_date, profile, paper_count, created_at) VALUES (?, ?, ?, ?)",
            (run_date, profile, paper_count, datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def recent_runs(self, limit: int = 10) -> list[dict]:
        rows = self.conn.execute(
            "SELECT run_date, profile, paper_count, created_at FROM daily_runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {"run_date": row[0], "profile": row[1], "paper_count": row[2], "created_at": row[3]}
            for row in rows
        ]

    def recent_papers(self, limit: int = 20) -> list[PaperItem]:
        rows = self.conn.execute("SELECT payload FROM papers ORDER BY last_seen DESC LIMIT ?", (limit,)).fetchall()
        return [paper_from_payload(row[0]) for row in rows]

    def save_feedback(self, paper_key_value: str, feedback: str) -> None:
        self.conn.execute(
            "INSERT INTO user_feedback(paper_key, feedback, created_at) VALUES (?, ?, ?)",
            (paper_key_value, feedback, datetime.utcnow().isoformat()),
        )
        self.conn.commit()


def paper_key(doi: str | None, title: str) -> str:
    return (doi or title).lower().strip()


def paper_from_payload(payload: str) -> PaperItem:
    raw = json.loads(payload)
    allowed = {field.name for field in fields(PaperItem)}
    cleaned = {key: value for key, value in raw.items() if key in allowed}
    for key in ("authors", "keywords", "matched_queries"):
        if key in cleaned and isinstance(cleaned[key], list):
            cleaned[key] = tuple(cleaned[key])
    return PaperItem(**cleaned)

