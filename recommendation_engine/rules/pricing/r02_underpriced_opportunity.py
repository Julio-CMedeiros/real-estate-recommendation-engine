"""Rule T01R02: Underpriced Opportunity - property priced below area average."""

from recommendation_engine.engine.rule import Rule, RuleResult
from recommendation_engine.engine.indicators import (
    PRICE_VS_AREA_AVG,
    DAYS_ON_MARKET,
    AREA_APPRECIATION_6M,
)
from recommendation_engine.models import Property


class UnderpricedOpportunityRule(Rule):
    code = "T01R02"
    version = "1.0.0"
    type = "pricing"
    required_indicators = [PRICE_VS_AREA_AVG, DAYS_ON_MARKET, AREA_APPRECIATION_6M]

    def prerequisites(self, indicators: dict) -> bool:
        return (
            indicators[PRICE_VS_AREA_AVG] < -8  # >8% below area avg
            and indicators[DAYS_ON_MARKET] < 14  # recently listed
        )

    def evaluate(self, property: Property, indicators: dict) -> RuleResult:
        discount_pct = abs(indicators[PRICE_VS_AREA_AVG])

        return RuleResult(
            code=self.code,
            type=self.type,
            priority="high" if discount_pct > 15 else "medium",
            title=f"Underpriced by {discount_pct:.0f}% - potential quick sale",
            description=(
                f"Listed {discount_pct:.1f}% below the area average with only "
                f"{indicators[DAYS_ON_MARKET]} days on market. "
                f"Area appreciation over 6 months: {indicators[AREA_APPRECIATION_6M]:.1f}%."
            ),
            metadata={
                "below_avg_pct": round(discount_pct, 1),
                "area_appreciation_6m": indicators[AREA_APPRECIATION_6M],
            },
        )
