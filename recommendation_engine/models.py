"""Property and Recommendation data models."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Property:
    """A real estate property listing."""

    id: int
    title: str
    type: str
    neighborhood: str
    city: str
    price: float
    area_m2: float
    bedrooms: int
    bathrooms: int
    energy_rating: str
    listed_date: str
    status: str = "active"


@dataclass
class Recommendation:
    """A generated recommendation for a property."""

    code: str           # e.g., T01R03
    type: str           # pricing, timing, investment, marketing
    priority: str       # high, medium, low
    title: str
    description: str
    property_id: int
    version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "type": self.type,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "property_id": self.property_id,
            "version": self.version,
            "metadata": self.metadata,
        }
