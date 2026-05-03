from __future__ import annotations

from datetime import date
from pathlib import Path

from stork_agent.models import PaperItem
from stork_agent.models import UserProfile


def render_markdown(papers: list[PaperItem], profile: UserProfile, report_date: date) -> str:
    lines = [
        f"# Literature Digest {report_date.isoformat()}",
        "",
        f"Profile: `{profile.name}`",
        f"Total recommendations: {len(papers)}",
        "",
    ]
    for index, paper in enumerate(papers, start=1):
        lines.extend(
            [
                f"## {index}. {paper.title}",
                "",
                f"- Source: {paper.source}",
                f"- Score: {paper.recommendation_score}",
                f"- Reason: {paper.recommendation_reason}",
                f"- Innovation: {paper.innovation_summary}",
            ]
        )
        if paper.authors:
            lines.append(f"- Authors: {', '.join(paper.authors[:8])}")
        if paper.venue:
            lines.append(f"- Venue: {paper.venue}")
        if paper.year:
            lines.append(f"- Year: {paper.year}")
        if paper.doi:
            lines.append(f"- DOI: {paper.doi}")
        if paper.url:
            lines.append(f"- URL: {paper.url}")
        if paper.library_access_url:
            lines.append(f"- Library Link: {paper.library_access_url}")
        if paper.matched_queries:
            lines.append(f"- Matched queries: {', '.join(paper.matched_queries)}")
        if paper.abstract:
            lines.extend(["", "<details>", "<summary>Abstract</summary>", "", paper.abstract, "", "</details>"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_markdown(papers: list[PaperItem], profile: UserProfile, report_date: date, output_dir: Path) -> Path | None:
    if not papers:
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report_date.isoformat()}.md"
    path.write_text(render_markdown(papers, profile, report_date), encoding="utf-8")
    return path

