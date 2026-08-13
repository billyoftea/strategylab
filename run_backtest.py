"""Run vnpy CTA backtest on one crypto symbol (default ETHUSDT) using parquet data fed directly.
Demonstrates realistic backtest (fees + slippage) on the vnpy engine.
"""
import os
import sys
from datetime import datetime

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from vnpy.trader.constant import Interval
from vnpy_ctastrategy.backtesting import BacktestingEngine

from data_loader import load_bar_data_from_parquet, vt_symbol_for, EXCHANGE
from strategy import MaCrossStrategy

SYMBOL = os.environ.get("VNPY_SYMBOL", "ETHUSDT")
CAPITAL = 100000
RATE = 0.001        # 0.1% taker fee
SLIPPAGE = 0.5      # ~0.5 USD
SIZE = 1.0          # spot: 1 unit = 1 coin
PRICETICK = 0.01
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")


def main():
    vtsym = vt_symbol_for(SYMBOL)
    bars = load_bar_data_from_parquet(SYMBOL)
    print(f"{SYMBOL}: {len(bars)} bars ({bars[0].datetime.date()}..{bars[-1].datetime.date()})  vt={vtsym}  exchange={EXCHANGE}")

    engine = BacktestingEngine()
    engine.set_parameters(
        vt_symbol=vtsym,
        interval=Interval.DAILY,
        start=bars[0].datetime,
        end=bars[-1].datetime,
        rate=RATE,
        slippage=SLIPPAGE,
        size=SIZE,
        pricetick=PRICETICK,
        capital=CAPITAL,
    )
    engine.add_strategy(MaCrossStrategy, {"fast_window": 10, "slow_window": 30, "target_value": 30000})

    # bypass DB: feed history_data directly
    engine.history_data = bars
    engine.load_data = lambda *a, **k: None  # safety no-op in case anything calls it

    engine.run_backtesting()
    df = engine.calculate_result()
    stats = engine.calculate_statistics(output=False)

    os.makedirs(OUT_DIR, exist_ok=True)
    base = f"{SYMBOL}_MAcross_{bars[0].datetime.date()}_{bars[-1].datetime.date()}"

    # stats
    print("\n=== 回测统计 ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # save daily df
    if df is not None and len(df):
        csv_path = os.path.join(OUT_DIR, f"{base}.csv")
        df.to_csv(csv_path)
        # NAV plot (total_balance)
        col = "total_balance" if "total_balance" in df.columns else df.columns[-1]
        nav = df[col]
        nav = nav / nav.iloc[0]
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(nav.index, nav.values, color="#1f77b4", linewidth=1.8)
        ax.set_title(f"vnpy 回测净值 — {SYMBOL} MA交叉(realistic, fee={RATE:.2%})")
        ax.set_ylabel("净值 (start=1)"); ax.grid(True, alpha=0.3)
        fig.autofmt_xdate(); fig.tight_layout()
        png = os.path.join(OUT_DIR, f"{base}.png")
        fig.savefig(png, dpi=110); plt.close(fig)
        print(f"\n报告: {png}\nCSV : {csv_path}")
    else:
        print("无逐日结果(可能策略没交易)")


if __name__ == "__main__":
    main()
