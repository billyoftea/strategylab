"""Core data contracts: FactorSpec + backtest/event-study configs.

FactorSpec is THE decoupling point — every factor source (manual, NL pattern,
RD-Agent) produces one, and the engine consumes it.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class FactorSpec:
    """A factor / K-line-pattern definition.

    Either `expression` (a Qlib expression like "Mean($close, 20)") or `code`
    (python factor source) must be provided. MVP favours `expression` — it can
    be injected directly into Qlib configs and evaluated by Qlib's data API.
    """

    name: str
    description: str
    expression: Optional[str] = None
    code: Optional[str] = None
    fields: list[str] = field(default_factory=list)
    source: str = "manual"  # manual | nl_pattern | rdagent

    def __post_init__(self) -> None:
        if not self.expression and not self.code:
            raise ValueError("FactorSpec requires `expression` or `code`")
        if self.expression and not self.fields:
            # best-effort: infer referenced $fields from the expression
            self.fields = sorted(set(re.findall(r"\$([a-z_]+)", self.expression)))

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "FactorSpec":
        return cls(**d)


@dataclass
class EventStudyConfig:
    """Config for EventStudy evaluator (pattern -> forward return distribution)."""

    market: str = "csi300"
    start_time: str = "2015-01-01"
    end_time: str = "2024-12-31"
    horizons: list[int] = field(default_factory=lambda: [1, 3, 5, 10, 20])


@dataclass
class BacktestConfig:
    """Config for PortfolioBacktest evaluator (factor -> IC + Topk portfolio)."""

    market: str = "csi300"
    benchmark: str = "SH000300"
    train_start: str = "2010-01-01"
    train_end: str = "2018-12-31"
    valid_start: str = "2019-01-01"
    valid_end: str = "2020-12-31"
    test_start: str = "2021-01-01"
    test_end: str = "2024-12-31"
    topk: int = 50
    n_drop: int = 5
