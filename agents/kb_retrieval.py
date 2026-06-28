"""FAQ 加权评分检索 — 规则见 data/agent_kb/RETRIEVAL.md"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

KB_PATH = settings.data_dir / "agent_kb" / "faq.json"
META_PATH = settings.data_dir / "agent_kb" / "index_meta.json"

_PUNCT_MAP = str.maketrans(
    {
        "，": ",",
        "。": ".",
        "？": "?",
        "！": "!",
        "：": ":",
        "；": ";",
        "（": "(",
        "）": ")",
        "　": " ",
    }
)


@dataclass
class RetrievalHit:
    entry: dict
    score: float


@dataclass
class RetrievalResult:
    hits: list[RetrievalHit]
    threshold: float
    max_score: float
    index_version: str
    kb_last_sync: str
    kb_entries: int

    @property
    def is_empty(self) -> bool:
        return len(self.hits) == 0


def _term_match(query: str, term: str) -> bool:
    """术语匹配：子串命中；排除已知交叉误命中（如「物质保修」→「质保」）。"""
    term = _normalize(term)
    if not term or term not in query:
        return False
    if term == "质保" and "物质保修" in query:
        return False
    return True


def _normalize(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "").translate(_PUNCT_MAP).lower().strip()
    return re.sub(r"\s+", " ", t)


def _load_meta() -> dict:
    if not META_PATH.exists():
        return {"retrieval_threshold": 0.7, "max_chunks": 3, "index_version": "v1", "kb_last_sync": ""}
    with open(META_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_kb() -> list[dict]:
    with open(KB_PATH, encoding="utf-8") as f:
        return json.load(f)


def _score_entry(query: str, entry: dict) -> float:
    if entry.get("enabled") is False:
        return 0.0

    score = 0.0
    q_norm = _normalize(entry.get("question", ""))
    if q_norm and q_norm in query:
        score += 0.45

    kw_hits = 0
    for kw in entry.get("keywords", []):
        if _term_match(query, kw):
            kw_hits += 1
    score += min(0.60, kw_hits * 0.30)

    syn_hits = 0
    for syn in entry.get("synonyms", []):
        if _term_match(query, syn):
            syn_hits += 1
    score += min(0.40, syn_hits * 0.20)

    category = _normalize(entry.get("category", ""))
    if category and _term_match(query, category):
        score += 0.15
    else:
        for tag in entry.get("tags", []):
            if _term_match(query, tag):
                score += 0.15
                break

    priority = int(entry.get("priority", 3))
    score += 0.02 * (priority - 3)

    # 仅命中一个泛化关键词、且未匹配标准问法时封顶（避免「暗物质保修期」误命中）
    question_norm = _normalize(entry.get("question", ""))
    if kw_hits == 1 and syn_hits == 0 and question_norm not in query:
        score = min(score, 0.55)

    return min(1.0, max(0.0, score))


def retrieve(query: str) -> RetrievalResult:
    meta = _load_meta()
    threshold = float(meta.get("retrieval_threshold", 0.7))
    max_chunks = int(meta.get("max_chunks", 3))
    kb = _load_kb()
    q = _normalize(query)

    scored: list[RetrievalHit] = []
    max_score = 0.0
    for entry in kb:
        s = _score_entry(q, entry)
        max_score = max(max_score, s)
        if s >= threshold:
            scored.append(RetrievalHit(entry=entry, score=round(s, 4)))

    scored.sort(key=lambda h: (-h.score, -int(h.entry.get("priority", 3)), h.entry["id"]))
    return RetrievalResult(
        hits=scored[:max_chunks],
        threshold=threshold,
        max_score=round(max_score, 4),
        index_version=str(meta.get("index_version", "")),
        kb_last_sync=str(meta.get("kb_last_sync", "")),
        kb_entries=len(kb),
    )


def build_retrieval_log(query: str, result: RetrievalResult) -> str:
    hit_ids = [h.entry["id"] for h in result.hits]
    return (
        f"query={query!r}; max_score={result.max_score}; threshold={result.threshold}; "
        f"hits={len(result.hits)}; hit_ids={hit_ids}; "
        f"index_version={result.index_version}; kb_last_sync={result.kb_last_sync}; "
        f"kb_entries={result.kb_entries}"
    )
