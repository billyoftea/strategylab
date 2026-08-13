# StrategyLab — 设计文档 (Design Spec)

> 基于 **RD-Agent + Qlib** 的因子 / K 线形态回测实验室
> 日期:2026-08-13 ｜ 状态:待用户复核

---

## 1. 目标 (Why)

把"**提出一个因子/形态 → 在沪深300 上回测 → 出标准化报告**"这条链路,
做成一个统一工具。三类"因子来源"(手动、自然语言生成、RD-Agent 自主)
**共用同一个回测引擎和报告格式**,避免给因子和形态各写一套。

> 核心洞察:**K 线形态本质上就是一个因子**(OHLC 的函数 → 每只股票每天一个值)。
> 所以"裸 K 线形态回测"只是"由自然语言生成的因子",复用因子回测基础设施。

## 2. 已确认范围 (Scope)

| 项 | 决定 |
|---|---|
| 股票池 | **沪深300 (csi300)**,用 Qlib 自带 `cn_data` |
| 数据导入 | **后置** —— 先不导 NAS parquet,Phase 3 再做 |
| 因子回测模式 | 手动 + RD-Agent 自主,**两者都要** |
| K 线形态交互 | **先做"自然语言 → 形态 → 回测"一次性模式**;AI 自主探索后置 |
| 形态验证方式 | **C 事件研究**(形态出现→未来 N 天收益分布;自写小回测器);通用因子仍可选用 A+B |

## 3. 架构:一个引擎 + 多个因子来源 (Architecture)

```
   因子来源(FactorSource)                  统一契约              引擎                 输出
 ┌───────────────────────────┐
 │ ① ManualSource            │  你写 Qlib 表达式/代码        ┐
 │ ② NLPatternSource (MVP)   │  自然语言 → DeepSeek 生成 ────┼──→ FactorSpec ──→ Engine ──→ BacktestReport
 │ ③ RDAgentSource (后置)    │  包 fin_factor 自循环产出 ────┘   (csi300/          (IC/年化/夏普/
 └───────────────────────────┘                                     LightGBM/         回撤/净值曲线/多空)
                                                                   TopkDropout)
```

数据流是单向的:`Source → FactorSpec → Engine → Report`。三个来源互不依赖,新增来源只需"能产出 FactorSpec"。

## 4. 组件与接口 (Components)

### 4.1 `FactorSpec` —— 统一因子契约(最关键的接口)

所有来源产出它,引擎消费它。这是整个系统的解耦点。

```python
@dataclass
class FactorSpec:
    name: str                   # 因子名,如 "hammer_pattern"
    description: str            # 人类可读描述
    expression: str | None      # Qlib 表达式,如 "($close-$open)/$open"(MVP 主用)
    code: str | None            # 或 python 因子代码(复杂因子 / RD-Agent 风格)
    fields: list[str]           # 依赖字段 ["$open","$high","$low","$close"]
    source: str                 # "manual" | "nl_pattern" | "rdagent"
```

> MVP 优先用 `expression`(简单、可注入 Qlib 的 Alpha158 feature 列表);`code` 留给复杂因子和 RD-Agent。

### 4.2 `Engine` —— 回测引擎(两个评估器)

引擎按"评估什么"分发到两个评估器,产出统一 `BacktestReport`:

**① `PortfolioBacktest`(A+B,用于通用因子)**
- 输入:`FactorSpec` + `BacktestConfig`(csi300、train/test、LightGBM、topk=50)
- 行为:因子表达式注入 Qlib `conf_baseline.yaml` 模板的 `feature_expressions` → `qrun` → 取 `SigAnaRecord(IC)` + `PortAnaRecord(组合)`
- 复用 RD-Agent 的模板(csi300 + LightGBM + TopkDropout + A 股涨跌停/手续费),不重写。

**② `EventStudy`(C,用于 K 线形态 —— 用户指定)**
- 输入:`FactorSpec`(形态表达式)+ `EventStudyConfig`(前瞻天数如 [1,3,5,10,20]、基准)
- 行为:用 Qlib 取 OHLC + 算形态信号(每股每日 0/1)→ 对信号**触发日**算未来 N 天收益 → 聚合(均值/中位数/胜率/t 值/分布/累计曲线)
- **自写小回测器**(纯 pandas,约 100 行),不依赖 Qlib 组合回测。
- 直答:"这形态出现后,股票倾向涨还是跌?涨多少?概率多大?"

### 4.3 `FactorSource` —— 因子来源(可插拔)

| 来源 | 输入 | 产出 | 阶段 |
|---|---|---|---|
| `ManualSource` | Qlib 表达式或 python 代码 | FactorSpec | MVP |
| `NLPatternSource` | 自然语言形态描述("锤子线") | LLM 生成表达式 → FactorSpec | MVP |
| `RDAgentSource` | (无,自主) | 跑 `fin_factor` 拿因子 → FactorSpec | Phase 2 |

**NLPatternSource 细节(MVP 重点)**:
- 用 DeepSeek(复用 `~/rdagent_work/.env` 的 `DEEPSEEK_API_KEY`),prompt 约束它只输出**合法 Qlib 表达式**(可用字段 `$open/$high/$low/$close/$volume/$factor`)。
- 生成后先在沙箱里 dry-check 表达式语法(Qlib parse),失败则带报错重试 1 次,仍失败则回退提示用户。

### 4.4 `BacktestReport` —— 标准报告(按评估器两种)

**PortfolioBacktest 报告(A+B)**:IC/Rank IC/ICIR + 年化/夏普/最大回撤/换手 + 净值曲线/多空价差。

**EventStudy 报告(C)**:各前瞻天数的 平均收益/中位数/胜率/t 值 + 收益分布直方图 + "形态触发后累计收益"曲线 + 触发次数/覆盖股票数。

两种都落盘:JSON + Markdown 摘要 + PNG 图,每次回测一个目录。

## 5. 技术栈 & 运行环境 (Stack)

| 项 | 选择 |
|---|---|
| 语言 | Python 3.11 |
| 运行环境 | WSL Ubuntu-24.04;**新建独立 conda env `strategylab`**(装 `pyqlib` + `lightgbm` + `pandas` + `matplotlib` + `typer` + `litellm`) |
| Qlib 数据 | 复用已下好的 `~/.qlib/qlib_data/cn_data`(CSI300) |
| LLM(NL→形态) | DeepSeek(复用 .env 的 key) |
| RD-Agent(Phase 2) | 复用已部署的 rdagent env / `fin_factor` |
| 项目文件 | Windows 桌面 `C:\Users\xu.ang\Desktop\strategylab\`,WSL 经 `/mnt/c/...` 执行 |

> 为什么 StrategyLab 自己装 `pyqlib` 而不钻进 RD-Agent 的 Docker:`pyqlib` 直接装在 conda 里,跑回测、注入因子、抽报告都最可控;RD-Agent 的 Docker 是给它自主循环用的,我们 MVP 要的是"我指定因子→回测",直接调 Qlib 更简单。RD-Agent 自主来源(Phase 2)再走它的 env。

## 6. MVP 范围与阶段 (Phases)

**Phase 1 —— MVP(本次实现计划的目标)**
1. `FactorSpec` 契约 + 序列化
2. **`EventStudy` 评估器(C)** + **`NLPatternSource`**(NL→形态→事件研究)—— 你的优先项,先做
3. `ManualSource` + **`PortfolioBacktest` 评估器(A+B)** —— 通用因子回测
4. CLI:`strategylab pattern --nl "锤子线"`(事件研究)/ `strategylab backtest --expr "..."`(组合回测)
5. 烟测:一个已知形态(如锤子线)事件研究出合理前瞻收益分布 + 一个已知因子(20 日动量)组合回测出预期 IC 量级。

**Phase 2(后置)**:RDAgentSource(`fin_factor` 包装)、事件研究 C、更多报告维度。

**Phase 3(后置)**:数据导入(NAS parquet → Qlib `.bin`,见 dump_bin 流程)。

## 7. 错误处理 & 测试 (Reliability)

- **表达式语法错**:捕获 Qlib parse 报错 → 友好提示 + 指出出错位置。
- **LLM 生成不可运行**:沙箱 dry-check → 带报错重试 1 次 → 仍失败回退人工。
- **数据缺失/停牌**:沿用 Qlib 的 Fillna/CSZScoreNorm 处理(模板已配)。
- **测试**:
  - offline 单测:FactorSpec 序列化、报告指标计算(造数据验证 IC 公式)。
  - e2e 烟测:20 日动量因子 → 期望 IC 在合理区间(如 |IC|>0.02),作回归基线。
- 所有真实回测标 `@pytest.mark.offline` 之外,CI 只跑 offline 单测。

## 8. 待定 / 显式后置 (Out of Scope for MVP)

- NAS parquet → Qlib `.bin` 数据导入(Phase 3)
- AI 自主探索 K 线形态(Phase 2)
- 形态跑组合回测 A+B(让形态除事件研究外也能跑组合,Phase 2 增强)
- Web UI(暂用 CLI + Markdown 报告)
- GPU(默认 LightGBM,CPU 即可;torch 留给 Phase 2 神经模型)

---

## 决策日志

- **2026-08-13**:用户确认 —— csi300、因子两种模式都要、形态先做一次性 NL、形态验证 A+B。
- **2026-08-13(修订)**:形态验证方式从 A+B 改为 **C 事件研究**(形态出现→未来 N 天收益分布),更贴"验证某形态"本意;通用因子仍用 A+B。引擎相应拆成 `EventStudy` + `PortfolioBacktest` 两个评估器。
- 用"一个引擎 + 多个因子来源"而非两套系统,因形态本质是因子。
- StrategyLab 独立 conda env 装 pyqlib(不钻 RD-Agent Docker),换取 MVP 可控性。
