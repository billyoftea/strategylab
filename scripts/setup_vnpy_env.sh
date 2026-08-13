#!/bin/bash
# Path B crypto MVP: 建 vnpy 环境
set +e
source /home/xuang/miniconda3/etc/profile.d/conda.sh
echo "=== create env vnpy (py3.11) ==="
conda create -n vnpy python=3.11 -y -c conda-forge --override-channels 2>&1 | tail -3
conda activate vnpy
pip install --upgrade pip
echo "=== install vnpy + cta/portfolio + ccxt ==="
pip install vnpy vnpy_ctastrategy vnpy_portfoliostrategy ccxt pandas matplotlib 2>&1 | tail -20
echo "=== verify ==="
python -c "import vnpy; from vnpy_ctastrategy.backtesting import BacktestingEngine; print('vnpy_cta OK')"
python -c "from vnpy_portfoliostrategy.backtesting import BacktestingEngine as PE; print('vnpy_portfolio OK')" 2>&1 | tail -2
python -c "import ccxt; print('ccxt', ccxt.__version__)"
echo "SETUP_DONE"
