"""
简化版FastAPI - 先实现数据获取
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import sys
import json

# 添加src到路径
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

app = FastAPI(
    title="StrategyLab API",
    description="基于LLM的A股策略验证工具",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 数据模型 ==========

class StrategyParseRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    current_params: Optional[Dict] = {}


class StrategyParseResponse(BaseModel):
    status: str
    questions: Optional[List[Dict]] = None
    current_params: Optional[Dict] = None
    strategy: Optional[Dict] = None


class BacktestRequest(BaseModel):
    strategy_params: Dict[str, Any]
    start_date: str = "2022-01-01"
    end_date: str = "2024-12-31"
    initial_capital: float = 1000000.0


class BacktestResponse(BaseModel):
    status: str
    result: Optional[Dict] = None
    analysis: Optional[Dict] = None
    error: Optional[str] = None


class FactorInfo(BaseModel):
    name: str
    desc: str
    category: str


# ========== 模拟数据 ==========

FACTORS = [
    {"name": "mom_20", "desc": "20日动量", "category": "动量"},
    {"name": "mom_60", "desc": "60日动量", "category": "动量"},
    {"name": "mom_120", "desc": "120日动量", "category": "动量"},
    {"name": "rsi_14", "desc": "14日RSI", "category": "动量"},
    {"name": "volatility_20", "desc": "20日波动率", "category": "波动"},
    {"name": "atr_14", "desc": "14日ATR", "category": "波动"},
    {"name": "turnover", "desc": "换手率", "category": "量价"},
    {"name": "volume_ratio", "desc": "量比", "category": "量价"},
]

# ========== API 路由 ==========

@app.get("/")
async def root():
    return {"message": "StrategyLab API", "version": "0.1.0"}


@app.get("/api/factors", response_model=List[FactorInfo])
async def get_factors():
    """获取可用因子列表"""
    return FACTORS


@app.post("/api/strategy/parse", response_model=StrategyParseResponse)
async def parse_strategy(request: StrategyParseRequest):
    """解析用户输入的策略描述"""
    message = request.message.lower()
    current_params = request.current_params or {}
    
    # 提取因子类型
    if "动量" in message or "mom" in message:
        current_params["factor_type"] = "momentum"
        if "60" in message or "中期" in message:
            current_params["factor_name"] = "mom_60"
        elif "20" in message or "短期" in message:
            current_params["factor_name"] = "mom_20"
        elif "120" in message or "长期" in message:
            current_params["factor_name"] = "mom_120"
        else:
            current_params["factor_name"] = "mom_60"
    
    # 提取持仓数量
    import re
    match = re.search(r'(\d+)只', message)
    if match:
        current_params["top_n"] = int(match.group(1))
    
    # 提取调仓频率
    if "日频" in message or "每天" in message:
        current_params["rebalance_freq"] = "daily"
    elif "周频" in message or "每周" in message:
        current_params["rebalance_freq"] = "weekly"
    elif "月频" in message or "每月" in message:
        current_params["rebalance_freq"] = "monthly"
    
    # 检查是否还需要澄清
    required_fields = ["factor_name", "top_n", "rebalance_freq"]
    missing_fields = [f for f in required_fields if f not in current_params]
    
    if missing_fields:
        questions = []
        if "factor_name" in missing_fields:
            questions.append({
                "field": "factor_name",
                "question": "请确认因子类型和周期",
                "options": [
                    {"value": "mom_20", "label": "20日动量（短期）"},
                    {"value": "mom_60", "label": "60日动量（中期）"},
                    {"value": "mom_120", "label": "120日动量（长期）"},
                    {"value": "rsi_14", "label": "14日RSI（均值回归）"},
                ]
            })
        if "top_n" in missing_fields:
            questions.append({
                "field": "top_n",
                "question": "请确认持仓数量",
                "options": [
                    {"value": 10, "label": "前10只（集中）"},
                    {"value": 30, "label": "前30只（适中）"},
                    {"value": 50, "label": "前50只（分散）"},
                    {"value": 100, "label": "前100只（广撒网）"},
                ]
            })
        if "rebalance_freq" in missing_fields:
            questions.append({
                "field": "rebalance_freq",
                "question": "请确认调仓频率",
                "options": [
                    {"value": "daily", "label": "日频（高频，成本高）"},
                    {"value": "weekly", "label": "周频（平衡）"},
                    {"value": "monthly", "label": "月频（低成本）"},
                ]
            })
        
        return StrategyParseResponse(
            status="clarifying",
            questions=questions,
            current_params=current_params
        )
    
    # 策略已确认
    strategy = {
        "name": f"{current_params.get('factor_name', '未知因子')}策略",
        "params": current_params,
        "code_preview": generate_code_preview(current_params)
    }
    
    return StrategyParseResponse(
        status="confirmed",
        current_params=current_params,
        strategy=strategy
    )


def generate_code_preview(params: Dict) -> str:
    """生成策略代码预览"""
    factor = params.get("factor_name", "mom_60")
    top_n = params.get("top_n", 50)
    freq = params.get("rebalance_freq", "monthly")
    
    return f"""# 策略参数
factor_name = "{factor}"  # 选股因子
top_n = {top_n}  # 持仓数量
rebalance_freq = "{freq}"  # 调仓频率

# 策略逻辑
1. 按 {factor} 对所有股票排序
2. 选取前 {top_n} 只股票
3. {freq} 调仓一次
4. 等权配置
"""


@app.post("/api/backtest/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """执行回测并返回结果和分析"""
    try:
        # 模拟回测结果
        import random
        random.seed(42)
        
        result = {
            "total_return": 0.25,
            "annual_return": 0.15,
            "max_drawdown": 0.18,
            "max_drawdown_duration": 45,
            "volatility": 0.22,
            "sharpe_ratio": 1.2,
            "total_trades": 120,
            "win_rate": 0.58,
            "profit_factor": 1.4,
            "avg_holding_days": 15,
            "equity_curve": [
                {"date": "2024-01", "value": 100, "benchmark": 100},
                {"date": "2024-02", "value": 105, "benchmark": 102},
                {"date": "2024-03", "value": 103, "benchmark": 101},
                {"date": "2024-04", "value": 108, "benchmark": 104},
                {"date": "2024-05", "value": 112, "benchmark": 103},
                {"date": "2024-06", "value": 115, "benchmark": 106},
            ],
            "trades": [],
            "monthly_returns": {},
            "benchmark_return": 0.06,
            "alpha": 0.09,
            "beta": 0.85,
        }
        
        # 模拟分析
        analysis = {
            "summary": f"策略采用{request.strategy_params.get('factor_name', 'mom_60')}进行选股，回测期内年化收益15%，跑赢基准。",
            "logic_analysis": "策略逻辑自洽，动量因子与定期调仓匹配。",
            "market_fit": "当前市场环境适合趋势跟踪策略。",
            "risks": [
                {"type": "回撤风险", "description": "最大回撤18%，需评估承受能力", "severity": "medium"},
                {"type": "风格切换", "description": "动量策略在风格切换时可能失效", "severity": "high"},
            ],
            "suggestions": [
                {"area": "风控优化", "suggestion": "添加止损规则", "expected_impact": "降低回撤"},
                {"area": "频率优化", "suggestion": "测试周频vs月频", "expected_impact": "平衡成本与收益"},
            ]
        }
        
        return BacktestResponse(
            status="success",
            result=result,
            analysis=analysis
        )
        
    except Exception as e:
        return BacktestResponse(
            status="error",
            error=str(e)
        )


# ========== 启动 ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
