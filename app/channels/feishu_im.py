import asyncio
import json
import logging

from app.config import settings
from app.models.event import AgentEvent
from app.models.llm_output import LLMOutput

logger = logging.getLogger(__name__)


async def send_incident_card(event: AgentEvent, llm: LLMOutput, score: dict) -> str | None:
    if not settings.feishu_app_id or not settings.feishu_chat_id:
        logger.info("Feishu not configured, skipping card send (mock mode)")
        return "mock-msg-id"

    try:
        return await asyncio.to_thread(_send_feishu_sync, event, llm, score)
    except ImportError:
        logger.warning("Feishu SDK not installed, using mock")
        return "mock-msg-id"


def _send_feishu_sync(event: AgentEvent, llm: LLMOutput, score: dict) -> str:
    grade = score.get("labels", {}).get("grade_display", "")
    steps_text = "\n".join(f"{s.order}. [{s.risk}] {s.action}" for s in llm.steps[:3])
    card = {
        "header": {"title": f"🔴 Agent 异常 | {event.agent_id} | Score {score['total']} {grade}"},
        "elements": [
            {"tag": "div", "text": f"错误：{event.error or 'N/A'}"},
            {"tag": "div", "text": f"今日：¥{event.cost_yuan_today} / ¥{event.budget_yuan_daily}"},
            {"tag": "div", "text": steps_text},
        ],
    }
    if event.retry_webhook:
        card["elements"].append({
            "tag": "action",
            "actions": [{"tag": "button", "text": "一键重试", "url": event.retry_webhook}],
        })
    logger.info("Feishu card prepared: %s", json.dumps(card, ensure_ascii=False)[:200])
    return "feishu-msg-sent"
