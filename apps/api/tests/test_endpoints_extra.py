"""Additional endpoint tests: trends clamping, journal-compare rules, config errors, DI caching."""

import httpx
import pytest

from app.dependencies import get_handlers
from app.main import app
from tests.test_endpoints import MockToolHandlers


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
async def test_trends_year_clamping(
    client: httpx.AsyncClient, mock_handlers: MockToolHandlers
):
    """Out-of-range years are clamped to 1970..2026 and capped at 10 years."""
    response = await client.post(
        "/api/trends", json={"field": "AI", "start_year": 1900, "end_year": 2100}
    )
    assert response.status_code == 200
    years = mock_handlers.last_trends_args["years"]
    assert years == list(range(1970, 1980))  # clamped low bound, first 10 years


@pytest.mark.asyncio
async def test_trends_sorts_swapped_years(
    client: httpx.AsyncClient, mock_handlers: MockToolHandlers
):
    """start_year > end_year is sorted before building the range."""
    response = await client.post(
        "/api/trends", json={"field": "AI", "start_year": 2024, "end_year": 2020}
    )
    assert response.status_code == 200
    assert mock_handlers.last_trends_args["years"] == [2020, 2021, 2022, 2023, 2024]


@pytest.mark.asyncio
async def test_journal_compare_truncates_to_four(
    client: httpx.AsyncClient, mock_handlers: MockToolHandlers
):
    """More than 4 queries are truncated to the first 4."""
    response = await client.post(
        "/api/journal-compare",
        json={"queries": ["Nature", "Science", "Cell", "Lancet", "BMJ", "JAMA"]},
    )
    assert response.status_code == 200
    journals = response.json()["journals"]
    assert [j["query"] for j in journals] == ["Nature", "Science", "Cell", "Lancet"]


@pytest.mark.asyncio
async def test_journal_compare_issn_heuristic(
    client: httpx.AsyncClient, mock_handlers: MockToolHandlers
):
    """Digit-only queries (with dashes) are routed as ISSN, others as title."""
    await client.post(
        "/api/journal-compare",
        json={"queries": ["0028-0836", "Nature"]},
    )
    issued_queries = []
    for call_args in mock_handlers.journal_arg_history:
        issued_queries.append("issn" if "issn" in call_args else "title")
    assert issued_queries == ["issn", "title"]


@pytest.mark.asyncio
async def test_config_post_os_error_path(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    """A filesystem failure during config save returns success=False, not a 500."""

    def raise_oserror(api_key: str | None, insttoken: str | None) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("app.routers.health._save_config", raise_oserror)
    response = await client.post("/api/config", json={"api_key": "k123"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "Could not write config" in body["error"]


def test_get_handlers_is_cached() -> None:
    """get_handlers() returns the same singleton instance (lru_cache)."""
    get_handlers.cache_clear()
    assert get_handlers() is get_handlers()
    get_handlers.cache_clear()
