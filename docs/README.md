# CoAgent 文档索引

本目录按「先跑起来看到价值 → 再深入架构与决策」组织。

## 快速入口

| 文档 | 适合谁 | 内容 |
|------|--------|------|
| [../README.md](../README.md) | 首次访客 | 产品价值、Quickstart、演示路径 |
| [dev-deploy-test.md](./dev-deploy-test.md) | 开发者 | 环境变量、API、测试、部署 |
| [showcase/README.md](./showcase/README.md) | 演示 / 分享 | FAQ Agent 切口与 CoAgent 闭环 |

## 架构与契约

| 文档 | 内容 |
|------|------|
| [architecture/README.md](./architecture/README.md) | C4 · Inline Observer 入口 |
| [architecture/r1-inline-observer.md](./architecture/r1-inline-observer.md) | OTLP 轨迹观察与事故提升 |
| [adr/0001-otel-trajectory-contract.md](./adr/0001-otel-trajectory-contract.md) | Trajectory 主契约 ADR |

## Showcase FAQ Agent

| 文档 | 内容 |
|------|------|
| [showcase/faq-agent-decisions.md](./showcase/faq-agent-decisions.md) | 场景 / 包装 / LLM / 观测决策锁定 |
| [showcase/faq-agent-status.md](./showcase/faq-agent-status.md) | 交付结果、演示脚本、已知问题 |
| [superpowers/specs/2026-08-12-showcase-faq-agent-design.md](./superpowers/specs/2026-08-12-showcase-faq-agent-design.md) | 设计摘要 |

## 产品叙事（黑客松 / 路演存档）

`intro/` 与 `HACKATHON_CONTEXT.md` 保留早期路演材料。
运行与接入以本索引上方文档及 README Quickstart 为准。
部分旧文仍可能提及 `MOCK_LLM`，**生产路径已移除 Mock，必须以真实 `LLM_API_KEY` 运行**。
