#!/usr/bin/env python3
"""Backward-compatibility shim for Elsevier MCP Server.

This module re-exports components from the elsevier_mcp package for
backward compatibility with existing imports and configuration files.
"""

import warnings

warnings.warn(
    "Importing from 'elsevier_mcp_complete' is deprecated and will be removed in a future release. "
    "Please import from 'elsevier_mcp' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from elsevier_mcp.client import BASE_URL, get_headers
from elsevier_mcp.server import VERSION, ElsevierMCPServer, handle_request, main, run_stdio

__all__ = [
    "BASE_URL",
    "VERSION",
    "ElsevierMCPServer",
    "get_headers",
    "handle_request",
    "main",
    "run_stdio",
]

if __name__ == "__main__":
    raise SystemExit(main())
