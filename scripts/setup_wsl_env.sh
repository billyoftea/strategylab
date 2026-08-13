#!/bin/bash
# StrategyLab WSL 环境构建:conda env strategylab + pyqlib 等
set +e
source /home/xuang/miniconda3/etc/profile.d/conda.sh
echo "=== creating env strategylab (py3.11, conda-forge) ==="
conda create -n strategylab python=3.11 -y -c conda-forge --override-channels 2>&1 | tail -3
conda activate strategylab
pip install --upgrade pip
echo "=== installing deps ==="
pip install pyqlib lightgbm matplotlib typer openai jinja2 pyarrow 2>&1 | tail -10
echo "=== verify ==="
python -c "import qlib, lightgbm, typer, openai; print('qlib', qlib.__version__, 'OK')"
echo "SETUP_DONE"
