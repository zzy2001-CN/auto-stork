from stork_mailer.config import SearchConfig
from stork_mailer.sources import abstract_from_inverted_index
from stork_mailer.sources import openalex_work_to_item
from stork_mailer.sources import semantic_paper_to_item


KEYWORDS = ("semi-supervised", "weakly supervised", "medical image", "segmentation", "ct")


def test_abstract_from_openalex_inverted_index() -> None:
    assert abstract_from_inverted_index({"hello": [0], "world": [1]}) == "hello world"


def test_openalex_work_to_item() -> None:
    item = openalex_work_to_item(
        {
            "title": "Semi-supervised Medical Image Segmentation",
            "doi": "https://doi.org/10.1234/example",
            "publication_year": 2026,
            "id": "https://openalex.org/W1",
            "abstract_inverted_index": {
                "We": [0],
                "propose": [1],
                "a": [2],
                "medical": [3],
                "image": [4],
                "segmentation": [5],
                "method.": [6],
            },
            "primary_location": {"source": {"display_name": "Medical Image Analysis"}},
        },
        "semi-supervised medical image segmentation",
        SearchConfig(queries=("q",), include_keywords=KEYWORDS).include_keywords,
    )

    assert item is not None
    assert item.source == "OpenAlex"
    assert item.quartile == "Unknown"
    assert item.doi == "10.1234/example"
    assert item.venue == "Medical Image Analysis"


def test_semantic_paper_to_item() -> None:
    item = semantic_paper_to_item(
        {
            "title": "Weakly supervised CT image segmentation",
            "abstract": "We propose a framework for medical image segmentation.",
            "venue": "MICCAI",
            "year": 2026,
            "externalIds": {"DOI": "10.1234/s2"},
            "url": "https://semanticscholar.org/paper/1",
            "publicationDate": "2026-04-28",
        },
        "weakly supervised medical image segmentation",
        SearchConfig(queries=("q",), include_keywords=KEYWORDS).include_keywords,
    )

    assert item is not None
    assert item.source == "Semantic Scholar"
    assert item.quartile == "Unknown"
    assert item.doi == "10.1234/s2"
