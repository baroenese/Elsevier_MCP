"""Papers search and info routes."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from elsevier_mcp.handlers import ToolHandlers
from app.dependencies import get_handlers

router = APIRouter(tags=["papers"])

class SearchBody(BaseModel):
    """Search request body."""
    query: str
    author: str | None = None
    year: int | None = None
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
    clauses = [f"TITLE-ABS-KEY({body.query})"]
    if body.author:
        clauses.append(f"AUTHOR-NAME({body.author})")
    if body.year:
        clauses.append(f"PUBYEAR IS {body.year}")
    if body.open_access:
        clauses.append("OPENACCESS(1)")
    return " AND ".join(clauses)

@router.post("/search")
async def search_papers(body: SearchBody, handlers: ToolHandlers = Depends(get_handlers)):
    """Search for papers."""
    query = _compose_search_query(body)
    return await handlers.search_papers(query=query, count=body.count)

@router.post("/abstract")
async def get_abstract(body: AbstractBody, handlers: ToolHandlers = Depends(get_handlers)):
    """Get paper abstract."""
    return await handlers.get_paper_abstract(eid=body.eid, doi=body.doi)

@router.post("/institution")
async def get_institution(body: InstitutionBody, handlers: ToolHandlers = Depends(get_handlers)):
    """Get institution papers."""
    return await handlers.get_institution_papers(institution=body.institution, year=body.year)
