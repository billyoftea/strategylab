# StrategyLab

基于 **RD-Agent + Qlib** 的因子 / K 线形态回测实验室。
**一个回测引擎 + 多个因子来源**(手动表达式 / 自然语言生成形态 / RD-Agent 自主),在沪深300 上回测,出标准化报告。

> 核心思想:**K 线形态本质就是因子**。所以形态回测复用因子引擎,不造两套。

## ✅ 状态:MVP 已完成 + 真实数据验证(2026-08-13)

| 能力 | 命令 | 状态 |
|---|---|---|
| 事件研究(形态→未来 N 天收益) | `pattern --expr` / `--nl` | ✅ 真实数据跑通 |
| 组合回测(因子→IC+Topk) | `backtest --expr` | ✅ 真实数据跑通 |
| 自然语言生成形态 | `pattern --nl` | ✅ 代码就绪,需 DEEPSEEK key 才能实跑 |

## 运行环境(均已就位)
- WSL `Ubuntu-24.04`,conda env **`strategylab`**(pyqlib 0.9.7 + lightgbm)
- 数据:Qlib `~/.qlib/qlib_data/cn_data`(CSI300,已下载)
- 文件:Windows 桌板 `strategylab\`,WSL 经 `/mnt/c/...` 执行
- NL 形态:DeepSeek(复用 `~/rdagent_work/.env` 的 `DEEPSEEK_API_KEY`)

## 使用

```bash
wsl -d Ubuntu-24.04
source ~/miniconda3/etc/profile.d/conda.sh && conda activate strategylab
cd /mnt/c/Users/xu.ang/Desktop/strategylab

# ① 事件研究:某形态出现后,未来 1/3/5/10/20 天收益分布
python -m strategylab.cli pattern --expr '($close > Mean($close, 20))'
python -m strategylab.cli pattern --nl "锤子线"            # 自然语言(需 DeepSeek key)

# ② 组合回测:因子 Rank IC + Topk 多头组合
python -m strategylab.cli backtest --expr 'Mean($close, 20)' --topk 50
```
报告输出:`reports/<run>/report.md` + `<run>.png` + `summary.json`。

## 真实数据烟测结果(csi300)
**事件研究**(收盘>20日均线):触发 27087 次/321 只;前瞻收益 1d **+0.07%(t=4.1)** / 5d **+0.27%(t=6.2)** / 20d **+1.73%(t=18.4)** —— 正向显著(动量直觉)。
**组合回测**(20日均价因子,Topk50):Rank IC 0.004 / 年化 11.68% / 夏普 0.45 / 回撤 -48%(因子朴素,IC 弱属正常)。
**离线单测**:4 passed。

## 架构
```
来源(手动 / NL形态 / RD-Agent[Phase2]) → FactorSpec(统一契约) → 引擎 → 报告
                                                       ├─ EventStudy(形态:前瞻收益分布)
                                                       └─ PortfolioBacktest(因子:IC+Topk)
```
详见 [DESIGN.md](./DESIGN.md)。

## 后置(Phase 2/3)
- RD-Agent 自主来源(包 `fin_factor`)、形态组合回测、事件研究增强
- 数据导入:NAS parquet → Qlib `.bin`(dump_bin)
