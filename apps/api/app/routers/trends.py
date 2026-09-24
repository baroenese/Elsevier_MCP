"""Research trends routes."""
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
async def get_trends(body: TrendsBody, handlers: ToolHandlers = Depends(get_handlers)):
    """Analyze research trends."""
    return await handlers.analyze_research_trends(field=body.field, start_year=body.start_year, end_year=body.end_year)
