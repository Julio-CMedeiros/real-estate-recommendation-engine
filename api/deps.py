"""FastAPI dependencies: DB connection, API key auth, rate limiting."""

from collections.abc import Iterator

from fastapi import Depends, Header, HTTPException
from sqlalchemy.engine import Connection

from recommendation_engine.database import get_engine

from .auth import verify_api_key
from .rate_limit import TokenBucket

_engine = get_engine()
_rate_limiter = TokenBucket(capacity=60, refill_per_second=1.0)


def get_db() -> Iterator[Connection]:
    with _engine.connect() as conn:
        yield conn


def require_api_key(
    x_api_key: str | None = Header(default=None),
    conn: Connection = Depends(get_db),
) -> str:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="missing API key")
    consumer = verify_api_key(conn, x_api_key)
    if not consumer:
        raise HTTPException(status_code=401, detail="invalid or revoked API key")
    if not _rate_limiter.allow(consumer):
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    return consumer
