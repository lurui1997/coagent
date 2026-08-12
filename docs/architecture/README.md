# CoAgent Architecture (C4)

本目录描述 **Inline Observer（R1）** 接入后的系统结构，采用 [C4 Model](https://c4model.com/) 四层中的 Context / Container / Component。

| 文档 | 说明 |
|------|------|
| [c4-inline-observer.html](./c4-inline-observer.html) | 可交互 C4 图（Context / Container / Component） |
| [../adr/0001-otel-trajectory-contract.md](../adr/0001-otel-trajectory-contract.md) | Trajectory 主契约：OTLP/JSON + GenAI 语义约定 |
| [../dev-deploy-test.md](../dev-deploy-test.md) | API、本地运行与测试 |

## 一句话

Demo Agent（cs/rag/content）导出 Trajectory → CoAgent `/v1/traces` 观察并检测 → 提升为 `AgentEvent` → 现有 Playbook / 评分 / 审计处置闭环。
