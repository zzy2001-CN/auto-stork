from __future__ import annotations

from datetime import date
from pathlib import Path

from stork_mailer.parser import Article


def render_markdown(articles: list[Article], report_date: date) -> str:
    lines = [
        f"# Stork 文献筛选日报 {report_date.isoformat()}",
        "",
        f"筛选条件：SCI/JCR 1-2 区，且主题与半监督医学图像分割相关。",
        "",
        f"共筛选出 {len(articles)} 篇。",
        "",
    ]

    for index, article in enumerate(articles, start=1):
        lines.extend(
            [
                f"## {index}. {article.title}",
                "",
                f"- 分区：{article.ranking}",
                f"- 创新点：{article.innovation}",
            ]
        )
        if article.journal:
            lines.append(f"- 期刊：{article.journal}")
        if article.doi:
            lines.append(f"- DOI：{article.doi}")
        if article.abstract:
            lines.extend(["", "<details>", "<summary>原始摘要</summary>", "", article.abstract, "", "</details>"])
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_report(articles: list[Article], report_date: date, output_dir: Path) -> Path | None:
    if not articles:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report_date.isoformat()}.md"
    path.write_text(render_markdown(articles, report_date), encoding="utf-8")
    return path

