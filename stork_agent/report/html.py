from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path

from stork_agent.models import PaperItem
from stork_agent.models import UserProfile


def render_html(papers: list[PaperItem], profile: UserProfile, report_date: date) -> str:
    rows = "\n".join(render_paper(paper, index) for index, paper in enumerate(papers, start=1))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Literature Digest {report_date.isoformat()}</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 960px; margin: 32px auto; line-height: 1.5; color: #1f2933; }}
    article {{ border-bottom: 1px solid #d9e2ec; padding: 20px 0; }}
    .meta {{ color: #52606d; font-size: 14px; }}
    .score {{ font-weight: 700; }}
  </style>
</head>
<body>
  <h1>Literature Digest {report_date.isoformat()}</h1>
  <p>Profile: <code>{escape(profile.name)}</code>. Total recommendations: {len(papers)}.</p>
  {rows}
</body>
</html>
"""


def render_paper(paper: PaperItem, index: int) -> str:
    url = f'<p><a href="{escape(paper.url)}">Open record</a></p>' if paper.url else ""
    library_url = f'<p><a href="{escape(paper.library_access_url)}">Library link</a></p>' if paper.library_access_url else ""
    abstract = f"<details><summary>Abstract</summary><p>{escape(paper.abstract)}</p></details>" if paper.abstract else ""
    return f"""<article>
  <h2>{index}. {escape(paper.title)}</h2>
  <p class="meta">{escape(paper.source)} · {escape(paper.venue or 'Unknown venue')} · {paper.year or 'Unknown year'}</p>
  <p class="score">Score: {paper.recommendation_score}</p>
  <p><strong>Reason:</strong> {escape(paper.recommendation_reason)}</p>
  <p><strong>Innovation:</strong> {escape(paper.innovation_summary)}</p>
  {url}
  {library_url}
  {abstract}
</article>"""


def write_html(papers: list[PaperItem], profile: UserProfile, report_date: date, output_dir: Path) -> Path | None:
    if not papers:
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report_date.isoformat()}.html"
    path.write_text(render_html(papers, profile, report_date), encoding="utf-8")
    return path
