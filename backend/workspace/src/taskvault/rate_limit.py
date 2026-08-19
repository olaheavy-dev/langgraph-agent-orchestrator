"""Per-key token bucket.

The limit exists because of the 2026-03-14 incident; the numbers are not
arbitrary and the reasoning is in adr-003-rate-limiting. Change them there first.
"""

import time
from dataclasses import dataclass, field

CAPACITY = 100
REFILL_SECONDS = 60.0


@dataclass
class Bucket:
    tokens: float = CAPACITY
    last_refill: float = field(default_factory=time.monotonic)

    def _refill(self, now: float) -> None:
        elapsed = now - self.last_refill
        self.tokens = min(CAPACITY, self.tokens + elapsed * (CAPACITY / REFILL_SECONDS))
        self.last_refill = now


class RateLimiter:
    """Buckets live in process memory, which is correct only for a single
    instance. adr-003-rate-limiting records what has to change before a second
    one is deployed.
    """

    def __init__(self) -> None:
        self._buckets: dict[str, Bucket] = {}

    def allow(self, key: str) -> bool:
        bucket = self._buckets.setdefault(key, Bucket())
        bucket._refill(time.monotonic())
        bucket.tokens -= 1
        return bucket.tokens >= -1
