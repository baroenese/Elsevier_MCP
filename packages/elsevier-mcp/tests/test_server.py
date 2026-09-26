"""Tests for JSON-RPC 2.0 protocol handling in elsevier_mcp.server."""

import json
from typing import Any

import pytest
import respx

from elsevier_mcp.client import BASE_URL
from elsevier_mcp.server import VERSION, ElsevierMCPServer, handle_request


@pytest.mark.asyncio
async def test_handle_initialize(server: ElsevierMCPServer) -> None:
    """Verify initialize request returns correct capabilities and protocolVersion."""
    req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    resp = await handle_request(server, req)
    assert resp is not None
    assert resp["id"] == 1
    result = resp["result"]
    assert result["protocolVersion"] == "2024-11-05"
    assert result["serverInfo"]["version"] == VERSION
    assert "tools" in result["capabilities"]
    assert "resources" in result["capabilities"]
    assert "prompts" in result["capabilities"]


@pytest.mark.asyncio
async def test_handle_notifications_ignored(server: ElsevierMCPServer) -> None:
    """Verify notifications (missing id or notifications/*) return None without response."""
    notif1 = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    assert await handle_request(server, notif1) is None

    notif2 = {"jsonrpc": "2.0", "method": "some/event"}
    assert await handle_request(server, notif2) is None


@pytest.mark.asyncio
async def test_handle_tools_list(server: ElsevierMCPServer) -> None:
    """Verify tools/list exposes all 7 tools with schemas."""
    req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    resp = await handle_request(server, req)
    assert resp is not None
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert len(tools) == 7
    assert "search_papers" in tool_names
    assert "get_paper_abstract" in tool_names
    assert "get_author_info" in tool_names
    assert "analyze_research_trends" in tool_names
    assert "get_institution_papers" in tool_names
    assert "search_open_access_papers" in tool_names
    assert "get_journal_metrics" in tool_names


@pytest.mark.asyncio
@respx.mock
async def test_handle_tools_call(
    server: ElsevierMCPServer,
    sample_scopus_search_response: dict[str, Any],
) -> None:
    """Verify tools/call dispatches to handler and packages result in text content."""
    respx.get(f"{BASE_URL}/content/search/scopus").respond(
        status_code=200, json=sample_scopus_search_response
    )
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "search_papers",
            "arguments": {"query": "deep learning", "count": 5},
        },
    }
    resp = await handle_request(server, req)
    assert resp is not None
    assert resp["id"] == 3
    content = resp["result"]["content"]
    assert content[0]["type"] == "text"
    parsed_inner = json.loads(content[0]["text"])
    assert parsed_inner["success"] is True
    assert parsed_inner["total_results"] == 42


@pytest.mark.asyncio
async def test_handle_tools_call_unknown(server: ElsevierMCPServer) -> None:
    """Verify calling an unknown tool returns code -32601."""
    req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "non_existent_tool", "arguments": {}},
    }
    resp = await handle_request(server, req)
    assert resp is not None
    assert resp["error"]["code"] == -32601
    assert "Tool not found" in resp["error"]["message"]


@pytest.mark.asyncio
async def test_handle_prompts_list_and_get(server: ElsevierMCPServer) -> None:
    """Verify prompts/list and prompts/get for systematic literature review."""
    req_list = {"jsonrpc": "2.0", "id": 5, "method": "prompts/list", "params": {}}
    resp_list = await handle_request(server, req_list)
    assert resp_list is not None
    assert len(resp_list["result"]["prompts"]) == 3

    req_get = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "prompts/get",
        "params": {
            "name": "systematic_literature_review",
            "arguments": {"topic": "Quantum Computing"},
        },
    }
    resp_get = await handle_request(server, req_get)
    assert resp_get is not None
    messages = resp_get["result"]["messages"]
    assert "Quantum Computing" in messages[0]["content"]["text"]


@pytest.mark.asyncio
async def test_handle_resources(server: ElsevierMCPServer) -> None:
    """Verify resources/list, resources/templates/list, and resources/read."""
    # List resources
    resp_res = await handle_request(server, {"jsonrpc": "2.0", "id": 7, "method": "resources/list"})
    assert resp_res is not None
    assert len(resp_res["result"]["resources"]) == 1

    # List templates
    resp_tpl = await handle_request(
        server, {"jsonrpc": "2.0", "id": 8, "method": "resources/templates/list"}
    )
    assert resp_tpl is not None
    assert len(resp_tpl["result"]["resourceTemplates"]) == 3

    # Read syntax resource
    resp_read = await handle_request(
        server,
        {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "resources/read",
            "params": {"uri": "elsevier://docs/scopus-search-syntax"},
        },
    )
    assert resp_read is not None
    contents = resp_read["result"]["contents"]
    assert "Scopus Search API Query Syntax" in contents[0]["text"]


@pytest.mark.asyncio
@respx.mock
async def test_handle_resources_dynamic_encoded(
    server: ElsevierMCPServer,
    sample_serial_response: dict[str, Any],
) -> None:
    """Verify reading dynamic resource with URL-encoded query properly decodes and fetches."""
    respx.get(f"{BASE_URL}/content/serial/title").respond(
        status_code=200, json=sample_serial_response
    )
    resp = await handle_request(
        server,
        {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "resources/read",
            "params": {"uri": "elsevier://journal/Nature%20Machine%20Intelligence"},
        },
    )
    assert resp is not None
    contents = resp["result"]["contents"]
    assert "Nature Machine Intelligence" in contents[0]["text"]
    assert "CiteScore" in contents[0]["text"]


@pytest.mark.asyncio
async def test_handle_unknown_method(server: ElsevierMCPServer) -> None:
    """Verify unknown method returns code -32601."""
    req = {"jsonrpc": "2.0", "id": 10, "method": "unknown_rpc_method", "params": {}}
    resp = await handle_request(server, req)
    assert resp is not None
    assert resp["error"]["code"] == -32601


def test_backward_compatibility_shim() -> None:
    """Verify importing from elsevier_mcp_complete works and issues DeprecationWarning."""
    with pytest.deprecated_call():
        import elsevier_mcp_complete

        assert hasattr(elsevier_mcp_complete, "ElsevierMCPServer")
        assert hasattr(elsevier_mcp_complete, "main")
        assert elsevier_mcp_complete.VERSION == VERSION
