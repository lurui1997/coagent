from __future__ import annotations

from agents.content_bot import ContentBot
from agents.cs_bot import CSBot
from agents.rag_bot import RAGBot

AGENT_IDS = ("cs-bot", "rag-bot", "content-bot")

_INSTANCES: dict[str, CSBot | RAGBot | ContentBot] = {
    "cs-bot": CSBot(),
    "rag-bot": RAGBot(),
    "content-bot": ContentBot(),
}


def get_agent(agent_id: str) -> CSBot | RAGBot | ContentBot:
    if agent_id not in _INSTANCES:
        raise KeyError(f"Unknown agent: {agent_id}")
    return _INSTANCES[agent_id]
