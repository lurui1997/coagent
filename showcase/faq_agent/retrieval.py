from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
KB_PATH = DATA_DIR / "faq.json"
META_PATH = DATA_DIR / "index_meta.json"

_PUNCT_MAP = str.maketrans(
    {"，": ",", "。": ".", "？": "?", "！": "!", "：": ":", "；": ";", "（": "(", "）": ")", "　": " "}
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

    @property
    def is_empty(self) -> bool:
        return len(self.hits) == 0


def _normalize(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "").translate(_PUNCT_MAP).lower().strip()
    return re.sub(r"\s+", " ", t)


def _load_meta() -> dict:
    if not META_PATH.exists():
        return {"retrieval_threshold": 0.7, "max_chunks": 3}
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def _load_kb() -> list[dict]:
    return json.loads(KB_PATH.read_text(encoding="utf-8"))


def _score_entry(query: str, entry: dict) -> float:
    if entry.get("enabled") is False:
        return 0.0
    q = _normalize(query)
    score = 0.0
    question = _normalize(entry.get("question", ""))
    if question and question in q:
        score += 0.6
    for kw in entry.get("keywords") or []:
        kw_n = _normalize(kw)
        if kw_n and kw_n in q:
            score += 0.25
    for syn in entry.get("synonyms") or []:
        syn_n = _normalize(syn)
        if syn_n and syn_n in q:
            score += 0.15
    return min(score, 1.0)


def retrieve(query: str, *, force_empty: bool = False) -> RetrievalResult:
    meta = _load_meta()
    threshold = float(meta.get("retrieval_threshold", 0.7))
    max_chunks = int(meta.get("max_chunks", 3))
    if force_empty:
        return RetrievalResult(hits=[], threshold=threshold, max_score=0.0)

    scored = []
    for entry in _load_kb():
        s = _score_entry(query, entry)
        if s >= threshold:
            scored.append(RetrievalHit(entry=entry, score=s))
    scored.sort(key=lambda h: (-h.score, -int(h.entry.get("priority") or 0)))
    hits = scored[:max_chunks]
    return RetrievalResult(
        hits=hits,
        threshold=threshold,
        max_score=hits[0].score if hits else 0.0,
    )
