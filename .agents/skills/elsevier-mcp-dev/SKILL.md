---
name: elsevier-mcp-dev
description: >-
  Development runbook for the Elsevier MCP Server. Use when adding or modifying Elsevier MCP tools,
  testing Scopus/SciVal/Abstract API endpoints, verifying package builds, or debugging stdio JSON-RPC responses.
---

# Elsevier MCP Server Development Guide

This skill provides step-by-step procedures for extending, testing, and packaging the Elsevier MCP Server.

## 1. Adding or Modifying an MCP Tool

When introducing a new MCP tool (e.g. Scopus Affiliation search, Subject classification):

1. **Define the Tool Schema**:
   In `ElsevierMCPServer._define_tools()` in [`elsevier_mcp_complete.py`](file:///Users/bar666/u/Elsevier_MCP/elsevier_mcp_complete.py), add the tool descriptor:
   ```python
   "my_new_tool": {
       "name": "my_new_tool",
       "description": "Tool description in Japanese/English matching project style",
       "inputSchema": {
           "type": "object",
           "properties": {
               "param1": {"type": "string", "description": "Parameter description"}
           },
           "required": ["param1"]
       }
   }
   ```

2. **Implement the Async Tool Handler**:
   Add an `async def my_new_tool(self, arguments: dict) -> dict:` method to `ElsevierMCPServer`.
   - Call Elsevier REST endpoints using `requests` with `get_headers()`.
   - Parse and return structured JSON dictionary with `"success": True` or `"success": False, "error": str(e)`.

3. **Scopus API Query Syntax Conventions**:
   - **General Search**: `TITLE-ABS-KEY(query)`
   - **Affiliation**: `AFFIL("Institution Name")` (*Do not use `aff()` which causes HTTP 400*)
   - **Publication Year**: `PUBYEAR = 2024`
   - **Open Access**: `OPENACCESS(1)`
   - **Boolean Combination**: `TITLE-ABS-KEY(query) AND AFFIL("MIT") AND PUBYEAR = 2024`

4. **API Response Parsing Safeguards**:
   - `opensearch:totalResults` and `citedby-count` in Elsevier JSON responses are **strings**. Always convert via `int(...)` before formatting or arithmetic:
     ```python
     total = int(data.get('search-results', {}).get('opensearch:totalResults', 0))
     ```

---

## 2. Validation & Build Verification

Run the verification pipeline:

```bash
# 1. Check Python syntax
python -m compileall -q elsevier_mcp_complete.py examples test.py

# 2. Test live endpoints (if ELSEVIER_API_KEY is available)
python test.py

# 3. Validate packaging (use --no-isolation in sandboxed/offline environments)
python -m build --no-isolation
python -m twine check dist/*
```

---

## 3. Testing JSON-RPC Stdio Interface

To manually test MCP protocol handlers via stdio JSON-RPC:

```bash
# 1. Initialize handshake (declares tools, prompts, resources)
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python elsevier_mcp_complete.py

# 2. List tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python elsevier_mcp_complete.py

# 3. Call a tool
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_papers","arguments":{"query":"artificial intelligence","count":2}}}' | python elsevier_mcp_complete.py

# 4. List prompts
echo '{"jsonrpc":"2.0","id":4,"method":"prompts/list","params":{}}' | python elsevier_mcp_complete.py

# 5. Get a prompt template
echo '{"jsonrpc":"2.0","id":5,"method":"prompts/get","params":{"name":"systematic_literature_review","arguments":{"topic":"Reinforcement Learning","year_range":"2022-2024"}}}' | python elsevier_mcp_complete.py

# 6. List static resources & dynamic templates
echo '{"jsonrpc":"2.0","id":6,"method":"resources/list","params":{}}' | python elsevier_mcp_complete.py
echo '{"jsonrpc":"2.0","id":7,"method":"resources/templates/list","params":{}}' | python elsevier_mcp_complete.py

# 7. Read a resource
echo '{"jsonrpc":"2.0","id":8,"method":"resources/read","params":{"uri":"elsevier://docs/scopus-search-syntax"}}' | python elsevier_mcp_complete.py
```
