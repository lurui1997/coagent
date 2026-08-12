from __future__ import annotations

from app.config import settings

from agents.claude_runner import claude_print
from agents.coagent_client import CoAgentClient
from agents.cost_tracker import (
    TEMPLATE_CONFIG,
    build_content_prompt,
    build_over_budget_log,
    estimate_call_cost,
    load_state,
    record_run,
    reset_state,
    save_state,
)
from agents.scenario_events import build_over_budget_event, load_scenario_event
from agents.telemetry import SimulateBundle, spans_from_event

AGENT_ID = "content-bot"
AGENT_NAME = "内容生成 Agent"


class ContentBot:
    def __init__(self, client: CoAgentClient | None = None):
        self.client = client or CoAgentClient(settings.coagent_public_url)

    @property
    def budget(self) -> float:
        return settings.content_budget_yuan_daily

    def get_cost_status(self) -> dict:
        state = load_state()
        return {
            "agent": AGENT_ID,
            "date": state.date,
            "cost_yuan_today": state.cost_yuan,
            "budget_yuan_daily": state.budget,
            "utilization_pct": state.utilization_pct,
            "billable_tokens": state.billable_tokens,
            "run_count": state.run_count,
            "last_template": state.last_template,
            "over_budget": state.over_budget,
            "recent_runs": state.runs[-5:],
        }

    def reset_cost(self) -> dict:
        state = reset_state()
        return {"agent": AGENT_ID, "status": "reset", "cost_yuan_today": state.cost_yuan}

    def build_simulate(self) -> SimulateBundle:
        event = load_scenario_event("s3")
        return SimulateBundle(event=event, spans=spans_from_event(event), agent_id=AGENT_ID)

    def run_simulate(self) -> dict:
        bundle = self.build_simulate()
        telemetry = self.client.export_traces(bundle.to_otlp(), operator="content-bot/simulate")
        coagent = telemetry.get("incident") or {}
        return bundle.as_result(coagent, telemetry)

    def run_live(self, task: str, *, template: str = "longform") -> dict:
        if template not in TEMPLATE_CONFIG:
            template = "longform"

        state = load_state()
        budget = self.budget

        if state.over_budget:
            log = build_over_budget_log(state, task, None)
            event = build_over_budget_event(AGENT_ID, AGENT_NAME, state.cost_yuan, budget, log)
            spans = spans_from_event(event)
            telemetry = self.client.export_traces(
                SimulateBundle(event=event, spans=spans, agent_id=AGENT_ID, mode="live").to_otlp(),
                operator="content-bot/gate",
            )
            return {
                "agent": AGENT_ID,
                "mode": "live",
                "status": "cost_report",
                "symptom": "over_budget",
                "blocked": True,
                "message": "日预算已用尽，本次未调用 Claude",
                "cost_yuan_today": state.cost_yuan,
                "budget_yuan_daily": budget,
                "coagent": telemetry.get("incident") or {},
                "telemetry": telemetry,
            }

        prompt = build_content_prompt(task, template)
        claude = claude_print(prompt)
        if claude.returncode != 0:
            return {"agent": AGENT_ID, "mode": "live", "status": "error", "error": claude.combined[:500]}

        text = claude.stdout.strip()
        estimate = estimate_call_cost(prompt, text, template)
        state = record_run(state, task, estimate)
        save_state(state)

        base = {
            "agent": AGENT_ID,
            "mode": "live",
            "template": template,
            "content": text,
            "cost_yuan_today": state.cost_yuan,
            "budget_yuan_daily": budget,
            "utilization_pct": state.utilization_pct,
            "run_cost_yuan": estimate.cost_yuan,
            "billable_tokens": estimate.billable_tokens,
            "run_count": state.run_count,
        }

        if state.over_budget:
            log = build_over_budget_log(state, task, estimate)
            event = build_over_budget_event(AGENT_ID, AGENT_NAME, state.cost_yuan, budget, log)
            spans = spans_from_event(event)
            telemetry = self.client.export_traces(
                SimulateBundle(event=event, spans=spans, agent_id=AGENT_ID, mode="live").to_otlp(),
                operator="content-bot/live",
            )
            return {
                **base,
                "status": "cost_report",
                "symptom": "over_budget",
                "blocked": False,
                "coagent": telemetry.get("incident") or {},
                "telemetry": telemetry,
            }

        return {**base, "status": "ok"}
