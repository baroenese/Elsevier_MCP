"""Tests for TokenBucketRateLimiter."""

import asyncio
import time

import pytest

from elsevier_mcp.rate_limiter import TokenBucketRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_init_validation() -> None:
    """Validate argument constraints during initialization."""
    with pytest.raises(ValueError, match="Rate must be greater than 0"):
        TokenBucketRateLimiter(rate=0)

    with pytest.raises(ValueError, match="Burst must be greater than 0"):
        TokenBucketRateLimiter(rate=5.0, burst=0)


@pytest.mark.asyncio
async def test_rate_limiter_acquire_validation() -> None:
    """Validate argument constraints during acquire()."""
    limiter = TokenBucketRateLimiter(rate=5.0, burst=5.0)

    with pytest.raises(ValueError, match="Requested tokens must be greater than 0"):
        await limiter.acquire(0)

    with pytest.raises(ValueError, match="exceed burst capacity"):
        await limiter.acquire(10.0)


@pytest.mark.asyncio
async def test_rate_limiter_burst_consumption() -> None:
    """Verify burst tokens are immediately available without delay."""
    limiter = TokenBucketRateLimiter(rate=10.0, burst=5.0)
    start = time.monotonic()

    # Consuming available tokens up to burst should be near-instantaneous
    for _ in range(5):
        await limiter.acquire(1.0)

    duration = time.monotonic() - start
    assert duration < 0.1
    assert limiter.tokens == pytest.approx(0.0, abs=0.05)


@pytest.mark.asyncio
async def test_rate_limiter_waits_when_exhausted() -> None:
    """Verify acquiring when bucket is empty causes appropriate wait time."""
    # 10 tokens/sec -> 1 token takes 0.1s
    limiter = TokenBucketRateLimiter(rate=10.0, burst=1.0)
    await limiter.acquire(1.0)  # Consume the burst

    start = time.monotonic()
    await limiter.acquire(1.0)  # Must wait for refill (~0.1s)
    duration = time.monotonic() - start

    assert duration >= 0.08
