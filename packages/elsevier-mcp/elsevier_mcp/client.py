"""Async HTTP client for Elsevier APIs with rate limiting and exponential backoff retry."""

import asyncio
import logging
import os
import random
from typing import Any

import httpx

from elsevier_mcp.rate_limiter import TokenBucketRateLimiter

logger = logging.getLogger("elsevier_mcp.client")

BASE_URL = "https://api.elsevier.com"
DEFAULT_RATE_LIMIT = 6.0
DEFAULT_TIMEOUT = 15.0
DEFAULT_MAX_RETRIES = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def get_headers() -> dict[str, str]:
    """Return Elsevier API request headers or raise a clear configuration error.

    Returns:
        Dictionary of HTTP headers including X-ELS-APIKey and Accept.

    Raises:
        RuntimeError: If ELSEVIER_API_KEY environment variable is not set.
    """
    api_key = os.getenv("ELSEVIER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ELSEVIER_API_KEY environment variable is not set. "
            "Set it before calling Elsevier tools."
        )
    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}
    inst_token = os.getenv("ELSEVIER_INSTTOKEN")
    if inst_token:
        headers["X-ELS-Insttoken"] = inst_token
    return headers


class ElsevierAPIClient:
    """Asynchronous HTTP client managing connection pooling, rate limiting, and retries.

    Attributes:
        base_url: Base URL for Elsevier REST endpoints.
        rate_limiter: Token bucket rate limiter instance.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts for transient errors.
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        rate_limiter: TokenBucketRateLimiter | None = None,
        timeout: float | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the Elsevier API client.

        Args:
            base_url: Base endpoint URL.
            rate_limiter: Rate limiter to enforce request rate limits.
            timeout: Request timeout duration in seconds.
            max_retries: Maximum retry attempts for 429/5xx responses.
            client: Optional externally managed httpx.AsyncClient instance.
        """
        self.base_url = base_url.rstrip("/")

        if rate_limiter is None:
            rate_limit_env = os.getenv("ELSEVIER_RATE_LIMIT")
            rate = float(rate_limit_env) if rate_limit_env else DEFAULT_RATE_LIMIT
            self.rate_limiter = TokenBucketRateLimiter(rate=rate)
        else:
            self.rate_limiter = rate_limiter

        if timeout is None:
            timeout_env = os.getenv("ELSEVIER_TIMEOUT")
            self.timeout = float(timeout_env) if timeout_env else DEFAULT_TIMEOUT
        else:
            self.timeout = float(timeout)

        self.max_retries = max_retries
        self._client = client
        self._owns_client = client is None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or initialize the underlying httpx AsyncClient."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
            self._owns_client = True
        return self._client

    async def get(
        self,
        path_or_url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Send an asynchronous GET request with rate limiting and exponential backoff retry.

        Args:
            path_or_url: Relative endpoint path or absolute URL.
            params: Query parameters dictionary.
            headers: Optional HTTP headers (defaults to get_headers()).
            timeout: Optional per-request timeout override.

        Returns:
            httpx.Response object from the server.

        Raises:
            RuntimeError: If required environment variables are not set.
            httpx.RequestError: If network error persists after max retries.
        """
        req_headers = headers if headers is not None else get_headers()
        url = path_or_url if path_or_url.startswith("http") else f"{self.base_url}/{path_or_url.lstrip('/')}"
        req_timeout = timeout if timeout is not None else self.timeout

        client = await self._get_client()
        last_exception: Exception | None = None
        last_response: httpx.Response | None = None

        for attempt in range(self.max_retries + 1):
            await self.rate_limiter.acquire()

            try:
                logger.debug(
                    "GET %s (attempt %d/%d) params=%s",
                    url, attempt + 1, self.max_retries + 1, params
                )
                response = await client.get(url, headers=req_headers, params=params, timeout=req_timeout)

                if response.status_code not in RETRYABLE_STATUS_CODES:
                    return response

                last_response = response
                logger.warning(
                    "Received HTTP %d for %s (attempt %d/%d)",
                    response.status_code, url, attempt + 1, self.max_retries + 1
                )

            except httpx.RequestError as exc:
                last_exception = exc
                logger.warning(
                    "Request error for %s (attempt %d/%d): %s",
                    url, attempt + 1, self.max_retries + 1, exc
                )

            if attempt < self.max_retries:
                retry_after_delay = None
                if last_response is not None and last_response.status_code == 429:
                    retry_header = last_response.headers.get("Retry-After")
                    if retry_header:
                        try:
                            retry_after_delay = float(retry_header)
                        except (ValueError, TypeError):
                            pass

                if retry_after_delay is not None:
                    delay = retry_after_delay
                else:
                    delay = (2 ** attempt) * 0.5 + random.uniform(0.0, 0.5)

                logger.info("Backing off for %.2f seconds before retrying...", delay)
                await asyncio.sleep(delay)

        if last_response is not None:
            return last_response
        if last_exception is not None:
            raise last_exception

        raise RuntimeError(f"Request failed after {self.max_retries + 1} attempts")

    async def aclose(self) -> None:
        """Close the underlying HTTP client session."""
        if self._client is not None and self._owns_client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "ElsevierAPIClient":
        """Enter async context manager."""
        await self._get_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        await self.aclose()
