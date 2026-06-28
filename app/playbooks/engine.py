import asyncio
import json
from pathlib import Path
from typing import Any

from app.config import settings
from app.models.event import AgentEvent


class PlaybookEngine:
    def __init__(self, data_path: Path | None = None):
        path = data_path or settings.data_dir / "ops_playbooks.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self._playbooks = {p["id"]: p for p in data["playbooks"]}

    def get(self, playbook_id: str) -> dict | None:
        return self._playbooks.get(playbook_id)

    def all_ids(self) -> list[str]:
        return list(self._playbooks.keys())

    async def run_tool(self, playbook_id: str, tool_name: str, event: AgentEvent) -> dict[str, Any]:
        pb = self._playbooks[playbook_id]
        if tool_name not in pb["required_tools"]:
            return {"tool": tool_name, "result": {}, "success": False, "error": "unknown_tool"}
        mock = pb["tool_mocks"].get(tool_name, {})
        return {"tool": tool_name, "result": mock, "success": True}

    async def run_tools(self, playbook_id: str, event: AgentEvent) -> list[dict[str, Any]]:
        pb = self._playbooks[playbook_id]
        results = []
        for tool_name in pb["required_tools"]:
            results.append(await self.run_tool(playbook_id, tool_name, event))
        return results

    def tool_definitions(self, playbook_id: str) -> list[dict[str, str]]:
        pb = self._playbooks[playbook_id]
        descriptions = {
            "query_agent_metrics": "查询 Agent 运行指标（失败率、限流、空检索率、成本等）",
            "query_agent_config": "查询 Agent 配置（并发、模型、索引版本、预算等）",
            "search_ops_playbook": "检索 Ops 手册处置步骤",
        }
        return [
            {"name": name, "description": descriptions.get(name, name)}
            for name in pb["required_tools"]
        ]

    def build_llm_messages(self, playbook_id: str, event: AgentEvent, tool_results: list[dict]) -> list[dict]:
        pb = self._playbooks[playbook_id]
        tool_context = json.dumps(tool_results, ensure_ascii=False, indent=2)
        event_context = event.model_dump_json(indent=2)
        user_content = f"""分析以下 Agent 事件并输出 JSON（符合 LLMOutput schema）：

事件：
{event_context}

工具查询结果：
{tool_context}

Ops 手册参考：{pb['tool_mocks'].get('search_ops_playbook', {})}

输出要求：
- reasoning_chain 至少 3 步根因链
- steps 覆盖 OPS 手册建议
- retry_recommended: {pb.get('retry_recommended', False)}
- 只输出 JSON，无 markdown"""
        return [
            {"role": "system", "content": pb["system_prompt"]},
            {"role": "user", "content": user_content},
        ]

    def get_playbook_for_scoring(self, playbook_id: str) -> dict:
        return self._playbooks[playbook_id]
