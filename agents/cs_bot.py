from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

from agents.claude_runner import claude_print
from agents.coagent_client import CoAgentClient
from agents.scenario_events import build_rate_limit_event, load_scenario_event

AGENT_ID = "cs-bot"
AGENT_NAME = "客服 Agent"


class CSBot:
    def __init__(self, client: CoAgentClient | None = None):
        self.client = client or CoAgentClient(settings.coagent_public_url)

    def run_simulate(self) -> dict:
        event = load_scenario_event("s1")
        result = self.client.post_event(event, operator="cs-bot/simulate")
        return {"agent": AGENT_ID, "mode": "simulate", "coagent": result}

    def run_live(self, query: str) -> dict:
        prompt = (
            "你是电商客服 Agent（cs-bot）。用简洁中文回答用户问题，不超过 120 字。\n\n"
            f"用户问题：{query}"
        )
        claude = claude_print(prompt)
        if claude.is_rate_limited:
            event = build_rate_limit_event(
                AGENT_ID,
                AGENT_NAME,
                error=claude.combined[:500] or "Claude API rate limit",
                log_snippet=f"query={query!r}; claude_rc={claude.returncode}",
                coagent_base=settings.coagent_public_url,
            )
            coagent = self.client.post_event(event, operator="cs-bot/live")
            return {
                "agent": AGENT_ID,
                "mode": "live",
                "status": "run_fail",
                "symptom": "rate_limit",
                "coagent": coagent,
            }
        if claude.returncode != 0:
            return {
                "agent": AGENT_ID,
                "mode": "live",
                "status": "error",
                "error": claude.combined[:500],
            }
        return {
            "agent": AGENT_ID,
            "mode": "live",
            "status": "ok",
            "answer": claude.stdout.strip(),
        }

    def retry(self) -> dict:
        """CoAgent 一键重试回调：降并发后重新调用 Claude。"""
        prompt = (
            "你是电商客服 Agent。上一轮回合因 API 限流失败。"
            "现在并发已降为 5，请用一句话确认服务已恢复。"
        )
        claude = claude_print(prompt)
        return {
            "agent": AGENT_ID,
            "status": "ok" if claude.returncode == 0 else "failed",
            "message": claude.stdout.strip() or claude.stderr.strip() or "retry completed",
            "returncode": claude.returncode,
        }
