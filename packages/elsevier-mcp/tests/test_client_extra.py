"""Additional client tests: network-error retries, URL handling, env fallbacks, lifecycle."""

import httpx
import pytest
import respx

from elsevier_mcp.client import BASE_URL, DEFAULT_RATE_LIMIT, DEFAULT_TIMEOUT, ElsevierAPIClient
from elsevier_mcp.rate_limiter import TokenBucketRateLimiter


@pytest.fixture
def client() -> ElsevierAPIClient:
    """Fast isolated client with two retries."""
    return ElsevierAPIClient(rate_limiter=TokenBucketRateLimiter(rate=500.0, burst=500.0), timeout=5.0, max_retries=2)


@respx.mock
@pytest.mark.asyncio
async def test_retry_on_request_error_then_success(client: ElsevierAPIClient) -> None:
    """Network errors are retried and a later success is returned."""
    route = respx.get(f"{BASE_URL}/content/search/scopus")
    route.side_effect = [
        httpx.ConnectError("conn fail 1"),
        httpx.ConnectError("conn fail 2"),
        httpx.Response(200, json={"ok": True}),
    ]
    response = await client.get("/content/search/scopus")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert route.call_count == 3


@respx.mock
@pytest.mark.asyncio
async def test_request_error_raises_after_exhaustion(client: ElsevierAPIClient) -> None:
    """Persistent network errors raise the last httpx.RequestError after max retries."""
    route = respx.get(f"{BASE_URL}/content/search/scopus")
    route.side_effect = httpx.ConnectError("still down")
    with pytest.raises(httpx.ConnectError):
        await client.get("/content/search/scopus")
    assert route.call_count == client.max_retries + 1


@respx.mock
@pytest.mark.asyncio
async def test_absolute_url_bypasses_base_url(client: ElsevierAPIClient) -> None:
    """Absolute URLs are requested as-is instead of being joined with BASE_URL."""
    base_route = respx.get(f"{BASE_URL}/elsewhere")
    other_route = respx.get("https://example.com/api/x")
    other_route.return_value = httpx.Response(200, json={"via": "absolute"})

    response = await client.get("https://example.com/api/x")
    assert response.json() == {"via": "absolute"}
    assert other_route.call_count == 1
    assert base_route.call_count == 0


@respx.mock
@pytest.mark.asyncio
async def test_per_request_timeout_override(
    client: ElsevierAPIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A per-request timeout kwarg overrides the client default."""
    captured: list[float | None] = []

    async def fake_get(self: httpx.AsyncClient, url: str, **kwargs: object) -> httpx.Response:
        captured.append(kwargs.get("timeout"))  # type: ignore[arg-type]
        return httpx.Response(200, json={})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    await client.get("/content/search/scopus")
    assert captured == [client.timeout]

    await client.get("/content/search/scopus", timeout=2.5)
    assert captured[-1] == 2.5


def test_env_fallback_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    """ELSEVIER_RATE_LIMIT / ELSEVIER_TIMEOUT env vars configure the client."""
    monkeypatch.delenv("ELSEVIER_RATE_LIMIT", raising=False)
    monkeypatch.delenv("ELSEVIER_TIMEOUT", raising=False)
    default_client = ElsevierAPIClient()
    assert default_client.rate_limiter.rate == DEFAULT_RATE_LIMIT
    assert default_client.timeout == DEFAULT_TIMEOUT

    monkeypatch.setenv("ELSEVIER_RATE_LIMIT", "12.5")
    monkeypatch.setenv("ELSEVIER_TIMEOUT", "3.5")
    tuned_client = ElsevierAPIClient()
    assert tuned_client.rate_limiter.rate == 12.5
    assert tuned_client.timeout == 3.5


@pytest.mark.asyncio
async def test_context_manager_closes_session() -> None:
    """Async context manager owns and closes its underlying httpx session."""
    async with ElsevierAPIClient() as client:
        await client._get_client()
        assert client._client is not None
        assert not client._client.is_closed
    assert client._client is None

    # After close, the next request transparently re-creates a session.
    with respx.mock:
        respx.get(f"{BASE_URL}/ping").return_value = httpx.Response(200, json={})
        response = await client.get("/ping")
    assert response.status_code == 200
    await client.aclose()
