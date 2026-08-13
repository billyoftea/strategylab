"""NL -> K-line-pattern source: natural-language description -> DeepSeek -> Qlib expression.

The LLM is constrained to output a single Qlib expression over $open/$high/$low/
$close/$volume. The expression is validated by trying to evaluate it on a tiny Qlib
sample; on failure we retry once with the error message, then surface the issue.
"""
from __future__ import annotations

import os
import re
from typing import Optional

from ..data import init_qlib
from ..spec import FactorSpec

_SYSTEM_PROMPT = (
    "你是量化研究员。把用户描述的 K 线形态转成**一个 Qlib 表达式**。\n"
    "只能用这些字段(均为后复权值):$open $high $low $close $volume $factor。\n"
    "可用算子:Mean Sum Max Min Std Var Ref Abs If Greater Less Range Quantile 等 Qlib 表达式函数,以及 + - * / > < >= <= == & |。\n"
    "形态通常是 0/1 布尔条件(触发=1)。例如锤子线可写成:\n"
    "  If((($close-$open)>=0)&(($open-$low)>2*($close-$open)), 1, 0)\n"
    "**只输出一个表达式,不要任何解释、不要代码块、不要引号、不要前后缀。**"
)


def _client():
    from openai import OpenAI

    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY 未设置。请在 ~/rdagent_work/.env 填入,或 export DEEPSEEK_API_KEY。"
        )
    return OpenAI(api_key=key, base_url="https://api.deepseek.com")


def _extract_expression(text: str) -> str:
    text = text.strip()
    # strip ``` code fences if the model added them despite instructions
    fence = re.search(r"```(?:python|qlib)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    # take the last non-empty line that looks like an expression
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[-1] if lines else text


def _validate(expression: str) -> Optional[str]:
    """Return None if valid, else the error message."""
    try:
        from qlib.data import D

        init_qlib()
        # evaluate on one instrument over a tiny window
        D.features(["SH600519"], [expression], start_time="2023-01-01", end_time="2023-01-31")
        return None
    except Exception as e:  # noqa: BLE001
        return str(e)


def from_nl(description: str, model: str = "deepseek-chat", retries: int = 1) -> FactorSpec:
    description = description.strip()
    if not description:
        raise ValueError("description is empty")
    client = _client()

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    expression = None
    last_error = None
    user_msgs = [description]
    for attempt in range(retries + 1):
        for um in user_msgs:
            messages.append({"role": "user", "content": um})
        resp = client.chat.completions.create(model=model, messages=messages, temperature=0)
        candidate = _extract_expression(resp.choices[0].message.content)
        err = _validate(candidate)
        if err is None:
            expression = candidate
            break
        last_error = err
        user_msgs = [f"上一次表达式报错:{err}\n请修正后只输出一个正确的 Qlib 表达式。"]
        # drop prior user turns to keep context tight
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}]

    if expression is None:
        raise RuntimeError(f"DeepSeek 生成的表达式无法通过 Qlib 校验。最后报错:{last_error}")

    return FactorSpec(
        name=re.sub(r"[^0-9a-zA-Z_]+", "_", description)[:40] or "nl_pattern",
        description=description,
        expression=expression,
        source="nl_pattern",
    )
