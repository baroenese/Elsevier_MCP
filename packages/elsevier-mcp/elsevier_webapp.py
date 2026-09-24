#!/usr/bin/env python3
"""
Elsevier MCP Web UI — local FastAPI app that reuses the MCP server handlers.

The stdio MCP server (`elsevier_mcp_complete.main`) is untouched: AI clients keep
talking JSON-RPC over stdio. This module adds a browser UI that calls the same
`ElsevierMCPServer` handlers directly, each wrapped in `asyncio.to_thread`
because the handlers perform blocking `requests` calls internally.

Run with:  elsevier-mcp-webapp   (or: python -m elsevier_webapp)
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from elsevier_mcp_complete import VERSION, ElsevierMCPServer

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = Path.home() / ".elsevier-mcp"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Fallback for wheel installs where static/ ships under <prefix>/share/ (see pyproject data-files).
_STATIC_CANDIDATES = [
    BASE_DIR / "static",
    Path(sys.prefix) / "share" / "elsevier-mcp-server" / "static",
]


def _resolve_static_dir() -> Path:
    """Return the first existing static/ directory (dev checkout or installed data-files)."""
    for candidate in _STATIC_CANDIDATES:
        if candidate.is_dir():
            return candidate
    return _STATIC_CANDIDATES[0]


def load_config_into_env() -> None:
    """Load saved credentials from ~/.elsevier-mcp/config.json into os.environ.

    Values already present in the environment always win, so shell-exported
    variables are never overwritten. The key itself is never logged.
    """
    if not CONFIG_FILE.is_file():
        return
    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Warning: could not read {CONFIG_FILE}: {exc}", file=sys.stderr)
        return
    for env_name, config_key in (("ELSEVIER_API_KEY", "api_key"), ("ELSEVIER_INSTTOKEN", "insttoken")):
        value = config.get(config_key)
        if value and not os.environ.get(env_name):
            os.environ[env_name] = value


def save_config(api_key: str | None, insttoken: str | None) -> None:
    """Persist credentials to ~/.elsevier-mcp/config.json with 0600 permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config: dict[str, str] = {}
    if CONFIG_FILE.is_file():
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            config = {}
    if api_key is not None:
        if api_key == "":
            config.pop("api_key", None)
        else:
            config["api_key"] = api_key
    if insttoken is not None:
        if insttoken == "":
            config.pop("insttoken", None)
        else:
            config["insttoken"] = insttoken
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    CONFIG_FILE.chmod(0o600)


def _run_sync_handler(server: ElsevierMCPServer, name: str, arguments: dict) -> dict:
    """Run an async MCP handler to completion on a worker thread.

    Handlers in elsevier_mcp_complete.py are declared async but use blocking
    `requests` internally, so they must not run on the uvicorn event loop.
    """
    return asyncio.run(getattr(server, name)(arguments))


load_config_into_env()
_server = ElsevierMCPServer()

app = FastAPI(title="Elsevier MCP Web UI", version=VERSION, docs_url="/api/docs")


class SearchBody(BaseModel):
    query: str
    author: str | None = None
    year: str | None = None
    open_access: bool = False
    count: int = 10


class AbstractBody(BaseModel):
    eid: str | None = None
    doi: str | None = None


class TrendsBody(BaseModel):
    field: str
    start_year: int = 2020
    end_year: int = 2024


class InstitutionBody(BaseModel):
    institution: str
    year: int = 2024


class JournalCompareBody(BaseModel):
    queries: list[str]


class ConfigBody(BaseModel):
    api_key: str | None = None
    insttoken: str | None = None


async def call_tool(name: str, arguments: dict[str, Any]) -> dict:
    """Invoke an MCP tool handler off the event loop and normalize errors."""
    try:
        return await asyncio.to_thread(_run_sync_handler, _server, name, dict(arguments))
    except Exception as exc:  # noqa: BLE001 - handlers return dicts; this is the outer safety net
        return {"success": False, "error": str(exc)}


def _compose_search_query(query: str, author: str | None, open_access: bool) -> str:
    """Build an explicit Scopus query so search_papers uses it verbatim.

    Composing field codes here avoids TITLE-ABS-KEY mis-wrapping inside the handler
    (e.g. OPENACCESS(1) must stay outside the TITLE-ABS-KEY term).
    """
    composed = f"TITLE-ABS-KEY({query.strip()})"
    if author and author.strip():
        composed += f' AND AUTHOR-NAME("{author.strip()}")'
    if open_access:
        composed += " AND OPENACCESS(1)"
    return composed


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(_resolve_static_dir() / "index.html")


@app.get("/api/health")
async def health() -> dict:
    """Configuration status: which credentials are active and where they came from."""
    return {
        "success": True,
        "version": VERSION,
        "api_key_set": bool(os.environ.get("ELSEVIER_API_KEY")),
        "api_key_source": (
            "environment" if os.environ.get("ELSEVIER_API_KEY") else
            "config_file" if _config_has("api_key") else
            "not_set"
        ),
        "insttoken_set": bool(os.environ.get("ELSEVIER_INSTTOKEN")),
        "config_file": str(CONFIG_FILE),
    }


def _config_has(key: str) -> bool:
    if not CONFIG_FILE.is_file():
        return False
    try:
        return bool(json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get(key))
    except (OSError, json.JSONDecodeError):
        return False


@app.get("/api/tools")
async def tools() -> dict:
    """Expose the MCP tool registry so the UI and settings page stay in sync."""
    return {
        "success": True,
        "tools": [
            {"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]}
            for t in _server.tools.values()
        ],
    }


@app.post("/api/search")
async def search(body: SearchBody) -> JSONResponse:
    if not body.query.strip():
        return JSONResponse({"success": False, "error": "Query is required"}, status_code=400)
    arguments: dict[str, Any] = {
        "query": _compose_search_query(body.query, body.author, body.open_access),
        "count": max(1, min(body.count, 25)),
    }
    if body.year and body.year.strip():
        arguments["year"] = body.year.strip()
    result = await call_tool("search_papers", arguments)
    return JSONResponse(result, status_code=200 if result.get("success") else 502)


@app.post("/api/abstract")
async def abstract(body: AbstractBody) -> JSONResponse:
    result = await call_tool("get_paper_abstract", {"eid": body.eid or "", "doi": body.doi or ""})
    return JSONResponse(result, status_code=200 if result.get("success") else 502)


@app.post("/api/trends")
async def trends(body: TrendsBody) -> JSONResponse:
    if not body.field.strip():
        return JSONResponse({"success": False, "error": "Field is required"}, status_code=400)
    start, end = sorted((body.start_year, body.end_year))
    years = list(range(max(start, 1970), min(end, 2026) + 1))[:10]
    result = await call_tool("analyze_research_trends", {"field": body.field.strip(), "years": years})
    return JSONResponse(result, status_code=200 if result.get("success") else 502)


@app.post("/api/institution")
async def institution(body: InstitutionBody) -> JSONResponse:
    result = await call_tool("get_institution_papers", {"institution": body.institution, "year": body.year})
    return JSONResponse(result, status_code=200 if result.get("success") else 502)


@app.get("/api/journal-metrics")
async def journal_metrics(
    query: str = Query(default=""), issn: str = Query(default="")
) -> JSONResponse:
    if not query.strip() and not issn.strip():
        return JSONResponse({"success": False, "error": "query or issn is required"}, status_code=400)
    arguments: dict[str, Any] = {}
    if issn.strip():
        arguments["issn"] = issn.strip()
    else:
        arguments["title"] = query.strip()
    result = await call_tool("get_journal_metrics", arguments)
    return JSONResponse(result, status_code=200 if result.get("success") else 502)


@app.post("/api/journal-compare")
async def journal_compare(body: JournalCompareBody) -> JSONResponse:
    """Fetch metrics for several journals sequentially and return one entry per query."""
    queries = [q.strip() for q in body.queries if q.strip()][:4]
    if not queries:
        return JSONResponse({"success": False, "error": "At least one query is required"}, status_code=400)
    journals = []
    for q in queries:
        arguments = {"issn": q} if q.replace("-", "").isdigit() else {"title": q}
        result = await call_tool("get_journal_metrics", arguments)
        journals.append({"query": q, **result})
    return JSONResponse({"success": True, "journals": journals})


@app.get("/api/config")
async def get_config() -> dict:
    return await health()


@app.post("/api/config")
async def set_config(body: ConfigBody) -> dict:
    """Save credentials to ~/.elsevier-mcp/config.json (0600) and apply them live.

    Empty string clears a saved value; omitted fields are left untouched.
    """
    try:
        save_config(body.api_key, body.insttoken)
    except OSError as exc:
        return {"success": False, "error": f"Could not write config: {exc}"}
    if body.api_key:
        os.environ["ELSEVIER_API_KEY"] = body.api_key
    elif body.api_key == "" and _config_has("api_key") is False:
        os.environ.pop("ELSEVIER_API_KEY", None)
    if body.insttoken:
        os.environ["ELSEVIER_INSTTOKEN"] = body.insttoken
    return await health()


app.mount("/static", StaticFiles(directory=_resolve_static_dir()), name="static")


def main() -> int:
    """Console entry point for the local web UI."""
    if "--version" in sys.argv:
        print(VERSION)
        return 0
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: elsevier-mcp-webapp [--host HOST] [--port PORT] [--version]")
        print("Runs the Elsevier MCP Web UI (FastAPI) on localhost.")
        return 0

    host = "127.0.0.1"
    port = 8000
    argv = sys.argv[1:]
    if "--host" in argv:
        host = argv[argv.index("--host") + 1]
    if "--port" in argv:
        port = int(argv[argv.index("--port") + 1])

    if not os.environ.get("ELSEVIER_API_KEY"):
        print(
            "Warning: ELSEVIER_API_KEY is not set. Configure it on the Settings tab "
            f"or in {CONFIG_FILE}.",
            file=sys.stderr,
        )

    import uvicorn

    print(f"Elsevier MCP Web UI running at http://{host}:{port}", file=sys.stderr)
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
