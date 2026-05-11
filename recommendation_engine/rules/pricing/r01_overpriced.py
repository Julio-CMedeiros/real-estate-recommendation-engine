"""Rule T01R01: Overpriced Property - suggest price reduction."""

from recommendation_engine.engine.rule import Rule, RuleResult
from recommendation_engine.engine.indicators import (
    PRICE_VS_AREA_AVG,
    DAYS_ON_MARKET,
    SIMILAR_SOLD_LAST_30D,
)
from recommendation_engine.models import Property


class OverpricedRule(Rule):
    code = "T01R01"
    version = "2.0.0"
    type = "pricing"
    required_indicators = [PRICE_VS_AREA_AVG, DAYS_ON_MARKET, SIMILAR_SOLD_LAST_30D]

    def prerequisites(self, indicators: dict) -> bool:
        return (
            indicators[PRICE_VS_AREA_AVG] > 10  # >10% above area avg
            and indicators[DAYS_ON_MARKET] > 30  # on market >30 days
        )

    def evaluate(self, property: Property, indicators: dict) -> RuleResult:
        overprice_pct = indicators[PRICE_VS_AREA_AVG]
        suggested_reduction = min(overprice_pct * 0.6, 15)

        return RuleResult(
            code=self.code,
            type=self.type,
            priority="high" if overprice_pct > 20 else "medium",
            title=f"Consider reducing price by {suggested_reduction:.0f}%",
            description=(
                f"This property is priced {overprice_pct:.1f}% above the neighborhood "
                f"average and has been on the market for {indicators[DAYS_ON_MARKET]} days. "
                f"{indicators[SIMILAR_SOLD_LAST_30D]} similar properties sold last month at lower price points."
            ),
            metadata={
                "suggested_reduction_pct": round(suggested_reduction, 1),
                "current_premium_pct": round(overprice_pct, 1),
                "days_on_market": indicators[DAYS_ON_MARKET],
            },
        )
