from recommendation_engine.backtesting import (
    evaluate_overpriced_rule,
    evaluate_underpriced_rule,
    find_price_change_events,
    format_report,
    reconstruct_property_as_of,
    run_backtest,
    _run_rule,
)
from recommendation_engine.rules.pricing.r01_overpriced import OverpricedRule


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


def test_evaluate_overpriced_rule_against_seeded_events(temp_conn):
    results = evaluate_overpriced_rule(temp_conn)
    by_property = {r.property_id: r for r in results}
    assert set(by_property.keys()) == {1, 6}

    # Indicators are now evaluated as of eval_date (the day before the actual
    # price-change event), not the listing date. Property 1 (neighborhood 1,
    # which has market data) reconstructs to days_on_market=32 as of
    # 2026-03-19 — over the >30 threshold — but price_vs_area_avg is only
    # 5.11% (price/m2 545000/85=6411.76 vs area avg 6100 for 2026-03), under
    # the rule's >10% threshold, so it correctly does not fire: this is a
    # real miss, not an artifact of days_on_market=0.
    p1 = by_property[1]
    assert p1.eval_date == "2026-03-19"
    assert p1.fired is False
    assert p1.suggested_reduction_pct is None
    assert p1.actual_reduction_pct == 4.59
    assert p1.data_complete is True

    # Property 6 is in neighborhood 3 (Príncipe Real), which has no
    # market_snapshots rows at all — so price_vs_area_avg and
    # similar_sold_last_30d both fall back to their "no market data" defaults
    # (0.0 / 0) rather than a real measurement. data_complete=False flags
    # this as an unmeasurable event rather than a genuine "did not fire".
    p6 = by_property[6]
    assert p6.eval_date == "2026-02-14"
    assert p6.fired is False
    assert p6.suggested_reduction_pct is None
    assert p6.actual_reduction_pct == 5.56
    assert p6.data_complete is False


def test_run_rule_fired_path_extracts_suggested_reduction():
    snapshot = {
        "id": 99, "title": "Test", "type": "apartment", "price": 500000, "area_m2": 100,
        "bedrooms": 2, "bathrooms": 1, "energy_rating": "B", "listed_date": "2026-01-01",
        "status": "active",
    }
    indicators = {"price_vs_area_avg": 25, "days_on_market": 45, "similar_sold_last_30d": 18}
    fired, suggested = _run_rule(OverpricedRule(), snapshot, indicators)
    assert fired is True
    assert suggested == 15.0  # min(25 * 0.6, 15) == 15, capped


def test_run_rule_not_fired_returns_none_suggestion():
    snapshot = {
        "id": 99, "title": "Test", "type": "apartment", "price": 500000, "area_m2": 100,
        "bedrooms": 2, "bathrooms": 1, "energy_rating": "B", "listed_date": "2026-01-01",
        "status": "active",
    }
    indicators = {"price_vs_area_avg": 2, "days_on_market": 45, "similar_sold_last_30d": 18}
    fired, suggested = _run_rule(OverpricedRule(), snapshot, indicators)
    assert fired is False
    assert suggested is None


def test_evaluate_underpriced_rule_returns_not_backtestable_note():
    note = evaluate_underpriced_rule(None)
    assert "not yet backtestable" in note.lower()


def test_run_backtest_includes_both_rule_codes(temp_conn):
    results = run_backtest(temp_conn)
    assert set(results.keys()) == {"T01R01", "T01R02"}
    assert isinstance(results["T01R01"], list)
    assert isinstance(results["T01R02"], str)


def test_format_report_includes_both_codes_and_sample_size_caveat(temp_conn):
    results = run_backtest(temp_conn)
    report = format_report(results)
    assert "T01R01" in report
    assert "T01R02" in report
    assert "sample" in report.lower()
