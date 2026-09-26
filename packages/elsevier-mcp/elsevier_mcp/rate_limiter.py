"""Token bucket rate limiter for controlling API request throughput."""

import asyncio
import time


class TokenBucketRateLimiter:
    """Asynchronous token bucket rate limiter.

    Attributes:
        rate: Rate at which tokens are replenished per second.
        burst: Maximum bucket capacity.
        tokens: Current available token count.
        last_refill: Timestamp of the last token replenishment.
    """

    def __init__(self, rate: float = 6.0, burst: float | None = None) -> None:
        """Initialize the rate limiter.

        Args:
            rate: Replenishment rate in tokens per second (must be > 0).
            burst: Maximum burst capacity. Defaults to max(rate, 1.0).

        Raises:
            ValueError: If rate or burst is less than or equal to 0.
        """
        if rate <= 0:
            raise ValueError("Rate must be greater than 0")
        self.rate = float(rate)
        self.burst = float(burst) if burst is not None else max(self.rate, 1.0)
        if self.burst <= 0:
            raise ValueError("Burst must be greater than 0")
        self.tokens = self.burst
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> None:
        """Acquire the specified number of tokens, waiting if necessary.

        Refill and consumption happen under the lock, but waiting happens
        outside it so concurrent waiters do not serialize behind each other.

        Args:
            tokens: Number of tokens to consume (must be > 0 and <= burst).

        Raises:
            ValueError: If requested tokens exceed bucket burst capacity or <= 0.
        """
        if tokens <= 0:
            raise ValueError("Requested tokens must be greater than 0")
        if tokens > self.burst:
            raise ValueError(f"Requested tokens ({tokens}) exceed burst capacity ({self.burst})")

        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                self.last_refill = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return
                wait_time = (tokens - self.tokens) / self.rate

            await asyncio.sleep(wait_time)
