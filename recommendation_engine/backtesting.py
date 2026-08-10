"""Backtest recommendation rules against real historical outcomes.

Only rules whose predictions map to something the schema actually records
can be backtested. `OverpricedRule` predicts a price should drop, and
`price_history` records real price changes — so it gets a real evaluator.
`UnderpricedOpportunityRule` predicts a quick sale, which nothing in the
schema observes (no sale date, `properties.status` never changes) — it gets
an explicit "not yet backtestable" note instead of a fabricated metric.
"""

from sqlalchemy import text
from sqlalchemy.engine import Connection


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
