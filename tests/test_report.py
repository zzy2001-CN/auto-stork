from datetime import date

from stork_mailer.models import LiteratureItem
from stork_mailer.parser import Article
from stork_mailer.report import render_markdown


def test_render_markdown_contains_required_fields_for_articles() -> None:
    markdown = render_markdown(
        [
            Article(
                title="Semi-supervised Medical Image Segmentation",
                ranking="Q1",
                innovation="A novel framework is proposed.",
                journal="Medical Image Analysis",
                doi="10.1234/example",
            )
        ],
        date(2026, 4, 28),
    )

    assert "# Literature Digest 2026-04-28" in markdown
    assert "Total recommendations: 1" in markdown
    assert "- Score: 0.0" in markdown
    assert "- Innovation: A novel framework is proposed." in markdown


def test_render_markdown_groups_multiple_sources() -> None:
    markdown = render_markdown(
        {
            "OpenAlex": [
                LiteratureItem(
                    title="OpenAlex Paper",
                    source="OpenAlex",
                    quartile="Unknown",
                    innovation="A novel method is proposed.",
                    venue="Example Journal",
                    year=2026,
                    doi="10.1234/openalex",
                    url="https://doi.org/10.1234/openalex",
                    matched_keywords=("semi-supervised medical image segmentation",),
                )
            ],
            "Semantic Scholar": [
                LiteratureItem(
                    title="Semantic Scholar Paper",
                    source="Semantic Scholar",
                    quartile="Unknown",
                    innovation="This framework improves CT segmentation.",
                )
            ],
        },
        date(2026, 4, 28),
    )

    assert "## 1. OpenAlex Paper" in markdown
    assert "## 2. Semantic Scholar Paper" in markdown
    assert "- Source: OpenAlex" in markdown
    assert "- Matched queries: semi-supervised medical image segmentation" in markdown
