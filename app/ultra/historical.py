"""历史故障推演：相似事故检索 + What-if 反事实评分。"""

from __future__ import annotations

import re
from typing import Any

from app.models.event import AgentEvent
from app.models.llm_output import LLMOutput, Step
from app.scoring.scorer import compute_score


def find_similar_incidents(target: dict, candidates: list[dict], limit: int = 5) -> list[dict]:
    """按场景、Agent、错误关键词相似度检索历史事故。"""
    target_text = _incident_text(target)
    results: list[tuple[float, dict]] = []

    for cand in candidates:
        if cand["trace_id"] == target.get("trace_id"):
            continue
        score = 0.0
        if cand.get("scenario_id") == target.get("scenario_id"):
            score += 0.45
        if cand.get("agent_id") == target.get("agent_id"):
            score += 0.25
        cand_text = _incident_text(cand)
        overlap = _keyword_overlap(target_text, cand_text)
        score += overlap * 0.30
        if score > 0.2:
            results.append((score, {**cand, "similarity": round(score, 3)}))

    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:limit]]


def simulate_what_if(
    incident: dict,
    playbook: dict,
    changes: dict[str, Any],
) -> dict[str, Any]:
    """反事实模拟：修改事件参数后重算把握度评分（不调大模型）。"""
    event_data = dict(incident.get("event_json") or {})
    event_data.update(changes)
    event = AgentEvent.model_validate(event_data)

    llm_data = incident.get("llm_json") or {}
    llm = LLMOutput(
        impact=llm_data.get("impact", ""),
        hypothesis=llm_data.get("hypothesis", []),
        reasoning_chain=llm_data.get("reasoning_chain", []),
        steps=[Step.model_validate(s) for s in llm_data.get("steps", [])],
        comms_draft=llm_data.get("comms_draft", ""),
        retry_recommended=llm_data.get("retry_recommended", False),
    )

    original_score = incident.get("score_json") or {}
    tool_results = _mock_tools_from_playbook(playbook, changes)
    counterfactual = compute_score(event, llm, playbook, tool_results)

    # 原始因子（复算以便与反事实对比）
    orig_event = AgentEvent.model_validate(incident.get("event_json") or {})
    orig_tools = _mock_tools_from_playbook(playbook, {})
    original_recomputed = compute_score(orig_event, llm, playbook, orig_tools)

    delta = counterfactual["total"] - original_score.get("total", counterfactual["total"])
    narrative = _what_if_narrative(incident.get("scenario_id", ""), changes, delta, counterfactual)
    logic_chain = _build_logic_chain(
        incident,
        changes,
        original_score,
        original_recomputed,
        counterfactual,
        narrative,
    )

    return {
        "trace_id": incident["trace_id"],
        "changes": changes,
        "original_score": original_score.get("total"),
        "counterfactual_score": counterfactual["total"],
        "delta": delta,
        "original_grade": original_score.get("grade"),
        "counterfactual_grade": counterfactual["grade"],
        "grade_changed": original_score.get("grade") != counterfactual["grade"],
        "factors": counterfactual["factors"],
        "original_factors": original_recomputed["factors"],
        "narrative": narrative,
        "logic_chain": logic_chain,
    }


def _incident_text(inc: dict) -> str:
    ev = inc.get("event_json") or {}
    llm = inc.get("llm_json") or {}
    parts = [
        inc.get("scenario_id", ""),
        inc.get("agent_id", ""),
        ev.get("error", ""),
        ev.get("log_snippet", ""),
        " ".join(llm.get("hypothesis") or []),
    ]
    return " ".join(str(p) for p in parts).lower()


def _keyword_overlap(a: str, b: str) -> float:
    tokens_a = set(re.findall(r"[\w\u4e00-\u9fff]+", a))
    tokens_b = set(re.findall(r"[\w\u4e00-\u9fff]+", b))
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def _mock_tools_from_playbook(playbook: dict, changes: dict[str, Any]) -> list[dict]:
    mocks = playbook.get("tool_mocks", {})
    results = []
    for tool in playbook.get("required_tools", []):
        data = dict(mocks.get(tool, {}))
        if tool == "query_agent_config" and "concurrent" in changes:
            data["concurrent"] = changes["concurrent"]
        results.append({"tool": tool, "result": data, "success": True})
    return results


def _fmt_factor(factors: dict, key: str) -> str:
    val = factors.get(key)
    return f"{float(val) * 100:.0f}%" if val is not None else "—"


def _change_description(key: str, val: Any, event: dict) -> str:
    before = event.get(key, "—")
    labels = {
        "concurrent": "并发",
        "budget_yuan_daily": "日预算",
        "log_snippet": "运行日志",
        "cost_yuan_today": "日成本",
    }
    label = labels.get(key, key)
    return f"{label}: {before} → {val}"


def _build_logic_chain(
    incident: dict,
    changes: dict[str, Any],
    original_score: dict,
    original_recomputed: dict,
    counterfactual: dict,
    narrative: str,
) -> list[dict[str, Any]]:
    """构建 What-if 推演逻辑链（供前端可视化）。"""
    event = incident.get("event_json") or {}
    orig_f = original_recomputed.get("factors") or original_score.get("factors") or {}
    new_f = counterfactual.get("factors") or {}
    llm = incident.get("llm_json") or {}

    grade_labels = {
        "executable": "🟢 可执行",
        "needs_confirmation": "🟡 需确认",
        "escalate": "🔴 升级",
    }

    return [
        {
            "step": 1,
            "key": "baseline",
            "title": "基准状态",
            "summary": f"{incident.get('agent_id')} · {incident.get('scenario_id')} · 评分 {original_score.get('total', '—')}",
            "links": [
                {"rel": "Agent", "to": incident.get("agent_id", "")},
                {"rel": "场景", "to": incident.get("scenario_id", "")},
                {"rel": "分级", "to": grade_labels.get(original_score.get("grade", ""), "")},
            ],
            "reasoning_chain": llm.get("reasoning_chain") or [],
        },
        {
            "step": 2,
            "key": "intervention",
            "title": "假设干预",
            "summary": "对事件参数施加反事实变更（不调大模型）",
            "links": [
                {"rel": _change_description(k, v, event), "to": "变更"}
                for k, v in changes.items()
            ],
        },
        {
            "step": 3,
            "key": "propagation",
            "title": "因子传导",
            "summary": "数据·手册·推理 三因子重算",
            "links": [
                {
                    "rel": "数据完备",
                    "from": _fmt_factor(orig_f, "data_completeness"),
                    "to": _fmt_factor(new_f, "data_completeness"),
                },
                {
                    "rel": "手册匹配",
                    "from": _fmt_factor(orig_f, "playbook_match"),
                    "to": _fmt_factor(new_f, "playbook_match"),
                },
                {
                    "rel": "推理一致",
                    "from": _fmt_factor(orig_f, "reasoning_consistency"),
                    "to": _fmt_factor(new_f, "reasoning_consistency"),
                },
            ],
        },
        {
            "step": 4,
            "key": "conclusion",
            "title": "推演结论",
            "summary": narrative,
            "links": [
                {
                    "rel": "评分",
                    "from": str(original_score.get("total", "—")),
                    "to": str(counterfactual.get("total", "—")),
                },
                {
                    "rel": "分级",
                    "from": grade_labels.get(original_score.get("grade", ""), "—"),
                    "to": grade_labels.get(counterfactual.get("grade", ""), "—"),
                },
                {"rel": "Δ", "to": f"{counterfactual.get('total', 0) - original_score.get('total', 0):+d}"},
            ],
        },
    ]


def _what_if_narrative(scenario_id: str, changes: dict, delta: int, score: dict) -> str:
    parts = []
    if "concurrent" in changes:
        parts.append(f"若 concurrent 调整为 {changes['concurrent']}")
    if "budget_yuan_daily" in changes:
        parts.append(f"若日预算调整为 ¥{changes['budget_yuan_daily']}")
    if "log_snippet" in changes:
        parts.append("若运行日志/指标恢复稳定")
    if not parts:
        parts.append("若应用假设变更")
    direction = "上升" if delta > 0 else ("下降" if delta < 0 else "不变")
    grade = score.get("grade", "")
    grade_label = {"executable": "🟢 可执行", "needs_confirmation": "🟡 需确认", "escalate": "🔴 升级"}.get(grade, grade)
    return f"{'，'.join(parts)}，评分预计{direction} {abs(delta)} 分 → {score['total']} ({grade_label})"
