import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import admin, agents, demo, events
from app.config import settings
from app.db import get_feedback_stats, get_incident, get_latest_scores, init_db, list_audit_actions, list_feedback_history, list_incidents
from app.static_assets import static_asset_url, static_dir_version, versioned_static_url
from app.timeutil import format_display
from app.ultra.api import router as ultra_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="CoAgent", description="ToB Agent Ops Copilot", lifespan=lifespan)

BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = BASE_DIR / "web" / "static"
static_dir.mkdir(parents=True, exist_ok=True)


@app.middleware("http")
async def cache_policy(request: Request, call_next):
    path = request.url.path
    if path.startswith("/static/") and not request.query_params.get("v"):
        filename = path.removeprefix("/static/")
        redirect_to = versioned_static_url(static_dir, filename)
        if redirect_to:
            return RedirectResponse(redirect_to, status_code=302)

    response = await call_next(request)
    content_type = response.headers.get("content-type", "")

    if "text/html" in content_type:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    elif path.startswith("/static/") and request.query_params.get("v"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"

    return response


app.include_router(events.router)
app.include_router(agents.router)
app.include_router(admin.router)
app.include_router(demo.router)
app.include_router(ultra_router)

templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))
templates.env.filters["format_cn_time"] = format_display
templates.env.globals["static_asset"] = lambda name: static_asset_url(static_dir, name)
templates.env.globals["static_v"] = static_dir_version(static_dir, "style.css", "theme.js")

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def admin_page(request: Request, tab: int = 1, trace: str | None = None):
    # 旧版 Tab 4/5/6 兼容；Tab 3 现为「审计复盘」，不可再映射到工作台
    legacy_tab_map = {4: 3, 5: 3, 6: 2}
    tab = legacy_tab_map.get(tab, tab)
    if tab not in (1, 2, 3):
        tab = 1
    agents_path = settings.data_dir / "agents.json"
    with open(agents_path, encoding="utf-8") as f:
        agents = json.load(f)
    latest_scores = get_latest_scores()
    incidents = list_incidents(20)
    stats = get_feedback_stats()
    audit_logs = list_audit_actions(limit=50)
    feedback_history = list_feedback_history(30)
    audit_detail = None
    if trace:
        audit_detail = get_incident(trace)
        if audit_detail:
            audit_detail["audit_actions"] = list_audit_actions(trace)
    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "tab": tab,
            "agents": agents,
            "latest_scores": latest_scores,
            "incidents": incidents,
            "stats": stats,
            "audit_logs": audit_logs,
            "feedback_history": feedback_history,
            "audit_detail": audit_detail,
            "demo_mode": settings.demo_mode,
            "escalate_user": settings.feishu_escalate_user_id or "@oncall",
            "active_trace": trace,
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
