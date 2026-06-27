#!/usr/bin/env python3
"""One-shot generator for CoAgent Excalidraw diagrams."""
import json
from pathlib import Path

OUT = Path(__file__).parent

# Colors from excalidraw-diagram color-palette.md
C = {
    "primary_fill": "#3b82f6",
    "primary_stroke": "#1e3a5f",
    "secondary_fill": "#60a5fa",
    "start_fill": "#fed7aa",
    "start_stroke": "#c2410c",
    "end_fill": "#a7f3d0",
    "end_stroke": "#047857",
    "decision_fill": "#fef3c7",
    "decision_stroke": "#b45309",
    "ai_fill": "#ddd6fe",
    "ai_stroke": "#6d28d9",
    "error_fill": "#fecaca",
    "error_stroke": "#b91c1c",
    "title": "#1e40af",
    "subtitle": "#3b82f6",
    "body": "#64748b",
    "text_dark": "#374151",
    "evidence_bg": "#1e293b",
    "evidence_text": "#22c55e",
    "line": "#64748b",
}


def base_doc(elements):
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20},
        "files": {},
    }


_n = [100000]


def nid(prefix="el"):
    _n[0] += 1
    return f"{prefix}_{_n[0]}"


def rect(x, y, w, h, text, fill, stroke, rid=None, font_size=16):
    rid = rid or nid("rect")
    tid = nid("txt")
    return [
        {
            "type": "rectangle",
            "id": rid,
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "strokeColor": stroke,
            "backgroundColor": fill,
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": _n[0],
            "version": 1,
            "versionNonce": _n[0] + 1,
            "isDeleted": False,
            "groupIds": [],
            "boundElements": [{"id": tid, "type": "text"}],
            "link": None,
            "locked": False,
            "roundness": {"type": 3},
        },
        {
            "type": "text",
            "id": tid,
            "x": x + 8,
            "y": y + h / 2 - (font_size * 1.25 * text.count("\n")) / 2 - 4,
            "width": w - 16,
            "height": font_size * 1.25 * (text.count("\n") + 1),
            "text": text,
            "originalText": text,
            "fontSize": font_size,
            "fontFamily": 3,
            "textAlign": "center",
            "verticalAlign": "middle",
            "strokeColor": C["text_dark"],
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 1,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": _n[0] + 2,
            "version": 1,
            "versionNonce": _n[0] + 3,
            "isDeleted": False,
            "groupIds": [],
            "boundElements": None,
            "link": None,
            "locked": False,
            "containerId": rid,
            "lineHeight": 1.25,
        },
    ], rid


def diamond(x, y, size, text, did=None):
    did = did or nid("dia")
    tid = nid("txt")
    return [
        {
            "type": "diamond",
            "id": did,
            "x": x,
            "y": y,
            "width": size,
            "height": size,
            "strokeColor": C["decision_stroke"],
            "backgroundColor": C["decision_fill"],
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": _n[0],
            "version": 1,
            "versionNonce": _n[0] + 1,
            "isDeleted": False,
            "groupIds": [],
            "boundElements": [{"id": tid, "type": "text"}],
            "link": None,
            "locked": False,
        },
        {
            "type": "text",
            "id": tid,
            "x": x + 10,
            "y": y + size / 2 - 12,
            "width": size - 20,
            "height": 24,
            "text": text,
            "originalText": text,
            "fontSize": 14,
            "fontFamily": 3,
            "textAlign": "center",
            "verticalAlign": "middle",
            "strokeColor": C["text_dark"],
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 1,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": _n[0] + 2,
            "version": 1,
            "versionNonce": _n[0] + 3,
            "isDeleted": False,
            "groupIds": [],
            "boundElements": None,
            "link": None,
            "locked": False,
            "containerId": did,
            "lineHeight": 1.25,
        },
    ], did


def label(x, y, text, size=20, color=None):
    tid = nid("lbl")
    return {
        "type": "text",
        "id": tid,
        "x": x,
        "y": y,
        "width": len(text) * size * 0.55,
        "height": size * 1.4,
        "text": text,
        "originalText": text,
        "fontSize": size,
        "fontFamily": 3,
        "textAlign": "left",
        "verticalAlign": "top",
        "strokeColor": color or C["title"],
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "angle": 0,
        "seed": _n[0],
        "version": 1,
        "versionNonce": _n[0] + 1,
        "isDeleted": False,
        "groupIds": [],
        "boundElements": None,
        "link": None,
        "locked": False,
        "containerId": None,
        "lineHeight": 1.25,
    }


def arrow(x1, y1, x2, y2, start=None, end=None, label_text=None):
    aid = nid("arr")
    dx, dy = x2 - x1, y2 - y1
    el = {
        "type": "arrow",
        "id": aid,
        "x": x1,
        "y": y1,
        "width": abs(dx) or 1,
        "height": abs(dy) or 1,
        "strokeColor": C["primary_stroke"],
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "angle": 0,
        "seed": _n[0],
        "version": 1,
        "versionNonce": _n[0] + 1,
        "isDeleted": False,
        "groupIds": [],
        "boundElements": None,
        "link": None,
        "locked": False,
        "points": [[0, 0], [dx, dy]],
        "startBinding": {"elementId": start, "focus": 0, "gap": 4} if start else None,
        "endBinding": {"elementId": end, "focus": 0, "gap": 4} if end else None,
        "startArrowhead": None,
        "endArrowhead": "arrow",
    }
    out = [el]
    if label_text:
        out.append(
            label((x1 + x2) / 2 - 40, (y1 + y2) / 2 - 24, label_text, 12, C["body"])
        )
    return out


def zone(x, y, w, h, title):
    zid = nid("zone")
    return [
        {
            "type": "rectangle",
            "id": zid,
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "strokeColor": C["line"],
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 1,
            "strokeStyle": "dashed",
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": _n[0],
            "version": 1,
            "versionNonce": _n[0] + 1,
            "isDeleted": False,
            "groupIds": [],
            "boundElements": None,
            "link": None,
            "locked": False,
            "roundness": {"type": 3},
        },
        label(x + 12, y + 8, title, 16, C["subtitle"]),
    ]


def evidence(x, y, w, h, text):
    rid = nid("ev")
    tid = nid("evtxt")
    return [
        {
            "type": "rectangle",
            "id": rid,
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "strokeColor": C["evidence_bg"],
            "backgroundColor": C["evidence_bg"],
            "fillStyle": "solid",
            "strokeWidth": 1,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": _n[0],
            "version": 1,
            "versionNonce": _n[0] + 1,
            "isDeleted": False,
            "groupIds": [],
            "boundElements": [{"id": tid, "type": "text"}],
            "link": None,
            "locked": False,
            "roundness": {"type": 3},
        },
        {
            "type": "text",
            "id": tid,
            "x": x + 10,
            "y": y + 10,
            "width": w - 20,
            "height": h - 20,
            "text": text,
            "originalText": text,
            "fontSize": 13,
            "fontFamily": 3,
            "textAlign": "left",
            "verticalAlign": "top",
            "strokeColor": C["evidence_text"],
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 1,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": _n[0] + 2,
            "version": 1,
            "versionNonce": _n[0] + 3,
            "isDeleted": False,
            "groupIds": [],
            "boundElements": None,
            "link": None,
            "locked": False,
            "containerId": rid,
            "lineHeight": 1.25,
        },
    ]


def arrow_waypoints(x, y, points, start=None, end=None, label_text=None, dashed=False):
    """Orthogonal arrow through waypoints; points are relative to (x,y)."""
    aid = nid("arr")
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    el = {
        "type": "arrow",
        "id": aid,
        "x": x,
        "y": y,
        "width": max(xs) - min(xs) or 1,
        "height": max(ys) - min(ys) or 1,
        "strokeColor": C["primary_stroke"],
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "dashed" if dashed else "solid",
        "roughness": 0,
        "opacity": 100,
        "angle": 0,
        "seed": _n[0],
        "version": 1,
        "versionNonce": _n[0] + 1,
        "isDeleted": False,
        "groupIds": [],
        "boundElements": None,
        "link": None,
        "locked": False,
        "points": points,
        "startBinding": {"elementId": start, "focus": 0, "gap": 6} if start else None,
        "endBinding": {"elementId": end, "focus": 0, "gap": 6} if end else None,
        "startArrowhead": None,
        "endArrowhead": "arrow",
    }
    out = [el]
    if label_text:
        mid = points[len(points) // 2]
        out.append(label(x + mid[0] - 36, y + mid[1] - 28, label_text, 12, C["body"]))
    return out


def flow_chip(x, y, text, fill, stroke):
    return rect(x, y, 118, 36, text, fill, stroke, font_size=12)


def build_architecture():
    els = []
    # ── Header ──
    els.append(label(40, 16, "CoAgent 技术架构", 28))
    els.append(label(40, 52, "FastAPI · Python 3.11 · async Pipeline · 配置驱动 Playbook", 14, C["body"]))

    # ── Summary flow (Level 1 zoom) ──
    els.append(label(40, 88, "主链路", 14, C["subtitle"]))
    chips = [
        ("Webhook", C["start_fill"], C["start_stroke"]),
        ("Router", C["decision_fill"], C["decision_stroke"]),
        ("Playbook", C["primary_fill"], C["primary_stroke"]),
        ("LLM", C["ai_fill"], C["ai_stroke"]),
        ("Score", C["end_fill"], C["end_stroke"]),
        ("Admin / 飞书", C["secondary_fill"], C["primary_stroke"]),
    ]
    chip_ids = []
    cx = 110
    for i, (t, fill, stroke) in enumerate(chips):
        r, rid = flow_chip(cx + i * 138, 82, t, fill, stroke)
        els.extend(r)
        chip_ids.append(rid)
        if i < len(chips) - 1:
            els.extend(arrow(cx + i * 138 + 118, 100, cx + (i + 1) * 138, 100))

    # ── External (left column) ──
    els.extend(zone(40, 140, 210, 460, "外部系统"))
    ext_specs = [
        ("Agent 运行时", "cs-bot · rag-bot\n· content-bot", C["start_fill"], C["start_stroke"], 168),
        ("LLM API", "OpenAI 兼容\nhttpx async", C["ai_fill"], C["ai_stroke"], 318),
        ("飞书 IM", "S1 卡片\nRetry · L2 降级", C["end_fill"], C["end_stroke"], 468),
    ]
    ext = []
    for title, body, fill, stroke, ey in ext_specs:
        r, rid = rect(58, ey, 174, 72, f"{title}\n{body}", fill, stroke, font_size=13)
        els.extend(r)
        ext.append((rid, ey + 36))

    # ── CoAgent service (center) ──
    els.extend(zone(280, 140, 800, 460, "CoAgent 服务"))

    # Layer 1: Presentation + API
    els.append(label(300, 168, "接入 & 表现", 13, C["body"]))
    r, web = rect(300, 188, 175, 62, "Admin HTMX\n4 Tabs · EventSource", C["secondary_fill"], C["primary_stroke"], font_size=13)
    els.extend(r)
    r, api = rect(500, 188, 175, 62, "API Layer\nevents · admin · demo", C["primary_fill"], C["primary_stroke"], font_size=13)
    els.extend(r)
    r, health = rect(700, 188, 120, 62, "health\nreplay · stats", C["secondary_fill"], C["primary_stroke"], font_size=12)
    els.extend(r)

    # Layer 2: Orchestrator (hero)
    els.append(label(300, 268, "编排", 13, C["body"]))
    r, orch = rect(420, 282, 240, 68, "Orchestrator\n幂等 · 超时 30s · timeline 持久化", C["start_fill"], C["start_stroke"], font_size=14)
    els.extend(r)

    # Layer 3: Domain pipeline (horizontal spine)
    els.append(label(300, 368, "领域层 Pipeline", 13, C["body"]))
    pipe_y = 388
    pipe_specs = [
        ("Scenario Router", "(type,symptom)\n→ playbook_id", C["decision_fill"], C["decision_stroke"]),
        ("PlaybookEngine", "ops_playbooks.json\nmock tools ×3", C["primary_fill"], C["primary_stroke"]),
        ("LLM Client", "LLMOutput\nretry ×1", C["ai_fill"], C["ai_stroke"]),
        ("把握度评分器", "数据·手册·推理\n🟢🟡🔴", C["end_fill"], C["end_stroke"]),
    ]
    pipe = []
    px = 292
    for t, sub, fill, stroke in pipe_specs:
        r, rid = rect(px, pipe_y, 148, 72, f"{t}\n{sub}", fill, stroke, font_size=12)
        els.extend(r)
        pipe.append(rid)
        px += 168

    # Layer 4: Infra
    els.append(label(300, 478, "基础设施", 13, C["body"]))
    r, sse = rect(320, 498, 130, 52, "SSE Manager\npub/sub", C["secondary_fill"], C["primary_stroke"], font_size=12)
    els.extend(r)
    r, db = rect(490, 498, 130, 52, "SQLite\ncoagent.db", C["secondary_fill"], C["primary_stroke"], font_size=12)
    els.extend(r)
    r, cfg = rect(660, 498, 130, 52, "Settings\n.env", C["secondary_fill"], C["primary_stroke"], font_size=12)
    els.extend(r)

    # Layer 5: Data
    els.extend(zone(300, 562, 760, 52, "数据层 data/"))
    r, data = rect(318, 578, 724, 28, "ops_playbooks.json  ·  scenarios/s1|s2|s3.json  ·  agents.json  ·  calibration/", C["primary_fill"], C["primary_stroke"], font_size=12)

    els.extend(r)

    # ── Evidence (right column) ──
    els.append(label(1100, 140, "接口 & 协议", 14, C["subtitle"]))
    els.extend(evidence(1100, 168, 290, 188, 'POST /events\n{\n  "type": "run_fail",\n  "symptom": "rate_limit",\n  "agent_id": "cs-bot",\n  "event_id": "evt-s1-demo"\n}'))
    els.extend(evidence(1100, 372, 290, 228, "SSE incident 事件序\n─────────────────\nincident_started\ntool_called ×3\nllm_reasoning\nllm_result\nscore_computed\nchannel_sync\nincident_completed"))

    # ── Arrows (minimal crossings) ──
    # External Agent → API
    els.extend(arrow(232, ext[0][1], 500, 219, ext[0][0], api, "POST /events"))
    # Admin → API trigger
    els.extend(arrow(475, 219, 500, 219, web, api))
    # API → Orchestrator
    els.extend(arrow_waypoints(587, 250, [[0, 0], [0, 32]], api, orch))
    # Orchestrator → pipeline entry
    els.extend(arrow_waypoints(540, 350, [[0, 0], [-248, 0], [-248, 38]], orch, pipe[0]))
    # Pipeline spine left → right
    for i in range(len(pipe) - 1):
        els.extend(arrow(292 + (i + 1) * 168 - 20, pipe_y + 36, 292 + (i + 1) * 168, pipe_y + 36, pipe[i], pipe[i + 1]))
    # LLM ↔ external LLM API (out left, return)
    els.extend(arrow_waypoints(688, pipe_y + 36, [[0, 0], [40, 0], [40, -68], [-490, -68], [-490, 0]], pipe[2], ext[1][0], "chat"))
    # Scorer → SQLite
    els.extend(arrow_waypoints(884, pipe_y + 72, [[0, 0], [0, 62], [-394, 62], [-394, 0]], pipe[3], db))
    # Orchestrator → SSE
    els.extend(arrow_waypoints(540, 350, [[0, 0], [-220, 0], [-220, 148]], orch, sse))
    # Playbook → data
    els.extend(arrow_waypoints(514, pipe_y + 72, [[0, 0], [0, 118]], pipe[1], data))
    # Scorer → Feishu (S1)
    els.extend(arrow_waypoints(884, pipe_y + 36, [[0, 0], [60, 0], [60, 120], [-710, 120], [-710, -6]], pipe[3], ext[2][0], "S1"))
    # SSE → Admin (live timeline)
    els.extend(arrow_waypoints(385, 498, [[0, 0], [-85, 0], [-85, -280]], sse, web, "SSE", dashed=True))

    return base_doc(els)


def build_business_flow():
    els = []
    els.append(label(40, 20, "CoAgent 业务流程图", 28))
    els.append(label(40, 58, "Incident 处置：听见异常 → 推理 → Score → 人工动作 → 飞轮", 14, C["body"]))

    cx = 380
    y = 100
    step_h = 100
    ids = []

    steps = [
        ("运维 / Webhook", "POST /events\nPOST /admin/trigger/s1", C["start_fill"], C["start_stroke"]),
        ("幂等检查", "event_id 10min\n→ duplicate?", C["decision_fill"], C["decision_stroke"]),
        ("Scenario Router", "run_fail+rate_limit → cs_rate_limit\nempty_retrieval → rag\nover_budget → cost", C["decision_fill"], C["decision_stroke"]),
        ("PlaybookEngine", "query_agent_metrics\nquery_agent_config\nsearch_ops_playbook", C["primary_fill"], C["primary_stroke"]),
        ("LLM Client", "reasoning_chain ≥3\nsteps + retry_recommended", C["ai_fill"], C["ai_stroke"]),
        ("把握度评分", "D 0.35 + P 0.35 + C 0.30\n→ 🟢🟡🔴 grade", C["end_fill"], C["end_stroke"]),
    ]

    for i, (title, body, fill, stroke) in enumerate(steps):
        r, rid = rect(cx - 140, y + i * step_h, 280, 75, f"{title}\n{body}", fill, stroke, font_size=13)
        els.extend(r)
        ids.append(rid)
        if i > 0:
            els.extend(arrow(cx, y + (i - 1) * step_h + 75, cx, y + i * step_h, ids[i - 1], rid))

    # Branch after score
    branch_y = y + len(steps) * step_h + 20
    d, did = diamond(cx - 60, branch_y, 120, "grade?")
    els.extend(d)
    els.extend(arrow(cx, y + (len(steps) - 1) * step_h + 75, cx, branch_y, ids[-1], did))

    branches = [
        (80, branch_y + 160, "🟢 executable\nScore ≥80\n一键 Retry", C["end_fill"], C["end_stroke"]),
        (cx - 140, branch_y + 160, "🟡 needs_confirmation\n60–79\n禁止 Retry", C["decision_fill"], C["decision_stroke"]),
        (680, branch_y + 160, "🔴 escalate\n<60\n@负责人升级", C["error_fill"], C["error_stroke"]),
    ]
    bids = []
    for bx, by, text, fill, stroke in branches:
        r, rid = rect(bx, by, 200, 80, text, fill, stroke, font_size=13)
        els.extend(r)
        bids.append((rid, bx + 100, by))
        els.extend(arrow(cx - 30, branch_y + 120, bx + 100, by, did, rid))

    # Audit + complete
    audit_y = branch_y + 280
    r, audit = rect(cx - 140, audit_y, 280, 70, "SQLite 持久化\ntimeline_json · llm_json · score_json", C["secondary_fill"], C["primary_stroke"], font_size=13)
    els.extend(r)
    for _, bx, by in bids:
        els.extend(arrow(bx, by + 80, cx, audit_y, None, audit))

    r, complete = rect(cx - 140, audit_y + 100, 280, 60, "incident_completed\nSSE → Admin Tab1/3", C["end_fill"], C["end_stroke"], font_size=13)
    els.extend(r)
    els.extend(arrow(cx, audit_y + 70, cx, audit_y + 100, audit, complete))

    r, fly = rect(cx - 140, audit_y + 190, 280, 60, "Tab4 飞轮\n👍/👎 → stats", C["primary_fill"], C["primary_stroke"], font_size=13)
    els.extend(r)
    els.extend(arrow(cx, audit_y + 160, cx, audit_y + 190, complete, fly))

    # S1 feishu side path
    r, fs = rect(720, y + 4 * step_h, 200, 75, "飞书 S1\n卡片 + Retry\n(L2 降级)", C["end_fill"], C["end_stroke"], font_size=13)
    els.extend(r)
    els.extend(arrow(cx + 140, y + 4 * step_h + 35, 720, y + 4 * step_h + 35, ids[4], fs, "cs_rate_limit"))
    els.extend(arrow(820, y + 4 * step_h + 75, cx + 140, audit_y + 20, fs, audit, "channel_sync"))

    # Evidence timeline (left column)
    els.extend(evidence(40, 100, 260, 200, "S1 · S2 · S3\n\nS1: 87 executable\nS2: 72 needs_confirmation\nS3: 58 escalate\n\n耗时 ~8–15s"))

    # Replay note (bottom left, away from main flow)
    els.append(label(40, 340, "Replay", 16, C["subtitle"]))
    els.append(label(40, 365, "POST /admin/replay/{trace_id}", 13, C["body"]))
    els.append(label(40, 388, "只读重放 timeline，不调 LLM", 12, C["body"]))

    return base_doc(els)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, builder in [
        ("coagent-architecture.excalidraw", build_architecture),
        ("coagent-business-flow.excalidraw", build_business_flow),
    ]:
        path = OUT / name
        path.write_text(json.dumps(builder(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
