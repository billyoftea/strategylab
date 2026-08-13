"""PortfolioBacktest evaluator (A+B) for a SINGLE factor.

MVP evaluates one factor at a time, rank-based, NO model training — the standard
single-factor evaluation: cross-sectional rank-IC + a Topk long-only equal-weight
portfolio. (Combining many factors with LightGBM, as RD-Agent's conf_baseline does,
is deferred — it serves a different purpose.)
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

import numpy as np
import pandas as pd

from ..data import init_qlib, load_features
from ..spec import BacktestConfig, FactorSpec


def _pivot(series: pd.Series) -> pd.DataFrame:
    df = series.unstack(level=0)
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


@dataclass
class PortfolioResult:
    summary: dict
    daily_ic: pd.Series          # rank IC per day
    port_return: pd.Series       # portfolio daily return
    bench_return: pd.Series      # benchmark daily return


def run_portfolio_backtest(
    spec: FactorSpec, cfg: Optional[BacktestConfig] = None
) -> PortfolioResult:
    if not spec.expression:
        raise ValueError("PortfolioBacktest requires FactorSpec.expression")
    cfg = cfg or BacktestConfig()
    init_qlib()

    raw = load_features(
        [spec.expression, "$close"],
        market=cfg.market,
        start_time=cfg.train_start,
        end_time=cfg.test_end,
    )
    factor = _pivot(raw.iloc[:, 0])
    close = _pivot(raw["$close"])

    # next-day return: return earned from t to t+1
    fwd1 = close.shift(-1) / close - 1

    # ---- IC: daily cross-sectional rank correlation (factor vs next-day return) ----
    ic_records = []
    for date in factor.index:
        f = factor.loc[date]
        r = fwd1.reindex(index=factor.index).loc[date]
        m = f.notna() & r.notna()
        if m.sum() >= 10:
            ic_records.append((date, f[m].rank().corr(r[m].rank())))
    daily_ic = pd.Series(dict(ic_records)).dropna()

    # ---- Topk long-only equal-weight portfolio ----
    port_records = []
    for date in factor.index:
        f = factor.loc[date]
        r = fwd1.reindex(index=factor.index).loc[date]
        m = f.notna() & r.notna()
        if m.sum() >= cfg.topk:
            topk = f[m].nlargest(cfg.topk).index
            port_records.append((date, float(r.loc[topk].mean())))
    port_return = pd.Series(dict(port_records)).dropna()

    # ---- benchmark: csi300 index ----
    try:
        from qlib.data import D

        bench = D.features(
            [cfg.benchmark], ["$close"],
            start_time=str(factor.index[0].date()),
            end_time=str(factor.index[-1].date()),
        )["$close"]
        bench_ret = bench.pct_change().shift(-1)
        bench_ret.index = pd.to_datetime(bench_ret.index)
        bench_return = bench_return_series = bench_ret.reindex(port_return.index).fillna(0.0)
    except Exception:
        bench_return = pd.Series(0.0, index=port_return.index)

    def _metrics(ret: pd.Series) -> dict:
        if ret.empty:
            return {"ann_return": None, "ann_vol": None, "sharpe": None, "max_dd": None}
        ann_ret = float(ret.mean() * 252)
        ann_vol = float(ret.std() * np.sqrt(252))
        sharpe = float(ann_ret / ann_vol) if ann_vol else float("nan")
        cum = (1 + ret).cumprod()
        max_dd = float((cum / cum.cummax() - 1).min())
        return {"ann_return": ann_ret, "ann_vol": ann_vol, "sharpe": sharpe, "max_dd": max_dd}

    summary = {
        "type": "portfolio_backtest",
        "factor": spec.to_dict(),
        "config": asdict(cfg),
        "n_days": int(len(port_return)),
        "rank_ic_mean": float(daily_ic.mean()) if not daily_ic.empty else None,
        "rank_ic_std": float(daily_ic.std()) if not daily_ic.empty else None,
        "rank_icir": float(daily_ic.mean() / daily_ic.std()) if not daily_ic.empty and daily_ic.std() else None,
        "portfolio": _metrics(port_return),
        "benchmark": _metrics(bench_return),
        "excess": _metrics(port_return - bench_return.reindex(port_return.index).fillna(0.0)),
    }
    return PortfolioResult(summary=summary, daily_ic=daily_ic, port_return=port_return, bench_return=bench_return)
