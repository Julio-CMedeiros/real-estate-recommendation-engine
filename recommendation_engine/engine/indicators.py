"""Indicator computation functions.

Each indicator takes property + market context and returns a typed value.
Indicators are computed once and shared across all rules that need them.
"""

import sqlite3
from datetime import datetime


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
    property_row: sqlite3.Row,
    conn: sqlite3.Connection,
    requested: list[str] | None = None,
) -> dict:
    """Compute all (or selected) indicators for a property.

    Parameters
    ----------
    property_row : sqlite3.Row
        The property record from the database.
    conn : sqlite3.Connection
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


def _price_vs_area_avg(prop: sqlite3.Row, conn: sqlite3.Connection) -> float:
    """How much (%) the property price/m² deviates from area average."""
    market = conn.execute(
        "SELECT avg_price_m2 FROM market_snapshots "
        "WHERE neighborhood_id = ? ORDER BY month DESC LIMIT 1",
        [prop["neighborhood_id"]],
    ).fetchone()
    if not market or not market["avg_price_m2"]:
        return 0.0
    prop_price_m2 = prop["price"] / prop["area_m2"]
    return round(((prop_price_m2 - market["avg_price_m2"]) / market["avg_price_m2"]) * 100, 2)


def _days_on_market(prop: sqlite3.Row, _conn: sqlite3.Connection) -> int:
    """Days since the property was listed."""
    listed = datetime.strptime(prop["listed_date"], "%Y-%m-%d")
    return (datetime.now() - listed).days


def _price_reductions_count(prop: sqlite3.Row, conn: sqlite3.Connection) -> int:
    """Number of price reductions since listing."""
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM price_history "
        "WHERE property_id = ? AND event = 'price_change'",
        [prop["id"]],
    ).fetchone()
    return row["cnt"] if row else 0


def _rental_yield_gross(prop: sqlite3.Row, _conn: sqlite3.Connection) -> float:
    """Estimated gross rental yield %."""
    tier = _NEIGHBORHOOD_TIER.get(prop["neighborhood_id"], "mid")
    monthly_rent = prop["area_m2"] * _RENT_TIERS[tier]
    return round((monthly_rent * 12 / prop["price"]) * 100, 2)


def _area_appreciation_6m(prop: sqlite3.Row, conn: sqlite3.Connection) -> float:
    """6-month price appreciation % for the neighborhood."""
    rows = conn.execute(
        "SELECT avg_price_m2 FROM market_snapshots "
        "WHERE neighborhood_id = ? ORDER BY month DESC LIMIT 6",
        [prop["neighborhood_id"]],
    ).fetchall()
    if len(rows) < 2:
        return 0.0
    latest = rows[0]["avg_price_m2"]
    oldest = rows[-1]["avg_price_m2"]
    return round(((latest - oldest) / oldest) * 100, 2)


def _inventory_pressure(prop: sqlite3.Row, conn: sqlite3.Connection) -> float:
    """Ratio of active listings to monthly sales. High = buyer's market."""
    market = conn.execute(
        "SELECT listings_count, sold_count FROM market_snapshots "
        "WHERE neighborhood_id = ? ORDER BY month DESC LIMIT 1",
        [prop["neighborhood_id"]],
    ).fetchone()
    if not market or not market["sold_count"]:
        return 0.0
    return round(market["listings_count"] / market["sold_count"], 2)


def _similar_sold_last_30d(prop: sqlite3.Row, conn: sqlite3.Connection) -> int:
    """Number of similar properties sold in the area last month."""
    market = conn.execute(
        "SELECT sold_count FROM market_snapshots "
        "WHERE neighborhood_id = ? ORDER BY month DESC LIMIT 1",
        [prop["neighborhood_id"]],
    ).fetchone()
    return market["sold_count"] if market else 0


def _energy_rating_value(prop: sqlite3.Row, _conn: sqlite3.Connection) -> float:
    """Price multiplier impact of current energy rating."""
    return _ENERGY_MULTIPLIER.get(prop["energy_rating"], 1.0)


def _avg_days_on_market_area(prop: sqlite3.Row, conn: sqlite3.Connection) -> int:
    """Average days on market for the neighborhood."""
    market = conn.execute(
        "SELECT avg_days_on_market FROM market_snapshots "
        "WHERE neighborhood_id = ? ORDER BY month DESC LIMIT 1",
        [prop["neighborhood_id"]],
    ).fetchone()
    return market["avg_days_on_market"] if market else 60


def _area_sold_last_month(prop: sqlite3.Row, conn: sqlite3.Connection) -> int:
    return _similar_sold_last_30d(prop, conn)


def _area_listings_count(prop: sqlite3.Row, conn: sqlite3.Connection) -> int:
    market = conn.execute(
        "SELECT listings_count FROM market_snapshots "
        "WHERE neighborhood_id = ? ORDER BY month DESC LIMIT 1",
        [prop["neighborhood_id"]],
    ).fetchone()
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
