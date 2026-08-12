# Showcase FAQ Agent

企业 FAQ Agent 切口：真实问答 + 量化看板 + 空检索质量事故接入 CoAgent。

## 为什么放在本仓

展示 CoAgent 的业务价值，而不是「又一个 RAG Demo」。

值班人看到的闭环是：

```text
FAQ 空检索 → OTLP 上报 → CoAgent 检测并开事故
→ 把握度分级 → 审计复盘
```

## 文档

| 文档 | 说明 |
|------|------|
| [faq-agent-decisions.md](./faq-agent-decisions.md) | D1–D7 决策锁定 |
| [faq-agent-status.md](./faq-agent-status.md) | 交付状态与已知问题 |
| [../superpowers/specs/2026-08-12-showcase-faq-agent-design.md](../superpowers/specs/2026-08-12-showcase-faq-agent-design.md) | 设计摘要 |

## 代码与入口

- 包路径：[`showcase/faq_agent/`](../../showcase/faq_agent/)
- 看板：http://localhost:8000/showcase/faq/
- 空检索演示：`POST /showcase/faq/demo/empty-retrieval`

完整 5 分钟价值演示见仓库根目录 [README Quickstart](../../README.md#quickstart)。
