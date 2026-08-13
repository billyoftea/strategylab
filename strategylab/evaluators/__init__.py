"""Evaluators: turn a FactorSpec into a result/report.

- EventStudy: pattern fires -> forward N-day return distribution (for K-line patterns)
- PortfolioBacktest: factor -> IC + Topk portfolio (for general factors), via Qlib qrun
"""
from .event_study import EventStudyResult, run_event_study
from .portfolio import PortfolioResult, run_portfolio_backtest

__all__ = [
    "EventStudyResult",
    "run_event_study",
    "PortfolioResult",
    "run_portfolio_backtest",
]
