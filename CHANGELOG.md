# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
