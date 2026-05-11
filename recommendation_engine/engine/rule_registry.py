"""Auto-discovery and registration of rule modules.

Rules are discovered by scanning the rules/ directory for Python modules
that define a subclass of Rule. This lets you add rules by adding files -
no changes to the engine core needed.
"""

import importlib
import pkgutil
from pathlib import Path

from .rule import Rule

_RULES_PACKAGE = "recommendation_engine.rules"
_RULES_DIR = Path(__file__).parent.parent / "rules"


def discover_rules() -> list[Rule]:
    """Scan the rules directory and return instances of all Rule subclasses.

    Walks through all sub-packages (pricing/, timing/, etc.) and imports
    every module. Any class that subclasses Rule gets instantiated and returned.
    """
    rules: list[Rule] = []

    for package_info in pkgutil.walk_packages(
        path=[str(_RULES_DIR)],
        prefix=f"{_RULES_PACKAGE}.",
    ):
        if package_info.ispkg:
            continue
        try:
            module = importlib.import_module(package_info.name)
        except Exception:
            continue

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, Rule)
                and attr is not Rule
                and hasattr(attr, "code")
                and attr.code  # skip base classes without a code
            ):
                rules.append(attr())

    # Sort by code for deterministic ordering
    rules.sort(key=lambda r: r.code)
    return rules
