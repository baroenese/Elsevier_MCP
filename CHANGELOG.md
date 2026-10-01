# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2026-09-27

### Added
- Playwright e2e smoke suite for `apps/web` (`nx e2e web`): every page shell, nav tabs, and form controls rendered against the production build — no backend required.
- CI coverage gate: Python test suites fail below 90% coverage (`--cov-fail-under`).
- pytest-cov coverage reporting in `nx test` for both Python projects (`elsevier-mcp` 92.9%, `api` 92%).
- Ruff lint targets replacing `compileall` (`nx lint elsevier-mcp`, `nx lint api`) with pragmatic rule config.
- ESLint flat config (`typescript-eslint` recommended) for `apps/web` and `packages/ui`; `nx lint web`/`nx lint ui` now run eslint + `tsc --noEmit`.
- CI now runs both pytest suites and `compileall` with post-monorepo paths (tests previously never ran in CI); release workflow builds from `packages/elsevier-mcp`.
- 39 new tests: stdio loop (`-32700`/`-32603`, CLI flags), client retries/timeouts/env fallbacks/lifecycle, resource templates with error branches, remaining prompt templates, `inputSchema` ↔ Pydantic consistency, rate-limiter concurrency regression, API trends clamping, journal-compare rules, config error path, DI caching.

### Changed
- `test.py` live-check script migrated from `requests` to `httpx` (already a package dependency) with type hints; `requirements.txt` updated accordingly.
- Internal refactor of `handlers.py`: shared `_fetch_json`/`_validated`/`_to_int`/`_parse_total_results` helpers replace copy-pasted request and integer-coercion boilerplate; `get_journal_metrics` parsing split into testable helpers. External result shapes unchanged (locked by regression tests).

### Fixed
- `TokenBucketRateLimiter.acquire` no longer sleeps while holding the lock (concurrent waiters no longer serialize) and no longer discards fractional token credit after waiting.
- `tools/call` maps unexpected handler exceptions to JSON-RPC `-32603` instead of crashing the stdio loop.
- Removed legacy `elsevier_webapp.py` (superseded by `apps/api`) and its `static/` assets; `next lint` script (removed in Next 16) replaced with ESLint.

## [1.3.0] - 2026-10-01

### Added
- Converted repository into an Nx monorepo orchestrating:
  - `packages/elsevier-mcp`: Python MCP server library (relocated, fully preserving stdio JSON-RPC protocol).
  - `packages/ui`: Shared React/TypeScript UI component library (@elsevier-mcp/ui).
  - `apps/api`: Modular FastAPI backend service exposing REST endpoints for Scopus search, abstracts, trends, and journal metrics.
  - `apps/web`: Next.js 16 (App Router + Turbopack + Tailwind CSS v4) frontend with BFF Route Handlers proxying to FastAPI.
- Configured Nx task targets for testing, linting, building, and serving across Python and TypeScript projects.
- Comprehensive automated test suite with unified `npx nx run-many -t test` spanning 68 tests across all 4 packages.
- Frontend unit test suite in `apps/web/tests/` running on Node 24 native test runner (`node:test`).
- Two new MCP tools, both working on keys without author-retrieval entitlements (via the general search endpoint):
  - `search_author_papers`: publications by author through `AUTH-ID(...)`/`AUTH("...")` with an optional `AFFIL(...)` filter, count/year/start/sort.
  - `find_author_candidates`: homonym disambiguation — samples search results and groups them by author ID (field-selected when the key allows it, with graceful fallback) or by creator name + affiliation.
- `search_papers` gains pagination (`start` offset, 0–5999) and `sort` (`citedby-count`, `coverdate`, `relevancy` variants); the response echoes `start`.
- `POST /api/author-papers` REST endpoint (FastAPI) exposing `search_author_papers`; `get_author_info` is intentionally not exposed because its SciVal endpoint returns 403 on restricted keys.
- Institutions page in the web UI (institution/year form, `MetricTile` summary, top-cited papers table) — the backend endpoint previously had no frontend consumer; nav gains an Institutions tab.
- Previous/Next pagination on the Search page driven by the new `start` parameter, with a result-range summary.
- Root-segment App Router files for `apps/web`: global error boundary (`error.tsx`) with retry, route-transition loading skeleton (`loading.tsx`), and 404 page (`not-found.tsx`).
- Package-specific `packages/elsevier-mcp/README.md`; `MANIFEST.in` trimmed to files that actually exist in the package directory.
- Version drift guard test locking `server.VERSION` to the pyproject `[project].version`.
- Verified Romi Satria Wahono bibliography deliverables in `research/` (57 cross-validated publications, 2000–2026, with per-work CSV).

### Changed
- Dropped the unused `mcp>=1.0.0` dependency (the stdio JSON-RPC protocol is hand-rolled); `requirements.txt` synced.
- Documented live-verified API-key entitlement limits in the dev runbook: citation overview and ScienceDirect article retrieval return 403, SciVal author analytics 403 (so `get_author_info` errors on restricted keys), and general search rejects `AUTH-ID(...)` with 400 while `field=authid` is silently dropped.
- `.env` template renamed to `.env.example` and unignored (the `.env.*` ignore rule previously made it uncommittable).
- Dev runbook `.agents/skills/elsevier-mcp-dev/SKILL.md` refreshed to the monorepo layout (five-step tool workflow, shared helpers, live-tested API-key entitlement limits); AGENTS.md no longer claims PyPI distribution.

### Fixed
- Package build (`nx build elsevier-mcp`, release workflow) no longer fails: pyproject referenced a `README.md` and `MANIFEST.in` referenced `README_ja.md`/`LICENSE`/`example_mcp_config.json`/`examples/` that did not exist inside `packages/elsevier-mcp/`.
- `apps/api` `sys.path` fallback now resolves to the repository root instead of the nonexistent `apps/packages/elsevier-mcp` (imports only worked via the venv editable install).
- Removed dead code: GET branch of the `/api/config` BFF route (FastAPI only defines POST, so it would 405), no-arg `api.config()` branch in the web api-client, unused `/api/py/:path*` Next.js rewrite, unused `api_host`/`api_port` settings fields.
- Fixed author metadata parsing in `get_paper_abstract` and `parse_paper_entry` to correctly handle nested Scopus dictionary and array structures (`_parse_author_names`), preventing React object rendering exceptions.
- Added comprehensive edge-case unit tests for `_parse_author_names`.

## [1.2.0] - 2026-09-22

### Added
- Modular `elsevier_mcp` package structure separating concerns into `client`, `schemas`, `handlers`, `prompts`, `resources`, `server`, and `rate_limiter`.
- Asynchronous HTTP client using `httpx.AsyncClient` with connection pooling.
- Token bucket rate limiter (`TokenBucketRateLimiter`) with configurable rate via `ELSEVIER_RATE_LIMIT` environment variable (default: 6 req/s).
- Exponential backoff retry with jitter on HTTP 429 (rate limited) and 5xx (server error) responses, respecting `Retry-After` headers.
- Pydantic input models for all 7 MCP tools (`SearchPapersInput`, `GetPaperAbstractInput`, `GetAuthorInfoInput`, `AnalyzeResearchTrendsInput`, `GetInstitutionPapersInput`, `SearchOpenAccessPapersInput`, `GetJournalMetricsInput`).
- Configurable structured logging via standard library `logging` directed to stderr (`ELSEVIER_LOG_LEVEL` environment variable).
- Configurable HTTP timeout via `ELSEVIER_TIMEOUT` environment variable.
- Comprehensive pytest test suite under `tests/` utilizing `pytest-asyncio` and `respx` for mock HTTP routing (40 automated tests).
- Development extras `[project.optional-dependencies] dev` in `pyproject.toml`.

### Changed
- Converted `elsevier_mcp_complete.py` into a lightweight backward-compatibility shim that delegates to `elsevier_mcp`.
- Updated PyPI package entry point to `elsevier_mcp.server:main`.
- Dynamic current year calculation in `search_open_access_papers`, eliminating hardcoded publication year.

### Added
- `get_journal_metrics` tool for querying Scopus journal evaluation metrics (CiteScore, SJR, SNIP, Open Access status, and computed Q1-Q4 Quartiles).
- MCP Prompts protocol support (`prompts/list`, `prompts/get`) with built-in templates:
  - `systematic_literature_review`: Multi-paper synthesis, methodology comparison tables, and research gap discovery.
  - `paper_deep_dive`: Critical appraisal, methodology breakdown, and threats to validity.
  - `research_trend_analysis`: Momentum analysis, publication volume velocity, and emerging subfield detection.
- MCP Resources protocol support (`resources/list`, `resources/templates/list`, `resources/read`):
  - `elsevier://docs/scopus-search-syntax`: Complete Scopus query syntax reference and boolean operator guide.
  - `elsevier://paper/{eid}`: Dynamic resource rendering paper abstract and bibliographic metadata in Markdown.
  - `elsevier://trends/{field}`: Dynamic resource rendering annual publication volume and growth rates in Markdown.
  - `elsevier://journal/{query}`: Dynamic resource rendering journal CiteScore, SJR, SNIP, and Quartiles in Markdown.
- Support for explicit Scopus field code queries (`AUTH`, `TITLE`, `DOI`, `AFFIL`, etc.) in `search_papers` without nested wrapping.
- Antigravity project rules (`GEMINI.md`) and development skill (`elsevier-mcp-dev`).
- GitHub Actions CI and release workflows.
- Pull request template and security policy.

### Changed
- Modernized package metadata with `pyproject.toml`.
- Updated MCP installation docs to use the `elsevier-mcp-server` console command.

### Fixed
- Fixed source distribution builds by including the runtime module and package metadata.
- Removed committed virtual environment and Python bytecode artifacts from version control.
- Fixed Scopus institution paper search query syntax (`AFFIL("...")` instead of `aff(...)`).
- Fixed string-to-integer conversion for `opensearch:totalResults` in `test.py`.

## [1.0.0] - 2024-12-20

### Added
- MCP (Model Context Protocol) server for Elsevier APIs
- Scopus API integration for paper search
- SciVal API integration for author information
- Abstract Retrieval API for detailed paper metadata
- Research trend analysis functionality
- Institution paper statistics
- Open access paper search
- Comprehensive test suite
- Documentation and usage examples
- Cursor IDE configuration support

### Features
- **Paper Search**: Query academic papers by keywords, authors, and fields
- **Author Analysis**: Retrieve detailed researcher profiles and metrics
- **Research Trends**: Analyze year-over-year publication trends by field
- **Institution Statistics**: Get paper counts and metrics by institution
- **Open Access**: Search specifically for open access publications
- **Abstract Retrieval**: Fetch detailed abstracts and metadata

### APIs Integrated
- Scopus Search API
- SciVal Author Lookup API
- Abstract Retrieval API
- SciVal Analytics API

### Documentation
- Comprehensive README with setup instructions
- API usage examples
- Cursor IDE configuration guide
- Contributing guidelines
- MIT License

### Technical Details
- Python 3.7+ support
- JSON-RPC 2.0 MCP protocol implementation
- Error handling and rate limiting
- Environment variable configuration
- Cross-platform compatibility

### Testing
- Complete API endpoint testing
- Integration tests with live Elsevier APIs
- Example usage scripts
- CI/CD ready structure

---

## How to Update This Changelog

When making changes to this project:

1. Add new entries under `[Unreleased]`
2. Use the following categories:
   - `Added` for new features
   - `Changed` for changes in existing functionality
   - `Deprecated` for soon-to-be removed features
   - `Removed` for now removed features
   - `Fixed` for any bug fixes
   - `Security` in case of vulnerabilities

3. When releasing, move items from `[Unreleased]` to a new version section
4. Add a release date in YYYY-MM-DD format
