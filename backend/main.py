"""
FastAPI 主应用
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import sys

# 添加src到路径
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from data.manager import DataManager
from factors.calculator import FactorCalculator
from backtest.engine import BacktestEngine
from analysis.analyzer import LLMAnalyzer


app = FastAPI(
    title="StrategyLab API",
    description="基于LLM的A股策略验证工具",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化组件
data_manager = DataManager()
factor_calculator = FactorCalculator(data_manager)
backtest_engine = BacktestEngine(data_manager, factor_calculator)
analyzer = LLMAnalyzer()


# ========== 数据模型 ==========

class StrategyParseRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    current_params: Optional[Dict] = {}


class StrategyParseResponse(BaseModel):
    status: str  # "clarifying" | "confirmed"
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


# ========== API 路由 ==========

@app.get("/")
async def root():
    return {"message": "StrategyLab API", "version": "0.1.0"}


@app.get("/api/factors", response_model=List[FactorInfo])
async def get_factors():
    """获取可用因子列表"""
    return factor_calculator.get_factor_list()


@app.post("/api/strategy/parse", response_model=StrategyParseResponse)
async def parse_strategy(request: StrategyParseRequest):
    """
    解析用户输入的策略描述
    
    - 如果是初次输入，返回需要澄清的问题
    - 如果信息完整，返回确认的策略结构
    """
    # TODO: 集成LLM进行自然语言解析
    # 目前使用简单的规则匹配
    
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
            current_params["factor_name"] = "mom_60"  # 默认
    
    # 提取持仓数量
    if "前" in message and "只" in message:
        import re
        match = re.search(r'前(\d+)只', message)
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
        # 生成澄清问题
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
    """
    执行回测并返回结果和分析
    """
    try:
        # 执行回测
        result = backtest_engine.run_backtest(
            strategy_params=request.strategy_params,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital
        )
        
        # 转换为字典
        result_dict = {
            "total_return": result.total_return,
            "annual_return": result.annual_return,
            "max_drawdown": result.max_drawdown,
            "max_drawdown_duration": result.max_drawdown_duration,
            "volatility": result.volatility,
            "sharpe_ratio": result.sharpe_ratio,
            "total_trades": result.total_trades,
            "win_rate": result.win_rate,
            "profit_factor": result.profit_factor,
            "avg_holding_days": result.avg_holding_days,
            "equity_curve": result.equity_curve,
            "trades": result.trades[:20] if result.trades else [],  # 限制数量
            "monthly_returns": result.monthly_returns,
            "benchmark_return": result.benchmark_return,
            "alpha": result.alpha,
            "beta": result.beta,
        }
        
        # 深度分析
        analysis = analyzer.analyze_strategy(
            strategy_params=request.strategy_params,
            backtest_result=result_dict
        )
        
        return BacktestResponse(
            status="success",
            result=result_dict,
            analysis=analysis
        )
        
    except Exception as e:
        return BacktestResponse(
            status="error",
            error=str(e)
        )


@app.get("/api/data/status")
async def get_data_status():
    """获取数据更新状态"""
    return data_manager.get_update_status()


@app.post("/api/data/update")
async def update_data():
    """触发数据更新（仅管理员）"""
    # TODO: 添加权限检查
    try:
        data_manager.update_stock_list()
        # 异步更新价格数据
        # TODO: 使用后台任务
        return {"status": "updating", "message": "数据更新已启动"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 启动 ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
