"""
数据管理模块 - 负责本地数据存储和更新
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd
import akshare as ak


class DataManager:
    """本地数据管理器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.factors_dir = self.data_dir / "factors"
        self.cache_dir = self.data_dir / "cache"
        
        # 创建目录
        for d in [self.raw_dir, self.factors_dir, self.cache_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self.db_path = self.data_dir / "strategylab.db"
        self._init_db()
    
    def _init_db(self):
        """初始化SQLite数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_prices (
                    code TEXT,
                    date TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    amount REAL,
                    adj_factor REAL,
                    PRIMARY KEY (code, date)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_list (
                    code TEXT PRIMARY KEY,
                    name TEXT,
                    industry TEXT,
                    market TEXT,
                    list_date TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_update_log (
                    table_name TEXT PRIMARY KEY,
                    last_update TEXT,
                    record_count INTEGER
                )
            """)
    
    def update_stock_list(self) -> pd.DataFrame:
        """更新股票列表"""
        print("正在更新股票列表...")
        
        # 获取A股列表
        df = ak.stock_zh_a_spot_em()
        
        # 标准化列名
        df = df[["代码", "名称", "所属行业"]].copy()
        df.columns = ["code", "name", "industry"]
        
        # 判断市场
        df["market"] = df["code"].apply(
            lambda x: "sh" if x.startswith("6") else "sz"
        )
        df["list_date"] = None
        
        # 保存到数据库
        with sqlite3.connect(self.db_path) as conn:
            df.to_sql("stock_list", conn, if_exists="replace", index=False)
            self._log_update("stock_list", len(df))
        
        print(f"股票列表更新完成: {len(df)} 只")
        return df
    
    def update_price_data(
        self, 
        stock_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> None:
        """
        更新日线数据
        
        Args:
            stock_code: 股票代码，None则更新全部
            start_date: 开始日期 (YYYY-MM-DD)，None则自动判断
            end_date: 结束日期 (YYYY-MM-DD)，None则为昨天
        """
        if end_date is None:
            end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 获取股票列表
        if stock_code:
            stocks = [(stock_code, "")]
        else:
            stocks = self.get_stock_list()
            stocks = [(row["code"], row["name"]) for _, row in stocks.iterrows()]
        
        total = len(stocks)
        print(f"开始更新 {total} 只股票的日线数据...")
        
        for i, (code, name) in enumerate(stocks, 1):
            try:
                # 获取数据
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start_date or "20200101",
                    end_date=end_date.replace("-", ""),
                    adjust="qfq"  # 前复权
                )
                
                if df.empty:
                    continue
                
                # 标准化列名
                df = df[["日期", "开盘", "最高", "最低", "收盘", "成交量", "成交额"]].copy()
                df.columns = ["date", "open", "high", "low", "close", "volume", "amount"]
                df["code"] = code
                df["adj_factor"] = 1.0  # 前复权已处理
                
                # 保存到数据库
                with sqlite3.connect(self.db_path) as conn:
                    # 删除旧数据
                    conn.execute("DELETE FROM stock_prices WHERE code = ?", (code,))
                    # 插入新数据
                    df.to_sql("stock_prices", conn, if_exists="append", index=False)
                
                if i % 100 == 0:
                    print(f"已更新 {i}/{total} 只股票")
                    
            except Exception as e:
                print(f"更新 {code} 失败: {e}")
                continue
        
        self._log_update("stock_prices", self._count_records("stock_prices"))
        print(f"日线数据更新完成")
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql("SELECT * FROM stock_list", conn)
        return df
    
    def get_price_data(
        self, 
        stock_codes: List[str],
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取日线数据
        
        Returns:
            DataFrame with columns: code, date, open, high, low, close, volume, amount
        """
        codes_str = "','".join(stock_codes)
        query = f"""
            SELECT * FROM stock_prices 
            WHERE code IN ('{codes_str}')
            AND date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY code, date
        """
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql(query, conn)
        
        df["date"] = pd.to_datetime(df["date"])
        return df
    
    def _log_update(self, table_name: str, record_count: int):
        """记录更新日志"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO data_update_log 
                   (table_name, last_update, record_count) 
                   VALUES (?, ?, ?)""",
                (table_name, datetime.now().isoformat(), record_count)
            )
    
    def _count_records(self, table_name: str) -> int:
        """统计记录数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]
    
    def get_update_status(self) -> Dict[str, Any]:
        """获取数据更新状态"""
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql("SELECT * FROM data_update_log", conn)
        return df.to_dict("records")


if __name__ == "__main__":
    # 测试
    dm = DataManager()
    
    # 更新股票列表
    dm.update_stock_list()
    
    # 更新几只股票的日线数据测试
    dm.update_price_data("000001", start_date="2024-01-01")
    
    # 查询数据
    df = dm.get_price_data(["000001"], "2024-01-01", "2024-12-31")
    print(df.head())
