from datetime import date

from stork_mailer.parser import Article
from stork_mailer.report import render_markdown


def test_render_markdown_contains_required_fields() -> None:
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
    assert "文章" not in markdown
    assert "- 分区：Q1" in markdown
    assert "- 创新点：A novel framework is proposed." in markdown

