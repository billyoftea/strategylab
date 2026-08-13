"""EventStudy evaluator (option C): a pattern fires -> forward N-day return distribution.

Answers: "after this K-line pattern appears, does the stock tend to go up? by how
much? with what probability?" This is a small self-written backtester (pure pandas
on Qlib-loaded OHLC) — it does NOT use Qlib's portfolio backtest.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Optional

import numpy as np
import pandas as pd

from ..data import init_qlib, load_features
from ..spec import EventStudyConfig, FactorSpec


def _to_date_x_symbol(series: pd.Series) -> pd.DataFrame:
    """series indexed by (instrument, datetime) -> DataFrame[date, symbol]."""
    df = series.unstack(level=0)
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


@dataclass
class EventStudyResult:
    summary: dict  # JSON-serialisable
    close: pd.DataFrame
    trigger: pd.DataFrame
    fwd_returns: dict[int, pd.DataFrame]  # horizon -> forward-return frame


def run_event_study(
    spec: FactorSpec, cfg: Optional[EventStudyConfig] = None
) -> EventStudyResult:
    if not spec.expression:
        raise ValueError("EventStudy requires FactorSpec.expression")
    cfg = cfg or EventStudyConfig()
    init_qlib()

    # Load close + the pattern signal together (one Qlib call).
    raw = load_features(
        ["$close", spec.expression],
        market=cfg.market,
        start_time=cfg.start_time,
        end_time=cfg.end_time,
    )
    close = _to_date_x_symbol(raw["$close"])
    signal = _to_date_x_symbol(raw.iloc[:, 1])
    signal = signal.reindex_like(close)

    trigger = signal.fillna(0).astype(float) != 0  # boolean patterns -> 0/1

    fwd_returns: dict[int, pd.DataFrame] = {}
    by_horizon: dict[int, dict] = {}
    for h in cfg.horizons:
        fwd = close.shift(-h) / close - 1
        fwd_returns[h] = fwd
        vals = fwd.values[trigger.values]
        vals = vals[~np.isnan(vals)]
        if vals.size == 0:
            by_horizon[h] = {"count": 0, "mean": None, "median": None,
                             "win_rate": None, "std": None, "t_stat": None}
            continue
        mean = float(vals.mean())
        std = float(vals.std(ddof=1)) if vals.size > 1 else float("nan")
        tstat = (mean / (std / math.sqrt(vals.size))) if std and not np.isnan(std) else float("nan")
        by_horizon[h] = {
            "count": int(vals.size),
            "mean": mean,
            "median": float(np.median(vals)),
            "win_rate": float((vals > 0).mean()),
            "std": std,
            "t_stat": tstat,
        }

    summary = {
        "type": "event_study",
        "factor": spec.to_dict(),
        "config": asdict(cfg),
        "n_trigger_events": int(trigger.values.sum()),
        "n_symbols_covered": int((trigger.sum(axis=0) > 0).sum()),
        "by_horizon": {str(k): v for k, v in by_horizon.items()},
    }
    return EventStudyResult(summary=summary, close=close, trigger=trigger, fwd_returns=fwd_returns)
