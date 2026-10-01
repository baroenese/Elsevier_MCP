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
    start: int = 0
    sort: str | None = None


class AbstractBody(BaseModel):
    """Abstract request body."""

    eid: str | None = None
    doi: str | None = None


class InstitutionBody(BaseModel):
    """Institution request body."""

    institution: str
    year: int = 2024


class AuthorPapersBody(BaseModel):
    """Author papers request body."""

    author_id: str | None = None
    author_name: str | None = None
    affiliation: str | None = None
    year: str | int | None = None
    count: int = 10
    start: int = 0
    sort: str | None = None


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
        "start": max(0, min(body.start, 5999)),
    }
    if body.sort:
        arguments["sort"] = body.sort
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


@router.post("/author-papers")
async def search_author_papers(
    body: AuthorPapersBody, handlers: ToolHandlers = Depends(get_handlers)
) -> dict[str, Any]:
    """Search papers by Scopus author via the general search endpoint.

    Works with author_id (exact) or author_name plus an optional affiliation
    filter; the author-retrieval and SciVal endpoints are not entitled on all
    API keys, so this route never depends on them.
    """
    if not (body.author_id and body.author_id.strip()) and not (
        body.author_name and body.author_name.strip()
    ):
        return {"success": False, "error": "Either author_id or author_name must be provided"}
    arguments: dict[str, Any] = {
        "count": max(1, min(body.count, 25)),
        "start": max(0, min(body.start, 5999)),
    }
    if body.author_id and body.author_id.strip():
        arguments["author_id"] = body.author_id.strip()
    if body.author_name and body.author_name.strip():
        arguments["author_name"] = body.author_name.strip()
    if body.affiliation and body.affiliation.strip():
        arguments["affiliation"] = body.affiliation.strip()
    if body.year:
        arguments["year"] = str(body.year)
    if body.sort:
        arguments["sort"] = body.sort
    return await handlers.search_author_papers(arguments)
