"""Regression lock tests: pin external behavior of handlers before internal refactoring.

These tests assert on response shapes and error-message formats that callers
(MCP clients, apps/api) depend on. If one of these fails after a refactor, the
public contract changed unintentionally.
"""

from typing import Any

import httpx
import pytest
import respx

from elsevier_mcp.client import BASE_URL
from elsevier_mcp.handlers import ToolHandlers, parse_paper_entry
from elsevier_mcp.server import ElsevierMCPServer


@pytest.fixture
def handlers(api_client: Any) -> ToolHandlers:
    """Provide ToolHandlers wired to the isolated test client."""
    return ToolHandlers(client=api_client)


# ---------------------------------------------------------------------------
# parse helpers
# ---------------------------------------------------------------------------


def test_parse_paper_entry_non_numeric_citations() -> None:
    """Non-numeric citedby-count is coerced to 0 (Elsevier may send strings)."""
    parsed = parse_paper_entry({"dc:title": "T", "citedby-count": "not-a-number"})
    assert parsed["citations"] == 0
    assert parsed["citations"] == 0 or isinstance(parsed["citations"], int)


def test_parse_paper_entry_missing_fields_defaults() -> None:
    """Missing entry fields fall back to the documented default strings."""
    parsed = parse_paper_entry({})
    assert parsed == {
        "title": "No title",
        "authors": "Unknown",
        "journal": "Unknown",
        "year": "",
        "citations": 0,
        "doi": "",
        "eid": "",
    }


# ---------------------------------------------------------------------------
# API non-success branches for every handler
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_error_shapes_on_api_failure(handlers: ToolHandlers, sample_scopus_search_response: dict) -> None:
    """Each handler maps HTTP failure to its pinned error-message format."""
    scopus_route = respx.get(f"{BASE_URL}/content/search/scopus")
    scopus_route.return_value = httpx.Response(500, text="boom")

    res = await handlers.search_papers({"query": "test"})
    assert res == {"success": False, "error": "API Error: 500"}

    res = await handlers.get_institution_papers({"institution": "MIT"})
    assert res == {"success": False, "error": "API Error: 500"}

    res = await handlers.search_open_access_papers({"field": "AI"})
    assert res == {"success": False, "error": "API Error: 500"}

    res = await handlers.analyze_research_trends({"field": "AI", "years": [2024]})
    assert res == {"success": False, "error": "API Error 500 for year 2024"}


@respx.mock
@pytest.mark.asyncio
async def test_error_shapes_other_endpoints(handlers: ToolHandlers) -> None:
    """Abstract/author/journal endpoints map HTTP failure to their pinned formats."""
    abstract_route = respx.get(f"{BASE_URL}/content/abstract/eid/2-s2.0-x")
    abstract_route.return_value = httpx.Response(404, text="not found")
    res = await handlers.get_paper_abstract({"eid": "2-s2.0-x"})
    assert res == {"success": False, "error": "API Error: 404"}

    author_route = respx.get(f"{BASE_URL}/analytics/scival/author/123")
    author_route.return_value = httpx.Response(403, text="forbidden")
    res = await handlers.get_author_info({"author_id": "123"})
    assert res == {"success": False, "error": "API Error: 403"}

    serial_route = respx.get(f"{BASE_URL}/content/serial/title")
    serial_route.return_value = httpx.Response(400, text="bad request detail")
    res = await handlers.get_journal_metrics({"title": "Nature"})
    assert res["success"] is False
    assert res["error"] == "API Error 400: bad request detail"


# ---------------------------------------------------------------------------
# Unexpected exceptions -> error dict (never raised to caller)
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_network_exception_becomes_error_dict(handlers: ToolHandlers) -> None:
    """A raised exception (e.g. network error) is caught and stringified."""
    respx.get(f"{BASE_URL}/content/search/scopus").side_effect = httpx.ConnectError("network down")
    res = await handlers.search_papers({"query": "test"})
    assert res["success"] is False
    assert "network down" in res["error"]


# ---------------------------------------------------------------------------
# Validation error prefix
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validation_error_prefix(handlers: ToolHandlers) -> None:
    """Invalid arguments return the pinned 'Validation error:' prefix."""
    res = await handlers.search_papers({"query": ""})
    assert res["success"] is False
    assert res["error"].startswith("Validation error:")

    res = await handlers.get_paper_abstract({})
    assert res["success"] is False
    assert res["error"].startswith("Validation error:")


# ---------------------------------------------------------------------------
# Success shapes (string -> int coercion pinned)
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_success_shape_and_int_coercion(
    handlers: ToolHandlers, sample_scopus_search_response: dict
) -> None:
    """search_papers returns total_results as int even when API sends a string."""
    respx.get(f"{BASE_URL}/content/search/scopus").return_value = httpx.Response(
        200, json=sample_scopus_search_response
    )
    res = await handlers.search_papers({"query": "attention"})
    assert res["success"] is True
    assert isinstance(res["total_results"], int)
    assert res["total_results"] == 42
    assert set(res.keys()) == {"success", "total_results", "papers", "query"}


@respx.mock
@pytest.mark.asyncio
async def test_journal_metrics_shape(
    handlers: ToolHandlers, sample_serial_response: dict
) -> None:
    """get_journal_metrics returns the pinned journal result structure."""
    respx.get(f"{BASE_URL}/content/serial/title").return_value = httpx.Response(
        200, json=sample_serial_response
    )
    res = await handlers.get_journal_metrics({"title": "Nature Machine Intelligence"})
    assert res["success"] is True
    assert set(res.keys()) == {"success", "journal"}
    j = res["journal"]
    assert set(j.keys()) == {
        "title",
        "publisher",
        "issn",
        "eissn",
        "aggregation_type",
        "open_access",
        "citescore",
        "sjr",
        "snip",
        "best_quartile",
        "subject_rankings",
    }
    assert j["citescore"]["current"] == 28.5
    assert j["sjr"]["value"] == 5.42
    assert j["snip"]["value"] == 6.85
    assert j["best_quartile"] == "Q1"
    assert j["subject_rankings"][0] == {
        "subject_code": "1702",
        "rank": 1,
        "percentile": 99.0,
        "quartile": "Q1",
    }


@respx.mock
@pytest.mark.asyncio
async def test_trends_success_shape(handlers: ToolHandlers) -> None:
    """analyze_research_trends returns yearly counts and growth rates."""
    route = respx.get(f"{BASE_URL}/content/search/scopus")
    route.side_effect = [
        httpx.Response(200, json={"search-results": {"opensearch:totalResults": "100"}}),
        httpx.Response(200, json={"search-results": {"opensearch:totalResults": "150"}}),
    ]
    res = await handlers.analyze_research_trends({"field": "AI", "years": [2023, 2024]})
    assert res["success"] is True
    assert res["yearly_papers"] == {2023: 100, 2024: 150}
    assert res["growth_rates"] == {"2023-2024": 50.0}
    assert res["total_papers"] == 250


# ---------------------------------------------------------------------------
# Server-level contract: tools/call wraps handler dict into MCP content
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_server_tools_call_content_wrapping(
    server: ElsevierMCPServer, sample_scopus_search_response: dict
) -> None:
    """tools/call returns the handler dict serialized inside MCP text content."""
    respx.get(f"{BASE_URL}/content/search/scopus").return_value = httpx.Response(
        200, json=sample_scopus_search_response
    )
    response = await _call(server, "search_papers", {"query": "x"})
    assert response["result"]["content"][0]["type"] == "text"
    import json

    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["success"] is True
    assert isinstance(payload["total_results"], int)


async def _call(server: ElsevierMCPServer, tool: str, arguments: dict) -> dict:
    """Invoke the server's internal tools/call path via its request handler."""
    from elsevier_mcp.server import handle_request

    return await handle_request(
        server,
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": arguments}},
    )
