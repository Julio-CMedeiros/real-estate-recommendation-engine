"""Indicator computation functions.

Each indicator takes property + market context and returns a typed value.
Indicators are computed once and shared across all rules that need them.
"""

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Connection, RowMapping


# --- Indicator key constants ---

PRICE_VS_AREA_AVG = "price_vs_area_avg"
DAYS_ON_MARKET = "days_on_market"
PRICE_REDUCTIONS_COUNT = "price_reductions_count"
RENTAL_YIELD_GROSS = "rental_yield_gross"
AREA_APPRECIATION_6M = "area_appreciation_6m"
INVENTORY_PRESSURE = "inventory_pressure"
SIMILAR_SOLD_LAST_30D = "similar_sold_last_30d"
ENERGY_RATING_VALUE = "energy_rating_value"
HAS_PHOTOS = "has_photos"
HAS_DESCRIPTION = "has_description"
AVG_DAYS_ON_MARKET_AREA = "avg_days_on_market_area"
AREA_SOLD_LAST_MONTH = "area_sold_last_month"
AREA_LISTINGS_COUNT = "area_listings_count"


# Rent per m² by neighborhood tier
_RENT_TIERS = {"premium": 22.0, "mid": 16.0, "affordable": 11.0}
_NEIGHBORHOOD_TIER = {1: "premium", 2: "mid", 3: "premium", 4: "mid", 5: "mid", 6: "affordable"}

# Energy rating price multipliers (rough estimate)
_ENERGY_MULTIPLIER = {"A+": 1.10, "A": 1.07, "B": 1.03, "C": 1.00, "D": 0.96, "E": 0.92, "F": 0.88}


def compute_indicators(
    property_row: RowMapping,
    conn: Connection,
    requested: list[str] | None = None,
) -> dict:
    """Compute all (or selected) indicators for a property.

    Parameters
    ----------
    property_row : RowMapping
        The property record from the database.
    conn : Connection
        Active database connection for queries.
    requested : list[str] | None
        If provided, only compute these indicators. Otherwise compute all.

    Returns
    -------
    dict
        Mapping of indicator key -> computed value.
    """
    all_indicators = requested or list(_INDICATOR_FNS.keys())
    result = {}
    for key in all_indicators:
        fn = _INDICATOR_FNS.get(key)
        if fn:
            result[key] = fn(property_row, conn)
    return result


# --- Individual indicator functions ---


def _price_vs_area_avg(prop: RowMapping, conn: Connection) -> float:
    """How much (%) the property price/m² deviates from area average."""
    market = conn.execute(
        text(
            "SELECT avg_price_m2 FROM market_snapshots "
            "WHERE neighborhood_id = :neighborhood_id ORDER BY month DESC LIMIT 1"
        ),
        {"neighborhood_id": prop["neighborhood_id"]},
    ).mappings().fetchone()
    if not market or not market["avg_price_m2"]:
        return 0.0
    prop_price_m2 = prop["price"] / prop["area_m2"]
    return round(((prop_price_m2 - market["avg_price_m2"]) / market["avg_price_m2"]) * 100, 2)


def _days_on_market(prop: RowMapping, _conn: Connection) -> int:
    """Days since the property was listed."""
    listed = datetime.strptime(prop["listed_date"], "%Y-%m-%d")
    return (datetime.now() - listed).days


def _price_reductions_count(prop: RowMapping, conn: Connection) -> int:
    """Number of price reductions since listing."""
    row = conn.execute(
        text(
            "SELECT COUNT(*) as cnt FROM price_history "
            "WHERE property_id = :property_id AND event = 'price_change'"
        ),
        {"property_id": prop["id"]},
    ).mappings().fetchone()
    return row["cnt"] if row else 0


def _rental_yield_gross(prop: RowMapping, _conn: Connection) -> float:
    """Estimated gross rental yield %."""
    tier = _NEIGHBORHOOD_TIER.get(prop["neighborhood_id"], "mid")
    monthly_rent = prop["area_m2"] * _RENT_TIERS[tier]
    return round((monthly_rent * 12 / prop["price"]) * 100, 2)


def _area_appreciation_6m(prop: RowMapping, conn: Connection) -> float:
    """6-month price appreciation % for the neighborhood."""
    rows = conn.execute(
        text(
            "SELECT avg_price_m2 FROM market_snapshots "
            "WHERE neighborhood_id = :neighborhood_id ORDER BY month DESC LIMIT 6"
        ),
        {"neighborhood_id": prop["neighborhood_id"]},
    ).mappings().fetchall()
    if len(rows) < 2:
        return 0.0
    latest = rows[0]["avg_price_m2"]
    oldest = rows[-1]["avg_price_m2"]
    return round(((latest - oldest) / oldest) * 100, 2)


def _inventory_pressure(prop: RowMapping, conn: Connection) -> float:
    """Ratio of active listings to monthly sales. High = buyer's market."""
    market = conn.execute(
        text(
            "SELECT listings_count, sold_count FROM market_snapshots "
            "WHERE neighborhood_id = :neighborhood_id ORDER BY month DESC LIMIT 1"
        ),
        {"neighborhood_id": prop["neighborhood_id"]},
    ).mappings().fetchone()
    if not market or not market["sold_count"]:
        return 0.0
    return round(market["listings_count"] / market["sold_count"], 2)


def _similar_sold_last_30d(prop: RowMapping, conn: Connection) -> int:
    """Number of similar properties sold in the area last month."""
    market = conn.execute(
        text(
            "SELECT sold_count FROM market_snapshots "
            "WHERE neighborhood_id = :neighborhood_id ORDER BY month DESC LIMIT 1"
        ),
        {"neighborhood_id": prop["neighborhood_id"]},
    ).mappings().fetchone()
    return market["sold_count"] if market else 0


def _energy_rating_value(prop: RowMapping, _conn: Connection) -> float:
    """Price multiplier impact of current energy rating."""
    return _ENERGY_MULTIPLIER.get(prop["energy_rating"], 1.0)


def _avg_days_on_market_area(prop: RowMapping, conn: Connection) -> int:
    """Average days on market for the neighborhood."""
    market = conn.execute(
        text(
            "SELECT avg_days_on_market FROM market_snapshots "
            "WHERE neighborhood_id = :neighborhood_id ORDER BY month DESC LIMIT 1"
        ),
        {"neighborhood_id": prop["neighborhood_id"]},
    ).mappings().fetchone()
    return market["avg_days_on_market"] if market else 60


def _area_sold_last_month(prop: RowMapping, conn: Connection) -> int:
    return _similar_sold_last_30d(prop, conn)


def _area_listings_count(prop: RowMapping, conn: Connection) -> int:
    market = conn.execute(
        text(
            "SELECT listings_count FROM market_snapshots "
            "WHERE neighborhood_id = :neighborhood_id ORDER BY month DESC LIMIT 1"
        ),
        {"neighborhood_id": prop["neighborhood_id"]},
    ).mappings().fetchone()
    return market["listings_count"] if market else 0


# Registry of all indicator functions
_INDICATOR_FNS = {
    PRICE_VS_AREA_AVG: _price_vs_area_avg,
    DAYS_ON_MARKET: _days_on_market,
    PRICE_REDUCTIONS_COUNT: _price_reductions_count,
    RENTAL_YIELD_GROSS: _rental_yield_gross,
    AREA_APPRECIATION_6M: _area_appreciation_6m,
    INVENTORY_PRESSURE: _inventory_pressure,
    SIMILAR_SOLD_LAST_30D: _similar_sold_last_30d,
    ENERGY_RATING_VALUE: _energy_rating_value,
    AVG_DAYS_ON_MARKET_AREA: _avg_days_on_market_area,
    AREA_SOLD_LAST_MONTH: _area_sold_last_month,
    AREA_LISTINGS_COUNT: _area_listings_count,
}
