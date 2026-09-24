"""Research trends routes."""

from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from elsevier_mcp.handlers import ToolHandlers
from app.dependencies import get_handlers

router = APIRouter(tags=["trends"])


class TrendsBody(BaseModel):
    """Trends request body."""

    field: str
    start_year: int = 2020
    end_year: int = 2024


@router.post("/trends")
async def get_trends(
    body: TrendsBody, handlers: ToolHandlers = Depends(get_handlers)
) -> dict[str, Any]:
    """Analyze multi-year research trends for a field."""
    field = body.field.strip()
    if not field:
        return {"success": False, "error": "Field is required"}
    start, end = sorted((body.start_year, body.end_year))
    years = list(range(max(start, 1970), min(end, 2026) + 1))[:10]
    return await handlers.analyze_research_trends({"field": field, "years": years})
