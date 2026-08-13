"""Simple MA-crossover trend strategy (vnpy_ctastrategy).
Used as MVP to validate the factor -> vnpy realistic-backtest chain on crypto.
Long when fast MA > slow MA; flat when fast < slow.
"""
from vnpy_ctastrategy import CtaTemplate, StopOrder, TickData, BarData, TradeData, OrderData
from vnpy.trader.utility import ArrayManager


class MaCrossStrategy(CtaTemplate):
    author = "xab_vnpy"

    fast_window = 10
    slow_window = 30
    target_value = 30000  # USD notional per position; volume = target_value / price

    parameters = ["fast_window", "slow_window", "target_value"]
    variables = ["fast_ma", "slow_ma", "in_pos"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.am = ArrayManager(size=self.slow_window + 5)
        self.fast_ma = 0.0
        self.slow_ma = 0.0
        self.in_pos = False

    def on_init(self):
        self.write_log("策略初始化")
        # 不调 load_bar(它依赖 vnpy 数据库);ArrayManager 在 on_bar 里用回测 bar 自然预热

    def on_start(self):
        self.write_log("策略启动")

    def on_stop(self):
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        pass

    def on_bar(self, bar: BarData):
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.fast_ma = self.am.sma(self.fast_window)
        self.slow_ma = self.am.sma(self.slow_window)

        bull = self.fast_ma > self.slow_ma
        vol = max(1, int(self.target_value / bar.close_price))

        if bull and self.pos == 0:
            self.buy(bar.close_price, vol)
            self.in_pos = True
        elif (not bull) and self.pos > 0:
            self.sell(bar.close_price, self.pos)
            self.in_pos = False

        self.put_event()
