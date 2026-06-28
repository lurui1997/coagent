from __future__ import annotations

import os

import httpx

from app.models.event import AgentEvent


class CoAgentClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.environ.get("COAGENT_URL", "http://localhost:8000")).rstrip("/")

    def post_event(self, event: AgentEvent, operator: str = "agent-runtime") -> dict:
        resp = httpx.post(
            f"{self.base_url}/events",
            json=event.model_dump(),
            headers={"X-Operator": operator},
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()

    def health(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/health", timeout=3.0)
            return r.is_success
        except httpx.HTTPError:
            return False
