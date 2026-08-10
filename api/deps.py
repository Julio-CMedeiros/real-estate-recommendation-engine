"""FastAPI dependencies: DB connection, API key auth, rate limiting."""

import sqlite3
from collections.abc import Iterator

from fastapi import Depends, Header, HTTPException

from recommendation_engine.database import get_connection

from .auth import verify_api_key
from .rate_limit import TokenBucket

_rate_limiter = TokenBucket(capacity=60, refill_per_second=1.0)


def get_db() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def require_api_key(
    x_api_key: str | None = Header(default=None),
    conn: sqlite3.Connection = Depends(get_db),
) -> str:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="missing API key")
    consumer = verify_api_key(conn, x_api_key)
    if not consumer:
        raise HTTPException(status_code=401, detail="invalid or revoked API key")
    if not _rate_limiter.allow(consumer):
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    return consumer
