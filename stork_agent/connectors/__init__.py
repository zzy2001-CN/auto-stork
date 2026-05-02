from stork_agent.connectors.arxiv import ArxivConnector
from stork_agent.connectors.base import BaseConnector
from stork_agent.connectors.crossref import CrossrefConnector
from stork_agent.connectors.openalex import OpenAlexConnector
from stork_agent.connectors.pubmed import PubMedConnector
from stork_agent.connectors.semantic_scholar import SemanticScholarConnector
from stork_agent.connectors.stork_email import StorkEmailConnector
from stork_agent.connectors.institutional import AlertEmailConnector
from stork_agent.connectors.institutional import ElsevierConnector
from stork_agent.connectors.institutional import IEEEConnector
from stork_agent.connectors.institutional import WebOfScienceConnector


CONNECTORS = {
    "stork_email": StorkEmailConnector,
    "openalex": OpenAlexConnector,
    "semantic_scholar": SemanticScholarConnector,
    "pubmed": PubMedConnector,
    "arxiv": ArxivConnector,
    "crossref": CrossrefConnector,
    "web_of_science": WebOfScienceConnector,
    "elsevier": ElsevierConnector,
    "ieee": IEEEConnector,
    "alert_email": AlertEmailConnector,
}
