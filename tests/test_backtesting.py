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


from recommendation_engine.backtesting import evaluate_overpriced_rule


def test_evaluate_overpriced_rule_against_seeded_events(temp_conn):
    results = evaluate_overpriced_rule(temp_conn)
    by_property = {r.property_id: r for r in results}
    assert set(by_property.keys()) == {1, 6}

    # Both seeded events reconstruct to the property's listing-day state (the
    # only prior price_history row available is the 'listed' event itself),
    # so days_on_market=0 at that point — well under the rule's >30 threshold.
    # The rule correctly does not fire for either; both are real misses
    # against what actually happened (a real price drop later on).
    p1 = by_property[1]
    assert p1.fired is False
    assert p1.suggested_reduction_pct is None
    assert p1.actual_reduction_pct == 4.59

    p6 = by_property[6]
    assert p6.fired is False
    assert p6.suggested_reduction_pct is None
    assert p6.actual_reduction_pct == 5.56


from recommendation_engine.backtesting import evaluate_underpriced_rule, format_report, run_backtest


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
