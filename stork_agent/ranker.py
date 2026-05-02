from __future__ import annotations

from dataclasses import replace
from datetime import date

from stork_agent.models import PaperItem
from stork_agent.models import UserProfile


def rank_papers(papers: list[PaperItem], profile: UserProfile, today: date | None = None) -> list[PaperItem]:
    today = today or date.today()
    ranked = [rank_paper(paper, profile, today) for paper in papers]
    return sorted(ranked, key=lambda item: item.recommendation_score, reverse=True)


def rank_paper(paper: PaperItem, profile: UserProfile, today: date) -> PaperItem:
    score = 0.0
    reasons: list[str] = []
    haystack = " ".join(value for value in (paper.title, paper.abstract, paper.venue) if value).lower()

    matched = [keyword for keyword in profile.keywords if keyword.lower() in haystack]
    if matched:
        score += min(40.0, 15.0 + 5.0 * len(matched))
        reasons.append(f"matched {len(matched)} profile keyword(s)")

    if paper.publication_date:
        try:
            age_days = (today - date.fromisoformat(paper.publication_date[:10])).days
            if age_days <= 14:
                score += 20.0
                reasons.append("recent publication")
        except ValueError:
            pass

    source_count = len(paper.source.split(" / "))
    if source_count > 1 or paper.source == "Multiple Sources":
        score += 15.0
        reasons.append("found in multiple sources")

    if paper.citation_count:
        score += min(15.0, paper.citation_count / 10.0)
        reasons.append("citation signal")

    venue = (paper.venue or "").lower()
    if any(focus.lower() in venue for focus in profile.focus_venues):
        score += 10.0
        reasons.append("preferred venue")

    if paper.keywords:
        score += min(10.0, len(paper.keywords) * 2.0)
        reasons.append("keyword overlap")

    return replace(
        paper,
        recommendation_score=round(score, 2),
        recommendation_reason="; ".join(reasons) if reasons else "low-confidence match from configured sources",
    )

