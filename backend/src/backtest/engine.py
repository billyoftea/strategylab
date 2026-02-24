"""
回测引擎 - 基于Backtrader的策略执行
"""
import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BacktestResult:
    """回测结果数据结构"""
    # 收益指标
    total_return: float
    annual_return: float
    
    # 风险指标
    max_drawdown: float
    max_drawdown_duration: int
    volatility: float
    sharpe_ratio: float
    
    # 交易统计
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_holding_days: float
    
    # 曲线数据
    equity_curve: List[Dict]
    trades: List[Dict]
    monthly_returns: Dict[str, float]
    
    # 基准对比
    benchmark_return: float
    alpha: float
    beta: float


class FactorDataFeed(bt.feeds.PandasData):
    """自定义数据源，支持因子数据"""
    lines = ('mom_20', 'mom_60', 'mom_120', 'rsi_14', 
             'volatility_20', 'atr_14', 'turnover', 'volume_ratio')
    
    params = (
        ('mom_20', -1),
        ('mom_60', -1),
        ('mom_120', -1),
        ('rsi_14', -1),
        ('volatility_20', -1),
        ('atr_14', -1),
        ('turnover', -1),
        ('volume_ratio', -1),
    )


class StrategyTemplate(bt.Strategy):
    """策略模板基类"""
    
    params = (
        ('factor_name', 'mom_60'),
        ('top_n', 50),
        ('rebalance_freq', 'monthly'),  # daily, weekly, monthly
        ('weighting', 'equal'),  # equal, market_cap, factor
        ('max_position', 0.1),
        ('stop_loss', None),
    )
    
    def __init__(self):
        self.orders = {}
        self.trade_log = []
        self.rebalance_day = 1  # 每月/周第几天调仓
        
    def next(self):
        """每个bar执行"""
        # 判断是否需要调仓
        if not self._should_rebalance():
            return
        
        # 获取当前持仓
        current_positions = {d._name: self.getposition(d).size 
                            for d in self.datas if self.getposition(d)}
        
        # 计算目标持仓
        target_stocks = self._select_stocks()
        target_weights = self._calculate_weights(target_stocks)
        
        # 执行调仓
        self._execute_rebalance(current_positions, target_stocks, target_weights)
    
    def _should_rebalance(self) -> bool:
        """判断是否需要调仓"""
        if self.params.rebalance_freq == 'daily':
            return True
        elif self.params.rebalance_freq == 'weekly':
            return self.data.datetime.date(0).weekday() == 0
        elif self.params.rebalance_freq == 'monthly':
            return self.data.datetime.date(0).day == self.rebalance_day
        return False
    
    def _select_stocks(self) -> List[str]:
        """选股逻辑 - 基于因子排序"""
        # 获取所有股票的当前因子值
        factor_values = {}
        for d in self.datas:
            factor_val = getattr(d, self.params.factor_name)[0]
            if not np.isnan(factor_val):
                factor_values[d._name] = factor_val
        
        # 按因子值排序，取前N
        sorted_stocks = sorted(factor_values.items(), 
                              key=lambda x: x[1], 
                              reverse=True)
        return [s[0] for s in sorted_stocks[:self.params.top_n]]
    
    def _calculate_weights(self, stocks: List[str]) -> Dict[str, float]:
        """计算权重"""
        if self.params.weighting == 'equal':
            weight = 1.0 / len(stocks) if stocks else 0
            return {s: weight for s in stocks}
        # TODO: 支持其他加权方式
        return {s: 1.0 / len(stocks) for s in stocks}
    
    def _execute_rebalance(self, current: Dict, target: List, weights: Dict):
        """执行调仓"""
        # 卖出不在目标列表的股票
        for stock, size in current.items():
            if stock not in target and size > 0:
                data = self.getdatabyname(stock)
                self.close(data=data)
        
        # 买入/调整目标股票
        portfolio_value = self.broker.getvalue()
        
        for stock in target:
            data = self.getdatabyname(stock)
            target_value = portfolio_value * weights[stock]
            target_size = int(target_value / data.close[0])
            
            current_size = self.getposition(data).size
            
            if target_size > current_size:
                self.buy(data=data, size=target_size - current_size)
            elif target_size < current_size:
                self.sell(data=data, size=current_size - target_size)
    
    def notify_trade(self, trade):
        """记录交易"""
        if trade.isclosed:
            self.trade_log.append({
                'date': self.data.datetime.date(0).isoformat(),
                'stock': trade.data._name,
                'size': trade.size,
                'price': trade.price,
                'pnl': trade.pnlcomm,
            })


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, data_manager, factor_calculator):
        self.dm = data_manager
        self.fc = factor_calculator
        
    def run_backtest(
        self,
        strategy_params: Dict,
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000.0
    ) -> BacktestResult:
        """
        执行回测
        
        Args:
            strategy_params: 策略参数
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金
        """
        # 获取股票池（这里简化处理，用沪深300成分股或全A）
        stock_list = self.dm.get_stock_list()
        
        # 过滤：排除ST、退市、上市不足一年的股票
        stock_codes = stock_list['code'].tolist()[:500]  # 限制数量
        
        # 获取因子数据
        factor_df = self.fc.calculate_all_factors(stock_codes, start_date, end_date)
        
        if factor_df.empty:
            raise ValueError("无法获取因子数据")
        
        # 初始化Backtrader
        cerebro = bt.Cerebro()
        
        # 添加策略
        cerebro.addstrategy(StrategyTemplate, **strategy_params)
        
        # 添加数据
        for code in stock_codes:
            stock_df = factor_df[factor_df['code'] == code].copy()
            if len(stock_df) < 60:
                continue
            
            stock_df = stock_df.sort_values('date')
            stock_df.set_index('date', inplace=True)
            
            # 确保列名正确
            required_cols = ['open', 'high', 'low', 'close', 'volume', 
                           'mom_20', 'mom_60', 'mom_120', 'rsi_14',
                           'volatility_20', 'atr_14', 'turnover', 'volume_ratio']
            
            for col in required_cols:
                if col not in stock_df.columns:
                    stock_df[col] = 0
            
            feed = FactorDataFeed(
                dataname=stock_df,
                name=code,
                datetime=None,
                open=0,
                high=1,
                low=2,
                close=3,
                volume=4,
                openinterest=-1,
                mom_20=5,
                mom_60=6,
                mom_120=7,
                rsi_14=8,
                volatility_20=9,
                atr_14=10,
                turnover=11,
                volume_ratio=12,
            )
            cerebro.adddata(feed)
        
        # 设置初始资金
        cerebro.broker.setcash(initial_capital)
        
        # 设置手续费（简化）
        cerebro.broker.setcommission(commission=0.001)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='returns')
        
        # 运行回测
        results = cerebro.run()
        strat = results[0]
        
        # 提取结果
        return self._extract_results(strat, initial_capital, start_date, end_date)
    
    def _extract_results(
        self, 
        strat: bt.Strategy, 
        initial_capital: float,
        start_date: str,
        end_date: str
    ) -> BacktestResult:
        """提取回测结果"""
        final_value = strat.broker.getvalue()
        total_return = (final_value - initial_capital) / initial_capital
        
        # 计算年化收益
        days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
        annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
        
        # 获取分析器结果
        sharpe = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        trades = strat.analyzers.trades.get_analysis()
        
        # 构建权益曲线
        equity_curve = []
        # TODO: 从strat中获取每日净值
        
        # 交易统计
        total_trades = trades.get('total', {}).get('total', 0) if trades else 0
        won_trades = trades.get('won', {}).get('total', 0) if trades else 0
        win_rate = won_trades / total_trades if total_trades > 0 else 0
        
        # 计算盈亏比
        gross_pnl = trades.get('pnl', {}).get('gross', {}).get('total', 0) if trades else 0
        net_pnl = trades.get('pnl', {}).get('net', {}).get('total', 0) if trades else 0
        
        return BacktestResult(
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=drawdown.get('max', {}).get('drawdown', 0),
            max_drawdown_duration=drawdown.get('max', {}).get('len', 0),
            volatility=0,  # TODO: 计算波动率
            sharpe_ratio=sharpe.get('sharperatio', 0),
            total_trades=total_trades,
            win_rate=win_rate,
            profit_factor=0,  # TODO
            avg_holding_days=0,  # TODO
            equity_curve=equity_curve,
            trades=strat.trade_log,
            monthly_returns={},
            benchmark_return=0,  # TODO: 沪深300同期收益
            alpha=0,  # TODO
            beta=0,  # TODO
        )


if __name__ == "__main__":
    from data.manager import DataManager
    from factors.calculator import FactorCalculator
    
    dm = DataManager()
    fc = FactorCalculator(dm)
    engine = BacktestEngine(dm, fc)
    
    # 测试回测
    result = engine.run_backtest(
        strategy_params={
            'factor_name': 'mom_60',
            'top_n': 50,
            'rebalance_freq': 'monthly',
        },
        start_date='2024-01-01',
        end_date='2024-06-30',
    )
    
    print(f"总收益: {result.total_return:.2%}")
    print(f"年化收益: {result.annual_return:.2%}")
    print(f"最大回撤: {result.max_drawdown:.2%}")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
