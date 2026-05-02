from datetime import date

import yaml

from stork_agent.config import legacy_search_to_profile
from stork_agent.models import PaperItem
from stork_agent.models import UserProfile
from stork_agent.report.html import render_html


def test_legacy_search_yml_converts_to_default_profile(tmp_path) -> None:
    path = tmp_path / "search.yml"
    path.write_text(
        yaml.safe_dump(
            {
                "queries": ["semi-supervised segmentation"],
                "sources": ["stork", "openalex"],
                "lookback_days": 3,
                "per_query_limit": 5,
            }
        ),
        encoding="utf-8",
    )

    profile = legacy_search_to_profile(path)

    assert profile.name == "default"
    assert profile.keywords == ("semi-supervised segmentation",)
    assert profile.sources == ("stork_email", "openalex")
    assert profile.lookback_days == 3
    assert profile.daily_limit == 5


def test_html_report_contains_score_reason_and_summary() -> None:
    html = render_html(
        [
            PaperItem(
                title="Paper",
                source="OpenAlex",
                recommendation_score=42,
                recommendation_reason="matched profile",
                innovation_summary="We propose a method.",
            )
        ],
        UserProfile(name="default", keywords=("paper",)),
        date(2026, 5, 2),
    )

    assert "Score: 42" in html
    assert "matched profile" in html
    assert "We propose a method." in html
