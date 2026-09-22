# Elsevier MCP Server - Project Rules & Guidelines

## 1. Code Style & Architecture
- **Language & Standards**: Python 3.10+, strict adherence to PEP 8, line length limit of 120 chars (configured via Ruff).
- **Type Annotations & Docstrings**: All new functions, MCP tool handlers, and methods must include Python type hints and comprehensive docstrings (Args, Returns, Raises).
- **MCP Protocol Conformance**:
  - Maintain JSON-RPC 2.0 stdio request/response handling in `handle_request()` and `run_stdio()`.
  - Tool definitions in `ElsevierMCPServer._define_tools()` must define accurate `inputSchema` objects compliant with MCP tool specifications.
  - Tool handlers must return structured dictionaries: `{"success": True, ...}` on success or `{"success": False, "error": "..."}` on failure.

## 2. API & Authentication Conventions
- **Header Generation**: Always use `get_headers()` in `elsevier_mcp.client` (or re-exported from `elsevier_mcp`) to construct API headers with `X-ELS-APIKey` and `Accept: application/json`.
- **Environment Variables**:
  - `ELSEVIER_API_KEY`: Required for live API interactions.
  - `ELSEVIER_INSTTOKEN`: Optional token for institutional access.
  - `ELSEVIER_RATE_LIMIT`: Optional client rate limit in req/sec (default 6.0).
  - `ELSEVIER_LOG_LEVEL`: Optional logging level (DEBUG, INFO, WARNING, ERROR).
  - `ELSEVIER_TIMEOUT`: Optional HTTP request timeout in seconds (default 15.0).
  - Never hardcode API keys or secrets in source code, examples, or tests.

## 3. Verification & Quality Assurance Checklist
Before committing or finalizing changes:
1. **Syntax & Compilation**:
   `python -m compileall -q elsevier_mcp tests elsevier_mcp_complete.py examples`
2. **Automated Unit & Integration Testing**:
   `pytest tests/ -v`
3. **Live API Testing**:
   `python test.py` (when `ELSEVIER_API_KEY` is configured)
4. **Package Build & Distribution Checks**:
   `python -m build`
   `python -m twine check dist/*`
4. **Documentation & Changelog**:
   Update `CHANGELOG.md`, `README.md`, or `README_ja.md` if tool definitions or CLI behaviors change.
5. **Git Commits**: Use Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
