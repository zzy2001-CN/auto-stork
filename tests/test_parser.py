from stork_mailer.parser import parse_stork_digest


def test_parse_filters_relevant_q1_article() -> None:
    content = """
    Title: Semi-supervised Medical Image Segmentation with Consistency Learning
    Journal: Medical Image Analysis
    JCR: Q1
    DOI: 10.1234/example.2026.001
    Abstract: We propose a novel semi-supervised framework for medical image segmentation.
    The method improves MRI segmentation with limited labels.
    """

    articles = parse_stork_digest(content)

    assert len(articles) == 1
    assert articles[0].title == "Semi-supervised Medical Image Segmentation with Consistency Learning"
    assert articles[0].ranking == "Q1"
    assert articles[0].doi == "10.1234/example.2026.001"
    assert "propose" in articles[0].innovation.lower()


def test_parse_rejects_q3_article() -> None:
    content = """
    Title: Semi-supervised Medical Image Segmentation
    Journal: Example Journal
    JCR: Q3
    Abstract: We propose a method for medical image segmentation.
    """

    assert parse_stork_digest(content) == []


def test_parse_rejects_non_medical_topic() -> None:
    content = """
    Title: Semi-supervised Semantic Segmentation for Street Scenes
    Journal: Computer Vision Journal
    JCR: Q1
    Abstract: We propose a novel framework for street scene segmentation.
    """

    assert parse_stork_digest(content) == []


def test_parse_html_digest() -> None:
    content = """
    <html><body>
      <div>
        <p>Title: A Scribble-supervised Framework for CT Image Segmentation</p>
        <p>SCI 2区</p>
        <p>Abstract: This paper introduces a novel scribble-based medical image segmentation method for CT scans.</p>
      </div>
    </body></html>
    """

    articles = parse_stork_digest(content)

    assert len(articles) == 1
    assert articles[0].ranking == "Q2"

