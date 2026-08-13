"""Factor sources: each produces a FactorSpec.

- manual: you provide a Qlib expression / code
- nl_pattern: natural-language K-line pattern -> DeepSeek -> Qlib expression
"""
from .manual import from_expression, from_code
from .nl_pattern import from_nl

__all__ = ["from_expression", "from_code", "from_nl"]
