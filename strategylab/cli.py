"""StrategyLab CLI.

  strategylab pattern --nl "锤子线"            # NL -> 形态 -> 事件研究
  strategylab pattern --expr "Mean($close,20)" # 表达式 -> 事件研究
  strategylab backtest --expr "Mean($close,20)"# 表达式 -> IC + Topk 组合回测
"""
from __future__ import annotations

from pathlib import Path

import typer

from . import report
from ._env import load_env
from .evaluators import run_event_study, run_portfolio_backtest
from .sources import from_expression, from_nl
from .spec import BacktestConfig, EventStudyConfig

app = typer.Typer(add_completion=False, help="StrategyLab — 因子/K线形态回测 on Qlib")


def _f(v) -> str:
    return f"{v:.4f}" if isinstance(v, (int, float)) else "-"


def _p(v) -> str:
    return f"{v:.2%}" if isinstance(v, (int, float)) else "-"


@app.command()
def pattern(
    nl: str = typer.Option(None, "--nl", help="自然语言形态描述(走 DeepSeek 生成表达式)"),
    expr: str = typer.Option(None, "--expr", help="直接给 Qlib 形态表达式"),
    market: str = typer.Option("csi300", help="股票池"),
    start: str = typer.Option("2015-01-01"),
    end: str = typer.Option("2024-12-31"),
    out: str = typer.Option("reports", help="报告输出根目录"),
):
    """K 线形态事件研究:形态触发 -> 未来 N 天收益分布。"""
    load_env()
    if nl and not expr:
        spec = from_nl(nl)
        tag = "nl"
    elif expr and not nl:
        spec = from_expression(expr)
        tag = "expr"
    else:
        typer.secho("请指定 --nl 或 --expr 之一", err=True)
        raise typer.Exit(2)

    typer.echo(f"表达式: {spec.expression}")
    cfg = EventStudyConfig(market=market, start_time=start, end_time=end)
    result = run_event_study(spec, cfg)
    md = report.render_event_study(result, Path(out) / f"pattern_{tag}_{spec.name}")
    typer.echo(f"\n报告: {md}")
    typer.echo(f"触发事件 {result.summary['n_trigger_events']} 次,覆盖 {result.summary['n_symbols_covered']} 只股票\n")
    typer.echo(f"{'天数':>4} {'样本':>8} {'均值':>10} {'中位数':>10} {'胜率':>8} {'t值':>8}")
    for h, v in result.summary["by_horizon"].items():
        if v.get("count"):
            typer.echo(f"{h:>4} {v['count']:>8} {v['mean']:>10.4%} {v['median']:>10.4%} {v['win_rate']:>8.1%} {v['t_stat']:>8.2f}")
        else:
            typer.echo(f"{h:>4} {0:>8}  (无触发)")


@app.command()
def backtest(
    expr: str = typer.Option(..., "--expr", help="Qlib 因子表达式"),
    market: str = typer.Option("csi300"),
    topk: int = typer.Option(50, help="多头持有股票数"),
    out: str = typer.Option("reports", help="报告输出根目录"),
):
    """单因子组合回测:Rank IC + Topk 多头组合。"""
    load_env()
    spec = from_expression(expr)
    typer.echo(f"因子: {spec.expression}")
    cfg = BacktestConfig(market=market, topk=topk)
    result = run_portfolio_backtest(spec, cfg)
    md = report.render_portfolio(result, Path(out) / f"backtest_{spec.name}")
    s = result.summary
    p = s["portfolio"]
    typer.echo(f"\n报告: {md}")
    typer.echo(f"Rank IC 均值: {_f(s['rank_ic_mean'])}  ICIR: {_f(s['rank_icir'])}")
    typer.echo(f"组合: 年化 {_p(p['ann_return'])}  夏普 {_f(p['sharpe'])}  最大回撤 {_p(p['max_dd'])}  (基准 csi300)")


if __name__ == "__main__":
    app()
