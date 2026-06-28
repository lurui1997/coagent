"""场景自适应 Agent-Team 编排。"""

from __future__ import annotations

from typing import Any

from app.models.event import AgentEvent

MODES = ("single_agent", "sub_agent", "multi_agent", "agent_team")

MODE_LABELS = {
    "single_agent": "Single-Agent · 标准流水线",
    "sub_agent": "Sub-agent · 工具分析委派",
    "multi_agent": "Multi-Agent · Triage + Specialist",
    "agent_team": "Agent-Team · 成本/升级联合处置",
}


def select_orchestration_mode(event: AgentEvent, playbook_id: str, score_total: int | None = None) -> str:
    """按事件复杂度与场景选择编排模式。"""
    if event.type == "cost_report" or playbook_id == "cost_over_budget":
        return "agent_team"
    if event.symptom == "empty_retrieval" or playbook_id == "rag_empty_retrieval":
        return "multi_agent"
    if event.symptom == "rate_limit" or playbook_id == "cs_rate_limit":
        return "sub_agent"
    if score_total is not None and score_total < 60:
        return "agent_team"
    return "single_agent"


def build_team_plan(mode: str, event: AgentEvent, playbook_id: str) -> dict[str, Any]:
    """生成 Agent-Team 执行计划（MVP：结构化角色分工 + 模拟子任务）。"""
    agents = _agents_for_mode(mode, playbook_id)
    tasks = _tasks_for_mode(mode, event, playbook_id)
    return {
        "mode": mode,
        "mode_label": MODE_LABELS.get(mode, mode),
        "lead_agent": "coagent-orchestrator",
        "team_agents": agents,
        "tasks": tasks,
        "parallel": mode in ("multi_agent", "agent_team"),
    }


def _agents_for_mode(mode: str, playbook_id: str) -> list[dict[str, str]]:
    if mode == "single_agent":
        return [{"role": "ops-copilot", "focus": "全链路处置"}]
    if mode == "sub_agent":
        return [
            {"role": "metrics-analyst", "focus": "指标/配置采集"},
            {"role": "ops-copilot", "focus": "根因推理与评分"},
        ]
    if mode == "multi_agent":
        return [
            {"role": "triage-agent", "focus": "症状分类与优先级"},
            {"role": "rag-specialist", "focus": "索引/检索质量分析"},
            {"role": "ops-copilot", "focus": "处置建议合成"},
        ]
    return [
        {"role": "cost-analyst", "focus": "Token/成本拓扑分析"},
        {"role": "approval-agent", "focus": "止血方案审批链"},
        {"role": "ops-copilot", "focus": "升级与沟通草案"},
    ]


def _tasks_for_mode(mode: str, event: AgentEvent, playbook_id: str) -> list[dict[str, Any]]:
    base = [{"agent": "ops-copilot", "task": "playbook 约束推理", "status": "pending"}]
    if mode == "sub_agent":
        return [
            {"agent": "metrics-analyst", "task": "query_agent_metrics + config", "status": "pending"},
            *base,
        ]
    if mode == "multi_agent":
        return [
            {"agent": "triage-agent", "task": f"分类 {event.symptom}", "status": "pending"},
            {"agent": "rag-specialist", "task": "索引 lag / 空检索率分析", "status": "pending"},
            *base,
        ]
    if mode == "agent_team":
        return [
            {"agent": "cost-analyst", "task": "路由 Token 拓扑与预算偏差", "status": "pending"},
            {"agent": "approval-agent", "task": "高风险步骤审批链", "status": "pending"},
            *base,
        ]
    return base
