#!/usr/bin/env python3
"""
Basic local examples for the Elsevier MCP server implementation.

Set ELSEVIER_API_KEY before running this file. The examples call the same
handlers exposed through MCP, but run them directly from Python for quick
manual verification.
"""

import asyncio
import json
import os
from typing import Any

from elsevier_mcp import ElsevierMCPServer


async def show(name: str, result: dict[str, Any]) -> None:
    print(f"\n## {name}")
    print(json.dumps(result, ensure_ascii=False, indent=2))


async def main() -> int:
    if not os.getenv("ELSEVIER_API_KEY"):
        print("ELSEVIER_API_KEY is not set.")
        return 1

    server = ElsevierMCPServer()

    await show(
        "search_papers",
        await server.search_papers({"query": "artificial intelligence", "count": 3}),
    )
    await show(
        "get_author_info",
        await server.get_author_info({"author_id": "57817454300"}),
    )
    await show(
        "analyze_research_trends",
        await server.analyze_research_trends({"field": "machine learning", "years": [2022, 2023, 2024]}),
    )
    await show(
        "search_open_access_papers",
        await server.search_open_access_papers({"field": "quantum computing", "count": 3}),
    )
    await show(
        "get_journal_metrics",
        await server.get_journal_metrics({"title": "Nature Machine Intelligence"}),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
