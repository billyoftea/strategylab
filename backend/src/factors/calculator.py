"""
因子计算模块 - 预计算常用因子
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Callable
from pathlib import Path
import json


class FactorCalculator:
    """因子计算器"""
    
    def __init__(self, data_manager):
        self.dm = data_manager
        self.factors_dir = Path(data_manager.factors_dir)
        
        # 注册因子函数
        self.factor_registry = {
            # 动量因子
            "mom_20": self._calc_momentum_20,
            "mom_60": self._calc_momentum_60,
            "mom_120": self._calc_momentum_120,
            "rsi_14": self._calc_rsi_14,
            
            # 波动因子
            "volatility_20": self._calc_volatility_20,
            "atr_14": self._calc_atr_14,
            
            # 量价因子
            "turnover": self._calc_turnover,
            "volume_ratio": self._calc_volume_ratio,
            
            # 估值因子（需要财务数据，暂不实现）
            # "pe": self._calc_pe,
            # "pb": self._calc_pb,
        }
    
    def calculate_all_factors(
        self, 
        stock_codes: List[str],
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        计算所有预置因子
        
        Returns:
            DataFrame with columns: code, date, factor1, factor2, ...
        """
        # 获取价格数据
        price_df = self.dm.get_price_data(stock_codes, start_date, end_date)
        
        if price_df.empty:
            return pd.DataFrame()
        
        # 按股票分组计算因子
        results = []
        
        for code in stock_codes:
            stock_df = price_df[price_df["code"] == code].copy()
            if len(stock_df) < 60:  # 需要足够的历史数据
                continue
            
            stock_df = stock_df.sort_values("date")
            
            # 计算每个因子
            for factor_name, factor_func in self.factor_registry.items():
                try:
                    stock_df[factor_name] = factor_func(stock_df)
                except Exception as e:
                    print(f"计算 {code} 的 {factor_name} 失败: {e}")
                    stock_df[factor_name] = np.nan
            
            results.append(stock_df)
        
        if not results:
            return pd.DataFrame()
        
        result_df = pd.concat(results, ignore_index=True)
        
        # 保存到文件
        self._save_factors(result_df, start_date, end_date)
        
        return result_df
    
    def _save_factors(self, df: pd.DataFrame, start_date: str, end_date: str):
        """保存因子数据到Parquet文件"""
        filename = f"factors_{start_date}_{end_date}.parquet"
        filepath = self.factors_dir / filename
        df.to_parquet(filepath, index=False)
        print(f"因子数据已保存: {filepath}")
    
    def load_factors(self, start_date: str, end_date: str) -> pd.DataFrame:
        """加载预计算的因子数据"""
        filename = f"factors_{start_date}_{end_date}.parquet"
        filepath = self.factors_dir / filename
        
        if not filepath.exists():
            return pd.DataFrame()
        
        return pd.read_parquet(filepath)
    
    # ========== 因子计算函数 ==========
    
    def _calc_momentum_20(self, df: pd.DataFrame) -> pd.Series:
        """20日动量"""
        return df["close"].pct_change(20)
    
    def _calc_momentum_60(self, df: pd.DataFrame) -> pd.Series:
        """60日动量"""
        return df["close"].pct_change(60)
    
    def _calc_momentum_120(self, df: pd.DataFrame) -> pd.Series:
        """120日动量"""
        return df["close"].pct_change(120)
    
    def _calc_rsi_14(self, df: pd.DataFrame) -> pd.Series:
        """14日RSI"""
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calc_volatility_20(self, df: pd.DataFrame) -> pd.Series:
        """20日波动率（年化）"""
        return df["close"].pct_change().rolling(window=20).std() * np.sqrt(252)
    
    def _calc_atr_14(self, df: pd.DataFrame) -> pd.Series:
        """14日ATR"""
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=14).mean()
    
    def _calc_turnover(self, df: pd.DataFrame) -> pd.Series:
        """换手率（需要流通股本数据，暂用成交量/成交额估算）"""
        # 简化处理：用成交量标准化
        return df["volume"] / df["volume"].rolling(window=60).mean()
    
    def _calc_volume_ratio(self, df: pd.DataFrame) -> pd.Series:
        """量比：当日成交量/前5日均量"""
        return df["volume"] / df["volume"].rolling(window=5).mean()
    
    def get_factor_list(self) -> List[Dict[str, str]]:
        """获取因子列表及说明"""
        return [
            {"name": "mom_20", "desc": "20日动量", "category": "动量"},
            {"name": "mom_60", "desc": "60日动量", "category": "动量"},
            {"name": "mom_120", "desc": "120日动量", "category": "动量"},
            {"name": "rsi_14", "desc": "14日RSI", "category": "动量"},
            {"name": "volatility_20", "desc": "20日波动率", "category": "波动"},
            {"name": "atr_14", "desc": "14日ATR", "category": "波动"},
            {"name": "turnover", "desc": "换手率", "category": "量价"},
            {"name": "volume_ratio", "desc": "量比", "category": "量价"},
        ]


if __name__ == "__main__":
    from data.manager import DataManager
    
    dm = DataManager()
    fc = FactorCalculator(dm)
    
    # 计算因子
    df = fc.calculate_all_factors(
        stock_codes=["000001", "000002"],
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    
    print(df.head())
    print(f"\n因子列表: {fc.get_factor_list()}")
