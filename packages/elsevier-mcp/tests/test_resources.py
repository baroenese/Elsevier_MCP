"""Tests for dynamic resource templates and error rendering in elsevier_mcp.resources."""

from typing import Any

import httpx
import pytest
import respx

from elsevier_mcp.client import BASE_URL
from elsevier_mcp.handlers import ToolHandlers
from elsevier_mcp.resources import read_resource


@pytest.fixture
def handlers(api_client: Any) -> ToolHandlers:
    """ToolHandlers wired to the isolated test client."""
    return ToolHandlers(client=api_client)


@pytest.mark.asyncio
async def test_unknown_uri_raises_value_error(handlers: ToolHandlers) -> None:
    """An unknown URI raises ValueError with the URI in the message."""
    with pytest.raises(ValueError, match="Resource not found"):
        await read_resource("elsevier://unknown/thing", handlers)


@respx.mock
@pytest.mark.asyncio
async def test_paper_resource_success(
    handlers: ToolHandlers, sample_abstract_response: dict[str, Any]
) -> None:
    """elsevier://paper/{eid} renders title, citations, and abstract as markdown."""
    respx.get(f"{BASE_URL}/content/abstract/eid/2-s2.0-xyz").return_value = httpx.Response(
        200, json=sample_abstract_response
    )
    res = await read_resource("elsevier://paper/2-s2.0-xyz", handlers)
    text = res["contents"][0]["text"]
    assert "Deep Residual Learning for Image Recognition" in text
    assert "180000" in text
    assert res["contents"][0]["mimeType"] == "text/markdown"


@respx.mock
@pytest.mark.asyncio
async def test_paper_resource_error_branch(handlers: ToolHandlers) -> None:
    """A handler error renders a markdown error report instead of raising."""
    respx.get(f"{BASE_URL}/content/abstract/eid/2-s2.0-missing").return_value = httpx.Response(
        404, text="not found"
    )
    res = await read_resource("elsevier://paper/2-s2.0-missing", handlers)
    text = res["contents"][0]["text"]
    assert text.startswith("# Error")
    assert "2-s2.0-missing" in text


@respx.mock
@pytest.mark.asyncio
async def test_trends_resource_success(handlers: ToolHandlers) -> None:
    """elsevier://trends/{field} renders yearly volume and growth tables."""
    route = respx.get(f"{BASE_URL}/content/search/scopus")
    route.side_effect = [
        httpx.Response(200, json={"search-results": {"opensearch:totalResults": "10"}}),
        httpx.Response(200, json={"search-results": {"opensearch:totalResults": "20"}}),
        httpx.Response(200, json={"search-results": {"opensearch:totalResults": "30"}}),
    ]
    res = await read_resource("elsevier://trends/quantum%20computing", handlers)
    text = res["contents"][0]["text"]
    assert "Research Trend Report" in text
    assert "| 30 |" in text  # a yearly row
    assert "Growth Rates" in text


@respx.mock
@pytest.mark.asyncio
async def test_trends_resource_error_branch(handlers: ToolHandlers) -> None:
    """A per-year API failure renders a markdown error report."""
    respx.get(f"{BASE_URL}/content/search/scopus").return_value = httpx.Response(500, text="boom")
    res = await read_resource("elsevier://trends/AI", handlers)
    assert res["contents"][0]["text"].startswith("# Error")
    assert "AI" in res["contents"][0]["text"]


@respx.mock
@pytest.mark.asyncio
async def test_journal_resource_issn_detection(
    handlers: ToolHandlers, sample_serial_response: dict[str, Any]
) -> None:
    """A numeric query with a dash is treated as ISSN and requested via the issn param."""
    route = respx.get(f"{BASE_URL}/content/serial/title")
    route.return_value = httpx.Response(200, json=sample_serial_response)
    res = await read_resource("elsevier://journal/2522-5839", handlers)
    text = res["contents"][0]["text"]
    assert "CiteScore" in text
    assert "Subject Category Rankings" in text
    requested = route.calls[0].request.url.params
    assert requested["issn"] == "2522-5839"


@respx.mock
@pytest.mark.asyncio
async def test_journal_resource_error_branch(handlers: ToolHandlers) -> None:
    """Journal-not-found renders a markdown error report."""
    respx.get(f"{BASE_URL}/content/serial/title").return_value = httpx.Response(
        200, json={"serial-metadata-response": {"entry": []}}
    )
    res = await read_resource("elsevier://journal/Nonexistent Journal", handlers)
    text = res["contents"][0]["text"]
    assert text.startswith("# Error")
    assert "Nonexistent Journal" in text
