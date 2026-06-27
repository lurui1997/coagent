from pydantic import BaseModel, Field


class AgentEvent(BaseModel):
    event_id: str
    agent_id: str
    agent_name: str
    type: str
    symptom: str
    error: str | None = None
    log_snippet: str = ""
    cost_yuan_today: float = 0.0
    budget_yuan_daily: float = 0.0
    retry_webhook: str | None = None
    ts: str
