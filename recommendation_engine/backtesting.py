"""Backtest recommendation rules against real historical outcomes.

Only rules whose predictions map to something the schema actually records
can be backtested. `OverpricedRule` predicts a price should drop, and
`price_history` records real price changes — so it gets a real evaluator.
`UnderpricedOpportunityRule` predicts a quick sale, which nothing in the
schema observes (no sale date, `properties.status` never changes) — it gets
an explicit "not yet backtestable" note instead of a fabricated metric.
"""

from dataclasses import dataclass

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
        results.append({
            "property_id": event["property_id"],
            "as_of": prior["changed_date"],
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
    fired: bool
    suggested_reduction_pct: float | None
    actual_reduction_pct: float


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
            snapshot, conn, requested=rule.required_indicators, as_of=event["as_of"]
        )
        fired = rule.prerequisites(indicators)

        suggested_reduction_pct = None
        if fired:
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
            suggested_reduction_pct = rule_result.metadata["suggested_reduction_pct"]

        actual_reduction_pct = round(
            (event["old_price"] - event["new_price"]) / event["old_price"] * 100, 2
        )
        results.append(BacktestEventResult(
            property_id=event["property_id"],
            as_of=event["as_of"],
            fired=fired,
            suggested_reduction_pct=suggested_reduction_pct,
            actual_reduction_pct=actual_reduction_pct,
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
            fired_str = "FIRED" if r.fired else "did not fire"
            suggested_str = (
                f"{r.suggested_reduction_pct:.1f}%" if r.suggested_reduction_pct is not None else "n/a"
            )
            lines.append(
                f"  property {r.property_id} as of {r.as_of}: {fired_str} | "
                f"suggested reduction: {suggested_str} | actual reduction: {r.actual_reduction_pct:.1f}%"
            )
        lines.append(f"  ({len(outcome)} event(s) tested — sample too small for precision/recall)")
    return "\n".join(lines)
