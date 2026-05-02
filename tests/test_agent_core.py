from datetime import date

from stork_agent.config import legacy_search_to_profile
from stork_agent.deduper import dedupe_papers
from stork_agent.models import PaperItem
from stork_agent.models import UserProfile
from stork_agent.ranker import rank_paper
from stork_agent.summarizer import summarize_innovation


def test_dedupe_prefers_doi_then_merges_sources() -> None:
    papers = dedupe_papers(
        [
            PaperItem(title="Paper A", doi="10.1/ABC", source="OpenAlex"),
            PaperItem(title="Different title", doi="10.1/abc", source="Semantic Scholar"),
        ]
    )

    assert len(papers) == 1
    assert papers[0].source == "Multiple Sources"


def test_ranker_adds_score_and_reason() -> None:
    paper = PaperItem(
        title="Semi-supervised medical image segmentation",
        abstract="We propose a novel framework for medical image segmentation.",
        publication_date="2026-05-01",
        source="OpenAlex / Semantic Scholar",
        keywords=("segmentation",),
        citation_count=20,
    )
    ranked = rank_paper(
        paper,
        UserProfile(name="default", keywords=("semi-supervised medical image segmentation",)),
        date(2026, 5, 2),
    )

    assert ranked.recommendation_score > 0
    assert "matched" in ranked.recommendation_reason


def test_summarizer_handles_missing_abstract() -> None:
    assert summarize_innovation("A title", None) == "摘要缺失，需人工判断"

