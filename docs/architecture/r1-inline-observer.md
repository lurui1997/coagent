# R1：Demo Agent Inline Observer 接入说明

**状态：** 已实现（仓库内 `cs-bot` / `rag-bot` / `content-bot`）  
**契约：** [ADR-0001](../adr/0001-otel-trajectory-contract.md)  
**C4 图：** [c4-inline-observer.html](../architecture/c4-inline-observer.html)

## 目标

让演示 Agent 在运行时导出 Trajectory，由 CoAgent **持续观察**并在异常时自动打开既有处置流水线（Playbook → 诊断 → 评分 → 审计）。
Showcase FAQ Agent 走同一条 OTLP → Detector → Orchestrator 路径，用于质量事故叙事。

## 数据流

```text
Agent.build_simulate() / live 失败路径
  → OTLP/JSON spans（GenAI 属性 + coagent.*）
  → POST /v1/traces
  → 解析并写入 trajectory_* 表
  → Detector 识别 rate_limit / empty_retrieval / over_budget
  → 提升为 AgentEvent
  → Orchestrator.process_event(...)
```

管理台 `POST /agents/{id}/run?mode=simulate` **在进程内**调用 `TelemetryService`，避免对自身 `localhost` HTTP 回环。

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/traces` | 接收 OTLP/JSON；`?promote=true\|false` 控制是否提升事故 |
| GET | `/telemetry/runs` | 最近轨迹运行列表 |
| GET | `/telemetry/runs/{run_id}` | 单次运行详情（含 spans） |
| POST | `/agents/{id}/run` | simulate 走 Inline Observer；live 仍可由 Agent 客户端导出 |

## 关键属性（子集）

| 属性 | 用途 |
|------|------|
| `coagent.agent_id` / `coagent.agent_name` | 定位 Agent |
| `coagent.symptom` / `coagent.event_type` | 显式事故类型（演示优先） |
| `coagent.run_id` | 轨迹运行 ID |
| `gen_ai.*` / `error.type` / HTTP 429 | 启发式检测（无显式 symptom 时） |

## 本地验证

需要真实 `LLM_API_KEY`（生产 Mock 已移除）。若仅验证 Inline Observer 上报，可用 `promote=false` 或测试 stub。

```bash
set -a && source .env && set +a
DEMO_MODE=true uvicorn app.main:app --reload --port 8000
# 另开终端
curl -s -X POST http://localhost:8000/agents/cs-bot/run \
  -H 'Content-Type: application/json' \
  -d '{"mode":"simulate"}' | python3 -m json.tool
curl -s http://localhost:8000/telemetry/runs | python3 -m json.tool
```

Showcase 质量事故（空检索 promote）：

```bash
curl -s -X POST 'http://localhost:8000/showcase/faq/demo/empty-retrieval' | python3 -m json.tool
```

测试：

```bash
PYTHONPATH=. DEMO_MODE=true python -m pytest tests/test_telemetry.py tests/test_agents_api.py tests/test_showcase_faq.py -q
```

## 非目标（R1）

- 完整 OTLP/protobuf Collector
- 长期 Trace 查询 UI（当前仅 runs API + SQLite）
- 强制 LLM/工具流量代理
- 生产 Agent 平台双向 webhook（后续里程碑）
