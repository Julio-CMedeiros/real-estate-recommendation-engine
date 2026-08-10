from sqlalchemy import text

from recommendation_engine.engine.indicators import compute_indicators


def _load_property(conn, property_id):
    return conn.execute(
        text("SELECT * FROM properties WHERE id = :id"), {"id": property_id}
    ).mappings().fetchone()


def test_price_vs_area_avg_matches_seeded_market_snapshot(temp_conn):
    prop = _load_property(temp_conn, 1)  # Chiado apartment, neighborhood_id=1
    indicators = compute_indicators(prop, temp_conn, requested=["price_vs_area_avg"])
    # price=520000, area_m2=85 -> 6117.65/m2; latest Chiado (2026-04) avg_price_m2=6180
    expected = round(((520000 / 85 - 6180) / 6180) * 100, 2)
    assert indicators["price_vs_area_avg"] == expected


def test_inventory_pressure_matches_seeded_market_snapshot(temp_conn):
    prop = _load_property(temp_conn, 4)  # Parque das Nações, neighborhood_id=4
    indicators = compute_indicators(prop, temp_conn, requested=["inventory_pressure"])
    # Latest Parque das Nações snapshot (2026-04): listings_count=79, sold_count=31
    assert indicators["inventory_pressure"] == round(79 / 31, 2)


def test_area_appreciation_6m_matches_seeded_history(temp_conn):
    prop = _load_property(temp_conn, 1)  # neighborhood_id=1 (Chiado)
    indicators = compute_indicators(prop, temp_conn, requested=["area_appreciation_6m"])
    # Chiado has 6 snapshots: latest (2026-04)=6180, oldest (2025-11)=5800
    expected = round(((6180 - 5800) / 5800) * 100, 2)
    assert indicators["area_appreciation_6m"] == expected


def test_price_reductions_count_matches_seeded_history(temp_conn):
    prop = _load_property(temp_conn, 1)  # property 1 has one 'price_change' event
    indicators = compute_indicators(prop, temp_conn, requested=["price_reductions_count"])
    assert indicators["price_reductions_count"] == 1


def test_price_vs_area_avg_as_of_none_matches_omitted(temp_conn):
    prop = _load_property(temp_conn, 1)
    with_none = compute_indicators(prop, temp_conn, requested=["price_vs_area_avg"], as_of=None)
    without = compute_indicators(prop, temp_conn, requested=["price_vs_area_avg"])
    assert with_none == without


def test_price_vs_area_avg_with_as_of_uses_historical_snapshot(temp_conn):
    prop = _load_property(temp_conn, 1)  # Chiado, neighborhood_id=1, price=520000, area_m2=85
    indicators = compute_indicators(
        prop, temp_conn, requested=["price_vs_area_avg"], as_of="2025-12-15"
    )
    # As of 2025-12-15, the latest matching Chiado snapshot is 2025-12 (avg_price_m2=5850) —
    # not the true-latest 2026-04 snapshot (6180) the no-as_of tests above use.
    expected = round(((520000 / 85 - 5850) / 5850) * 100, 2)
    assert indicators["price_vs_area_avg"] == expected


def test_area_appreciation_6m_with_as_of_uses_limited_window(temp_conn):
    prop = _load_property(temp_conn, 1)
    indicators = compute_indicators(
        prop, temp_conn, requested=["area_appreciation_6m"], as_of="2026-01-15"
    )
    # As of 2026-01-15, only the Nov/Dec/Jan Chiado snapshots exist (5800, 5850, 5920).
    expected = round(((5920 - 5800) / 5800) * 100, 2)
    assert indicators["area_appreciation_6m"] == expected


def test_similar_sold_last_30d_with_as_of_uses_historical_snapshot(temp_conn):
    prop = _load_property(temp_conn, 1)
    indicators = compute_indicators(
        prop, temp_conn, requested=["similar_sold_last_30d"], as_of="2025-12-15"
    )
    assert indicators["similar_sold_last_30d"] == 14  # 2025-12 Chiado sold_count


def test_days_on_market_with_as_of_is_deterministic(temp_conn):
    prop = _load_property(temp_conn, 1)  # listed_date = 2026-02-15
    indicators = compute_indicators(
        prop, temp_conn, requested=["days_on_market"], as_of="2026-03-20"
    )
    assert indicators["days_on_market"] == 33
