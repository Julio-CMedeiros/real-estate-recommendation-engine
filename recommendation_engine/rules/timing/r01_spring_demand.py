"""Rule T02R01: Spring Demand Surge - best time to list."""

from recommendation_engine.engine.rule import Rule, RuleResult
from recommendation_engine.engine.indicators import (
    AREA_APPRECIATION_6M,
    INVENTORY_PRESSURE,
    AVG_DAYS_ON_MARKET_AREA,
)
from recommendation_engine.models import Property


class SpringDemandRule(Rule):
    code = "T02R01"
    version = "1.1.0"
    type = "timing"
    required_indicators = [AREA_APPRECIATION_6M, INVENTORY_PRESSURE, AVG_DAYS_ON_MARKET_AREA]

    def prerequisites(self, indicators: dict) -> bool:
        return (
            indicators[AREA_APPRECIATION_6M] > 3  # area is appreciating
            and indicators[INVENTORY_PRESSURE] < 3  # supply is tight
        )

    def evaluate(self, property: Property, indicators: dict) -> RuleResult:
        return RuleResult(
            code=self.code,
            type=self.type,
            priority="medium",
            title="Strong listing conditions - low inventory, rising prices",
            description=(
                f"The area has appreciated {indicators[AREA_APPRECIATION_6M]:.1f}% over 6 months "
                f"with a supply ratio of {indicators[INVENTORY_PRESSURE]:.1f}x "
                f"(avg {indicators[AVG_DAYS_ON_MARKET_AREA]} days to sell). "
                f"Listing now could capture above-average demand."
            ),
            metadata={
                "appreciation_6m": indicators[AREA_APPRECIATION_6M],
                "inventory_ratio": indicators[INVENTORY_PRESSURE],
                "avg_days_to_sell": indicators[AVG_DAYS_ON_MARKET_AREA],
            },
        )
