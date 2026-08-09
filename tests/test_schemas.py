import pytest
from pydantic import ValidationError

from api.schemas import Priority, RecommendationOut, RuleType


def test_recommendation_out_round_trip():
    data = {
        "code": "T01R01",
        "type": "pricing",
        "priority": "high",
        "title": "Reduce price",
        "description": "desc",
        "property_id": 1,
        "version": "1.0.0",
        "metadata": {"a": 1},
    }
    assert RecommendationOut.model_validate(data).model_dump() == data


def test_recommendation_out_rejects_missing_field():
    with pytest.raises(ValidationError):
        RecommendationOut.model_validate({"code": "T01R01"})


def test_rule_type_rejects_invalid_value():
    with pytest.raises(ValueError):
        RuleType("not-a-type")


def test_priority_accepts_known_values():
    assert Priority("high") == Priority.high
