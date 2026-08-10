import pytest
from fastapi import HTTPException

from api.auth import create_api_key
from api.deps import require_api_key


def test_require_api_key_accepts_valid_key(temp_conn):
    raw_key = create_api_key(temp_conn, "acme")
    assert require_api_key(x_api_key=raw_key, conn=temp_conn) == "acme"


def test_require_api_key_rejects_missing_key(temp_conn):
    with pytest.raises(HTTPException) as exc_info:
        require_api_key(x_api_key=None, conn=temp_conn)
    assert exc_info.value.status_code == 401


def test_require_api_key_rejects_invalid_key(temp_conn):
    with pytest.raises(HTTPException) as exc_info:
        require_api_key(x_api_key="bogus", conn=temp_conn)
    assert exc_info.value.status_code == 401


def test_require_api_key_rate_limits_after_capacity(temp_conn, monkeypatch):
    import api.deps as deps_module
    from api.rate_limit import TokenBucket

    monkeypatch.setattr(
        deps_module, "_rate_limiter", TokenBucket(capacity=1, refill_per_second=0.0, clock=lambda: 0.0)
    )
    raw_key = create_api_key(temp_conn, "acme")
    assert require_api_key(x_api_key=raw_key, conn=temp_conn) == "acme"
    with pytest.raises(HTTPException) as exc_info:
        require_api_key(x_api_key=raw_key, conn=temp_conn)
    assert exc_info.value.status_code == 429
