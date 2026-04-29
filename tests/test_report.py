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

    assert "# Stork 文献筛选日报 2026-04-28" in markdown
    assert "## Stork Email" in markdown
    assert "- 分区：Q1" in markdown
    assert "- 创新点：A novel framework is proposed." in markdown


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

    assert "## OpenAlex" in markdown
    assert "## Semantic Scholar" in markdown
    assert "- 分区：Unknown" in markdown
    assert "- 匹配关键词：semi-supervised medical image segmentation" in markdown
