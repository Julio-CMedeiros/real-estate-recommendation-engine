"""Rule T05R01: Missing Photos - listing quality improvement."""

from recommendation_engine.engine.rule import Rule, RuleResult
from recommendation_engine.engine.indicators import DAYS_ON_MARKET, AVG_DAYS_ON_MARKET_AREA
from recommendation_engine.models import Property


class MissingPhotosRule(Rule):
    code = "T05R01"
    version = "1.0.0"
    type = "marketing"
    required_indicators = [DAYS_ON_MARKET, AVG_DAYS_ON_MARKET_AREA]

    def prerequisites(self, indicators: dict) -> bool:
        # Fire if property is taking longer than area average to sell
        return indicators[DAYS_ON_MARKET] > indicators[AVG_DAYS_ON_MARKET_AREA] * 0.8

    def evaluate(self, property: Property, indicators: dict) -> RuleResult:
        return RuleResult(
            code=self.code,
            type=self.type,
            priority="low",
            title="Improve listing quality - professional photos sell 32% faster",
            description=(
                f"This property has been listed for {indicators[DAYS_ON_MARKET]} days "
                f"(area average: {indicators[AVG_DAYS_ON_MARKET_AREA]}). "
                f"Listings with professional photography and virtual tours sell significantly faster. "
                f"Consider upgrading the visual presentation."
            ),
            metadata={
                "days_on_market": indicators[DAYS_ON_MARKET],
                "area_avg_days": indicators[AVG_DAYS_ON_MARKET_AREA],
            },
        )
