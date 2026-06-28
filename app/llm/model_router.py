"""按 playbook / 评分分级 / 成本策略选择大模型。"""

from __future__ import annotations

from typing import Any

from app.config import settings


class ModelRouter:
    """Pro MVP：playbook 级 model 字段 + 分级/成本 fallback。"""

    DEFAULT_MODEL = "gpt-4o-mini"
    COST_ESCALATION_MODEL = "gpt-4o-mini"

    def resolve(
        self,
        playbook: dict[str, Any],
        *,
        grade: str | None = None,
        event_type: str | None = None,
        use_fallback: bool = False,
    ) -> str:
        primary = playbook.get("llm_model") or settings.llm_model or self.DEFAULT_MODEL
        fallback = playbook.get("fallback_model") or primary

        if use_fallback:
            return fallback

        # 成本事件强制降级小模型
        if event_type == "cost_report":
            return playbook.get("cost_model") or self.COST_ESCALATION_MODEL

        # 需升级场景优先 fallback（降本）
        if grade == "escalate" and playbook.get("fallback_model"):
            return fallback

        return primary
