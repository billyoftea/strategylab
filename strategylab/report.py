"""Render evaluator results to a per-run directory: summary.json + report.md + PNG."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # non-interactive
import matplotlib.pyplot as plt  # noqa: E402


def _write_json(out_dir: Path, summary: dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "summary.json"
    p.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return p


def render_event_study(result, out_dir: str | Path, name: str = "event_study") -> Path:
    import numpy as np

    out_dir = Path(out_dir)
    _write_json(out_dir, result.summary)

    # cumulative mean return curve across horizons
    fig, ax = plt.subplots(figsize=(9, 5))
    for h, fwd in result.fwd_returns.items():
        triggered = fwd[result.trigger]
        daily_mean = triggered.mean(axis=1).dropna()
        if daily_mean.empty:
            continue
        cum = (1 + daily_mean).cumprod()
        ax.plot(cum.index, cum.values, label=f"horizon {h}d (n={int(result.summary['by_horizon'][str(h)].get('count', 0))})")
    ax.axhline(1.0, color="grey", lw=0.8, ls="--")
    ax.set_title(f"Event Study: {result.summary['factor']['name']}\n(triggered cumulative mean return)")
    ax.set_ylabel("cumulative return (start=1)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / f"{name}.png", dpi=110)
    plt.close(fig)

    md = [f"# Event Study 报告 — {result.summary['factor']['name']}", ""]
    md.append(f"- 来源:`{result.summary['factor']['source']}`")
    md.append(f"- 表达式:`{result.summary['factor']['expression']}`")
    md.append(f"- 触发事件数:{result.summary['n_trigger_events']}  覆盖股票:{result.summary['n_symbols_covered']}")
    md.append(f"- 区间:{result.summary['config']['start_time']} ~ {result.summary['config']['end_time']}  池:{result.summary['config']['market']}")
    md.append("\n## 各前瞻天数收益分布\n")
    md.append("| 天数 | 样本 | 均值 | 中位数 | 胜率 | t值 |")
    md.append("|---|---|---|---|---|---|")
    for h, v in result.summary["by_horizon"].items():
        if v.get("count", 0) == 0:
            md.append(f"| {h} | 0 | - | - | - | - |")
        else:
            md.append(
                f"| {h} | {v['count']} | {v['mean']:.4%} | {v['median']:.4%} | {v['win_rate']:.1%} | {v['t_stat']:.2f} |"
            )
    md.append(f"\n![curve]({name}.png)")
    (out_dir / "report.md").write_text("\n".join(md), encoding="utf-8")
    return out_dir / "report.md"


def render_portfolio(result, out_dir: str | Path, name: str = "portfolio") -> Path:
    out_dir = Path(out_dir)
    _write_json(out_dir, result.summary)

    cum = (1 + result.port_return.fillna(0)).cumprod()
    bench = (1 + result.bench_return.reindex(result.port_return.index).fillna(0)).cumprod()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(cum.index, cum.values, label="Topk portfolio")
    if not bench.empty:
        ax.plot(bench.index, bench.values, label="benchmark (csi300)", alpha=0.7)
    ax.set_title(f"Portfolio Backtest: {result.summary['factor']['name']}")
    ax.set_ylabel("cumulative (start=1)"); ax.legend(fontsize=9)
    fig.tight_layout(); fig.savefig(out_dir / f"{name}.png", dpi=110); plt.close(fig)

    s = result.summary
    p = s["portfolio"]; e = s["excess"]
    md = [f"# Portfolio Backtest 报告 — {s['factor']['name']}", ""]
    md.append(f"- 表达式:`{s['factor']['expression']}`  来源:`{s['factor']['source']}`")
    md.append(f"- Rank IC 均值:{_fmt(s['rank_ic_mean'])}  ICIR:{_fmt(s['rank_icir'])}")
    md.append("\n## 组合表现\n")
    md.append("| | 年化 | 波动 | 夏普 | 最大回撤 |")
    md.append("|---|---|---|---|---|")
    md.append(f"| 组合 | {_pct(p['ann_return'])} | {_pct(p['ann_vol'])} | {_f2(p['sharpe'])} | {_pct(p['max_dd'])} |")
    md.append(f"| 超额 | {_pct(e['ann_return'])} | {_pct(e['ann_vol'])} | {_f2(e['sharpe'])} | {_pct(e['max_dd'])} |")
    md.append(f"\n![curve]({name}.png)")
    (out_dir / "report.md").write_text("\n".join(md), encoding="utf-8")
    return out_dir / "report.md"


def _fmt(v):
    return f"{v:.4f}" if isinstance(v, (int, float)) else str(v)


def _pct(v):
    return f"{v:.2%}" if isinstance(v, (int, float)) else "-"


def _f2(v):
    return f"{v:.2f}" if isinstance(v, (int, float)) else "-"
