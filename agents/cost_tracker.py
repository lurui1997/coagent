"""content-bot 日累计成本追踪 — 基于 Token 估算与模板倍率。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.config import settings

STATE_PATH = settings.data_dir / "agent_state" / "content_bot_cost.json"

# 模板倍率：模拟 v3-longform 等多阶段流水线 Token 消耗（对齐 S3 场景）
TEMPLATE_CONFIG: dict[str, dict] = {
    "standard": {
        "label": "standard",
        "prompt_suffix": "写一段 150–200 字中文文案。",
        "pipeline_mult": 1.0,
    },
    "longform": {
        "label": "v3-longform",
        "prompt_suffix": "写 800–1200 字长文，含标题、导语、正文与行动号召（CTA）。",
        "pipeline_mult": 15.0,
    },
    "batch": {
        "label": "marketing-batch",
        "prompt_suffix": "为同一 brief 生成 5 条不同角度的短文案（每条 80–120 字），用 --- 分隔。",
        "pipeline_mult": 28.0,
    },
}


@dataclass
class CostEstimate:
    input_tokens: int
    output_tokens: int
    billable_tokens: int
    cost_yuan: float
    template: str


@dataclass
class DailyCostState:
    date: str
    cost_yuan: float
    tokens_in: int
    tokens_out: int
    billable_tokens: int
    run_count: int
    last_template: str
    runs: list[dict]

    @property
    def budget(self) -> float:
        return settings.content_budget_yuan_daily

    @property
    def over_budget(self) -> bool:
        return self.cost_yuan > self.budget

    @property
    def utilization_pct(self) -> float:
        if self.budget <= 0:
            return 100.0
        return round(self.cost_yuan / self.budget * 100, 2)


def estimate_tokens(text: str) -> int:
    """中文为主：约 1.8 字符 / token。"""
    if not text:
        return 0
    return max(1, int(len(text) / 1.8))


def estimate_call_cost(
    prompt: str,
    output: str,
    template: str = "standard",
) -> CostEstimate:
    cfg = TEMPLATE_CONFIG.get(template, TEMPLATE_CONFIG["standard"])
    in_tok = estimate_tokens(prompt)
    out_tok = estimate_tokens(output)
    raw_tokens = in_tok + out_tok
    billable = int(raw_tokens * cfg["pipeline_mult"])
    rate = settings.content_cost_per_1k_tokens
    cost = round(billable / 1000 * rate, 4)
    return CostEstimate(
        input_tokens=in_tok,
        output_tokens=out_tok,
        billable_tokens=billable,
        cost_yuan=cost,
        template=cfg["label"],
    )


def _empty_state() -> DailyCostState:
    return DailyCostState(
        date=str(date.today()),
        cost_yuan=0.0,
        tokens_in=0,
        tokens_out=0,
        billable_tokens=0,
        run_count=0,
        last_template="standard",
        runs=[],
    )


def load_state() -> DailyCostState:
    if not STATE_PATH.exists():
        return _empty_state()
    with open(STATE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("date") != str(date.today()):
        return _empty_state()
    return DailyCostState(
        date=data["date"],
        cost_yuan=float(data.get("cost_yuan", 0)),
        tokens_in=int(data.get("tokens_in", 0)),
        tokens_out=int(data.get("tokens_out", 0)),
        billable_tokens=int(data.get("billable_tokens", 0)),
        run_count=int(data.get("run_count", 0)),
        last_template=str(data.get("last_template", "standard")),
        runs=list(data.get("runs", []))[-50:],
    )


def save_state(state: DailyCostState) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": state.date,
        "cost_yuan": round(state.cost_yuan, 4),
        "tokens_in": state.tokens_in,
        "tokens_out": state.tokens_out,
        "billable_tokens": state.billable_tokens,
        "run_count": state.run_count,
        "last_template": state.last_template,
        "budget_yuan_daily": state.budget,
        "utilization_pct": state.utilization_pct,
        "runs": state.runs[-50:],
    }
    with open(STATE_PATH, encoding="utf-8", mode="w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def record_run(state: DailyCostState, task: str, estimate: CostEstimate) -> DailyCostState:
    state.cost_yuan = round(state.cost_yuan + estimate.cost_yuan, 4)
    state.tokens_in += estimate.input_tokens
    state.tokens_out += estimate.output_tokens
    state.billable_tokens += estimate.billable_tokens
    state.run_count += 1
    state.last_template = estimate.template
    state.runs.append(
        {
            "task": task[:120],
            "template": estimate.template,
            "cost_yuan": estimate.cost_yuan,
            "billable_tokens": estimate.billable_tokens,
            "cumulative_yuan": state.cost_yuan,
        }
    )
    return state


def reset_state() -> DailyCostState:
    state = _empty_state()
    save_state(state)
    return state


def build_content_prompt(task: str, template: str = "standard") -> str:
    cfg = TEMPLATE_CONFIG.get(template, TEMPLATE_CONFIG["standard"])
    return (
        "你是营销内容生成 Agent（content-bot）。根据 brief 生成内容。\n\n"
        f"Brief：{task}\n\n"
        f"要求：{cfg['prompt_suffix']}"
    )


def build_over_budget_log(state: DailyCostState, task: str, estimate: CostEstimate | None) -> str:
    est = estimate
    extra = ""
    if est:
        extra = (
            f"; last_run_billable={est.billable_tokens}; last_run_cost={est.cost_yuan}; "
            f"template={est.template}"
        )
    return (
        f"task={task!r}; tokens_today={state.billable_tokens}; "
        f"cost_yuan_today={state.cost_yuan}; budget={state.budget}; "
        f"run_count={state.run_count}; utilization={state.utilization_pct}%{extra}"
    )
