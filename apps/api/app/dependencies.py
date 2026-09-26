"""Dependencies for FastAPI app."""
from functools import lru_cache

from elsevier_mcp.handlers import ToolHandlers


@lru_cache
def get_handlers() -> ToolHandlers:
    """Return a singleton instance of ToolHandlers."""
    return ToolHandlers()
