---
description: "Workspace instructions for ZCode/agents: purpose, layout, verification commands, and gotchas of the Elsevier MCP Server."
tags:
  - agents
  - development-guide
  - conventions
title: AGENTS.md — Elsevier MCP Server Instructions
---

# AGENTS.md — Elsevier MCP Server

## Purpose

MCP server exposing Elsevier academic APIs (Scopus search, SciVal journal metrics, Abstract Retrieval) over JSON-RPC 2.0 stdio. Published as the `elsevier-mcp-server` PyPI package (Python 3.10+, MIT).

## Layout — package architecture

- `elsevier_mcp/` — core package:
  - `client.py` — `ElsevierAPIClient` with async `httpx`, retry logic, rate limiting, and `get_headers()`.
  - `rate_limiter.py` — `TokenBucketRateLimiter` managing request throttling.
  - `schemas.py` — Pydantic input models for validation.
  - `handlers.py` — `ToolHandlers` class with tool definitions and query execution.
  - `prompts.py` — MCP prompt definitions and message generator.
  - `resources.py` — static/dynamic MCP resource definitions and readers.
  - `server.py` — `ElsevierMCPServer`, JSON-RPC 2.0 dispatch, stdio event loop, and CLI entry point.
- `elsevier_mcp_complete.py` — backward-compatibility shim re-exporting server components with DeprecationWarning.
- `tests/` — pytest suite with `respx` mock HTTP routing (unit and integration tests).
- `test.py` — live API integration test script (needs `ELSEVIER_API_KEY` set).
- `examples/basic_usage.py` — client example.
- `README.md` / `README_ja.md` (Japanese), `CHANGELOG.md` — must be updated together when tools or CLI behavior change.
- `.agents/skills/elsevier-mcp-dev/SKILL.md` — detailed runbook for adding tools and testing JSON-RPC over stdio.

## Verification commands

```bash
python -m compileall -q elsevier_mcp tests elsevier_mcp_complete.py  # syntax check
pytest tests/ -v                                                     # offline unit test suite (mocked via respx)
python test.py                                                       # live endpoint tests, requires ELSEVIER_API_KEY
python -m build --no-isolation && python -m twine check dist/*       # packaging check
```

## Conventions and gotchas

- **MCP result shape**: tool handlers return `{"success": True, ...}` or `{"success": False, "error": "..."}` — always a dict, never raise to the caller.
- **Tool registration**: every tool needs an accurate `inputSchema` in `_define_tools()`, not just a handler method.
- **Auth**: use `get_headers()` for all API calls (`X-ELS-APIKey`, `Accept: application/json`). Env vars: `ELSEVIER_API_KEY` (required for live calls), `ELSEVIER_INSTTOKEN` (optional). Never hardcode keys.
- **Scopus query syntax**: use `AFFIL("Institution Name")` — lowercase `aff()` returns HTTP 400. General search wraps in `TITLE-ABS-KEY(query)`; year via `PUBYEAR = 2024`; OA via `OPENACCESS(1)`.
- **Elsevier JSON quirks**: numeric fields like `opensearch:totalResults` and `citedby-count` arrive as **strings** — wrap in `int(...)` before formatting/arithmetic.
- **Style**: PEP 8, 120-char lines, type hints + docstrings (Args/Returns/Raises) on all new functions and handlers. Tool names and code are English, but tool/parameter descriptions and docstrings in `_define_tools()` are written in Japanese — match that when adding tools.
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). Branching: work happens on `lokal/develop`, merged to `main`.

## Testing the stdio protocol manually

`echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python elsevier_mcp_complete.py`

Full initialize/tools/call/prompts/resources command set is in `.agents/skills/elsevier-mcp-dev/SKILL.md` §3.
