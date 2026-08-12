"""Guard: diagnostic LLM prompts must require Simplified Chinese user-facing text."""

import json
from pathlib import Path

import pytest

from app.diagnostic_agent import DiagnosticAgent
from app.llm.client import LLMClient
from app.llm.language import USER_FACING_ZH_RULE, with_json_schema_instruction
from app.models.event import AgentEvent
from app.playbooks.engine import PlaybookEngine

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _s2_event() -> AgentEvent:
    with open(DATA_DIR / "scenarios" / "s2.json", encoding="utf-8") as f:
        return AgentEvent.model_validate(json.load(f))


def test_language_rule_mentions_simplified_chinese():
    assert "简体中文" in USER_FACING_ZH_RULE


def test_playbook_system_prompts_require_chinese():
    with open(DATA_DIR / "ops_playbooks.json", encoding="utf-8") as f:
        data = json.load(f)
    for pb in data["playbooks"]:
        assert "简体中文" in pb["system_prompt"], pb["id"]


def test_build_llm_messages_require_chinese():
    engine = PlaybookEngine(DATA_DIR / "ops_playbooks.json")
    msgs = engine.build_llm_messages("rag_empty_retrieval", _s2_event(), [])
    blob = "\n".join(m["content"] for m in msgs)
    assert "简体中文" in blob


def test_diagnostic_react_messages_require_chinese():
    agent = DiagnosticAgent(PlaybookEngine(DATA_DIR / "ops_playbooks.json"), LLMClient())
    msgs = agent._build_react_messages("rag_empty_retrieval", _s2_event())
    blob = "\n".join(m["content"] for m in msgs)
    assert "简体中文" in blob


def test_schema_instruction_requires_chinese_and_json():
    text = with_json_schema_instruction('{"impact":"string"}')
    assert "简体中文" in text
    assert "json" in text.lower() or "JSON" in text


def test_scenario_narratives_prefer_chinese():
    """Demo events should not force the model into English-only narratives."""
    for name in ("s1.json", "s2.json", "s3.json"):
        with open(DATA_DIR / "scenarios" / name, encoding="utf-8") as f:
            event = json.load(f)
        err = event.get("error") or ""
        log = event.get("log_snippet") or ""
        combined = f"{err} {log}"
        assert any("\u4e00" <= ch <= "\u9fff" for ch in combined), name
