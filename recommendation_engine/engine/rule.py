"""Base Rule class and RuleResult - the contract every rule implements."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..models import Property


@dataclass
class RuleResult:
    """Output of a rule evaluation."""

    code: str
    type: str
    priority: str
    title: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


class Rule(ABC):
    """Base class for all recommendation rules.

    Every rule must declare:
    - code: structured identifier (T##R##)
    - version: semver string for tracking changes
    - type: category (pricing, timing, investment, etc.)
    - required_indicators: list of indicator keys the rule needs
    """

    code: str = ""
    version: str = "1.0.0"
    type: str = ""
    required_indicators: list[str] = []

    @abstractmethod
    def prerequisites(self, indicators: dict) -> bool:
        """Check if conditions are met to generate a recommendation.

        Return True if the rule should fire, False to skip.
        This prevents noise - e.g., don't suggest a price cut on day 1.
        """
        ...

    @abstractmethod
    def evaluate(self, property: Property, indicators: dict) -> RuleResult:
        """Generate the recommendation.

        Only called if prerequisites() returned True.
        Must return a RuleResult with all fields populated.
        """
        ...
