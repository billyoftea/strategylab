"""parquet OHLCV -> vnpy BarData. Bypasses vnpy DB (feed engine.history_data directly)."""
import os
import pandas as pd
from vnpy.trader.object import BarData
from vnpy.trader.constant import Exchange, Interval

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _crypto_exchange() -> Exchange:
    """Pick any available Exchange enum member (crypto gateways not installed,
    so BINANCE etc. may be absent). For pure backtest the exchange is just a label."""
    for name in ("BINANCE", "OKX", "GATE", "BYBIT", "COINBASE", "KRAKEN"):
        if hasattr(Exchange, name):
            return getattr(Exchange, name)
    return list(Exchange)[0]


EXCHANGE = _crypto_exchange()


def load_bar_data_from_parquet(symbol: str, data_dir: str = DATA_DIR) -> list:
    """Load one symbol's parquet OHLCV -> sorted list[BarData]."""
    path = os.path.join(data_dir, f"{symbol}.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(f"missing {path} — run fetch_data.py first")
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    bars: list[BarData] = []
    for dt, row in df.iterrows():
        bars.append(BarData(
            gateway_name="backtest",
            symbol=symbol,
            exchange=EXCHANGE,
            datetime=dt.to_pydatetime().replace(tzinfo=None),  # naive to match engine start/end
            interval=Interval.DAILY,
            open_price=float(row["open"]),
            high_price=float(row["high"]),
            low_price=float(row["low"]),
            close_price=float(row["close"]),
            volume=float(row["volume"]),
            turnover=0.0,
            open_interest=0.0,
        ))
    return bars


def vt_symbol_for(symbol: str) -> str:
    return f"{symbol}.{EXCHANGE.value}"


if __name__ == "__main__":
    print("EXCHANGE =", EXCHANGE)
    for s in ("BTCUSDT", "ETHUSDT"):
        try:
            b = load_bar_data_from_parquet(s)
            print(f"{s}: {len(b)} bars, {b[0].datetime.date()}..{b[-1].datetime.date()}, vt={vt_symbol_for(s)}")
        except FileNotFoundError as e:
            print(e)
