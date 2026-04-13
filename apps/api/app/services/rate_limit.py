"""
Minimal in-process rate limiter for sensitive endpoints.

Token-bucket-ish: each unique (key, window) gets a counter that resets
every window. If the counter exceeds the limit, the caller gets 429.

This is deliberately in-memory and per-process. It's the right shape for
single-instance production and for tests. Behind a load balancer you'd
promote this to Redis-backed (INCR + EXPIRE), which is on the Tier 5
Celery roadmap item — same API, swap the backing store.

Usage in a FastAPI router:

    from app.services.rate_limit import rate_limit

    @router.post("/login")
    def login(
        request: Request,
        _rl: None = Depends(rate_limit("login", per_minute=10)),
        ...
    ):
        ...

The dependency raises 429 automatically if the bucket is exhausted.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, status


# ── In-memory store ─────────────────────────────────────────────────────

_lock = threading.Lock()
# _buckets[(scope, client_id)] = (window_start_epoch, count)
_buckets: dict[tuple[str, str], tuple[float, int]] = defaultdict(
    lambda: (0.0, 0)
)


def _client_id(request: Request) -> str:
    """
    Build a stable-ish client identifier from the request.
    Uses X-Forwarded-For when present (reverse-proxy aware) and
    falls back to the client host.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Take the first IP in the chain (the actual client)
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _consume(scope: str, client: str, limit: int, window_seconds: int) -> bool:
    """Return True if the request should proceed, False if over limit."""
    now = time.time()
    key = (scope, client)
    with _lock:
        window_start, count = _buckets[key]
        if now - window_start > window_seconds:
            # New window
            _buckets[key] = (now, 1)
            return True
        if count >= limit:
            return False
        _buckets[key] = (window_start, count + 1)
        return True


def rate_limit(
    scope: str,
    *,
    per_minute: int,
) -> Callable:
    """
    Dependency factory. `scope` is a namespace so different endpoints
    get independent counters.
    """
    window_seconds = 60

    def dependency(request: Request) -> None:
        client = _client_id(request)
        if not _consume(scope, client, per_minute, window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Rate limit exceeded for {scope}: "
                    f"{per_minute} requests per minute. "
                    f"Please slow down and retry shortly."
                ),
                headers={"Retry-After": "60"},
            )

    return dependency


def reset() -> None:
    """Test helper — clear all buckets."""
    with _lock:
        _buckets.clear()
