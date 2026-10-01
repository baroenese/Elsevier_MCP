# elsevier-mcp-server

MCP (Model Context Protocol) server exposing Elsevier academic APIs — Scopus search, SciVal journal metrics, and Abstract Retrieval — over JSON-RPC 2.0 on stdio.

This is the core Python package of the [Elsevier_MCP monorepo](https://github.com/yasufumi-nakata/Elsevier_MCP). See the repository root for full documentation ([English](https://github.com/yasufumi-nakata/Elsevier_MCP) / [Japanese](https://github.com/yasufumi-nakata/Elsevier_MCP/blob/main/README_ja.md)), including the FastAPI service (`apps/api`) and Next.js UI (`apps/web`) built on top of this package.

## Installation (from source)

The package is currently distributed via this repository and GitHub Releases; it is **not yet published to PyPI**.

```bash
git clone https://github.com/yasufumi-nakata/Elsevier_MCP
pip install ./Elsevier_MCP/packages/elsevier-mcp
```

Requires Python 3.10+.

## Quick start

```bash
export ELSEVIER_API_KEY=your_key_here
elsevier-mcp-server
```

Manual stdio smoke test:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' | elsevier-mcp-server
```

## Tools

| Tool | Purpose |
|---|---|
| `search_papers` | Scopus keyword search (`TITLE-ABS-KEY`, year filter, sorted by citations) |
| `get_paper_abstract` | Abstract + metadata by EID or DOI |
| `get_author_info` | Researcher profile by Scopus author ID (SciVal) |
| `analyze_research_trends` | Year-by-year publication counts + growth rates |
| `get_institution_papers` | Institution publication totals + top-cited papers |
| `search_open_access_papers` | Open-access search for a research field |
| `get_journal_metrics` | CiteScore, SJR, SNIP, quartiles, subject rankings |

Also registers 3 prompts (`systematic_literature_review`, `paper_deep_dive`, `research_trend_analysis`) and 4 resources (Scopus search syntax guide + 3 markdown renderers).

## Configuration (environment variables)

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `ELSEVIER_API_KEY` | yes (for live calls) | — | Elsevier API key |
| `ELSEVIER_INSTTOKEN` | no | — | Institutional token |
| `ELSEVIER_RATE_LIMIT` | no | `6` | Max requests per second |
| `ELSEVIER_LOG_LEVEL` | no | `INFO` | Logging level |
| `ELSEVIER_TIMEOUT` | no | `15` | HTTP timeout (seconds) |

## Development

```bash
pip install -e '.[dev]'
pytest tests/ -v --cov=elsevier_mcp
ruff check .
```

## License

MIT
