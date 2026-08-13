"""Fetch crypto daily OHLCV via ccxt, multi-exchange fallback (binance->okx->gate).
China network may block some exchanges; try each until one works.
Saves one parquet per symbol to ./data/.
"""
import os
import time
import ccxt
import pandas as pd

SYMBOLS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"]
TIMEFRAME = "1d"
DAYS = 365 * 3
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def make_exchanges():
    """Candidate exchanges in fallback order."""
    return [
        ("binance", ccxt.binance()),
        ("okx", ccxt.okx()),
        ("gate", ccxt.gate()),
    ]


def fetch_one(ex, symbol, days):
    since = ex.milliseconds() - days * 24 * 60 * 60 * 1000
    out = []
    while since < ex.milliseconds():
        try:
            chunk = ex.fetch_ohlcv(symbol, TIMEFRAME, since, limit=1000)
        except Exception as e:
            raise RuntimeError(f"{symbol} fetch error: {e}")
        if not chunk:
            break
        out += chunk
        since = chunk[-1][0] + 1
        time.sleep(ex.rateLimit / 1000.0)
    df = pd.DataFrame(out, columns=["ts", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["ts"], unit="ms")
    df = df.drop_duplicates("ts").sort_values("ts")
    df = df.set_index("datetime").drop(columns=["ts"])
    return df


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    exchanges = make_exchanges()

    # pick the first exchange that can actually reach the market
    ex_name, ex = None, None
    for name, e in exchanges:
        try:
            e.load_markets()
            # probe: fetch 1 bar
            e.fetch_ohlcv(SYMBOLS[0], TIMEFRAME, limit=1)
            ex_name, ex = name, e
            print(f"using exchange: {name}")
            break
        except Exception as e2:
            print(f"exchange {name} unreachable: {str(e2)[:80]}")

    if ex is None:
        raise RuntimeError("所有候选交易所都连不上(可能被墙)。需要代理,或提供你自己的 crypto parquet。")

    for sym in SYMBOLS:
        fname = sym.replace("/", "")
        try:
            df = fetch_one(ex, sym, DAYS)
            path = os.path.join(OUT_DIR, f"{fname}.parquet")
            df.to_parquet(path)
            print(f"{sym}: {len(df)} bars  {df.index[0].date()}..{df.index[-1].date()}  -> {path}")
        except Exception as e:
            print(f"{sym}: FAIL ({str(e)[:100]})")

    print("FETCH_DONE")


if __name__ == "__main__":
    main()
