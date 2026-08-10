"""Backtest recommendation rules against real historical outcomes.

Only rules whose predictions map to something the schema actually records
can be backtested. `OverpricedRule` predicts a price should drop, and
`price_history` records real price changes — so it gets a real evaluator.
`UnderpricedOpportunityRule` predicts a quick sale, which nothing in the
schema observes (no sale date, `properties.status` never changes) — it gets
an explicit "not yet backtestable" note instead of a fabricated metric.

Indicator as_of-awareness: only `price_vs_area_avg`, `days_on_market`,
`area_appreciation_6m`, and `similar_sold_last_30d` actually respect the
`as_of` parameter passed into `compute_indicators`. Every other indicator in
`recommendation_engine/engine/indicators.py` ignores `as_of` and always
returns a present-day value. A rule can only be safely backtested today if
its `required_indicators` is a subset of those four — adding a rule that
requires any other indicator to a future evaluator here would silently leak
future data into a "historical" verdict.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Connection

from recommendation_engine.engine.indicators import compute_indicators
from recommendation_engine.models import Property
from recommendation_engine.rules.pricing.r01_overpriced import OverpricedRule


def find_price_change_events(conn: Connection) -> list[dict]:
    """Find every price_change event that has a prior price_history row to
    reconstruct the property's state just before the change."""
    events = conn.execute(
        text(
            "SELECT property_id, price, changed_date FROM price_history "
            "WHERE event = 'price_change' ORDER BY property_id, changed_date"
        )
    ).mappings().fetchall()

    results = []
    for event in events:
        prior = conn.execute(
            text(
                "SELECT price, changed_date FROM price_history "
                "WHERE property_id = :property_id AND changed_date < :changed_date "
                "ORDER BY changed_date DESC LIMIT 1"
            ),
            {"property_id": event["property_id"], "changed_date": event["changed_date"]},
        ).mappings().fetchone()
        if prior is None:
            continue
        # `as_of` is the price-provenance date (when the old price took
        # effect) — used only to know what the price *was*. Indicators must
        # instead be evaluated as of `eval_date`, the day immediately before
        # the actual price-change event, i.e. "would the rule have fired
        # right before this happened" rather than "on the day it was listed".
        event_dt = datetime.strptime(event["changed_date"], "%Y-%m-%d")
        eval_date = (event_dt - timedelta(days=1)).strftime("%Y-%m-%d")
        results.append({
            "property_id": event["property_id"],
            "as_of": prior["changed_date"],
            "eval_date": eval_date,
            "old_price": prior["price"],
            "new_price": event["price"],
            "event_date": event["changed_date"],
        })
    return results


def reconstruct_property_as_of(conn: Connection, property_id: int, as_of: str, price: float) -> dict:
    """Build a property snapshot with `price` overridden to its historical value.

    Every other field is treated as unchanged over time — a reasonable
    simplification given this dataset has no historical snapshots of
    area_m2, bedrooms, etc.
    """
    row = conn.execute(
        text("SELECT * FROM properties WHERE id = :id"), {"id": property_id}
    ).mappings().fetchone()
    snapshot = dict(row)
    snapshot["price"] = price
    return snapshot


@dataclass
class BacktestEventResult:
    """One historical price-change event evaluated against a rule's prediction."""

    property_id: int
    as_of: str
    eval_date: str
    fired: bool
    suggested_reduction_pct: float | None
    actual_reduction_pct: float
    data_complete: bool = True


def _has_market_snapshot(conn: Connection, neighborhood_id: int, as_of_month: str) -> bool:
    """Check whether any market_snapshots row exists for this neighborhood at
    or before as_of_month — i.e. whether indicators derived from
    market_snapshots have real data to work with rather than falling back to
    an ambiguous default."""
    row = conn.execute(
        text(
            "SELECT 1 FROM market_snapshots "
            "WHERE neighborhood_id = :neighborhood_id AND month <= :as_of_month LIMIT 1"
        ),
        {"neighborhood_id": neighborhood_id, "as_of_month": as_of_month},
    ).fetchone()
    return row is not None


def _run_rule(rule, snapshot: dict, indicators: dict) -> tuple[bool, float | None]:
    """Run a rule's prerequisites/evaluate against a reconstructed snapshot.

    Returns (fired, suggested_reduction_pct). suggested_reduction_pct is only
    populated when fired is True and the rule's metadata contains that key
    (which OverpricedRule's does).
    """
    fired = rule.prerequisites(indicators)
    if not fired:
        return False, None
    prop = Property(
        id=snapshot["id"],
        title=snapshot["title"],
        type=snapshot["type"],
        neighborhood="",
        city="",
        price=snapshot["price"],
        area_m2=snapshot["area_m2"],
        bedrooms=snapshot["bedrooms"],
        bathrooms=snapshot["bathrooms"],
        energy_rating=snapshot["energy_rating"],
        listed_date=snapshot["listed_date"],
        status=snapshot["status"],
    )
    rule_result = rule.evaluate(prop, indicators)
    return True, rule_result.metadata["suggested_reduction_pct"]


def evaluate_overpriced_rule(conn: Connection) -> list[BacktestEventResult]:
    """Backtest OverpricedRule: for every real price decrease, would the rule
    have fired beforehand, and how close was its suggested reduction to what
    actually happened?"""
    rule = OverpricedRule()
    results = []
    for event in find_price_change_events(conn):
        if event["new_price"] >= event["old_price"]:
            continue  # not a price decrease — not this rule's prediction to check

        snapshot = reconstruct_property_as_of(
            conn, event["property_id"], event["as_of"], event["old_price"]
        )
        indicators = compute_indicators(
            snapshot, conn, requested=rule.required_indicators, as_of=event["eval_date"]
        )
        fired, suggested_reduction_pct = _run_rule(rule, snapshot, indicators)

        data_complete = _has_market_snapshot(
            conn, snapshot["neighborhood_id"], event["eval_date"][:7]
        )

        actual_reduction_pct = round(
            (event["old_price"] - event["new_price"]) / event["old_price"] * 100, 2
        )
        results.append(BacktestEventResult(
            property_id=event["property_id"],
            as_of=event["as_of"],
            eval_date=event["eval_date"],
            fired=fired,
            suggested_reduction_pct=suggested_reduction_pct,
            actual_reduction_pct=actual_reduction_pct,
            data_complete=data_complete,
        ))
    return results


def evaluate_underpriced_rule(conn: Connection) -> str:
    """UnderpricedOpportunityRule predicts a quick sale, which nothing in the
    schema records (no sale date, status never changes) — not backtestable
    without a schema change, so this is an honest note, not a fake metric."""
    return "not yet backtestable — schema has no sale-outcome data (no sold_date, status never changes)"


_EVALUATORS = {
    "T01R01": evaluate_overpriced_rule,
    "T01R02": evaluate_underpriced_rule,
}


def run_backtest(conn: Connection) -> dict:
    """Run every registered evaluator. Returns {rule_code: list[BacktestEventResult] | str}."""
    return {code: fn(conn) for code, fn in _EVALUATORS.items()}


def format_report(results: dict) -> str:
    """Render backtest results as a human-readable report, one section per
    rule code and one line per evaluated event."""
    lines = []
    for code, outcome in results.items():
        lines.append(f"=== {code} ===")
        if isinstance(outcome, str):
            lines.append(f"  {outcome}")
            continue
        if not outcome:
            lines.append("  No backtestable events found.")
            continue
        for r in outcome:
            if not r.data_complete:
                lines.append(
                    f"  property {r.property_id}: SKIPPED — no market data for its neighborhood "
                    f"as of {r.eval_date} (actual reduction was {r.actual_reduction_pct:.1f}%, "
                    f"but no valid measurement possible)"
                )
                continue
            fired_str = "FIRED" if r.fired else "did not fire"
            suggested_str = (
                f"{r.suggested_reduction_pct:.1f}%" if r.suggested_reduction_pct is not None else "n/a"
            )
            lines.append(
                f"  property {r.property_id} (evaluated as of {r.eval_date}): {fired_str} | "
                f"suggested reduction: {suggested_str} | actual reduction: {r.actual_reduction_pct:.1f}%"
            )
        lines.append(f"  ({len(outcome)} event(s) tested — sample too small for precision/recall)")
    return "\n".join(lines)
