"""Elsevier MCP Server package."""

from elsevier_mcp.client import ElsevierAPIClient, get_headers
from elsevier_mcp.handlers import ToolHandlers
from elsevier_mcp.rate_limiter import TokenBucketRateLimiter
from elsevier_mcp.server import VERSION, ElsevierMCPServer, main

__version__ = VERSION

__all__ = [
    "VERSION",
    "ElsevierAPIClient",
    "ElsevierMCPServer",
    "TokenBucketRateLimiter",
    "ToolHandlers",
    "__version__",
    "get_headers",
    "main",
]
