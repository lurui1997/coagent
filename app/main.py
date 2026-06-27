import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import admin, demo, events
from app.config import settings
from app.db import get_feedback_stats, get_latest_scores, init_db, list_incidents

app = FastAPI(title="CoAgent", description="ToB Agent Ops Copilot")

app.include_router(events.router)
app.include_router(admin.router)
app.include_router(demo.router)

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))

static_dir = BASE_DIR / "web" / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
async def admin_page(request: Request, tab: int = 1):
    agents_path = settings.data_dir / "agents.json"
    with open(agents_path, encoding="utf-8") as f:
        agents = json.load(f)
    latest_scores = get_latest_scores()
    incidents = list_incidents(20)
    stats = get_feedback_stats()
    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "tab": tab,
            "agents": agents,
            "latest_scores": latest_scores,
            "incidents": incidents,
            "stats": stats,
            "demo_mode": settings.demo_mode,
            "escalate_user": settings.feishu_escalate_user_id or "@oncall",
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
