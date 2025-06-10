"""Simple in-memory rate limiting utilities.

This module implements a rudimentary token bucket rate limiter. It is used to
protect write-heavy routes such as acknowledgements from abuse. In a real
deployment you would use Redis or another external store to coordinate state
between processes.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Dict

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_active_user
from app.db.models import User


@dataclass
class TokenBucket:
    capacity: int
    refill_rate: float  # tokens per second
    tokens: float = field(default=0.0)
    last_checked: float = field(default_factory=time.time)

    def consume(self, amount: int = 1) -> bool:
        now = time.time()
        # Refill based on time elapsed
        elapsed = now - self.last_checked
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_checked = now
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


class RateLimiter:
    """Thread-safe in-memory token bucket rate limiter."""

    def __init__(self, capacity: int = 5, refill_rate: float = 1.0) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: Dict[str, TokenBucket] = {}
        self.lock = threading.Lock()

    def allow(self, key: str, amount: int = 1) -> bool:
        with self.lock:
            bucket = self.buckets.get(key)
            if bucket is None:
                bucket = TokenBucket(capacity=self.capacity, refill_rate=self.refill_rate, tokens=self.capacity)
                self.buckets[key] = bucket
            return bucket.consume(amount)


# Create a singleton rate limiter; settings could be configured via env
rate_limiter = RateLimiter(capacity=10, refill_rate=0.2)  # 10 tokens max, 0.2 tokens per second (~3/min)


async def enforce_rate_limit(current_user: User = Depends(get_current_active_user)) -> None:
    """FastAPI dependency to enforce a per-user rate limit."""

    key = f"{current_user.id}"
    if not rate_limiter.allow(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait a moment and try again.",
        )