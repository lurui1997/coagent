"""运行时纠偏：基于评分与 LLM 输出生成参数/提示词修正建议。"""

from __future__ import annotations

from typing import Any


def build_correction_suggestions(
    incident: dict[str, Any],
) -> list[dict[str, str]]:
    """根据场景与评分生成可应用的纠偏建议。"""
    scenario = incident.get("scenario_id", "")
    score = incident.get("score_json") or {}
    llm = incident.get("llm_json") or {}
    grade = score.get("grade", "")
    suggestions: list[dict[str, str]] = []

    if scenario == "s1" or incident.get("agent_id") == "cs-bot":
        suggestions.append({
            "param": "concurrent",
            "current": "10",
            "suggested": "5",
            "reason": "429 限流：降低并发至昨日水平",
        })
        if grade != "executable":
            suggestions.append({
                "param": "system_prompt",
                "current": "default",
                "suggested": "限流时优先等待 60s 再重试，避免连续触发 429",
                "reason": "提升推理一致性",
            })

    elif scenario == "s2" or incident.get("agent_id") == "rag-bot":
        suggestions.append({
            "param": "kb_sync",
            "current": "lag 1d",
            "suggested": "force sync + rebuild index",
            "reason": "空检索根因：索引滞后",
        })
        suggestions.append({
            "param": "fallback_prompt",
            "current": "disabled",
            "suggested": "strict — 无检索结果时拒绝作答",
            "reason": "防止幻觉答复",
        })

    elif scenario == "s3" or incident.get("agent_id") == "content-bot":
        suggestions.append({
            "param": "model",
            "current": "gpt-4o",
            "suggested": "gpt-4o-mini",
            "reason": "超预算：强制降级模型止血",
        })
        suggestions.append({
            "param": "max_tokens",
            "current": "4096",
            "suggested": "2048",
            "reason": "降低 Token 消耗",
        })

    # 低评分通用建议
    if grade == "needs_confirmation" and not suggestions:
        suggestions.append({
            "param": "system_prompt",
            "current": "default",
            "suggested": "增加 playbook 约束与兜底步骤",
            "reason": f"评分 {score.get('total')} 需确认",
        })

    if llm.get("retry_recommended") is False and scenario == "s2":
        suggestions.append({
            "param": "retry_policy",
            "current": "enabled",
            "suggested": "disabled",
            "reason": "空检索场景禁止盲重试",
        })

    return suggestions
