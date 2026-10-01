---
name: elsevier-mcp-dev
description: >-
  Development runbook for the Elsevier MCP Server. Use when adding or modifying Elsevier MCP tools,
  testing Scopus/SciVal/Abstract API endpoints, verifying package builds, or debugging stdio JSON-RPC responses.
---

# Elsevier MCP Server Development Guide

This skill provides step-by-step procedures for extending, testing, and packaging the Elsevier MCP Server
(core package: `packages/elsevier-mcp/`, Nx project name `elsevier-mcp`).

## 1. Adding or Modifying an MCP Tool

A tool touches five places (four in code, one in docs). Existing example: `search_papers`.

1. **Pydantic input model** — `packages/elsevier-mcp/elsevier_mcp/schemas.py`:
   ```python
   class MyNewToolInput(BaseModel):
       """Input schema for my_new_tool."""
       param1: str = Field(..., description="Parameter description (Japanese, matching project style)")
   ```

2. **Tool descriptor** — `define_tools()` in `packages/elsevier-mcp/elsevier_mcp/handlers.py`:
   add an entry whose `inputSchema` matches the Pydantic model. `tests/test_tool_schemas.py`
   enforces schema ↔ model consistency automatically, so keep them in sync.
   Tool/parameter descriptions are written in **Japanese** (project convention).

3. **Handler** — async method on `ToolHandlers` in `handlers.py`:
   ```python
   async def my_new_tool(self, arguments: dict) -> dict:
       """<Japanese summary> ... Args/Returns/Raises docstring."""
       args, error = _validated(MyNewToolInput, arguments)
       if error:
           return error
       data = await _fetch_json(self.client, "/content/...", params={...})
       if isinstance(data, dict) and "error" in data:
           return {"success": False, "error": data["error"]}
       return {"success": True, ...}
   ```
   - Always return a dict with `"success": True/False` — never raise to the caller.
   - Reuse the shared helpers `_fetch_json`, `_validated`, `_to_int`, `_parse_total_results`
     instead of re-rolling try/except skeletons.
   - Call Elsevier REST endpoints through `ElsevierAPIClient` (httpx, `get_headers()` adds
     `X-ELS-APIKey`/`Accept`); do not use `requests` and do not call httpx directly.

4. **Server wrapper** — thin async method on `ElsevierMCPServer` in `server.py` forwarding to
   the handler (`tools/call` dispatches via `getattr(server, tool_name)`), plus registration in
   the dispatch surface if a new capability type is added.

5. **Tests & docs**:
   - Handler tests in `packages/elsevier-mcp/tests/` (respx-mocked; realistic sample payloads
     live in `conftest.py`). `test_tool_schemas.py` covers the new tool's schema automatically.
   - Update `README.md` + `README_ja.md` + `CHANGELOG.md` together (repo convention).

### Scopus API Query Syntax Conventions

- **General Search**: `TITLE-ABS-KEY(query)`
- **Affiliation**: `AFFIL("Institution Name")` (*lowercase `aff()` causes HTTP 400*)
- **Publication Year**: `PUBYEAR = 2024`
- **Open Access**: `OPENACCESS(1)`
- **Author**: `AUTH-ID(12345678901)` or `AUTH("Surname, Initials")` — beware homonym
  contamination with initials-only queries
- **Boolean Combination**: `TITLE-ABS-KEY(query) AND AFFIL("MIT") AND PUBYEAR = 2024`

### API Response Parsing Safeguards

`opensearch:totalResults` and `citedby-count` in Elsevier JSON responses are **strings**.
Always convert via `int(...)` (or `_to_int` / `_parse_total_results`) before formatting or
arithmetic:

```python
total = int(data.get('search-results', {}).get('opensearch:totalResults', 0))
```

### Known API-key entitlement limits (live-verified 2026-10-01)

- Author retrieval (`/content/author/...`) and `view=COMPLETE` return **401**; the SciVal
  author analytics endpoint (`/analytics/scival/author/...`, used by `get_author_info`)
  returns **403 ENTITLEMENTS_ERROR** — the tool returns an error dict on this key.
- Citation overview (`/content/abstract/citations`) → **403**: no citation-overview tool.
- ScienceDirect Article Retrieval (`/content/article`) → **403**: no full-text tool.
- General search rejects `AUTH-ID(...)` with **400 INVALID_INPUT** ("Error translating query");
  use `AUTH("Surname, Initials")` plus an `AFFIL(...)` filter instead. `field=authid` is
  accepted but author IDs are silently dropped from the response, so
  `find_author_candidates` groups by creator name + affiliation on this key.
- `SJR`/`SNIP` come from `serial/title?view=STANDARD`; CiteScore from `view=CITESCORE`.

---

## 2. Validation & Build Verification

```bash
# 1. Nx targets (preferred)
npx nx test elsevier-mcp        # pytest + coverage
npx nx lint elsevier-mcp        # ruff
npx nx build elsevier-mcp       # python -m build --no-isolation

# 2. Validate packaging
.venv/bin/python -m twine check packages/elsevier-mcp/dist/*

# 3. Test live endpoints (requires ELSEVIER_API_KEY; loads repo .env)
set -a; source .env; set +a
.venv/bin/python packages/elsevier-mcp/test.py
```

---

## 3. Testing JSON-RPC Stdio Interface

Use the backward-compatibility shim (repo venv, system python has no deps installed):

```bash
SHIM=packages/elsevier-mcp/elsevier_mcp_complete.py
PY=.venv/bin/python

# 1. Initialize handshake (declares tools, prompts, resources)
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | $PY $SHIM

# 2. List tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | $PY $SHIM

# 3. Call a tool (live API; needs ELSEVIER_API_KEY)
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_papers","arguments":{"query":"artificial intelligence","count":2}}}' | $PY $SHIM
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_journal_metrics","arguments":{"title":"Machine Learning"}}}' | $PY $SHIM

# 4. List prompts
echo '{"jsonrpc":"2.0","id":4,"method":"prompts/list","params":{}}' | $PY $SHIM

# 5. Get a prompt template
echo '{"jsonrpc":"2.0","id":5,"method":"prompts/get","params":{"name":"systematic_literature_review","arguments":{"topic":"Reinforcement Learning","year_range":"2022-2024"}}}' | $PY $SHIM

# 6. List static resources & dynamic templates
echo '{"jsonrpc":"2.0","id":6,"method":"resources/list","params":{}}' | $PY $SHIM
echo '{"jsonrpc":"2.0","id":7,"method":"resources/templates/list","params":{}}' | $PY $SHIM

# 7. Read a resource
echo '{"jsonrpc":"2.0","id":8,"method":"resources/read","params":{"uri":"elsevier://docs/scopus-search-syntax"}}' | $PY $SHIM
echo '{"jsonrpc":"2.0","id":9,"method":"resources/read","params":{"uri":"elsevier://journal/Nature"}}' | $PY $SHIM
```
