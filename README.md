# xab_vnpy

自写因子层(**xab**)+ **vnpy** 真实回测/实盘。crypto MVP 已跑通。

## 架构
```
fetch_data.py   ccxt(binance) → parquet(5 币日线)
data_loader.py  parquet → vnpy BarData(绕过 DB,直接喂 engine.history_data)
strategy.py     MA 交叉 CTA 趋势策略(MVP 示例)
run_backtest.py vnpy_ctastrategy 真实回测(手续费 + 滑点)→ 统计 + 净值图
```

## 运行(WSL)
```bash
wsl -d Ubuntu-24.04
source ~/miniconda3/etc/profile.d/conda.sh && conda activate vnpy
cd /mnt/c/Users/xu.ang/Desktop/xab_vnpy
python fetch_data.py                        # 取数(5 币 ×3 年日线)
python run_backtest.py                      # ETH MA 交叉回测
VNPY_SYMBOL=BTCUSDT python run_backtest.py  # 换币
```
报告输出 `reports/`。环境:WSL conda env `vnpy`(vnpy 4.4 + vnpy_ctastrategy + ccxt + pyarrow)。

## 状态
- ✅ MVP:单币 CTA 趋势回测(真实摩擦:手续费 0.1% + 滑点)。ETH(2023–2026)年化 ~5.6% / 夏普 0.48 / 回撤 15%。
- ⏳ 下一步:portfolio 截面因子(vnpy_portfoliostrategy)、接 xab 因子层、实盘(vnpy_binance)。

## vnpy 4.x 关键坑
- 数据**绕过 DB**:没装 vnpy_sqlite → parquet 转 BarData 后**直接赋值 `engine.history_data`**;策略 `on_init` **不能调 `load_bar()`**(它走 DB)。
- `Exchange.BINANCE` 不存在(没装 crypto 网关)→ 动态挑任一 Exchange 成员(回测里只是标签)。
- env 要带 `pyarrow` 才能存 parquet。

## 关联
- 因子研究层:xab(`../xab`)。
