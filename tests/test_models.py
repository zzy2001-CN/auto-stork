from stork_mailer.models import LiteratureItem
from stork_mailer.models import dedupe_by_title


def test_dedupe_by_strict_normalized_title() -> None:
    items = dedupe_by_title(
        [
            LiteratureItem(title="A Paper", source="OpenAlex", doi="10.1/example"),
            LiteratureItem(title="A   Paper", source="Semantic Scholar", url="https://example.com"),
        ]
    )

    assert len(items) == 1
    assert items[0].source == "OpenAlex / Semantic Scholar"
    assert items[0].doi == "10.1/example"
    assert items[0].url == "https://example.com"

