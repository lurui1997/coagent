from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


async def answer_with_llm(*, query: str, context: str) -> dict[str, Any]:
    """Call real DeepSeek (or compatible) chat API. No mock path."""
    if not (settings.llm_api_key or "").strip():
        raise RuntimeError("LLM_API_KEY required for showcase FAQ agent")

    system = (
        "你是企业客服知识库助手。仅依据提供的检索片段回答用户问题。"
        "若片段不足以回答，明确说不知道，不要编造政策或数字。"
        "用简洁中文回答。"
    )
    user = f"检索片段：\n{context}\n\n用户问题：{query}"
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
    }
    # DeepSeek V4 may enable thinking by default; disable for FAQ latency.
    if "deepseek-v4" in (settings.llm_model or ""):
        payload["thinking"] = {"type": "disabled"}

    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
    async with httpx.AsyncClient(timeout=settings.llm_timeout_s) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = message.get("content") or ""
    usage = data.get("usage") or {}
    return {
        "answer": content.strip(),
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "model": data.get("model") or settings.llm_model,
        "raw": data,
    }
