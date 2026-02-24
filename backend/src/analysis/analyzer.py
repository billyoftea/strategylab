"""
LLM分析模块 - 深度市场逻辑分析
"""
import os
from typing import Dict, List
from dataclasses import asdict
import json


class LLMAnalyzer:
    """LLM策略分析师"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.model = "deepseek-chat"
        
        # 市场知识库 - 因子有效性解释
        self.factor_knowledge = {
            "mom_20": {
                "name": "20日动量",
                "logic": "短期价格趋势延续，反映市场参与者行为偏差（追涨杀跌）",
                "effective_market": "趋势明显的牛市或熊市",
                "ineffective_market": "震荡市、反转行情",
                "risk": "高换手率、反转风险",
            },
            "mom_60": {
                "name": "60日动量",
                "logic": "中期趋势跟踪，过滤短期噪音，捕捉持续的市场共识",
                "effective_market": "有明确中期趋势的市场",
                "ineffective_market": "快速风格切换、政策突变",
                "risk": "中期回调风险、风格切换踏空",
            },
            "mom_120": {
                "name": "120日动量",
                "logic": "长期趋势投资，反映基本面改善的持续性",
                "effective_market": "基本面驱动的慢牛行情",
                "ineffective_market": "高波动、高换手市场",
                "risk": "长期趋势反转、黑天鹅事件",
            },
            "rsi_14": {
                "name": "14日RSI",
                "logic": "超买超卖指标，均值回归策略的核心",
                "effective_market": "震荡市、区间波动",
                "ineffective_market": "强趋势市场",
                "risk": "趋势延续导致过早反向",
            },
            "volatility_20": {
                "name": "20日波动率",
                "logic": "风险度量，低波动异象（低风险高收益）",
                "effective_market": "大多数市场环境",
                "ineffective_market": "极端行情、流动性危机",
                "risk": "波动率突增、尾部风险",
            },
        }
        
        # 策略模式知识库
        self.strategy_patterns = {
            "momentum": {
                "name": "动量策略",
                "core_logic": "趋势延续假设 - 过去表现好的股票未来继续表现好",
                "behavioral_basis": "反应不足、信息扩散缓慢、羊群效应",
                "market_conditions": "需要市场有持续性趋势，流动性充足",
                "typical_drawdown_causes": "趋势反转、V型反转、黑天鹅事件",
            },
            "mean_reversion": {
                "name": "均值回归策略",
                "core_logic": "价格围绕价值波动，极端偏离后会回归",
                "behavioral_basis": "过度反应、获利了结、套利行为",
                "market_conditions": "震荡市、无明显趋势",
                "typical_drawdown_causes": "趋势形成、结构性变化、黑天鹅",
            },
            "value": {
                "name": "价值策略",
                "core_logic": "买入低估资产，等待市场重新认识价值",
                "behavioral_basis": "过度悲观、短期主义、机构行为约束",
                "market_conditions": "市场恐慌后、风格偏向价值",
                "typical_drawdown_causes": "价值陷阱、风格持续偏离、流动性危机",
            },
        }
    
    def analyze_strategy(
        self,
        strategy_params: Dict,
        backtest_result: Dict,
    ) -> Dict:
        """
        深度分析策略
        
        Returns:
            {
                "summary": "策略表现总结",
                "logic_analysis": "逻辑自洽性分析",
                "market_fit": "市场环境适配度",
                "risks": "风险识别",
                "suggestions": "改进建议",
            }
        """
        factor_name = strategy_params.get("factor_name", "mom_60")
        factor_info = self.factor_knowledge.get(factor_name, {})
        
        # 识别策略模式
        strategy_pattern = self._identify_pattern(strategy_params)
        pattern_info = self.strategy_patterns.get(strategy_pattern, {})
        
        # 构建分析报告
        analysis = {
            "summary": self._generate_summary(strategy_params, backtest_result, factor_info),
            "logic_analysis": self._analyze_logic(strategy_params, pattern_info),
            "market_fit": self._analyze_market_fit(backtest_result, factor_info),
            "risks": self._identify_risks(strategy_params, backtest_result, factor_info),
            "suggestions": self._generate_suggestions(strategy_params, backtest_result, factor_info),
        }
        
        return analysis
    
    def _identify_pattern(self, params: Dict) -> str:
        """识别策略模式"""
        factor = params.get("factor_name", "")
        if "mom" in factor:
            return "momentum"
        elif "rsi" in factor:
            return "mean_reversion"
        elif factor in ["pe", "pb"]:
            return "value"
        return "momentum"  # 默认
    
    def _generate_summary(
        self, 
        params: Dict, 
        result: Dict,
        factor_info: Dict
    ) -> str:
        """生成策略表现总结"""
        total_return = result.get("total_return", 0)
        annual_return = result.get("annual_return", 0)
        max_dd = result.get("max_drawdown", 0)
        sharpe = result.get("sharpe_ratio", 0)
        
        factor_desc = factor_info.get("name", params.get("factor_name", "未知因子"))
        
        summary = f"""
策略采用{factor_desc}进行选股，回测期内：
- 总收益率 {total_return:.1%}，年化收益 {annual_return:.1%}
- 最大回撤 {max_dd:.1%}，夏普比率 {sharpe:.2f}

核心逻辑：{factor_info.get("logic", "趋势跟踪")}
        """.strip()
        
        return summary
    
    def _analyze_logic(self, params: Dict, pattern_info: Dict) -> str:
        """分析策略逻辑自洽性"""
        if not pattern_info:
            return "无法识别策略模式"
        
        analysis = f"""
【策略模式】{pattern_info.get("name", "未知")}

【核心假设】
{pattern_info.get("core_logic", "")}

【行为金融学基础】
{pattern_info.get("behavioral_basis", "")}

【逻辑自洽性检查】
- 入场逻辑（{params.get("factor_name", "")}选股）与出场逻辑（{'定期调仓' if params.get('rebalance_freq') else '未设置'}) {'一致' if params.get('rebalance_freq') else '需明确'}
- 选股周期（{params.get('rebalance_freq', '未知')}）与因子周期匹配度需验证
- 持仓数量（{params.get('top_n', '未知')}只）分散度{'充足' if params.get('top_n', 0) >= 30 else '偏低'}
        """.strip()
        
        return analysis
    
    def _analyze_market_fit(self, result: Dict, factor_info: Dict) -> str:
        """分析市场环境适配度"""
        annual_return = result.get("annual_return", 0)
        max_dd = result.get("max_drawdown", 0)
        
        # 简单判断市场环境
        if annual_return > 0.2 and max_dd < 0.15:
            market_condition = "表现优异，可能处于趋势明显的市场环境"
        elif annual_return > 0 and max_dd < 0.2:
            market_condition = "表现稳健，市场环境适中"
        elif annual_return < 0:
            market_condition = "表现不佳，可能处于不适合该策略的市场环境"
        else:
            market_condition = "波动较大，市场环境复杂"
        
        analysis = f"""
【当前市场环境判断】
{market_condition}

【因子有效性环境】
- 有效环境：{factor_info.get("effective_market", "未知")}
- 无效环境：{factor_info.get("ineffective_market", "未知")}

【适配度评估】
基于回测结果，当前策略与{factor_info.get('effective_market', '趋势')}市场环境{'匹配度较高' if annual_return > 0 else '匹配度较低'}。
建议结合当前市场风格（价值/成长、大盘/小盘）进一步判断。
        """.strip()
        
        return analysis
    
    def _identify_risks(self, params: Dict, result: Dict, factor_info: Dict) -> List[Dict]:
        """识别风险点"""
        risks = []
        
        # 因子固有风险
        if factor_info.get("risk"):
            risks.append({
                "type": "因子风险",
                "description": factor_info["risk"],
                "severity": "medium",
            })
        
        # 回撤风险
        max_dd = result.get("max_drawdown", 0)
        if max_dd > 0.25:
            risks.append({
                "type": "回撤风险",
                "description": f"最大回撤{max_dd:.1%}较高，需评估承受能力",
                "severity": "high",
            })
        
        # 换手率风险
        rebalance_freq = params.get("rebalance_freq", "monthly")
        if rebalance_freq == "daily":
            risks.append({
                "type": "交易成本",
                "description": "日频调仓换手率过高，实际收益可能被交易成本侵蚀",
                "severity": "high",
            })
        elif rebalance_freq == "weekly":
            risks.append({
                "type": "交易成本",
                "description": "周频调仓需关注冲击成本",
                "severity": "medium",
            })
        
        # 集中度风险
        top_n = params.get("top_n", 50)
        if top_n < 20:
            risks.append({
                "type": "集中度风险",
                "description": f"仅持仓{top_n}只，个股风险集中",
                "severity": "medium",
            })
        
        # 过拟合风险（简单判断）
        total_trades = result.get("total_trades", 0)
        if total_trades < 10 and result.get("annual_return", 0) > 0.3:
            risks.append({
                "type": "过拟合风险",
                "description": "交易次数少但收益高，可能存在过拟合或运气成分",
                "severity": "high",
            })
        
        return risks
    
    def _generate_suggestions(
        self, 
        params: Dict, 
        result: Dict,
        factor_info: Dict
    ) -> List[Dict]:
        """生成改进建议"""
        suggestions = []
        
        # 基于回撤的建议
        max_dd = result.get("max_drawdown", 0)
        if max_dd > 0.2:
            suggestions.append({
                "area": "风控优化",
                "suggestion": "添加止损规则或降低仓位，控制最大回撤在20%以内",
                "expected_impact": "降低收益波动，提高夏普比率",
            })
        
        # 基于调仓频率的建议
        rebalance_freq = params.get("rebalance_freq", "monthly")
        if rebalance_freq == "daily":
            suggestions.append({
                "area": "成本控制",
                "suggestion": "考虑改为周频或月频调仓，降低交易成本",
                "expected_impact": "实际收益可能提升5-10%",
            })
        
        # 基于持仓数量的建议
        top_n = params.get("top_n", 50)
        if top_n > 100:
            suggestions.append({
                "area": "收益增强",
                "suggestion": "减少持仓数量至30-50只，集中持有优势股票",
                "expected_impact": "提高收益集中度，但波动可能增加",
            })
        elif top_n < 10:
            suggestions.append({
                "area": "风险控制",
                "suggestion": "增加持仓数量至20-30只，分散个股风险",
                "expected_impact": "降低个股黑天鹅影响，曲线更平滑",
            })
        
        # 基于夏普比率的建议
        sharpe = result.get("sharpe_ratio", 0)
        if sharpe < 0.5:
            suggestions.append({
                "area": "策略优化",
                "suggestion": "考虑加入过滤器（如市场趋势判断），只在适合环境下运行策略",
                "expected_impact": "提高夏普比率，减少无效交易",
            })
        
        # 通用建议
        suggestions.append({
            "area": "验证增强",
            "suggestion": "进行样本外测试、参数敏感性分析、不同市场环境回测",
            "expected_impact": "提高策略稳健性，降低过拟合风险",
        })
        
        return suggestions
    
    async def analyze_with_llm(
        self,
        strategy_params: Dict,
        backtest_result: Dict,
    ) -> str:
        """
        使用DeepSeek API进行深度分析（可选增强）
        """
        # 构建prompt
        prompt = self._build_analysis_prompt(strategy_params, backtest_result)
        
        # TODO: 调用DeepSeek API
        # 目前返回本地分析结果
        analysis = self.analyze_strategy(strategy_params, backtest_result)
        return json.dumps(analysis, ensure_ascii=False, indent=2)
    
    def _build_analysis_prompt(self, params: Dict, result: Dict) -> str:
        """构建分析prompt"""
        return f"""
你是一位资深的量化策略分析师。请分析以下策略：

【策略参数】
{json.dumps(params, ensure_ascii=False, indent=2)}

【回测结果】
{json.dumps(result, ensure_ascii=False, indent=2)}

请从以下维度进行分析：
1. 策略表现总结（与基准对比）
2. 策略逻辑自洽性（入场/出场逻辑是否一致）
3. 市场环境适配度（当前市场环境是否适合该策略）
4. 潜在风险点（过拟合、幸存者偏差、流动性等）
5. 具体改进建议（可操作的优化方向）

要求：
- 分析要深入市场本源逻辑，不要只罗列数字
- 结合行为金融学原理解释策略有效性
- 指出策略的隐含假设和失效条件
"""


if __name__ == "__main__":
    analyzer = LLMAnalyzer()
    
    # 测试分析
    params = {
        "factor_name": "mom_60",
        "top_n": 50,
        "rebalance_freq": "monthly",
    }
    
    result = {
        "total_return": 0.25,
        "annual_return": 0.15,
        "max_drawdown": 0.18,
        "sharpe_ratio": 1.2,
        "total_trades": 120,
    }
    
    analysis = analyzer.analyze_strategy(params, result)
    print(json.dumps(analysis, ensure_ascii=False, indent=2))
