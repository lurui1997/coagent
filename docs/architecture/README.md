# CoAgent Architecture (C4)

本目录描述 **Inline Observer（R1）** 接入后的系统结构，采用 [C4 Model](https://c4model.com/) 四层中的 Context / Container / Component。

| 文档 | 说明 |
|------|------|
| [c4-inline-observer.html](./c4-inline-observer.html) | 可交互 C4 图（Context / Container / Component） |
| [r1-inline-observer.md](./r1-inline-observer.md) | OTLP 观察 → 检测 → 提升事故 |
| [../adr/0001-otel-trajectory-contract.md](../adr/0001-otel-trajectory-contract.md) | Trajectory 主契约：OTLP/JSON + GenAI 语义约定 |
| [../dev-deploy-test.md](../dev-deploy-test.md) | API、本地运行与测试 |
| [../showcase/README.md](../showcase/README.md) | FAQ Showcase 与质量事故闭环 |

## 一句话

Demo Agent（cs/rag/content）与 Showcase FAQ Agent 导出 Trajectory → CoAgent `/v1/traces` 观察并检测 → 提升为 `AgentEvent` → Playbook / 诊断 / 评分 / 审计处置闭环。

## 本地启动（真实 LLM）

```bash
set -a && source .env && set +a   # 需 LLM_API_KEY
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

价值演示路径见仓库 [README Quickstart](../../README.md#quickstart)。
