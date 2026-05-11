"""Rule T03R02: Appreciation Momentum - area with strong price growth."""

from recommendation_engine.engine.rule import Rule, RuleResult
from recommendation_engine.engine.indicators import (
    AREA_APPRECIATION_6M,
    AREA_SOLD_LAST_MONTH,
    AVG_DAYS_ON_MARKET_AREA,
)
from recommendation_engine.models import Property


class AppreciationMomentumRule(Rule):
    code = "T03R02"
    version = "1.0.0"
    type = "investment"
    required_indicators = [AREA_APPRECIATION_6M, AREA_SOLD_LAST_MONTH, AVG_DAYS_ON_MARKET_AREA]

    def prerequisites(self, indicators: dict) -> bool:
        return (
            indicators[AREA_APPRECIATION_6M] > 5  # >5% in 6 months
            and indicators[AREA_SOLD_LAST_MONTH] >= 15  # active market
        )

    def evaluate(self, property: Property, indicators: dict) -> RuleResult:
        appreciation = indicators[AREA_APPRECIATION_6M]

        return RuleResult(
            code=self.code,
            type=self.type,
            priority="medium",
            title=f"Area appreciating {appreciation:.1f}% over 6 months",
            description=(
                f"This neighborhood shows strong price momentum: "
                f"{appreciation:.1f}% appreciation with {indicators[AREA_SOLD_LAST_MONTH]} "
                f"sales last month (avg {indicators[AVG_DAYS_ON_MARKET_AREA]} days to sell)."
            ),
            metadata={
                "appreciation_6m": appreciation,
                "monthly_sales": indicators[AREA_SOLD_LAST_MONTH],
                "avg_days_on_market": indicators[AVG_DAYS_ON_MARKET_AREA],
            },
        )
