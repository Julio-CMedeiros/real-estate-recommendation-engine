"""Rule T03R01: High Yield Investment - strong rental return."""

from recommendation_engine.engine.rule import Rule, RuleResult
from recommendation_engine.engine.indicators import (
    RENTAL_YIELD_GROSS,
    AREA_APPRECIATION_6M,
    INVENTORY_PRESSURE,
)
from recommendation_engine.models import Property


class HighYieldRule(Rule):
    code = "T03R01"
    version = "1.2.0"
    type = "investment"
    required_indicators = [RENTAL_YIELD_GROSS, AREA_APPRECIATION_6M, INVENTORY_PRESSURE]

    def prerequisites(self, indicators: dict) -> bool:
        return indicators[RENTAL_YIELD_GROSS] >= 4.5  # min 4.5% gross yield

    def evaluate(self, property: Property, indicators: dict) -> RuleResult:
        yield_pct = indicators[RENTAL_YIELD_GROSS]
        appreciation = indicators[AREA_APPRECIATION_6M]

        return RuleResult(
            code=self.code,
            type=self.type,
            priority="high" if yield_pct >= 6 else "medium",
            title=f"Investment opportunity - {yield_pct:.1f}% gross yield",
            description=(
                f"Estimated gross rental yield of {yield_pct:.1f}% "
                f"with {appreciation:.1f}% area appreciation over 6 months. "
                f"Inventory pressure ratio: {indicators[INVENTORY_PRESSURE]:.1f}x."
            ),
            metadata={
                "gross_yield_pct": yield_pct,
                "area_appreciation_6m": appreciation,
                "inventory_pressure": indicators[INVENTORY_PRESSURE],
            },
        )
