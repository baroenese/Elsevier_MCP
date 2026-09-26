"""Journal metrics and comparison routes."""

from typing import Any

from elsevier_mcp.handlers import ToolHandlers
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.dependencies import get_handlers

router = APIRouter(tags=["journals"])


class JournalCompareBody(BaseModel):
    """Journal compare request body."""

    queries: list[str]


@router.get("/journal-metrics")
async def get_metrics(
    query: str = Query(default=""),
    issn: str = Query(default=""),
    handlers: ToolHandlers = Depends(get_handlers),
) -> dict[str, Any]:
    """Retrieve CiteScore, SJR, SNIP, and quartile rankings for a journal."""
    q = query.strip()
    i = issn.strip()
    if not q and not i:
        return {"success": False, "error": "query or issn is required"}

    arguments: dict[str, Any] = {}
    if i:
        arguments["issn"] = i
    else:
        arguments["title"] = q
    return await handlers.get_journal_metrics(arguments)


@router.post("/journal-compare")
async def compare_journals(
    body: JournalCompareBody, handlers: ToolHandlers = Depends(get_handlers)
) -> dict[str, Any]:
    """Compare metrics for up to 4 journals side-by-side."""
    queries = [q.strip() for q in body.queries if q.strip()][:4]
    if not queries:
        return {"success": False, "error": "At least one query is required"}

    journals = []
    for q in queries:
        args = {"issn": q} if q.replace("-", "").isdigit() else {"title": q}
        result = await handlers.get_journal_metrics(args)
        journals.append({"query": q, **result})
    return {"success": True, "journals": journals}
