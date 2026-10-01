"""MCP JSON-RPC 2.0 stdio server orchestrator."""

import asyncio
import json
import logging
import os
import sys
from typing import Any

from elsevier_mcp.client import ElsevierAPIClient
from elsevier_mcp.handlers import ToolHandlers, define_tools
from elsevier_mcp.prompts import define_prompts, get_prompt
from elsevier_mcp.resources import define_resource_templates, define_resources, read_resource

VERSION = "1.2.1"

logger = logging.getLogger("elsevier_mcp.server")


def _jsonrpc_response(
    req_id: Any,
    result: Any = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 response envelope.

    Args:
        req_id: Request id to echo back.
        result: Result payload (used when ``error`` is None).
        error: Optional error object with ``code`` and ``message``.

    Returns:
        JSON-RPC response dictionary.
    """
    response: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id}
    if error is not None:
        response["error"] = error
    else:
        response["result"] = result
    return response


def configure_logging() -> None:
    """Configure structured logging output to stderr to prevent interfering with stdio transport."""
    level_name = os.getenv("ELSEVIER_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        stream=sys.stderr,
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        force=True,
    )


class ElsevierMCPServer:
    """Top-level Elsevier Model Context Protocol (MCP) server."""

    def __init__(self, client: ElsevierAPIClient | None = None) -> None:
        """Initialize MCP server definitions and handlers.

        Args:
            client: Optional ElsevierAPIClient instance.
        """
        self.client = client
        self.handlers = ToolHandlers(client=self.client)
        self.tools = define_tools()
        self.prompts = define_prompts()
        self.resources = define_resources()
        self.resource_templates = define_resource_templates()

    async def search_papers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Search Scopus papers."""
        return await self.handlers.search_papers(arguments)

    async def get_paper_abstract(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Retrieve paper abstract."""
        return await self.handlers.get_paper_abstract(arguments)

    async def get_author_info(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Retrieve author info."""
        return await self.handlers.get_author_info(arguments)

    async def analyze_research_trends(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Analyze research trends."""
        return await self.handlers.analyze_research_trends(arguments)

    async def get_institution_papers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Retrieve institution publication statistics."""
        return await self.handlers.get_institution_papers(arguments)

    async def search_open_access_papers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Search open access papers."""
        return await self.handlers.search_open_access_papers(arguments)

    async def get_journal_metrics(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Retrieve journal metrics."""
        return await self.handlers.get_journal_metrics(arguments)

    async def search_author_papers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Search papers by Scopus author."""
        return await self.handlers.search_author_papers(arguments)

    async def find_author_candidates(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Disambiguate an author name into candidate Scopus author IDs."""
        return await self.handlers.find_author_candidates(arguments)

    async def get_prompt(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Generate prompt contents."""
        return get_prompt(name, arguments)

    async def read_resource(self, uri: str) -> dict[str, Any]:
        """Read and render resource contents."""
        return await read_resource(uri, self.handlers)


async def handle_request(server: ElsevierMCPServer, request: dict[str, Any]) -> dict[str, Any] | None:
    """Dispatch and process an incoming JSON-RPC 2.0 request.

    Args:
        server: ElsevierMCPServer instance.
        request: Decoded JSON-RPC request dictionary.

    Returns:
        JSON-RPC response dictionary, or None if request is a notification.
    """
    method = request.get("method")
    req_id = request.get("id")

    # JSON-RPC notifications have no "id" — must not produce any response.
    if req_id is None or (isinstance(method, str) and method.startswith("notifications/")):
        return None

    if method == "initialize":
        return _jsonrpc_response(req_id, result={
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {
                    "subscribe": False,
                    "listChanged": False,
                },
                "prompts": {
                    "listChanged": False,
                },
            },
            "serverInfo": {
                "name": "elsevier-mcp-complete-server",
                "version": VERSION,
            },
        })

    if method == "prompts/list":
        return _jsonrpc_response(req_id, result={"prompts": list(server.prompts.values())})

    if method == "prompts/get":
        prompt_name = request.get("params", {}).get("name", "")
        arguments = request.get("params", {}).get("arguments", {})
        if prompt_name in server.prompts:
            try:
                result = await server.get_prompt(prompt_name, arguments)
                return _jsonrpc_response(req_id, result=result)
            except Exception as exc:
                return _jsonrpc_response(req_id, error={"code": -32603, "message": str(exc)})
        return _jsonrpc_response(req_id, error={"code": -32602, "message": f"Prompt not found: {prompt_name}"})

    if method == "resources/list":
        return _jsonrpc_response(req_id, result={"resources": server.resources})

    if method == "resources/templates/list":
        return _jsonrpc_response(req_id, result={"resourceTemplates": server.resource_templates})

    if method == "resources/read":
        uri = request.get("params", {}).get("uri", "")
        try:
            result = await server.read_resource(uri)
            return _jsonrpc_response(req_id, result=result)
        except ValueError as exc:
            return _jsonrpc_response(req_id, error={"code": -32602, "message": str(exc)})
        except Exception as exc:
            return _jsonrpc_response(
                req_id, error={"code": -32603, "message": f"Failed to read resource: {exc!s}"}
            )

    if method == "tools/list":
        tools_list = [
            {
                "name": tool_def["name"],
                "description": tool_def["description"],
                "inputSchema": tool_def["inputSchema"],
            }
            for tool_def in server.tools.values()
        ]
        return _jsonrpc_response(req_id, result={"tools": tools_list})

    if method == "tools/call":
        tool_name = request.get("params", {}).get("name", "")
        arguments = request.get("params", {}).get("arguments", {})

        if tool_name in server.tools:
            try:
                handler = getattr(server, tool_name)
                result = await handler(arguments)
            except Exception as exc:
                logger.exception("tools/call handler %s raised unexpectedly", tool_name)
                return _jsonrpc_response(
                    req_id, error={"code": -32603, "message": f"Internal error in tool {tool_name}: {exc!s}"}
                )
            return _jsonrpc_response(req_id, result={
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2),
                    }
                ]
            })
        return _jsonrpc_response(req_id, error={"code": -32601, "message": f"Tool not found: {tool_name}"})

    return _jsonrpc_response(req_id, error={"code": -32601, "message": f"Method not found: {method}"})


async def run_stdio() -> None:
    """Run MCP server over standard I/O streams using JSON-RPC 2.0 framing."""
    configure_logging()
    server = ElsevierMCPServer()
    logger.info("Elsevier MCP Complete Server v%s started", VERSION)

    loop = asyncio.get_running_loop()

    while True:
        try:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break

            stripped = line.strip()
            if not stripped:
                continue

            try:
                request = json.loads(stripped)
            except json.JSONDecodeError as exc:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {exc}"},
                }
                print(json.dumps(err_resp), flush=True)
                continue

            response = await handle_request(server, request)
            if response is not None:
                print(json.dumps(response), flush=True)

        except EOFError:
            break
        except Exception as exc:
            logger.exception("Unexpected error in stdio processing")
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(exc)},
            }
            print(json.dumps(error_response), flush=True)


def main() -> int:
    """Console entry point for the stdio MCP server."""
    if "--version" in sys.argv:
        print(VERSION)
        return 0

    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: elsevier-mcp-server [--version]")
        print("Runs the Elsevier MCP server over stdio.")
        return 0

    if not os.getenv("ELSEVIER_API_KEY"):
        print(
            "Warning: ELSEVIER_API_KEY is not set; tools will return configuration errors until it is set.",
            file=sys.stderr,
        )

    asyncio.run(run_stdio())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
