from typing import Literal

from pydantic import BaseModel, Field


class Step(BaseModel):
    order: int
    action: str
    command: str | None = None
    risk: Literal["low", "medium", "high"]


class LLMOutput(BaseModel):
    impact: str
    hypothesis: list[str]
    reasoning_chain: list[str] = Field(min_length=3)
    steps: list[Step] = Field(min_length=1)
    comms_draft: str
    retry_recommended: bool
