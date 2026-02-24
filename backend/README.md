# StrategyLab Backend

## 项目结构

```
backend/
├── src/
│   ├── data/
│   │   └── manager.py       # 数据管理器
│   ├── factors/
│   │   └── calculator.py    # 因子计算器
│   ├── backtest/
│   │   └── engine.py        # 回测引擎
│   └── analysis/
│       └── analyzer.py      # LLM分析器
├── data/                     # 本地数据存储
│   ├── raw/                 # 原始数据
│   ├── factors/             # 预计算因子
│   └── cache/               # 缓存
├── main.py                   # FastAPI主应用
└── pyproject.toml           # 依赖配置
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
poetry install
```

### 2. 配置环境变量

```bash
export DEEPSEEK_API_KEY="your-api-key"
```

### 3. 初始化数据

```bash
python -c "from src.data.manager import DataManager; dm = DataManager(); dm.update_stock_list()"
```

### 4. 启动服务

```bash
poetry run uvicorn main:app --reload
```

## API 文档

启动后访问: http://localhost:8000/docs

## 核心模块

### 数据管理器 (DataManager)

- 本地SQLite存储
- 支持股票列表、日线数据管理
- 自动更新日志

### 因子计算器 (FactorCalculator)

预置因子：
- 动量类: mom_20, mom_60, mom_120, rsi_14
- 波动类: volatility_20, atr_14
- 量价类: turnover, volume_ratio

### 回测引擎 (BacktestEngine)

- 基于Backtrader
- 支持多因子选股策略
- 自动调仓、权重配置

### LLM分析器 (LLMAnalyzer)

深度分析维度：
- 策略逻辑自洽性
- 市场环境适配度
- 风险识别
- 改进建议

## 数据更新策略

- 股票列表: 每周更新
- 日线数据: 每日收盘后更新
- 因子数据: 依赖价格数据更新后重算
