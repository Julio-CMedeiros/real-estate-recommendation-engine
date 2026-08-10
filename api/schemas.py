"""Pydantic request/response models — decoupled from the engine's internal dataclasses."""

from enum import Enum
from typing import Any

from pydantic import BaseModel


class RuleType(str, Enum):
    pricing = "pricing"
    timing = "timing"
    investment = "investment"
    improvement = "improvement"
    marketing = "marketing"


class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class RecommendationOut(BaseModel):
    code: str
    type: str
    priority: str
    title: str
    description: str
    property_id: int
    version: str
    metadata: dict[str, Any]


class ErrorResponse(BaseModel):
    error: str
