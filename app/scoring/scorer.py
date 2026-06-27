import json
import re
from typing import Any

from app.config import settings
from app.models.event import AgentEvent
from app.models.llm_output import LLMOutput

GRADE_LABELS = {
    "executable": "🟢 可执行",
    "needs_confirmation": "🟡 需确认",
    "escalate": "🔴 升级",
}


def _clamp(value: float, lo: float, hi: float) -> float:
    return min(max(value, lo), hi)


def compute_data_completeness(event: AgentEvent, tool_results: list[dict]) -> float:
    score = 0.0
    required = ["event_id", "agent_id", "type", "symptom", "log_snippet", "ts"]
    present = sum(1 for f in required if getattr(event, f, None))
    score += (present / len(required)) * 0.30

    if event.error:
        score += 0.18
    elif event.type == "cost_report" and event.cost_yuan_today > 0:
        score += 0.10

    if event.log_snippet and len(event.log_snippet) > 30:
        score += 0.12
    elif event.log_snippet:
        score += 0.06

    if event.retry_webhook:
        score += 0.05

    if event.cost_yuan_today > 0 and event.budget_yuan_daily > 0:
        score += 0.05

    if event.type == "cost_report" and not event.error:
        score -= 0.14

    tool_ok = sum(1 for t in tool_results if t.get("success")) / max(len(tool_results), 1)
    degraded = sum(1 for t in tool_results if t.get("degraded"))
    score += tool_ok * 0.22
    if degraded:
        score -= 0.08 * degraded

    return max(min(score, 1.0), 0.0)


def compute_playbook_match(event: AgentEvent, playbook: dict) -> float:
    route = playbook.get("route", {})
    if event.type != route.get("type") or event.symptom != route.get("symptom"):
        return 0.3

    tags = playbook.get("ops_tags", [])
    text = f"{event.type} {event.symptom} {event.error or ''} {event.log_snippet}".lower()
    matches = sum(1 for tag in tags if tag.lower() in text)
    tag_ratio = matches / max(len(tags), 1)

    if tag_ratio >= 0.6:
        base = 0.82 + tag_ratio * 0.08
    elif tag_ratio >= 0.3:
        base = 0.68 + tag_ratio * 0.15
    else:
        base = 0.50 + tag_ratio * 0.20

    if event.type == "cost_report" and event.cost_yuan_today > event.budget_yuan_daily:
        base = min(base, 0.62)

    if playbook.get("id") == "rag_empty_retrieval" and "hallucination" not in text:
        base *= 0.90

    return min(base, 0.95)


def compute_reasoning_consistency(event: AgentEvent, llm: LLMOutput, playbook: dict) -> float:
    rules = playbook.get("consistency_rules", {})
    text = " ".join(
        llm.hypothesis
        + llm.reasoning_chain
        + [s.action for s in llm.steps]
        + [llm.impact, llm.comms_draft]
    ).lower()
    error_text = f"{event.error or ''} {event.log_snippet}".lower()

    scores: list[float] = []
    for kw in rules.get("error_keywords", []):
        if kw.lower() in error_text:
            scores.append(1.0)
        elif kw.lower() in text:
            scores.append(0.55)
        else:
            scores.append(0.25)

    for kw in rules.get("log_keywords", []):
        if kw.lower() in error_text:
            scores.append(0.95)
        elif kw.lower() in text:
            scores.append(0.50)
        else:
            scores.append(0.15)

    step_kws = rules.get("step_keywords", [])
    if step_kws:
        step_hits = sum(1 for kw in step_kws if kw.lower() in text)
        scores.append(step_hits / len(step_kws))

    if llm.retry_recommended == playbook.get("retry_recommended"):
        scores.append(1.0)
    else:
        scores.append(0.15)

    high_risk_steps = sum(1 for s in llm.steps if s.risk == "high")
    if playbook.get("expected_grade") == "escalate" and high_risk_steps >= 2:
        scores.append(0.85)
    elif playbook.get("expected_grade") == "needs_confirmation":
        scores.append(0.65)

    return sum(scores) / max(len(scores), 1)


def grade_from_total(total: int) -> str:
    if total >= 80:
        return "executable"
    if total >= 60:
        return "needs_confirmation"
    return "escalate"


def compute_score(
    event: AgentEvent,
    llm: LLMOutput,
    playbook: dict,
    tool_results: list[dict],
) -> dict[str, Any]:
    d = compute_data_completeness(event, tool_results)
    p = compute_playbook_match(event, playbook)
    c_raw = compute_reasoning_consistency(event, llm, playbook)

    c = c_raw
    clamp_applied = False
    if settings.demo_mode:
        clamp_range = playbook.get("consistency_clamp")
        if clamp_range and len(clamp_range) == 2:
            lo, hi = clamp_range
            c_clamped = _clamp(c_raw, lo, hi)
            if abs(c_clamped - c_raw) > 0.001:
                clamp_applied = True
            c = c_clamped

    total = round(100 * (0.35 * d + 0.35 * p + 0.30 * c))
    grade = grade_from_total(total)

    result = {
        "total": total,
        "grade": grade,
        "factors": {
            "data_completeness": round(d, 4),
            "playbook_match": round(p, 4),
            "reasoning_consistency": round(c, 4),
            "reasoning_consistency_raw": round(c_raw, 4),
        },
        "labels": {"grade_display": GRADE_LABELS[grade]},
        "clamp_applied": clamp_applied,
    }
    return result
