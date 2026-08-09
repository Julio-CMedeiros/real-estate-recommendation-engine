"""In-memory per-key token bucket rate limiter.

Single-process only — sufficient for a single-instance local deployment.
Move to a shared store (e.g. Redis) if this ever runs multiple instances.
"""

import time
from collections.abc import Callable


class TokenBucket:
    def __init__(
        self,
        capacity: int,
        refill_per_second: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self._clock = clock
        self._buckets: dict[str, tuple[float, float]] = {}

    def allow(self, key: str) -> bool:
        now = self._clock()
        tokens, last = self._buckets.get(key, (float(self.capacity), now))
        tokens = min(self.capacity, tokens + (now - last) * self.refill_per_second)
        if tokens < 1:
            self._buckets[key] = (tokens, now)
            return False
        self._buckets[key] = (tokens - 1, now)
        return True
