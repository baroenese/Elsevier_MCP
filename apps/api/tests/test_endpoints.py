"""Comprehensive endpoint test suite for FastAPI backend routes."""

from typing import Any
import pytest
import httpx
from app.main import app
from app.dependencies import get_handlers


class MockToolHandlers:
    """Mock ToolHandlers for testing FastAPI endpoints without calling live APIs."""

    def __init__(self) -> None:
        self.last_search_args: dict[str, Any] | None = None
        self.last_abstract_args: dict[str, Any] | None = None
        self.last_institution_args: dict[str, Any] | None = None
        self.last_trends_args: dict[str, Any] | None = None
        self.last_journal_args: dict[str, Any] | None = None

    async def search_papers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        self.last_search_args = arguments
        return {
            "success": True,
            "total_results": 1,
            "papers": [
                {
                    "title": "Deep Learning for Healthcare",
                    "authors": "Hinton, G.",
                    "journal": "Nature",
                    "year": "2024",
                    "citations": 100,
                    "doi": "10.1038/s41586-024-00001",
                    "eid": "2-s2.0-85000000001",
                }
            ],
            "query": arguments.get("query", ""),
        }

    async def get_paper_abstract(self, arguments: dict[str, Any]) -> dict[str, Any]:
        self.last_abstract_args = arguments
        return {
            "success": True,
            "paper": {
                "title": "Deep Learning for Healthcare",
                "abstract": "A comprehensive study on medical applications.",
                "authors": "Hinton, G.",
                "journal": "Nature",
                "year": "2024",
                "doi": arguments.get("doi", "10.1038/test"),
                "eid": arguments.get("eid", "2-s2.0-test"),
                "citations": "100",
            },
        }

    async def get_institution_papers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        self.last_institution_args = arguments
        return {
            "success": True,
            "institution": arguments.get("institution", ""),
            "year": arguments.get("year", 2024),
            "total_papers": 500,
            "top_papers": [],
        }

    async def analyze_research_trends(self, arguments: dict[str, Any]) -> dict[str, Any]:
        self.last_trends_args = arguments
        return {
            "success": True,
            "field": arguments.get("field", ""),
            "yearly_papers": {2022: 100, 2023: 150, 2024: 200},
            "growth_rates": {"2022-2023": 50.0, "2023-2024": 33.33},
            "total_papers": 450,
        }

    async def get_journal_metrics(self, arguments: dict[str, Any]) -> dict[str, Any]:
        self.last_journal_args = arguments
        title = arguments.get("title") or "Nature"
        return {
            "success": True,
            "journal": {
                "title": title,
                "publisher": "Springer Nature",
                "issn": "0028-0836",
                "eissn": "1476-4687",
                "aggregation_type": "Journal",
                "open_access": False,
                "citescore": {"current": 60.5, "year": "2023", "tracker": 62.1, "tracker_year": "2024"},
                "sjr": {"value": 15.2, "year": "2023"},
                "snip": {"value": 11.4, "year": "2023"},
                "best_quartile": "Q1",
                "subject_rankings": [
                    {"subject_code": "1000", "rank": 1, "percentile": 99.0, "quartile": "Q1"}
                ],
            },
        }


@pytest.fixture
def mock_handlers() -> MockToolHandlers:
    handlers = MockToolHandlers()
    app.dependency_overrides[get_handlers] = lambda: handlers
    yield handlers
    app.dependency_overrides.clear()


@pytest.fixture
async def client() -> httpx.AsyncClient:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client: httpx.AsyncClient):
    res = await client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["version"] == "2.0.0"
    assert "api_key_set" in data
    assert "config_file" in data


@pytest.mark.asyncio
async def test_tools_endpoint(client: httpx.AsyncClient):
    res = await client.get("/api/tools")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert isinstance(data["tools"], list)
    tool_names = [t["name"] for t in data["tools"]]
    assert "search_papers" in tool_names
    assert "get_journal_metrics" in tool_names
    assert "analyze_research_trends" in tool_names


@pytest.mark.asyncio
async def test_config_endpoint(client: httpx.AsyncClient):
    res = await client.post("/api/config", json={"api_key": "test_key_123", "insttoken": "inst_123"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["api_key_set"] is True


@pytest.mark.asyncio
async def test_search_papers_success(client: httpx.AsyncClient, mock_handlers: MockToolHandlers):
    payload = {
        "query": "quantum computing",
        "author": "Preskill",
        "year": "2024",
        "open_access": True,
        "count": 15,
    }
    res = await client.post("/api/search", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["papers"]) == 1
    assert "Preskill" in mock_handlers.last_search_args["query"]
    assert "OPENACCESS(1)" in mock_handlers.last_search_args["query"]
    assert mock_handlers.last_search_args["count"] == 15


@pytest.mark.asyncio
async def test_search_papers_empty_query_error(client: httpx.AsyncClient):
    res = await client.post("/api/search", json={"query": "   "})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert "Query is required" in data["error"]


@pytest.mark.asyncio
async def test_abstract_by_eid(client: httpx.AsyncClient, mock_handlers: MockToolHandlers):
    res = await client.post("/api/abstract", json={"eid": "2-s2.0-85000000001"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["paper"]["eid"] == "2-s2.0-85000000001"
    assert mock_handlers.last_abstract_args["eid"] == "2-s2.0-85000000001"


@pytest.mark.asyncio
async def test_abstract_by_doi(client: httpx.AsyncClient, mock_handlers: MockToolHandlers):
    res = await client.post("/api/abstract", json={"doi": "10.1038/s41586-024-00001"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["paper"]["doi"] == "10.1038/s41586-024-00001"


@pytest.mark.asyncio
async def test_abstract_neither_eid_nor_doi_error(client: httpx.AsyncClient):
    res = await client.post("/api/abstract", json={"eid": "", "doi": ""})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert "Either eid or doi" in data["error"]


@pytest.mark.asyncio
async def test_institution_papers_success(client: httpx.AsyncClient, mock_handlers: MockToolHandlers):
    res = await client.post("/api/institution", json={"institution": "MIT", "year": 2024})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["institution"] == "MIT"
    assert mock_handlers.last_institution_args["institution"] == "MIT"


@pytest.mark.asyncio
async def test_institution_papers_empty_error(client: httpx.AsyncClient):
    res = await client.post("/api/institution", json={"institution": "  "})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_trends_success(client: httpx.AsyncClient, mock_handlers: MockToolHandlers):
    res = await client.post("/api/trends", json={"field": "deep learning", "start_year": 2022, "end_year": 2024})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["total_papers"] == 450
    assert mock_handlers.last_trends_args["years"] == [2022, 2023, 2024]


@pytest.mark.asyncio
async def test_trends_empty_field_error(client: httpx.AsyncClient):
    res = await client.post("/api/trends", json={"field": "  "})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert "Field is required" in data["error"]


@pytest.mark.asyncio
async def test_journal_metrics_by_title(client: httpx.AsyncClient, mock_handlers: MockToolHandlers):
    res = await client.get("/api/journal-metrics?query=Nature")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["journal"]["title"] == "Nature"
    assert mock_handlers.last_journal_args["title"] == "Nature"


@pytest.mark.asyncio
async def test_journal_metrics_by_issn(client: httpx.AsyncClient, mock_handlers: MockToolHandlers):
    res = await client.get("/api/journal-metrics?issn=0028-0836")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert mock_handlers.last_journal_args["issn"] == "0028-0836"


@pytest.mark.asyncio
async def test_journal_metrics_missing_param_error(client: httpx.AsyncClient):
    res = await client.get("/api/journal-metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert "query or issn is required" in data["error"]


@pytest.mark.asyncio
async def test_journal_compare_success(client: httpx.AsyncClient):
    res = await client.post("/api/journal-compare", json={"queries": ["Nature", "Science"]})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["journals"]) == 2
    assert data["journals"][0]["query"] == "Nature"
    assert data["journals"][1]["query"] == "Science"


@pytest.mark.asyncio
async def test_journal_compare_empty_queries_error(client: httpx.AsyncClient):
    res = await client.post("/api/journal-compare", json={"queries": []})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert "At least one query" in data["error"]
