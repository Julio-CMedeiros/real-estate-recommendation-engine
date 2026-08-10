"""Engine runner - orchestrates indicator computation and rule evaluation."""

from sqlalchemy import text
from sqlalchemy.engine import Connection

from ..models import Property, Recommendation
from .indicators import compute_indicators
from .rule import Rule
from .rule_registry import discover_rules


def run_engine(
    conn: Connection,
    property_id: int | None = None,
    dry_run: bool = False,
) -> list[Recommendation]:
    """Run all rules against active properties and collect recommendations.

    Parameters
    ----------
    conn : Connection
        Database connection.
    property_id : int | None
        If set, only evaluate this property. Otherwise evaluate all active.
    dry_run : bool
        If True, generate recommendations but don't persist them.

    Returns
    -------
    list[Recommendation]
        Generated recommendations, sorted by priority.
    """
    # 1. Discover all rules
    rules = discover_rules()
    if not rules:
        return []

    # 2. Load properties
    if property_id:
        rows = conn.execute(
            text("SELECT * FROM properties WHERE id = :id AND status = 'active'"),
            {"id": property_id},
        ).mappings().fetchall()
    else:
        rows = conn.execute(
            text("SELECT * FROM properties WHERE status = 'active'")
        ).mappings().fetchall()

    recommendations: list[Recommendation] = []

    # 3. For each property, compute indicators and evaluate rules
    for prop_row in rows:
        # Collect all required indicators across rules (deduplicated)
        all_required = list({
            ind
            for rule in rules
            for ind in rule.required_indicators
        })

        # Compute indicators once per property
        indicators = compute_indicators(prop_row, conn, requested=all_required)

        prop = Property(
            id=prop_row["id"],
            title=prop_row["title"],
            type=prop_row["type"],
            neighborhood="",  # simplified
            city="",
            price=prop_row["price"],
            area_m2=prop_row["area_m2"],
            bedrooms=prop_row["bedrooms"],
            bathrooms=prop_row["bathrooms"],
            energy_rating=prop_row["energy_rating"],
            listed_date=prop_row["listed_date"],
            status=prop_row["status"],
        )

        # Evaluate each rule
        for rule in rules:
            # Filter indicators to only what this rule needs
            rule_indicators = {
                k: v for k, v in indicators.items()
                if k in rule.required_indicators
            }

            # Check prerequisites
            try:
                if not rule.prerequisites(rule_indicators):
                    continue
            except (KeyError, TypeError):
                continue

            # Generate recommendation
            try:
                result = rule.evaluate(prop, rule_indicators)
                recommendations.append(
                    Recommendation(
                        code=result.code,
                        type=result.type,
                        priority=result.priority,
                        title=result.title,
                        description=result.description,
                        property_id=prop.id,
                        version=rule.version,
                        metadata=result.metadata,
                    )
                )
            except Exception:
                continue

    # Sort: high > medium > low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda r: priority_order.get(r.priority, 99))

    if not dry_run:
        _persist(conn, recommendations)

    return recommendations


def _persist(conn: Connection, recs: list[Recommendation]) -> None:
    """Store recommendations in the database."""
    for rec in recs:
        conn.execute(
            text(
                "INSERT INTO recommendations "
                "(code, type, priority, title, description, property_id, version) "
                "VALUES (:code, :type, :priority, :title, :description, :property_id, :version)"
            ),
            {
                "code": rec.code,
                "type": rec.type,
                "priority": rec.priority,
                "title": rec.title,
                "description": rec.description,
                "property_id": rec.property_id,
                "version": rec.version,
            },
        )
    conn.commit()
