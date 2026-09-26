"""Papers search, abstract, and institution routes."""

from typing import Any

from elsevier_mcp.handlers import ToolHandlers
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import get_handlers

router = APIRouter(tags=["papers"])


class SearchBody(BaseModel):
    """Search request body."""

    query: str
    author: str | None = None
    year: str | int | None = None
    open_access: bool = False
    count: int = 10


class AbstractBody(BaseModel):
    """Abstract request body."""

    eid: str | None = None
    doi: str | None = None


class InstitutionBody(BaseModel):
    """Institution request body."""

    institution: str
    year: int = 2024


def _compose_search_query(body: SearchBody) -> str:
    """Build Scopus query with optional author and open access clauses."""
    clauses = [f"TITLE-ABS-KEY({body.query.strip()})"]
    if body.author and body.author.strip():
        clauses.append(f'AUTHOR-NAME("{body.author.strip()}")')
    if body.year:
        clauses.append(f"PUBYEAR = {body.year}")
    if body.open_access:
        clauses.append("OPENACCESS(1)")
    return " AND ".join(clauses)


@router.post("/search")
async def search_papers(
    body: SearchBody, handlers: ToolHandlers = Depends(get_handlers)
) -> dict[str, Any]:
    """Search for papers using Scopus query syntax."""
    if not body.query.strip():
        return {"success": False, "error": "Query is required"}
    query = _compose_search_query(body)
    arguments: dict[str, Any] = {
        "query": query,
        "count": max(1, min(body.count, 25)),
    }
    return await handlers.search_papers(arguments)


@router.post("/abstract")
async def get_abstract(
    body: AbstractBody, handlers: ToolHandlers = Depends(get_handlers)
) -> dict[str, Any]:
    """Get paper abstract by EID or DOI."""
    arguments: dict[str, Any] = {}
    if body.eid and body.eid.strip():
        arguments["eid"] = body.eid.strip()
    if body.doi and body.doi.strip():
        arguments["doi"] = body.doi.strip()
    if not arguments:
        return {"success": False, "error": "Either eid or doi must be provided"}
    return await handlers.get_paper_abstract(arguments)


@router.post("/institution")
async def get_institution(
    body: InstitutionBody, handlers: ToolHandlers = Depends(get_handlers)
) -> dict[str, Any]:
    """Get publication statistics for an academic institution."""
    if not body.institution.strip():
        return {"success": False, "error": "Institution name is required"}
    return await handlers.get_institution_papers(
        {"institution": body.institution.strip(), "year": body.year}
    )
