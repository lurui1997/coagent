import json
from pathlib import Path

import pytest

from app.config import settings
from app.llm.client import LLMClient, MOCK_RESPONSES
from app.models.event import AgentEvent
from app.playbooks.engine import PlaybookEngine
from app.scoring.scorer import compute_score, grade_from_total

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def engine():
    return PlaybookEngine(DATA_DIR / "ops_playbooks.json")


@pytest.mark.parametrize("scenario,playbook_id,expected_grade,score_range", [
    ("s1", "cs_rate_limit", "executable", (82, 88)),
    ("s2", "rag_empty_retrieval", "needs_confirmation", (65, 75)),
    ("s3", "cost_over_budget", "escalate", (50, 58)),
])
def test_score_ranges(scenario, playbook_id, expected_grade, score_range, engine):
    with open(DATA_DIR / "scenarios" / f"{scenario}.json") as f:
        event = AgentEvent.model_validate(json.load(f))
    llm = MOCK_RESPONSES[playbook_id]
    pb = engine.get_playbook_for_scoring(playbook_id)
    tool_results = [{"tool": "t", "success": True, "result": {}}] * 3
    settings.demo_mode = True
    score = compute_score(event, llm, pb, tool_results)
    assert score["grade"] == expected_grade
    assert score_range[0] <= score["total"] <= score_range[1]


def test_grade_thresholds():
    assert grade_from_total(85) == "executable"
    assert grade_from_total(70) == "needs_confirmation"
    assert grade_from_total(50) == "escalate"


def test_clamp_applied(engine):
    with open(DATA_DIR / "scenarios" / "s1.json") as f:
        event = AgentEvent.model_validate(json.load(f))
    llm = MOCK_RESPONSES["cs_rate_limit"]
    pb = engine.get_playbook_for_scoring("cs_rate_limit")
    tool_results = [{"tool": "t", "success": True, "result": {}}] * 3
    score = compute_score(event, llm, pb, tool_results)
    assert "reasoning_consistency_raw" in score["factors"]
    assert "reasoning_consistency" in score["factors"]
