from sqlalchemy import text

from recommendation_engine.backtesting import find_price_change_events, reconstruct_property_as_of


def test_find_price_change_events_returns_seeded_events(temp_conn):
    events = find_price_change_events(temp_conn)
    by_property = {e["property_id"]: e for e in events}
    assert set(by_property.keys()) == {1, 6}

    p1 = by_property[1]
    assert p1["as_of"] == "2026-02-15"
    assert p1["old_price"] == 545000
    assert p1["new_price"] == 520000
    assert p1["event_date"] == "2026-03-20"

    p6 = by_property[6]
    assert p6["as_of"] == "2025-12-05"
    assert p6["old_price"] == 720000
    assert p6["new_price"] == 680000
    assert p6["event_date"] == "2026-02-15"


def test_find_price_change_events_excludes_properties_without_a_prior_row(temp_conn):
    # Property 2 only has a 'listed' row, no 'price_change' — must not appear.
    events = find_price_change_events(temp_conn)
    assert all(e["property_id"] != 2 for e in events)


def test_reconstruct_property_as_of_overrides_price_only(temp_conn):
    snapshot = reconstruct_property_as_of(temp_conn, property_id=1, as_of="2026-02-15", price=545000)
    assert snapshot["price"] == 545000
    assert snapshot["id"] == 1
    assert snapshot["area_m2"] == 85  # unchanged from the current row
    assert snapshot["neighborhood_id"] == 1
