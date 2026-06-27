import asyncio
import json
import logging
import time
from typing import Any

import httpx

from app.config import settings
from app.models.event import AgentEvent
from app.models.llm_output import LLMOutput

logger = logging.getLogger(__name__)

_TOKEN_CACHE: dict[str, Any] = {"token": "", "expires_at": 0.0}

_GRADE_HEADER_TEMPLATE = {
    "executable": "green",
    "needs_confirmation": "orange",
    "escalate": "red",
}


class FeishuAPIError(RuntimeError):
    pass


def _plain_text(content: str) -> dict:
    return {"tag": "plain_text", "content": content}


def _lark_md(content: str) -> dict:
    return {"tag": "lark_md", "content": content}


def build_incident_card(event: AgentEvent, llm: LLMOutput, score: dict) -> dict:
    """Build Feishu interactive message card (schema 2.0)."""
    grade = score.get("grade", "")
    total = score.get("total", 0)
    grade_display = score.get("labels", {}).get("grade_display", "")

    steps_lines = "\n".join(
        f"{step.order}. **[{step.risk}]** {step.action}" for step in llm.steps[:5]
    )

    elements: list[dict] = [
        {"tag": "div", "text": _lark_md(f"**Agent：** `{event.agent_id}` · `{event.agent_name}`")},
        {"tag": "div", "text": _lark_md(f"**错误：** {event.error or 'N/A'}")},
        {
            "tag": "div",
            "text": _lark_md(
                f"**今日成本：** ¥{event.cost_yuan_today} / ¥{event.budget_yuan_daily}"
            ),
        },
        {"tag": "hr"},
        {"tag": "div", "text": _lark_md(f"**处置建议**\n{steps_lines or '—'}")},
    ]

    actions: list[dict] = []
    if event.retry_webhook and llm.retry_recommended:
        actions.append(
            {
                "tag": "button",
                "text": _plain_text("一键重试"),
                "type": "primary",
                "url": event.retry_webhook,
            }
        )

    if actions:
        elements.append({"tag": "action", "actions": actions})

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": _plain_text(f"Agent 异常 | Score {total} {grade_display}"),
            "template": _GRADE_HEADER_TEMPLATE.get(grade, "red"),
        },
        "elements": elements,
    }


def _api_base() -> str:
    return settings.feishu_api_base.rstrip("/")


def _parse_api_response(data: dict) -> dict:
    if data.get("code") != 0:
        raise FeishuAPIError(
            f"Feishu API error: {data.get('msg', 'unknown')} (code={data.get('code')})"
        )
    return data


def get_tenant_access_token(client: httpx.Client | None = None) -> str:
    now = time.time()
    if _TOKEN_CACHE["token"] and now < _TOKEN_CACHE["expires_at"]:
        return _TOKEN_CACHE["token"]

    payload = {
        "app_id": settings.feishu_app_id,
        "app_secret": settings.feishu_app_secret,
    }
    url = f"{_api_base()}/auth/v3/tenant_access_token/internal"

    if client is None:
        with httpx.Client(timeout=settings.feishu_timeout_s) as c:
            resp = c.post(url, json=payload)
            resp.raise_for_status()
            data = _parse_api_response(resp.json())
    else:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = _parse_api_response(resp.json())

    token = data["tenant_access_token"]
    expire = int(data.get("expire", 7200))
    _TOKEN_CACHE["token"] = token
    _TOKEN_CACHE["expires_at"] = now + max(expire - 60, 60)
    return token


def send_interactive_card(
    chat_id: str,
    card: dict,
    *,
    client: httpx.Client | None = None,
    token: str | None = None,
) -> str:
    access_token = token or get_tenant_access_token(client)
    url = f"{_api_base()}/im/v1/messages"
    params = {"receive_id_type": "chat_id"}
    body = {
        "receive_id": chat_id,
        "msg_type": "interactive",
        "content": json.dumps(card, ensure_ascii=False),
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }

    if client is None:
        with httpx.Client(timeout=settings.feishu_timeout_s) as c:
            resp = c.post(url, params=params, json=body, headers=headers)
            resp.raise_for_status()
            data = _parse_api_response(resp.json())
    else:
        resp = client.post(url, params=params, json=body, headers=headers)
        resp.raise_for_status()
        data = _parse_api_response(resp.json())

    message_id = data.get("data", {}).get("message_id")
    if not message_id:
        raise FeishuAPIError("Feishu API returned no message_id")
    return message_id


def _send_feishu_sync(event: AgentEvent, llm: LLMOutput, score: dict) -> str:
    card = build_incident_card(event, llm, score)
    message_id = send_interactive_card(settings.feishu_chat_id, card)
    logger.info("Feishu card sent: message_id=%s agent=%s", message_id, event.agent_id)
    return message_id


async def send_incident_card(event: AgentEvent, llm: LLMOutput, score: dict) -> str | None:
    if not settings.feishu_app_id or not settings.feishu_app_secret or not settings.feishu_chat_id:
        logger.info("Feishu not configured, skipping card send (mock mode)")
        return "mock-msg-id"

    return await asyncio.to_thread(_send_feishu_sync, event, llm, score)


def reset_token_cache() -> None:
    """Test helper: clear cached tenant token."""
    _TOKEN_CACHE["token"] = ""
    _TOKEN_CACHE["expires_at"] = 0.0
