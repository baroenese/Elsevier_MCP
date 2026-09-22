"""Tests for ElsevierAPIClient and headers resolution."""

import os
import httpx
import pytest
import respx

from elsevier_mcp.client import BASE_URL, ElsevierAPIClient, get_headers
from elsevier_mcp.rate_limiter import TokenBucketRateLimiter


def test_get_headers_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify headers include API key and optional institution token."""
    monkeypatch.setenv("ELSEVIER_API_KEY", "test-key-abc")
    monkeypatch.setenv("ELSEVIER_INSTTOKEN", "test-token-xyz")

    headers = get_headers()
    assert headers["X-ELS-APIKey"] == "test-key-abc"
    assert headers["Accept"] == "application/json"
    assert headers["X-ELS-Insttoken"] == "test-token-xyz"


def test_get_headers_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify missing API key raises RuntimeError."""
    monkeypatch.delenv("ELSEVIER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ELSEVIER_API_KEY"):
        get_headers()


@pytest.mark.asyncio
@respx.mock
async def test_client_get_success(api_client: ElsevierAPIClient) -> None:
    """Verify successful GET request without retries."""
    route = respx.get(f"{BASE_URL}/content/search/scopus").respond(
        status_code=200, json={"test": "ok"}
    )

    resp = await api_client.get("/content/search/scopus", params={"query": "test"})
    assert resp.status_code == 200
    assert resp.json() == {"test": "ok"}
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_client_retry_on_429(api_client: ElsevierAPIClient) -> None:
    """Verify retry behavior and Retry-After handling on HTTP 429."""
    route = respx.get(f"{BASE_URL}/test-429")
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "0.01"}),
        httpx.Response(200, json={"status": "recovered"}),
    ]

    resp = await api_client.get("/test-429")
    assert resp.status_code == 200
    assert resp.json() == {"status": "recovered"}
    assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_client_retry_on_503(api_client: ElsevierAPIClient) -> None:
    """Verify retry behavior on server errors (HTTP 503)."""
    route = respx.get(f"{BASE_URL}/test-503")
    route.side_effect = [
        httpx.Response(503),
        httpx.Response(200, json={"status": "ok"}),
    ]

    resp = await api_client.get("/test-503")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_client_no_retry_on_404(api_client: ElsevierAPIClient) -> None:
    """Verify client does not retry client error statuses like 404."""
    route = respx.get(f"{BASE_URL}/test-404").respond(status_code=404)

    resp = await api_client.get("/test-404")
    assert resp.status_code == 404
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_client_exhausts_retries() -> None:
    """Verify client returns last response once retry limit is reached."""
    route = respx.get(f"{BASE_URL}/test-fail").respond(status_code=500)
    limiter = TokenBucketRateLimiter(rate=500.0, burst=500.0)

    async with ElsevierAPIClient(rate_limiter=limiter, max_retries=2) as client:
        resp = await client.get("/test-fail")
        assert resp.status_code == 500
        assert route.call_count == 3  # 1 initial + 2 retries
