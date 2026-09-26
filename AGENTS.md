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

## Layout — Nx monorepo architecture

- `packages/elsevier-mcp/` — core Python MCP package:
  - `elsevier_mcp/` — `client.py`, `rate_limiter.py`, `schemas.py`, `handlers.py`, `prompts.py`, `resources.py`, `server.py`
  - `elsevier_mcp_complete.py` — backward-compatibility shim
  - `tests/` — pytest suite (mocked via respx)
  - `test.py` — live API integration test script (needs `ELSEVIER_API_KEY` set)
  - `pyproject.toml`, `setup.py`, `project.json`
- `apps/api/` — FastAPI backend service exposing REST endpoints (`health`, `search`, `abstract`, `trends`, `journals`).
- `apps/web/` — Next.js 16 Web UI (App Router, Tailwind CSS v4, BFF Route Handlers).
- `packages/ui/` — shared `@elsevier-mcp/ui` React components (`MetricTile`, `QuartileBadge`, etc.).
- `research/`, `knowledge/` — research notes / deliverable reports (some in Bahasa Indonesia), not application code; don't mix them into package builds.
- `nx.json`, `package.json`, `tsconfig.base.json` — Nx monorepo configuration.
- `README.md` / `README_ja.md` (Japanese), `CHANGELOG.md` — must be updated together when tools or CLI behavior change.
- `.agents/skills/elsevier-mcp-dev/SKILL.md` — detailed runbook for adding tools and testing JSON-RPC over stdio.

## Verification commands

```bash
# Nx monorepo verification
npx nx test elsevier-mcp                                             # Python unit tests (respx mocked)
npx nx test api                                                      # FastAPI route + endpoint tests
npx nx build web                                                     # Next.js 16 production build
npx nx lint api && npx nx lint elsevier-mcp                          # Python syntax check

# Direct Python commands (system python has no pytest — use the repo venv at .venv/bin/python)
pytest packages/elsevier-mcp/tests/ -v
pytest apps/api/tests/ -v
python packages/elsevier-mcp/test.py                                 # live endpoint tests, requires ELSEVIER_API_KEY
```

## Conventions and gotchas

- **MCP result shape**: tool handlers return `{"success": True, ...}` or `{"success": False, "error": "..."}` — always a dict, never raise to the caller.
- **Tool registration**: every tool needs an accurate `inputSchema` in `_define_tools()`, not just a handler method.
- **Auth**: use `get_headers()` for all API calls (`X-ELS-APIKey`, `Accept: application/json`). Env vars: `ELSEVIER_API_KEY` (required for live calls), `ELSEVIER_INSTTOKEN` (optional). Optional tuning knobs: `ELSEVIER_RATE_LIMIT` (req/sec, default 6), `ELSEVIER_LOG_LEVEL` (default `INFO`), `ELSEVIER_TIMEOUT` (seconds, default 15). Never hardcode keys.
- **Scopus query syntax**: use `AFFIL("Institution Name")` — lowercase `aff()` returns HTTP 400. General search wraps in `TITLE-ABS-KEY(query)`; year via `PUBYEAR = 2024`; OA via `OPENACCESS(1)`.
- **Elsevier JSON quirks**: numeric fields like `opensearch:totalResults` and `citedby-count` arrive as **strings** — wrap in `int(...)` before formatting/arithmetic.
- **Style**: PEP 8, 120-char lines, type hints + docstrings (Args/Returns/Raises) on all new functions and handlers. Tool names and code are English, but tool/parameter descriptions and docstrings in `_define_tools()` are written in Japanese — match that when adding tools.
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). Branching: work happens on `lokal/develop`, merged to `main`.

## Research notes (`knowledge/`, `research/`)

- Notes and deliverable reports may be written in Bahasa Indonesia; code, tool descriptions, and this file stay English.
- Every note carries OK-style frontmatter (e.g. `description`/`tags`/`title`) — the OK workspace indexes the repo root as its content dir (`content.dir: .`).
- Deliverable reports live in these folders and are mirrored into OK; never mix them into package builds or the PyPI output.

## Testing the stdio protocol manually

`echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python elsevier_mcp_complete.py`

Full initialize/tools/call/prompts/resources command set is in `.agents/skills/elsevier-mcp-dev/SKILL.md` §3.
