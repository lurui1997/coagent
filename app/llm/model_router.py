"""按 .env 全局配置或 playbook 策略选择大模型。"""

from __future__ import annotations

from typing import Any

from app.config import settings


class ModelRouter:
    """优先使用 .env 的 LLM_MODEL；可选 LLM_RESPECT_PLAYBOOK_MODEL=true 恢复 playbook 级路由。"""

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
        env_primary = settings.llm_model or self.DEFAULT_MODEL
        env_fallback = settings.llm_fallback_model or env_primary
        pb_primary = playbook.get("llm_model") or env_primary
        pb_fallback = playbook.get("fallback_model") or pb_primary

        if settings.llm_respect_playbook_model:
            primary, fallback = pb_primary, pb_fallback
        else:
            primary, fallback = env_primary, env_fallback

        if use_fallback:
            return fallback

        if settings.llm_respect_playbook_model and event_type == "cost_report":
            return playbook.get("cost_model") or self.COST_ESCALATION_MODEL

        if settings.llm_respect_playbook_model and grade == "escalate" and playbook.get("fallback_model"):
            return fallback

        return primary
