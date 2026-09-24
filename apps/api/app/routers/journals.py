"""Journal metrics routes."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from elsevier_mcp.handlers import ToolHandlers
from app.dependencies import get_handlers

router = APIRouter(tags=["journals"])

class JournalCompareBody(BaseModel):
    """Journal compare request body."""
    queries: list[str]

@router.get("/journal-metrics")
async def get_metrics(query: str | None = None, issn: str | None = None, handlers: ToolHandlers = Depends(get_handlers)):
    """Get journal metrics."""
    return await handlers.get_journal_metrics(query=query, issn=issn)

@router.post("/journal-compare")
async def compare_journals(body: JournalCompareBody, handlers: ToolHandlers = Depends(get_handlers)):
    """Compare multiple journals."""
    results = {}
    # Fetch metrics for up to 4 journals
    for q in body.queries[:4]:
        results[q] = await handlers.get_journal_metrics(query=q)
    return results
