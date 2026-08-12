import json
import logging
import re
from typing import Any

import httpx

from app.config import settings
from app.llm.model_router import ModelRouter
from app.models.llm_output import LLMOutput

logger = logging.getLogger(__name__)

JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class LLMClient:
    def __init__(self):
        self.router = ModelRouter()

    def _require_api_key(self) -> None:
        if not (settings.llm_api_key or "").strip():
            raise RuntimeError(
                "LLM_API_KEY is required. Configure DeepSeek (or compatible) credentials in .env; "
                "production mock LLM path has been removed."
            )

    def _parse_json_content(self, content: str) -> dict[str, Any]:
        text = JSON_FENCE_RE.sub("", content.strip())
        return json.loads(text)

    async def _chat_completion(
        self,
        messages: list[dict],
        model: str,
        *,
        temperature: float,
        json_mode: bool = True,
    ) -> str:
        self._require_api_key()
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}

        async with httpx.AsyncClient(timeout=settings.llm_timeout_s) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if json_mode and resp.status_code == 400:
                logger.info("LLM rejected response_format, retrying without json_mode for %s", model)
                payload.pop("response_format", None)
                resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

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
        schema_hint = (
            '{"impact":"string","hypothesis":["string"],'
            '"reasoning_chain":["string","string","string"],'
            '"steps":[{"order":1,"action":"string","command":"string|null","risk":"low|medium|high"}],'
            '"comms_draft":"string","retry_recommended":bool}'
        )
        messages = messages + [
            {"role": "system", "content": f"Respond with valid JSON only matching: {schema_hint}"}
        ]

        content = await self._chat_completion(messages, model, temperature=0.3)
        data = self._parse_json_content(content)
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

    async def react_step(
        self,
        messages: list[dict],
        playbook_id: str,
        *,
        playbook: dict | None = None,
        event_type: str | None = None,
        remaining_tools: list[str] | None = None,
        use_fallback: bool = False,
    ) -> dict[str, Any]:
        model = self.router.resolve(
            playbook or {},
            event_type=event_type,
            use_fallback=use_fallback,
        )
        schema_hint = (
            '{"thought":"string","action":"tool|finish","tool":"string or null when finish"}'
        )
        step_messages = messages + [
            {
                "role": "system",
                "content": (
                    f"Respond with valid JSON only matching: {schema_hint}. "
                    f"Remaining tools: {remaining_tools or []}"
                ),
            }
        ]

        content = await self._chat_completion(step_messages, model, temperature=0.2)
        return self._parse_json_content(content)
