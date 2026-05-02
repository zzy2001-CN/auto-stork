from datetime import date

from stork_agent.connectors.arxiv import arxiv_atom_to_papers
from stork_agent.connectors.crossref import crossref_to_paper
from stork_agent.connectors.openalex import openalex_to_paper
from stork_agent.connectors.pubmed import pubmed_xml_to_papers
from stork_agent.connectors.semantic_scholar import semantic_to_paper


def test_openalex_to_paper_mock() -> None:
    paper = openalex_to_paper(
        {
            "id": "https://openalex.org/W1",
            "title": "Semi-supervised Medical Image Segmentation",
            "doi": "https://doi.org/10.1/test",
            "publication_year": 2026,
            "publication_date": "2026-05-01",
            "cited_by_count": 5,
            "abstract_inverted_index": {"We": [0], "propose": [1], "method.": [2]},
            "primary_location": {"source": {"display_name": "Journal"}},
            "authorships": [{"author": {"display_name": "Ada Lovelace"}}],
            "open_access": {"oa_url": "https://example.com/oa"},
        },
        "semi-supervised medical image segmentation",
    )

    assert paper is not None
    assert paper.source == "OpenAlex"
    assert paper.doi == "10.1/test"
    assert paper.authors == ("Ada Lovelace",)


def test_semantic_to_paper_mock() -> None:
    paper = semantic_to_paper(
        {
            "paperId": "S2",
            "title": "A Paper",
            "abstract": "We propose a method.",
            "venue": "Venue",
            "year": 2026,
            "externalIds": {"DOI": "10.1/s2"},
            "url": "https://example.com",
            "citationCount": 3,
            "authors": [{"name": "Grace Hopper"}],
        },
        "query",
    )

    assert paper.source == "Semantic Scholar"
    assert paper.source_ids == {"semantic_scholar": "S2"}


def test_pubmed_xml_to_papers_mock() -> None:
    xml = """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>PubMed Paper</ArticleTitle><Abstract><AbstractText>We propose a method.</AbstractText></Abstract><Journal><Title>Journal</Title><JournalIssue><PubDate><Year>2026</Year></PubDate></JournalIssue></Journal></Article></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">10.1/pubmed</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>"""
    papers = pubmed_xml_to_papers(xml, "query")

    assert len(papers) == 1
    assert papers[0].source_ids == {"pmid": "123"}
    assert papers[0].doi == "10.1/pubmed"


def test_arxiv_atom_to_papers_mock() -> None:
    xml = """<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/1</id><title>arXiv Paper</title><summary>We propose a method.</summary><published>2026-05-01T00:00:00Z</published><author><name>Author</name></author></entry></feed>"""
    papers = arxiv_atom_to_papers(xml, "query", date(2026, 4, 1))

    assert len(papers) == 1
    assert papers[0].source == "arXiv"


def test_crossref_to_paper_mock() -> None:
    paper = crossref_to_paper(
        {
            "title": ["Crossref Paper"],
            "DOI": "10.1/crossref",
            "container-title": ["Journal"],
            "published-online": {"date-parts": [[2026]]},
            "author": [{"given": "Alan", "family": "Turing"}],
        },
        "query",
    )

    assert paper.source == "Crossref"
    assert paper.authors == ("Alan Turing",)

