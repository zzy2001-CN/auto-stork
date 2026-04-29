from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from typing import Iterable

from bs4 import BeautifulSoup

from stork_mailer.models import LiteratureItem


RANKING_RE = re.compile(
    r"\b(?:JCR\s*)?Q\s*([12])\b|SCI\s*([一二12])\s*区|(?:中科院|CAS)\s*([一二12])\s*区",
    re.IGNORECASE,
)
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)

TOPIC_KEYWORDS = (
    "semi-supervised",
    "semisupervised",
    "semi supervised",
    "weakly supervised",
    "scribble",
    "pseudo-label",
    "pseudo label",
    "consistency regularization",
    "medical image segmentation",
    "medical imaging segmentation",
    "medical image",
    "segmentation",
    "mri",
    "ct",
    "ultrasound",
    "histopathology",
    "retinal",
)

INNOVATION_HINTS = (
    "propose",
    "proposes",
    "proposed",
    "novel",
    "method",
    "framework",
    "contribution",
    "improve",
    "improves",
    "improved",
    "introduce",
    "introduces",
    "present",
    "presents",
)


@dataclass(frozen=True)
class Article:
    title: str
    ranking: str
    innovation: str
    journal: str | None = None
    doi: str | None = None
    abstract: str | None = None


def parse_stork_digest(content: str) -> list[Article]:
    """Parse Stork email HTML/text into filtered articles."""
    text = html_to_text(content)
    blocks = split_article_blocks(text)
    articles: list[Article] = []

    for block in blocks:
        parsed = parse_article_block(block)
        if parsed is not None and is_relevant_article(parsed):
            articles.append(parsed)

    return dedupe_articles(articles)


def parse_stork_digest_items(content: str) -> list[LiteratureItem]:
    return [article_to_item(article) for article in parse_stork_digest(content)]


def article_to_item(article: Article) -> LiteratureItem:
    return LiteratureItem(
        title=article.title,
        source="Stork Email",
        quartile=article.ranking,
        innovation=article.innovation,
        venue=article.journal,
        doi=article.doi,
        abstract=article.abstract,
        matched_keywords=matched_topic_keywords(
            " ".join(value for value in (article.title, article.abstract, article.journal) if value)
        ),
    )


def html_to_text(content: str) -> str:
    if looks_like_html(content):
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n")
    else:
        text = content

    text = unescape(text).replace("\r\n", "\n").replace("\r", "\n")
    lines = [normalize_spaces(line) for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def looks_like_html(content: str) -> bool:
    return bool(re.search(r"<(?:html|body|div|table|p|li|br|span|a)\b", content, re.I))


def split_article_blocks(text: str) -> list[str]:
    lines = text.splitlines()
    marker_indexes = [
        idx
        for idx, line in enumerate(lines)
        if re.match(r"^(?:title|paper|article|论文|题目)\s*[:：]", line, re.I)
    ]

    if len(marker_indexes) >= 2:
        blocks = []
        for pos, start in enumerate(marker_indexes):
            end = marker_indexes[pos + 1] if pos + 1 < len(marker_indexes) else len(lines)
            blocks.append("\n".join(lines[start:end]))
        return blocks

    chunks = re.split(r"\n\s*(?:[-=]{3,}|#{2,}|\d+\s*[.)、]\s+)\s*", text)
    candidates = [chunk.strip() for chunk in chunks if len(chunk.strip()) > 40]
    if len(candidates) > 1:
        return candidates

    return [text] if text.strip() else []


def parse_article_block(block: str) -> Article | None:
    ranking = extract_ranking(block)
    if ranking is None:
        return None

    title = extract_field(block, ("title", "paper", "article", "题目", "论文题目"))
    abstract = extract_field(block, ("abstract", "summary", "摘要"))
    journal = extract_field(block, ("journal", "source", "期刊", "来源"))
    doi = extract_doi(block)

    if title is None:
        title = infer_title(block)

    if not title:
        return None

    abstract = clean_optional(abstract)
    innovation = summarize_innovation(abstract or block)
    return Article(
        title=title,
        ranking=ranking,
        innovation=innovation,
        journal=clean_optional(journal),
        doi=doi,
        abstract=abstract,
    )


def extract_ranking(text: str) -> str | None:
    match = RANKING_RE.search(text)
    if match is None:
        return None
    raw = next(group for group in match.groups() if group)
    normalized = {"一": "1", "二": "2"}.get(raw, raw)
    return f"Q{normalized}"


def extract_field(text: str, labels: Iterable[str]) -> str | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    pattern = re.compile(
        rf"^(?:{label_pattern})\s*[:：]\s*(.+?)(?=\n(?:[A-Za-z][\w /-]{{1,30}}|[\u4e00-\u9fff]{{1,8}})\s*[:：]|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return None
    return normalize_spaces(match.group(1))


def extract_doi(text: str) -> str | None:
    match = DOI_RE.search(text)
    return match.group(0).rstrip(".") if match else None


def infer_title(text: str) -> str | None:
    for line in text.splitlines():
        clean = normalize_spaces(line)
        if not clean:
            continue
        if ":" in clean or "：" in clean:
            continue
        if RANKING_RE.search(clean) or len(clean) < 8:
            continue
        return clean[:240]
    return None


def is_relevant_article(article: Article) -> bool:
    haystack = " ".join(
        item for item in (article.title, article.abstract, article.journal) if item
    ).lower()
    has_semi_supervised = any(
        keyword in haystack
        for keyword in (
            "semi-supervised",
            "semisupervised",
            "semi supervised",
            "weakly supervised",
            "scribble",
            "pseudo-label",
            "pseudo label",
            "consistency regularization",
        )
    )
    has_medical_segmentation = (
        "segmentation" in haystack
        and any(
            keyword in haystack
            for keyword in (
                "medical",
                "mri",
                "ct",
                "ultrasound",
                "histopathology",
                "retinal",
            )
        )
    )
    return has_semi_supervised and has_medical_segmentation


def matched_topic_keywords(text: str) -> tuple[str, ...]:
    lower = text.lower()
    return tuple(keyword for keyword in TOPIC_KEYWORDS if keyword in lower)


def summarize_innovation(text: str, max_sentences: int = 2) -> str:
    sentences = split_sentences(text)
    hinted = [
        sentence
        for sentence in sentences
        if any(hint in sentence.lower() for hint in INNOVATION_HINTS)
    ]
    selected = hinted[:max_sentences] or sentences[:max_sentences]
    summary = " ".join(selected).strip()
    return summary[:700] if summary else "待人工总结"


def split_sentences(text: str) -> list[str]:
    normalized = normalize_spaces(text)
    if not normalized:
        return []
    parts = re.split(r"(?<=[.!?。！？])\s+", normalized)
    return [part.strip() for part in parts if len(part.strip()) > 10]


def dedupe_articles(articles: Iterable[Article]) -> list[Article]:
    seen: set[str] = set()
    unique: list[Article] = []
    for article in articles:
        key = (article.doi or article.title).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(article)
    return unique


def clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = normalize_spaces(value)
    return cleaned or None


def normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()

