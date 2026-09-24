"""Tests for tool handlers in elsevier_mcp.handlers."""

from typing import Any
import pytest
import respx

from elsevier_mcp.client import BASE_URL, ElsevierAPIClient
from elsevier_mcp.handlers import (
    ToolHandlers,
    _parse_author_names,
    build_scopus_query,
    parse_paper_entry,
)


def test_build_scopus_query() -> None:
    """Verify Scopus query string construction."""
    # Plain query wrapped in TITLE-ABS-KEY
    q1 = build_scopus_query("quantum computing")
    assert q1 == "TITLE-ABS-KEY(quantum computing)"

    # Pre-coded query kept intact
    q2 = build_scopus_query("AUTH(Hinton)")
    assert q2 == "AUTH(Hinton)"

    # With institution and year
    q3 = build_scopus_query("AI", year=2024, institution="MIT")
    assert 'AFFIL("MIT")' in q3
    assert "TITLE-ABS-KEY(AI)" in q3
    assert "PUBYEAR = 2024" in q3

    # With open access
    q4 = build_scopus_query("AI", open_access=True)
    assert "OPENACCESS(1)" in q4


def test_parse_paper_entry() -> None:
    """Verify paper entry parsing and citation conversion."""
    raw = {
        "dc:title": "Test Title",
        "dc:creator": "Test Author",
        "prism:publicationName": "Test Journal",
        "prism:coverDate": "2024-01-01",
        "citedby-count": "42",
        "prism:doi": "10.1234/test",
        "eid": "2-s2.0-12345",
    }
    parsed = parse_paper_entry(raw, open_access=True)
    assert parsed["title"] == "Test Title"
    assert parsed["citations"] == 42
    assert parsed["open_access"] is True


def test_parse_author_names() -> None:
    """Verify author name normalization across different Scopus response formats."""
    # String input
    assert _parse_author_names("Alice Smith") == "Alice Smith"

    # Empty or None
    assert _parse_author_names(None) == "Unknown"
    assert _parse_author_names("") == "Unknown"
    assert _parse_author_names({}) == "Unknown"

    # Dict with author list containing ce:indexed-name
    scopus_abstract_authors = {
        "author": [
            {"ce:indexed-name": "He K.", "ce:surname": "He"},
            {"ce:indexed-name": "Zhang X.", "ce:surname": "Zhang"},
        ]
    }
    assert _parse_author_names(scopus_abstract_authors) == "He K., Zhang X."

    # Preferred name precedence
    pref_authors = {
        "author": [
            {
                "preferred-name": {"ce:indexed-name": "LeCun Y."},
                "ce:indexed-name": "Lecun Y.",
            }
        ]
    }
    assert _parse_author_names(pref_authors) == "LeCun Y."

    # Fallback to surname and given-name
    surname_only = {
        "author": [
            {"ce:surname": "Turing", "ce:given-name": "Alan M."},
        ]
    }
    assert _parse_author_names(surname_only) == "Turing Alan M."

    # List of author names
    assert _parse_author_names(["Bengio Y.", "Hinton G."]) == "Bengio Y., Hinton G."


@pytest.mark.asyncio
@respx.mock
async def test_search_papers_success(
    api_client: ElsevierAPIClient,
    sample_scopus_search_response: dict[str, Any],
) -> None:
    """Verify search_papers successfully returns structured paper items."""
    respx.get(f"{BASE_URL}/content/search/scopus").respond(
        status_code=200, json=sample_scopus_search_response
    )
    handlers = ToolHandlers(client=api_client)

    result = await handlers.search_papers({"query": "transformers", "count": 10})
    assert result["success"] is True
    assert result["total_results"] == 42
    assert len(result["papers"]) == 2
    assert result["papers"][0]["citations"] == 105432
    assert result["papers"][0]["doi"] == "10.5555/3295222.3295349"


@pytest.mark.asyncio
async def test_search_papers_validation_error(api_client: ElsevierAPIClient) -> None:
    """Verify search_papers returns failure on invalid input parameters."""
    handlers = ToolHandlers(client=api_client)
    result = await handlers.search_papers({"query": "AI", "count": 100})
    assert result["success"] is False
    assert "Validation error" in result["error"]


@pytest.mark.asyncio
@respx.mock
async def test_get_paper_abstract_eid(
    api_client: ElsevierAPIClient,
    sample_abstract_response: dict[str, Any],
) -> None:
    """Verify get_paper_abstract retrieves abstract by EID."""
    eid = "2-s2.0-84984577884"
    respx.get(f"{BASE_URL}/content/abstract/eid/{eid}").respond(
        status_code=200, json=sample_abstract_response
    )
    handlers = ToolHandlers(client=api_client)

    result = await handlers.get_paper_abstract({"eid": eid})
    assert result["success"] is True
    assert result["paper"]["title"] == "Deep Residual Learning for Image Recognition"
    assert result["paper"]["doi"] == "10.1109/CVPR.2016.90"


@pytest.mark.asyncio
@respx.mock
async def test_get_author_info(
    api_client: ElsevierAPIClient,
    sample_author_response: dict[str, Any],
) -> None:
    """Verify get_author_info returns author profile data."""
    author_id = "55239922200"
    respx.get(f"{BASE_URL}/analytics/scival/author/{author_id}").respond(
        status_code=200, json=sample_author_response
    )
    handlers = ToolHandlers(client=api_client)

    result = await handlers.get_author_info({"author_id": author_id})
    assert result["success"] is True
    assert result["author"]["name"] == "Yoshua Bengio"
    assert result["author"]["current_institution"] == "Université de Montréal"


@pytest.mark.asyncio
@respx.mock
async def test_analyze_research_trends(api_client: ElsevierAPIClient) -> None:
    """Verify analyze_research_trends performs multi-year queries and growth rate math."""
    respx.get(f"{BASE_URL}/content/search/scopus").side_effect = [
        respx.MockResponse(200, json={"search-results": {"opensearch:totalResults": "100"}}),
        respx.MockResponse(200, json={"search-results": {"opensearch:totalResults": "150"}}),
        respx.MockResponse(200, json={"search-results": {"opensearch:totalResults": "225"}}),
    ]
    handlers = ToolHandlers(client=api_client)

    result = await handlers.analyze_research_trends({
        "field": "reinforcement learning",
        "years": [2022, 2023, 2024],
    })
    assert result["success"] is True
    assert result["yearly_papers"] == {2022: 100, 2023: 150, 2024: 225}
    assert result["growth_rates"]["2022-2023"] == 50.0
    assert result["growth_rates"]["2023-2024"] == 50.0
    assert result["total_papers"] == 475


@pytest.mark.asyncio
@respx.mock
async def test_get_institution_papers(
    api_client: ElsevierAPIClient,
    sample_scopus_search_response: dict[str, Any],
) -> None:
    """Verify get_institution_papers returns institution paper statistics."""
    respx.get(f"{BASE_URL}/content/search/scopus").respond(
        status_code=200, json=sample_scopus_search_response
    )
    handlers = ToolHandlers(client=api_client)

    result = await handlers.get_institution_papers({
        "institution": "Stanford University",
        "year": 2024,
    })
    assert result["success"] is True
    assert result["institution"] == "Stanford University"
    assert result["total_papers"] == 42
    assert len(result["top_papers"]) == 2


@pytest.mark.asyncio
@respx.mock
async def test_search_open_access_papers(
    api_client: ElsevierAPIClient,
    sample_scopus_search_response: dict[str, Any],
) -> None:
    """Verify search_open_access_papers returns open access flagged results."""
    respx.get(f"{BASE_URL}/content/search/scopus").respond(
        status_code=200, json=sample_scopus_search_response
    )
    handlers = ToolHandlers(client=api_client)

    result = await handlers.search_open_access_papers({
        "field": "climate change",
        "count": 5,
    })
    assert result["success"] is True
    assert result["total_open_access"] == 42
    assert result["papers"][0]["open_access"] is True


@pytest.mark.asyncio
@respx.mock
async def test_get_journal_metrics(
    api_client: ElsevierAPIClient,
    sample_serial_response: dict[str, Any],
) -> None:
    """Verify get_journal_metrics extracts CiteScore, SJR, SNIP and Q1 quartile."""
    respx.get(f"{BASE_URL}/content/serial/title").respond(
        status_code=200, json=sample_serial_response
    )
    handlers = ToolHandlers(client=api_client)

    result = await handlers.get_journal_metrics({"title": "Nature Machine Intelligence"})
    assert result["success"] is True
    journal = result["journal"]
    assert journal["title"] == "Nature Machine Intelligence"
    assert journal["citescore"]["current"] == 28.5
    assert journal["sjr"]["value"] == 5.42
    assert journal["snip"]["value"] == 6.85
    assert journal["best_quartile"] == "Q1"
    assert len(journal["subject_rankings"]) == 2


@pytest.mark.asyncio
@respx.mock
async def test_get_journal_metrics_not_found(api_client: ElsevierAPIClient) -> None:
    """Verify get_journal_metrics handles journal not found gracefully."""
    respx.get(f"{BASE_URL}/content/serial/title").respond(
        status_code=200, json={"serial-metadata-response": {"entry": []}}
    )
    handlers = ToolHandlers(client=api_client)

    result = await handlers.get_journal_metrics({"title": "NonExistentJournalXYZ"})
    assert result["success"] is False
    assert "Journal not found" in result["error"]
