from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path

from stork_mailer.models import LiteratureItem
from stork_mailer.parser import Article
from stork_mailer.parser import article_to_item


def render_markdown(
    results: list[Article] | list[LiteratureItem] | dict[str, list[LiteratureItem]],
    report_date: date,
) -> str:
    grouped = normalize_results(results)
    total = sum(len(items) for items in grouped.values())
    lines = [
        f"# Stork 文献筛选日报 {report_date.isoformat()}",
        "",
        "筛选条件：半监督/弱监督医学图像分割相关文献；Stork 邮件结果保留邮件自带 SCI/JCR 分区，新增来源无分区时标为 Unknown。",
        "",
        f"共筛选出 {total} 篇。",
        "",
    ]

    for source, items in grouped.items():
        lines.extend([f"## {source}", ""])
        if not items:
            lines.extend(["无匹配文献。", ""])
            continue

        for index, item in enumerate(items, start=1):
            lines.extend(render_item(index, item))

    return "\n".join(lines).rstrip() + "\n"


def write_report(
    results: list[Article] | list[LiteratureItem] | dict[str, list[LiteratureItem]],
    report_date: date,
    output_dir: Path,
) -> Path | None:
    grouped = normalize_results(results)
    if not any(grouped.values()):
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report_date.isoformat()}.md"
    path.write_text(render_markdown(grouped, report_date), encoding="utf-8")
    return path


def normalize_results(
    results: list[Article] | list[LiteratureItem] | dict[str, list[LiteratureItem]],
) -> dict[str, list[LiteratureItem]]:
    if isinstance(results, dict):
        return {source: list(items) for source, items in results.items()}

    grouped: dict[str, list[LiteratureItem]] = defaultdict(list)
    for item in results:
        literature_item = article_to_item(item) if isinstance(item, Article) else item
        grouped[literature_item.source].append(literature_item)
    return dict(grouped)


def render_item(index: int, item: LiteratureItem) -> list[str]:
    lines = [
        f"### {index}. {item.title}",
        "",
        f"- 来源：{item.source}",
        f"- 分区：{item.quartile}",
        f"- 创新点：{item.innovation}",
    ]
    if item.venue:
        lines.append(f"- 期刊/会议：{item.venue}")
    if item.year:
        lines.append(f"- 年份：{item.year}")
    if item.doi:
        lines.append(f"- DOI：{item.doi}")
    if item.url:
        lines.append(f"- 链接：{item.url}")
    if item.matched_keywords:
        lines.append(f"- 匹配关键词：{', '.join(item.matched_keywords)}")
    if item.abstract:
        lines.extend(["", "<details>", "<summary>原始摘要</summary>", "", item.abstract, "", "</details>"])
    lines.append("")
    return lines

