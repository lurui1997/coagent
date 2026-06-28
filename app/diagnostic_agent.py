import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.config import settings
from app.llm.client import LLMClient
from app.models.event import AgentEvent
from app.models.llm_output import LLMOutput
from app.playbooks.engine import PlaybookEngine

logger = logging.getLogger(__name__)

RecordFn = Callable[[str, dict], Awaitable[None]]


class DiagnosticAgent:
    """ReAct 诊断 Agent：按需调用 Playbook 工具，最终输出 LLMOutput 供同一套把握度评分。"""

    def __init__(self, engine: PlaybookEngine, llm: LLMClient):
        self.engine = engine
        self.llm = llm

    async def run(
        self,
        event: AgentEvent,
        playbook_id: str,
        record: RecordFn,
    ) -> tuple[list[dict[str, Any]], LLMOutput, str]:
        pb = self.engine.get(playbook_id)
        if not pb:
            raise ValueError(f"Unknown playbook: {playbook_id}")

        await record(
            "diagnostic_agent_started",
            {"playbook_id": playbook_id, "tools": pb["required_tools"]},
        )

        tool_results: list[dict[str, Any]] = []
        called: set[str] = set()
        messages = self._build_react_messages(playbook_id, event)

        for step in range(settings.diagnostic_max_steps):
            action = await self._next_action(
                messages, playbook_id, pb, event, called, step + 1
            )
            await record(
                "agent_thought",
                {
                    "step": step + 1,
                    "thought": action.get("thought", ""),
                    "action": action.get("action"),
                    "tool": action.get("tool"),
                },
            )

            if action.get("action") == "finish":
                break

            if action.get("action") != "tool":
                logger.warning("Invalid ReAct action at step %s: %s", step + 1, action)
                break

            tool_name = action.get("tool")
            if not tool_name or tool_name in called:
                messages.append({"role": "assistant", "content": json.dumps(action, ensure_ascii=False)})
                messages.append(
                    {
                        "role": "user",
                        "content": f"Observation: tool {tool_name!r} skipped (already called or invalid)",
                    }
                )
                continue

            try:
                result = await asyncio.wait_for(
                    self.engine.run_tool(playbook_id, tool_name, event),
                    timeout=settings.tool_timeout_s,
                )
            except asyncio.TimeoutError:
                result = {
                    "tool": tool_name,
                    "result": pb["tool_mocks"].get(tool_name, {}),
                    "success": False,
                    "degraded": True,
                }

            tool_results.append(result)
            called.add(tool_name)
            await record("tool_called", result)

            messages.append({"role": "assistant", "content": json.dumps(action, ensure_ascii=False)})
            messages.append(
                {
                    "role": "user",
                    "content": f"Observation: {json.dumps(result, ensure_ascii=False)}",
                }
            )

            if not [t for t in pb["required_tools"] if t not in called]:
                await record(
                    "agent_thought",
                    {
                        "step": step + 2,
                        "thought": "所需工具均已调用，开始综合根因链与处置方案",
                        "action": "finish",
                    },
                )
                break

        await self._ensure_required_tools(playbook_id, event, pb, called, tool_results, record)

        messages = self.engine.build_llm_messages(playbook_id, event, tool_results)
        llm_output, llm_model = await asyncio.wait_for(
            self.llm.generate_with_retry(
                messages,
                playbook_id,
                playbook=pb,
                event_type=event.type,
            ),
            timeout=settings.llm_timeout_s,
        )
        return tool_results, llm_output, llm_model

    async def _next_action(
        self,
        messages: list[dict],
        playbook_id: str,
        pb: dict,
        event: AgentEvent,
        called: set[str],
        step: int,
    ) -> dict[str, Any]:
        remaining = [t for t in pb["required_tools"] if t not in called]
        if not remaining:
            return {"thought": "证据已齐，结束工具阶段", "action": "finish"}

        if settings.use_mock_llm:
            tool = remaining[0]
            thoughts = {
                "query_agent_metrics": "先查运行指标，确认失败率/限流/空检索/成本是否异常",
                "query_agent_config": "再查配置变更，对比昨日参数找根因线索",
                "search_ops_playbook": "检索 Ops 手册，对齐标准处置步骤",
            }
            return {
                "thought": thoughts.get(tool, f"调用 {tool} 补充证据"),
                "action": "tool",
                "tool": tool,
            }

        return await self.llm.react_step(
            messages,
            playbook_id,
            playbook=pb,
            event_type=event.type,
            remaining_tools=remaining,
        )

    async def _ensure_required_tools(
        self,
        playbook_id: str,
        event: AgentEvent,
        pb: dict,
        called: set[str],
        tool_results: list[dict[str, Any]],
        record: RecordFn,
    ) -> None:
        for tool_name in pb["required_tools"]:
            if tool_name in called:
                continue
            logger.warning("ReAct missed tool %s, backfilling", tool_name)
            try:
                result = await asyncio.wait_for(
                    self.engine.run_tool(playbook_id, tool_name, event),
                    timeout=settings.tool_timeout_s,
                )
            except asyncio.TimeoutError:
                result = {
                    "tool": tool_name,
                    "result": pb["tool_mocks"].get(tool_name, {}),
                    "success": False,
                    "degraded": True,
                }
            tool_results.append(result)
            called.add(tool_name)
            await record("tool_called", result)

    def _build_react_messages(self, playbook_id: str, event: AgentEvent) -> list[dict]:
        pb = self.engine.get(playbook_id)
        tools_json = json.dumps(self.engine.tool_definitions(playbook_id), ensure_ascii=False, indent=2)
        event_context = event.model_dump_json(indent=2)
        system = f"""{pb["system_prompt"]}

你是 Diagnostic Agent，使用 ReAct（Reason + Act）逐步收集证据后再给出最终诊断。
可用工具：
{tools_json}

每轮只输出一个 JSON（无 markdown）：
- 调用工具: {{"thought":"推理","action":"tool","tool":"<工具名>"}}
- 证据足够: {{"thought":"推理","action":"finish"}}

规则：在 finish 前至少调用 query_agent_metrics 与 search_ops_playbook；全部 required_tools 调用后再 finish。"""
        user = f"Agent 事件：\n{event_context}\n\n请开始 ReAct 诊断。"
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
