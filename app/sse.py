import asyncio
import json
import logging
from typing import Any

from app.timeutil import now_iso

logger = logging.getLogger(__name__)


class SSEManager:
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    def subscribe(self, trace_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.setdefault(trace_id, []).append(q)
        return q

    def unsubscribe(self, trace_id: str, q: asyncio.Queue) -> None:
        subs = self._subscribers.get(trace_id, [])
        if q in subs:
            subs.remove(q)
        if not subs:
            self._subscribers.pop(trace_id, None)

    async def emit(self, trace_id: str, event_type: str, payload: dict[str, Any]) -> None:
        event = {
            "type": event_type,
            "trace_id": trace_id,
            "ts": now_iso(),
            "payload": payload,
        }
        for q in self._subscribers.get(trace_id, []):
            await q.put(event)

    async def replay(self, trace_id: str, timeline: list[dict]) -> None:
        await self.emit(trace_id, "replay_started", {})
        for item in timeline:
            await self.emit(trace_id, item["type"], item.get("payload", {}))
            await asyncio.sleep(0.3)
        await self.emit(trace_id, "replay_completed", {})


sse_manager = SSEManager()
