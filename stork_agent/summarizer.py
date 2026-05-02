from __future__ import annotations

import re


HINTS = (
    "propose",
    "proposes",
    "proposed",
    "novel",
    "introduce",
    "introduces",
    "framework",
    "method",
    "approach",
    "contribution",
    "improve",
    "improves",
)


def summarize_innovation(title: str, abstract: str | None) -> str:
    if not abstract:
        return "摘要缺失，需人工判断"
    sentences = split_sentences(abstract)
    hinted = [sentence for sentence in sentences if any(hint in sentence.lower() for hint in HINTS)]
    selected = hinted[:2] or sentences[:2]
    return " ".join(selected)[:700] if selected else "摘要缺失，需人工判断"


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?。！？])\s+", normalized) if len(part.strip()) > 10]

