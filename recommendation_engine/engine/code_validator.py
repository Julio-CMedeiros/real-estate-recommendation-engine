"""Rule code format validation.

Codes follow the pattern T##R## where:
- T## is the rule type (e.g., T01 = pricing, T02 = timing)
- R## is the rule number within that type
"""

import re
from dataclasses import dataclass


TYPE_PREFIX = "T"
CODE_PREFIX = "R"
MIN_WIDTH = 2

_PATTERN = re.compile(
    rf"^{TYPE_PREFIX}\d{{{MIN_WIDTH}}}{CODE_PREFIX}\d{{{MIN_WIDTH}}}$"
)


def validate_code(code: str) -> bool:
    """Check if a rule code matches the T##R## pattern."""
    return bool(_PATTERN.match(code))


def build_code(type_id: int, rule_id: int) -> str:
    """Build a formatted rule code from type and rule IDs.

    >>> build_code(1, 3)
    'T01R03'
    """
    code = f"{TYPE_PREFIX}{type_id:0{MIN_WIDTH}d}{CODE_PREFIX}{rule_id:0{MIN_WIDTH}d}"
    if not validate_code(code):
        raise ValueError(f"Generated invalid code: {code}")
    return code


def parse_code(code: str) -> tuple[int, int]:
    """Parse a rule code into (type_id, rule_id).

    >>> parse_code('T01R03')
    (1, 3)
    """
    if not validate_code(code):
        raise ValueError(f"Invalid rule code format: {code}")
    type_id = int(code[1:1 + MIN_WIDTH])
    rule_id = int(code[1 + MIN_WIDTH + 1:])
    return type_id, rule_id


# Human-readable type names
TYPE_NAMES = {
    1: "pricing",
    2: "timing",
    3: "investment",
    4: "improvement",
    5: "marketing",
}
