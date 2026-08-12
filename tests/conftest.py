import os

# 部分 shell 环境 PYTEST_ADDOPTS 会导致 0 tests collected
os.environ.pop("PYTEST_ADDOPTS", None)

import pytest
from httpx import ASGITransport, AsyncClient

os.environ["DEMO_MODE"] = "true"
# Tests use process-local LLM stubs; production requires a real LLM_API_KEY.
os.environ.setdefault("LLM_API_KEY", "test-stub-key-not-for-production")

from app.config import settings
from app.db import init_db
from app.llm.client import LLMClient
from tests.llm_stubs import STUB_RESPONSES


async def _stub_generate(self, messages, playbook_id, *, playbook=None, event_type=None, use_fallback=False):
    model = self.router.resolve(playbook or {}, event_type=event_type, use_fallback=use_fallback)
    return STUB_RESPONSES[playbook_id], model


async def _stub_react_step(
    self,
    messages,
    playbook_id,
    *,
    playbook=None,
    event_type=None,
    remaining_tools=None,
    use_fallback=False,
):
    tool = (remaining_tools or ["search_ops_playbook"])[0]
    return {"thought": f"调用 {tool}", "action": "tool", "tool": tool}


@pytest.fixture(autouse=True)
def temp_db(request, tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(settings, "database_path", str(db_path))
    init_db()
    from app.telemetry.service import telemetry_service

    telemetry_service.ensure_schema()

    if request.node.get_closest_marker("live_llm"):
        # Real LLM path — do not stub client methods.
        if not os.environ.get("LLM_API_KEY") or os.environ["LLM_API_KEY"].startswith("test-stub"):
            pytest.skip("LLM_API_KEY not set for live_llm")
        monkeypatch.setattr(settings, "llm_api_key", os.environ["LLM_API_KEY"])
        if os.environ.get("LLM_BASE_URL"):
            monkeypatch.setattr(settings, "llm_base_url", os.environ["LLM_BASE_URL"])
        if os.environ.get("LLM_MODEL"):
            monkeypatch.setattr(settings, "llm_model", os.environ["LLM_MODEL"])
        if os.environ.get("LLM_FALLBACK_MODEL"):
            monkeypatch.setattr(settings, "llm_fallback_model", os.environ["LLM_FALLBACK_MODEL"])
    else:
        monkeypatch.setattr(settings, "llm_api_key", "test-stub-key-not-for-production")
        monkeypatch.setattr(LLMClient, "generate", _stub_generate)
        monkeypatch.setattr(LLMClient, "generate_with_retry", _stub_generate)
        monkeypatch.setattr(LLMClient, "react_step", _stub_react_step)

    yield db_path


@pytest.fixture
async def client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
