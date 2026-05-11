# 🏠 Real Estate Recommendation Engine

A **rule-based recommendation engine** that generates actionable real estate insights (pricing adjustments, investment opportunities, market timing alerts) by evaluating properties against configurable rules powered by market indicators.

> **This is a showcase project.** It demonstrates recommendation engine architecture, rule design patterns, indicator pipelines, and scoring systems I've built in production (at scale, across 11+ rule types and 60+ market indicators).

## How It Works

```
┌────────────────────────────────┐
│        Market Data             │
│  (listings, sales, trends)     │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│     Indicator Pipeline         │
│                                │
│  • price_vs_area_avg           │
│  • days_on_market              │
│  • price_change_velocity       │
│  • rental_yield_estimate       │
│  • inventory_pressure          │
│  • ...40+ indicators           │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│       Rule Engine              │
│                                │
│  Each rule:                    │
│  1. Declares required          │
│     indicators                 │
│  2. Defines prerequisites      │
│     (thresholds, conditions)   │
│  3. Generates a typed          │
│     recommendation with        │
│     metadata                   │
│                                │
│  Rules are versioned,          │
│  grouped by type, and          │
│  auto-discovered at startup.   │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│    Recommendations Output      │
│                                │
│  • code: T01R03                │
│  • type: pricing               │
│  • title: "Reduce asking ..."  │
│  • priority: high              │
│  • metadata: {discount, ...}   │
│  • version: 2.1.0              │
└────────────────────────────────┘
```

## Rule Types

| Code | Type | Description | Example |
|------|------|-------------|---------|
| `T01` | Pricing | Price adjustment recommendations | "Reduce price by 8%, 45 days on market, area avg is 12% lower" |
| `T02` | Timing | Best time to list or buy | "List now, spring demand up 23%, inventory is low" |
| `T03` | Investment | Buy/hold/sell signals | "Strong buy: 5.8% yield, 6.5% annual appreciation" |
| `T04` | Improvement | Renovations that add value | "Add energy cert upgrade, B→A adds €15k in this area" |
| `T05` | Marketing | Listing optimization | "Add professional photos, listings with photos sell 32% faster" |

## Indicators

The engine evaluates properties against **40+ indicators** computed from market data. Each indicator takes property + market context and returns a typed value.

```python
# Example indicators
PRICE_VS_AREA_AVG = "price_vs_area_avg"           # % above/below neighborhood avg
DAYS_ON_MARKET = "days_on_market"                   # Days since listing
PRICE_REDUCTIONS_COUNT = "price_reductions_count"   # Number of price drops
RENTAL_YIELD_GROSS = "rental_yield_gross"           # Estimated gross yield %
AREA_APPRECIATION_6M = "area_appreciation_6m"       # 6-month price trend %
INVENTORY_PRESSURE = "inventory_pressure"           # Supply vs demand ratio
SIMILAR_SOLD_LAST_30D = "similar_sold_last_30d"     # Comparable recent sales
ENERGY_RATING_VALUE = "energy_rating_value"         # Energy cert impact on price
```

## Rule Architecture

Rules are auto-discovered Python modules under `rules/`. Each rule:

1. **Declares its code** using a structured format (`T{type}R{rule}`)
2. **Specifies required indicators** - the engine pre-fetches only what's needed
3. **Defines prerequisites** - conditions that must be true to generate a recommendation
4. **Returns a typed recommendation** with title, description, priority, and metadata

```python
# rules/pricing/r01_overpriced.py

from engine.rule import Rule, RuleResult

class OverpricedRule(Rule):
    code = "T01R01"
    version = "2.0.0"
    type = "pricing"
    title = "Price Reduction Opportunity"
    
    required_indicators = [
        "price_vs_area_avg",
        "days_on_market",
        "similar_sold_last_30d",
    ]

    def prerequisites(self, indicators: dict) -> bool:
        return (
            indicators["price_vs_area_avg"] > 10  # >10% above area average
            and indicators["days_on_market"] > 30
        )

    def evaluate(self, property: dict, indicators: dict) -> RuleResult:
        overprice_pct = indicators["price_vs_area_avg"]
        suggested_reduction = min(overprice_pct * 0.6, 15)  # Cap at 15%
        
        return RuleResult(
            code=self.code,
            type=self.type,
            priority="high" if overprice_pct > 20 else "medium",
            title=f"Consider reducing price by {suggested_reduction:.0f}%",
            description=(
                f"This property is {overprice_pct:.1f}% above the area average "
                f"and has been listed for {indicators['days_on_market']} days. "
                f"Similar properties sold within 30 days at lower price points."
            ),
            metadata={
                "suggested_reduction_pct": round(suggested_reduction, 1),
                "current_premium_pct": round(overprice_pct, 1),
                "days_on_market": indicators["days_on_market"],
                "comparable_sales": indicators["similar_sold_last_30d"],
            },
        )
```

## Quick Start

```bash
pip install -e .

# Run recommendations for all active properties
python -m recommendation_engine

# Run for a specific property
python -m recommendation_engine --property-id 1

# Dry-run mode (evaluate but don't persist)
python -m recommendation_engine --dry-run
```

## Project Structure

```
recommendation_engine/
├── __main__.py              # CLI entry point
├── engine/
│   ├── runner.py            # Orchestrates indicator fetch → rule eval → output
│   ├── rule.py              # Base Rule class, RuleResult dataclass
│   ├── rule_registry.py     # Auto-discovery and registration of rules
│   ├── indicators.py        # Indicator computation functions
│   └── code_validator.py    # Rule code format validation (T##R##)
├── rules/
│   ├── pricing/
│   │   ├── r01_overpriced.py
│   │   └── r02_underpriced_opportunity.py
│   ├── timing/
│   │   └── r01_spring_demand.py
│   ├── investment/
│   │   ├── r01_high_yield.py
│   │   └── r02_appreciation_momentum.py
│   └── marketing/
│       └── r01_missing_photos.py
├── database.py              # SQLite with demo data
└── models.py                # Property, Recommendation types
```

## Design Principles

### 1. Rules are self-contained modules
Each rule knows what data it needs, when it applies, and what it produces. Adding a new rule = adding a new file. No changes to the engine core.

### 2. Indicators are decoupled from rules
Indicators are computed once and shared across rules. If 3 rules need `days_on_market`, it's computed once. This matters at scale (60+ indicators, 11+ rules).

### 3. Recommendations are typed and versioned
Every recommendation has a structured code (`T01R03`), a semver version, and typed metadata. This enables:
- Tracking which rule version generated an insight
- Filtering by type in downstream systems
- A/B testing rule changes

### 4. Prerequisites prevent noise
Rules only fire when conditions are met. A "reduce price" recommendation doesn't fire on day 1. A "buy signal" doesn't fire if yield is below threshold. This keeps signal-to-noise high.

## License

MIT
