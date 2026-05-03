from datetime import date

import pytest

from stork_agent.app import secret_status_rows
from stork_agent.connectors.institutional import AlertEmailConnector
from stork_agent.connectors.institutional import ElsevierConnector
from stork_agent.connectors.institutional import IEEEConnector
from stork_agent.connectors.institutional import OpenURLResolver
from stork_agent.connectors.institutional import WebOfScienceConnector
from stork_agent.connectors.institutional import parse_alert_email
from stork_agent.models import UserProfile


def test_wos_validate_config_requires_key_and_valid_type() -> None:
    with pytest.raises(RuntimeError, match="WOS_API_KEY"):
        WebOfScienceConnector({"WOS_API_TYPE": "starter"}).validate_config()

    with pytest.raises(RuntimeError, match="WOS_API_TYPE"):
        WebOfScienceConnector({"WOS_API_KEY": "key", "WOS_API_TYPE": "wrong"}).validate_config()

    WebOfScienceConnector({"WOS_API_KEY": "key", "WOS_API_TYPE": "expanded"}).validate_config()


def test_elsevier_and_ieee_validate_config() -> None:
    with pytest.raises(RuntimeError, match="ELSEVIER_API_KEY"):
        ElsevierConnector({}).validate_config()
    with pytest.raises(RuntimeError, match="IEEE_API_KEY"):
        IEEEConnector({}).validate_config()

    ElsevierConnector({"ELSEVIER_API_KEY": "key"}).validate_config()
    IEEEConnector({"IEEE_API_KEY": "key"}).validate_config()


def test_institutional_fetch_is_skeleton_only() -> None:
    profile = UserProfile(name="default", keywords=("segmentation",))
    connector = WebOfScienceConnector({"WOS_API_KEY": "key", "WOS_API_TYPE": "starter"})

    assert connector.fetch(profile, date(2026, 5, 1), 5) == []
    assert connector.warnings


def test_alert_email_parser_extracts_title_doi_and_source() -> None:
    content = """
    Web of Science Alert
    Title: Semi-supervised Medical Image Segmentation
    Journal: Medical Image Analysis
    DOI: 10.1234/example
    Abstract: We propose a method for medical image segmentation.
    URL: https://example.com/record
    """

    papers = parse_alert_email(content)

    assert len(papers) == 1
    assert papers[0].source == "Web of Science Alert"
    assert papers[0].doi == "10.1234/example"
    assert papers[0].url == "https://example.com/record"


def test_openurl_resolver_generates_link_without_accessing_it() -> None:
    assert OpenURLResolver(None).resolve("10.1234/example") is None
    assert OpenURLResolver("https://library.example.edu/openurl").resolve("10.1234/example") == "https://library.example.edu/openurl?doi=10.1234%2Fexample"


def test_secret_status_rows_never_exposes_values() -> None:
    rows = secret_status_rows({"WOS_API_KEY": "secret"})

    assert {"name": "WOS_API_KEY", "status": "configured"} in rows
    assert "secret" not in str(rows)
