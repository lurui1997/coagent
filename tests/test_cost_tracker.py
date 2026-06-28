import pytest

from agents.cost_tracker import estimate_call_cost, load_state, record_run, reset_state, save_state


@pytest.fixture(autouse=True)
def clean_cost_state(tmp_path, monkeypatch):
    state_file = tmp_path / "content_bot_cost.json"
    monkeypatch.setattr("agents.cost_tracker.STATE_PATH", state_file)
    reset_state()
    yield


def test_estimate_longform_cost_nonzero(monkeypatch):
    monkeypatch.setattr("agents.cost_tracker.settings.content_cost_per_1k_tokens", 0.024)
    est = estimate_call_cost("prompt " * 50, "output " * 80, "longform")
    assert est.billable_tokens > 0
    assert est.cost_yuan > 0
    assert est.template == "v3-longform"


def test_cumulative_over_budget(monkeypatch):
    monkeypatch.setattr("agents.cost_tracker.settings.content_budget_yuan_daily", 1.0)
    monkeypatch.setattr("agents.cost_tracker.settings.content_cost_per_1k_tokens", 0.24)

    state = load_state()
    est = estimate_call_cost("x" * 400, "y" * 600, "longform")
    state = record_run(state, "task-a", est)
    save_state(state)

    state = load_state()
    assert state.cost_yuan > 1.0
    assert state.over_budget


def test_record_run_accumulates():
    state = load_state()
    e1 = estimate_call_cost("a" * 200, "b" * 200, "standard")
    state = record_run(state, "t1", e1)
    e2 = estimate_call_cost("c" * 200, "d" * 200, "standard")
    state = record_run(state, "t2", e2)
    assert state.run_count == 2
    assert state.cost_yuan == round(e1.cost_yuan + e2.cost_yuan, 4)
