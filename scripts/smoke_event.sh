#!/bin/bash
# 真实数据烟测(WSL,需 strategylab env + cn_data 已就位)
# 跑一个手动表达式的事件研究 + 一个组合回测,验证整条链路。
set +e
source /home/xuang/miniconda3/etc/profile.d/conda.sh
conda activate strategylab
cd "$(dirname "$0")/.."

echo "=== offline 单测 ==="
python -m pytest -q tests/ 2>&1 | tail -10

echo ""
echo "=== 事件研究(手动表达式:收盘价上穿20日均线 后续收益)==="
python -m strategylab.cli pattern --expr '($close > Mean($close, 20))' --start 2020-01-01 --end 2024-12-31 2>&1 | tail -20

echo ""
echo "=== 组合回测(20日动量因子)==="
python -m strategylab.cli backtest --expr 'Mean($close, 20)' --topk 50 2>&1 | tail -10

echo ""
echo "=== 报告产物 ==="
ls -la reports/ 2>/dev/null
echo "SMOKE_DONE"
