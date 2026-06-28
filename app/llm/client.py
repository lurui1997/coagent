import json
import logging
from typing import Any

import httpx

from app.config import settings
from app.llm.model_router import ModelRouter
from app.models.llm_output import LLMOutput, Step

logger = logging.getLogger(__name__)

MOCK_RESPONSES = {
    "cs_rate_limit": LLMOutput(
        impact="cs-bot 客服 Agent 因并发配置从 5 提升至 10，触发 OpenAI 429 限流，失败率 38%，客服 thread 不可用。",
        hypothesis=["并发配置变更导致 RPM 超限", "OpenAI gpt-4o-mini 配额打满"],
        reasoning_chain=[
            "大促前 concurrent 从 5 调至 10",
            "OpenAI 返回 429 Rate limit exceeded",
            "cs-bot 客服 thread 全部失败，客户无法获得响应",
        ],
        steps=[
            Step(order=1, action="等待 60s 后重试", command="sleep 60 && retry", risk="low"),
            Step(order=2, action="降低 concurrent 至 5", command="config set concurrent=5", risk="medium"),
            Step(order=3, action="切换 backup API key", command="config set api_key=backup", risk="medium"),
        ],
        comms_draft="cs-bot 因 API 限流暂时不可用，已降并发并准备切换 backup key，预计 5 分钟内恢复。",
        retry_recommended=True,
    ),
    "rag_empty_retrieval": LLMOutput(
        impact="rag-bot 空检索率从 5% 飙升至 35%，FAQ 更新后索引未 rebuild，Agent 仍自信作答导致客诉上升。",
        hypothesis=["知识库索引 lag 1 天", "空检索导致幻觉答复"],
        reasoning_chain=[
            "FAQ 更新后 kb_last_sync 滞后 1 天",
            "空检索率从 5% 升至 35%",
            "Agent 无检索结果仍生成答案，客诉 +12",
        ],
        steps=[
            Step(order=1, action="Rebuild 知识库索引", command="kb rebuild --version v2.4", risk="medium"),
            Step(order=2, action="启用兜底 prompt 拒绝无检索作答", command="config set fallback_prompt=strict", risk="low"),
            Step(order=3, action="检查 FAQ 更新同步状态", command="kb sync --force", risk="low"),
        ],
        comms_draft="RAG Agent 空检索率异常，正在 rebuild 索引，请勿 Retry 重复幻觉答复。",
        retry_recommended=False,
    ),
    "cost_over_budget": LLMOutput(
        impact="content-bot 日成本 ¥28.5 超预算 ¥20（+42%），新模板 v3-longform + marketing-batch 路由 Token 突增 180%。",
        hypothesis=["新模板 max_tokens=4096 昨日发布", "marketing-batch 批量任务流量激增"],
        reasoning_chain=[
            "v3-longform 模板昨日发布，max_tokens 4096",
            "marketing-batch 路由 Token 1.2M/日 (+180%)",
            "日成本 ¥28.5 超预算 ¥20，需负责人止血",
        ],
        steps=[
            Step(order=1, action="对 marketing-batch 路由限流", command="route limit marketing-batch --rpm 10", risk="medium"),
            Step(order=2, action="降级至 gpt-4o-mini", command="config set model=gpt-4o-mini", risk="medium"),
            Step(order=3, action="暂停 batch 任务", command="batch pause --route marketing-batch", risk="high"),
            Step(order=4, action="升级负责人审批止血方案", command=None, risk="high"),
        ],
        comms_draft="content-bot 日成本超预算，已建议限流和暂停 batch，需 @负责人 审批后执行。",
        retry_recommended=False,
    ),
}


class LLMClient:
    def __init__(self):
        self.router = ModelRouter()

    async def generate(
        self,
        messages: list[dict],
        playbook_id: str,
        *,
        playbook: dict | None = None,
        event_type: str | None = None,
        use_fallback: bool = False,
    ) -> tuple[LLMOutput, str]:
        model = self.router.resolve(
            playbook or {},
            event_type=event_type,
            use_fallback=use_fallback,
        )
        if settings.use_mock_llm:
            return MOCK_RESPONSES[playbook_id], model

        schema_hint = (
            '{"impact":"string","hypothesis":["string"],'
            '"reasoning_chain":["string","string","string"],'
            '"steps":[{"order":1,"action":"string","command":"string|null","risk":"low|medium|high"}],'
            '"comms_draft":"string","retry_recommended":bool}'
        )
        messages = messages + [
            {"role": "system", "content": f"Respond with valid JSON only matching: {schema_hint}"}
        ]

        async with httpx.AsyncClient(timeout=settings.llm_timeout_s) as client:
            resp = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            return LLMOutput.model_validate(data), model

    async def generate_with_retry(
        self,
        messages: list[dict],
        playbook_id: str,
        *,
        playbook: dict | None = None,
        event_type: str | None = None,
    ) -> tuple[LLMOutput, str]:
        try:
            return await self.generate(
                messages,
                playbook_id,
                playbook=playbook,
                event_type=event_type,
            )
        except Exception as e:
            logger.warning("LLM first attempt failed: %s", e)
            return await self.generate(
                messages,
                playbook_id,
                playbook=playbook,
                event_type=event_type,
                use_fallback=True,
            )
