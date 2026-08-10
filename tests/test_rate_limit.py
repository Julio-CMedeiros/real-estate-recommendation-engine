from api.rate_limit import TokenBucket


def test_allows_up_to_capacity_then_blocks():
    bucket = TokenBucket(capacity=3, refill_per_second=0.0, clock=lambda: 0.0)
    assert bucket.allow("k") is True
    assert bucket.allow("k") is True
    assert bucket.allow("k") is True
    assert bucket.allow("k") is False


def test_refills_over_time():
    tick = {"t": 0.0}
    bucket = TokenBucket(capacity=1, refill_per_second=1.0, clock=lambda: tick["t"])
    assert bucket.allow("k") is True
    assert bucket.allow("k") is False
    tick["t"] = 1.0
    assert bucket.allow("k") is True


def test_keys_are_independent():
    bucket = TokenBucket(capacity=1, refill_per_second=0.0, clock=lambda: 0.0)
    assert bucket.allow("a") is True
    assert bucket.allow("b") is True
    assert bucket.allow("a") is False
