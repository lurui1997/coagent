from app.config import settings
from app.llm.model_router import ModelRouter


def test_resolve_env_model_by_default(monkeypatch):
    monkeypatch.setattr(settings, "llm_model", "kimi-k2.5")
    monkeypatch.setattr(settings, "llm_respect_playbook_model", False)
    router = ModelRouter()
    pb = {"llm_model": "gpt-4o", "fallback_model": "gpt-4o-mini"}
    assert router.resolve(pb) == "kimi-k2.5"


def test_resolve_playbook_primary_when_respected(monkeypatch):
    monkeypatch.setattr(settings, "llm_model", "kimi-k2.5")
    monkeypatch.setattr(settings, "llm_respect_playbook_model", True)
    router = ModelRouter()
    pb = {"llm_model": "gpt-4o", "fallback_model": "gpt-4o-mini"}
    assert router.resolve(pb) == "gpt-4o"


def test_resolve_cost_event_uses_cost_model_when_respected(monkeypatch):
    monkeypatch.setattr(settings, "llm_respect_playbook_model", True)
    router = ModelRouter()
    pb = {"llm_model": "gpt-4o", "cost_model": "gpt-4o-mini"}
    assert router.resolve(pb, event_type="cost_report") == "gpt-4o-mini"


def test_resolve_cost_event_uses_env_when_not_respected(monkeypatch):
    monkeypatch.setattr(settings, "llm_model", "kimi-k2.5")
    monkeypatch.setattr(settings, "llm_respect_playbook_model", False)
    router = ModelRouter()
    pb = {"llm_model": "gpt-4o", "cost_model": "gpt-4o-mini"}
    assert router.resolve(pb, event_type="cost_report") == "kimi-k2.5"


def test_resolve_escalate_uses_fallback_when_respected(monkeypatch):
    monkeypatch.setattr(settings, "llm_respect_playbook_model", True)
    router = ModelRouter()
    pb = {"llm_model": "gpt-4o", "fallback_model": "gpt-4o-mini"}
    assert router.resolve(pb, grade="escalate") == "gpt-4o-mini"


def test_resolve_explicit_fallback(monkeypatch):
    monkeypatch.setattr(settings, "llm_model", "kimi-k2.5")
    monkeypatch.setattr(settings, "llm_fallback_model", "gpt-4o-mini")
    monkeypatch.setattr(settings, "llm_respect_playbook_model", False)
    router = ModelRouter()
    pb = {"llm_model": "gpt-4o", "fallback_model": "gpt-4o-mini"}
    assert router.resolve(pb, use_fallback=True) == "gpt-4o-mini"
