from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from showcase.faq_agent.agent import FAQAgent
from showcase.faq_agent.metrics import MetricsStore
from app.static_assets import static_asset_url

router = APIRouter(prefix="/showcase/faq", tags=["showcase-faq"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
_static_dir = Path(__file__).resolve().parents[2] / "web" / "static"
templates.env.globals["static_asset"] = lambda name: static_asset_url(_static_dir, name)
_metrics = MetricsStore()
_agent = FAQAgent(metrics=_metrics)


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    force_empty: bool = False
    allow_answer_on_empty: bool = False
    promote: bool = True


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    summary = _metrics.summary()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"summary": summary, "title": "Showcase FAQ Agent · Metrics"},
    )


@router.get("/metrics")
async def metrics_json():
    return _metrics.summary()


@router.post("/ask")
async def ask(body: AskRequest):
    return await _agent.ask(
        body.query,
        force_empty=body.force_empty,
        allow_answer_on_empty=body.allow_answer_on_empty,
        promote=body.promote,
    )


@router.post("/demo/empty-retrieval")
async def demo_empty_retrieval(
    query: str = Query(default="完全不存在的冷门政策 xyz-999"),
):
    """Reproducible quality-incident path for CoAgent demo."""
    return await _agent.ask(query, force_empty=True, allow_answer_on_empty=False, promote=True)
