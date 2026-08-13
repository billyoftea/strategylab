"""Manual factor source: build a FactorSpec from a user-supplied expression or code."""
from __future__ import annotations

import re

from ..spec import FactorSpec


def from_expression(expression: str, name: str | None = None, description: str = "") -> FactorSpec:
    expression = expression.strip()
    if not expression:
        raise ValueError("expression is empty")
    name = name or _auto_name(expression)
    return FactorSpec(
        name=name,
        description=description or f"manual expression: {expression}",
        expression=expression,
        source="manual",
    )


def from_code(code: str, name: str = "manual_code_factor", description: str = "") -> FactorSpec:
    return FactorSpec(
        name=name,
        description=description or "manual python code factor",
        code=code,
        source="manual",
    )


def _auto_name(expression: str) -> str:
    slug = re.sub(r"[^0-9a-zA-Z_]+", "_", expression).strip("_")
    return f"manual_{slug[:40]}" or "manual_factor"
