import pytest
from httpx import ASGITransport, AsyncClient

from agents.cs_bot import CSBot
from agents.telemetry import spans_from_event
from app.telemetry.detector import detect_anomaly, detection_to_event
from app.telemetry.otlp_json import build_otlp_json, parse_otlp_json


@pytest.mark.asyncio
async def test_otlp_ingest_promotes_cs_rate_limit():
    from app.main import app

    bot = CSBot()
    payload = bot.build_simulate().to_otlp()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/v1/traces", json=payload, headers={"X-Operator": "pytest-otel"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["accepted_spans"] >= 2
    assert data["detected"] is True
    assert data["incident"]["status"] in ("ok", "duplicate")
    assert data["incident"].get("trace_id")

    run_id = data["run_id"]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        run = await client.get(f"/telemetry/runs/{run_id}")
    assert run.status_code == 200
    body = run.json()
    assert body["detected_symptom"] == "rate_limit"
    assert body["incident_trace_id"] == data["incident"]["trace_id"]


@pytest.mark.asyncio
async def test_otlp_ingest_without_promote_stores_only():
    from app.main import app

    bot = CSBot()
    payload = bot.build_simulate().to_otlp()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/v1/traces?promote=false", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["detected"] is True
    assert data["incident"] is None


def test_parse_roundtrip_preserves_symptom():
    bot = CSBot()
    bundle = bot.build_simulate()
    parsed = parse_otlp_json(bundle.to_otlp())
    detection = detect_anomaly(parsed)
    assert detection is not None
    assert detection.symptom == "rate_limit"
    event = detection_to_event(detection)
    assert event.type == "run_fail"
    assert event.agent_id == "cs-bot"


def test_heuristic_rate_limit_without_explicit_symptom():
    from app.telemetry.models import TelemetrySpan

    spans = [
        TelemetrySpan(
            trace_id="abc",
            span_id="1",
            name="gen_ai.chat",
            status_code="ERROR",
            status_message="HTTP 429 rate limit exceeded",
            attributes={"error.type": "rate_limit", "coagent.agent_id": "cs-bot"},
            resource_attributes={"service.name": "cs-bot"},
        )
    ]
    detection = detect_anomaly(spans)
    assert detection is not None
    assert detection.symptom == "rate_limit"


@pytest.mark.asyncio
async def test_agent_simulate_via_inline_observer_path():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for agent_id in ("cs-bot", "rag-bot", "content-bot"):
            resp = await client.post(f"/agents/{agent_id}/run", json={"mode": "simulate"})
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["coagent"].get("trace_id")
            assert data["telemetry"]["detected"] is True
            assert data["telemetry"]["accepted_spans"] >= 1
