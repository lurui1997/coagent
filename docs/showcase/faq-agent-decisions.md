# Showcase FAQ Agent — 决策记录

**日期：** 2026-08-12  
**状态：** 已锁定并进入实现  
**读者：** 仓库维护者 / GitHub 访客  

## 1. 目标转向

从黑客松 Demo 转向个人工程实践：做一个可产生业务价值、可分享的 Agent 切口，并与 CoAgent 结合做出可演示的真实效果。

## 2. 锁定决策

| # | 决策 | 选择 | 理由 |
|---|------|------|------|
| D1 | Agent 场景 | 知识库问答（RAG FAQ） | 指标清晰，贴合质量事故叙事 |
| D2 | 语料 | 通用企业 FAQ 样例包 | 可稳定注入空检索/幻觉类故障 |
| D3 | 成功标准 | 质量事故闭环为主，量化看板为配套 | GitHub 叙事不是「又一个 RAG」 |
| D4 | 包装 | 本仓独立包 `showcase/faq-agent` | 边界清晰，比加深 rag-bot / 另起新仓更合适 |
| D5 | 观测契约 | OTLP/JSON → CoAgent `/v1/traces` | 延续 ADR-0001 |
| D6 | LLM | 必须真实调用（DeepSeek）；拆除生产 Mock 链路 | 用户硬约束 |
| D7 | 测试策略 | 单测用进程内 stub 替换 LLMClient；`live_llm` 打真 API | 禁止把 Mock 当产品能力，但 CI/本地无 Key 仍可跑非 LLM 契约测试 |

## 3. MVP 范围

**做：**

- `showcase/faq-agent`：FAQ 检索 + DeepSeek 作答 + 指标落库 + HTML 量化看板
- 空检索 / 强制故障路径导出 OTLP，触发 CoAgent 事故
- 拆除 `MOCK_LLM` / `MOCK_RESPONSES` 生产路径
- 文档：决策、状态、已知问题

**不做（本迭代）：**

- 向量库 / 生产级 RAG
- 飞书通道
- 独立 git 仓库
- 完整 OTLP protobuf Collector

## 4. 核心指标（看板）

| 指标 | 定义 |
|------|------|
| `ask_count` | 问答请求数 |
| `empty_retrieval_rate` | 空检索次数 / 总请求 |
| `hallucination_risk_rate` | 空检索仍作答（或标记为风险）次数 / 总请求 |
| `p50/p95_latency_ms` | 端到端延迟 |
| `token_usage` / `est_cost` | 用量与估算成本 |
| `incident_promotions` | 提升为 CoAgent 事故的次数 |

## 5. 事故提升规则（推荐默认）

- 空检索 → `run_fail` + `empty_retrieval` → 提升事故  
- 可选：连续 N 次空检索才提升（MVP 先每次提升，带幂等 event_id）

## 6. 质量 vs 成本

优先交付「可复现闭环 + 可读看板」，不追求检索算法先进性。DeepSeek `deepseek-v4-flash` 作为默认模型。
