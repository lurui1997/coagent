import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.channels.feishu_im import (
    build_incident_card,
    get_tenant_access_token,
    reset_token_cache,
    send_incident_card,
    send_interactive_card,
)
from app.config import settings
from app.llm.client import MOCK_RESPONSES
from app.models.event import AgentEvent


def _resp(json_data: dict, status: int = 200) -> httpx.Response:
    req = httpx.Request("POST", "https://open.feishu.cn/open-apis/test")
    return httpx.Response(status, json=json_data, request=req)


@pytest.fixture(autouse=True)
def feishu_settings(monkeypatch):
    reset_token_cache()
    monkeypatch.setattr(settings, "feishu_app_id", "cli_test")
    monkeypatch.setattr(settings, "feishu_app_secret", "secret_test")
    monkeypatch.setattr(settings, "feishu_chat_id", "oc_test_chat")
    monkeypatch.setattr(settings, "feishu_api_base", "https://open.feishu.cn/open-apis")


def test_build_incident_card_structure():
    event = AgentEvent(
        event_id="evt-1",
        agent_id="cs-bot",
        agent_name="客服 Agent",
        type="run_fail",
        symptom="rate_limit",
        error="OpenAI 429",
        log_snippet="",
        cost_yuan_today=8.5,
        budget_yuan_daily=20,
        retry_webhook="http://localhost:8000/demo/retry/cs-bot",
        ts="2026-06-27T14:00:00+08:00",
    )
    llm = MOCK_RESPONSES["cs_rate_limit"]
    score = {"total": 87, "grade": "executable", "labels": {"grade_display": "🟢 可执行"}}

    card = build_incident_card(event, llm, score)
    assert card["header"]["template"] == "green"
    assert any(el.get("tag") == "action" for el in card["elements"])
    actions = next(el for el in card["elements"] if el.get("tag") == "action")
    assert actions["actions"][0]["url"] == event.retry_webhook


def test_get_tenant_access_token_caches():
    mock_client = MagicMock()
    mock_client.post.return_value = _resp(
        {"code": 0, "tenant_access_token": "tok_abc", "expire": 7200}
    )

    token1 = get_tenant_access_token(mock_client)
    token2 = get_tenant_access_token(mock_client)

    assert token1 == "tok_abc"
    assert token2 == "tok_abc"
    assert mock_client.post.call_count == 1


def test_send_interactive_card():
    mock_client = MagicMock()
    mock_client.post.side_effect = [
        _resp({"code": 0, "tenant_access_token": "tok_abc", "expire": 7200}),
        _resp({"code": 0, "data": {"message_id": "om_test123"}}),
    ]

    card = {"config": {"wide_screen_mode": True}, "elements": []}
    msg_id = send_interactive_card("oc_test_chat", card, client=mock_client)

    assert msg_id == "om_test123"
    assert mock_client.post.call_count == 2
    send_call = mock_client.post.call_args_list[1]
    assert send_call.kwargs["params"] == {"receive_id_type": "chat_id"}
    body = send_call.kwargs["json"]
    assert body["receive_id"] == "oc_test_chat"
    assert body["msg_type"] == "interactive"
    assert json.loads(body["content"]) == card


@pytest.mark.asyncio
async def test_send_incident_card_mock_when_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "feishu_app_id", "")
    event = AgentEvent(
        event_id="evt-1",
        agent_id="cs-bot",
        agent_name="客服 Agent",
        type="run_fail",
        symptom="rate_limit",
        ts="2026-06-27T14:00:00+08:00",
    )
    msg_id = await send_incident_card(event, MOCK_RESPONSES["cs_rate_limit"], {"total": 87})
    assert msg_id == "mock-msg-id"


@pytest.mark.asyncio
async def test_send_incident_card_calls_api(monkeypatch):
    event = AgentEvent(
        event_id="evt-1",
        agent_id="cs-bot",
        agent_name="客服 Agent",
        type="run_fail",
        symptom="rate_limit",
        error="429",
        retry_webhook="http://localhost:8000/demo/retry/cs-bot",
        ts="2026-06-27T14:00:00+08:00",
    )
    with patch("app.channels.feishu_im.send_interactive_card", return_value="om_live") as mock_send:
        msg_id = await send_incident_card(
            event, MOCK_RESPONSES["cs_rate_limit"], {"total": 87, "grade": "executable", "labels": {}}
        )
    assert msg_id == "om_live"
    mock_send.assert_called_once()
