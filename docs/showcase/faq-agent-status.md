# Showcase FAQ Agent — 实现状态与问题

**日期：** 2026-08-12  
**对照决策：** [faq-agent-decisions.md](./faq-agent-decisions.md)

## 1. 已交付

| 项 | 路径 / 入口 | 说明 |
|----|-------------|------|
| 决策文档 | `docs/showcase/faq-agent-decisions.md` | D1–D7 锁定 |
| Showcase 包 | `showcase/faq_agent/` | FAQ 检索、真实 LLM 作答、指标、OTLP 提升 |
| 量化看板 | http://localhost:8000/showcase/faq | Ask count / 空检索率 / 幻觉风险 / 延迟 / 成本 / 事故数 |
| 空检索演示 | `POST /showcase/faq/demo/empty-retrieval` | 强制空检索并 promote 到 CoAgent |
| 拆除生产 Mock | `app/llm/client.py`、`app/config.py` | 无 `MOCK_LLM`；缺 Key 直接报错 |
| 测试策略 | `tests/conftest.py` + `tests/llm_stubs.py` | 非 live 用进程内 stub；`live_llm` 打真 API |

## 2. 推荐演示脚本

```bash
set -a && source .env && set +a
uvicorn app.main:app --reload --port 8000

# 正常问答
curl -s -X POST http://localhost:8000/showcase/faq/ask \
  -H 'Content-Type: application/json' \
  -d '{"query":"退货政策是什么"}' | python3 -m json.tool

# 质量事故：空检索 → CoAgent
curl -s -X POST 'http://localhost:8000/showcase/faq/demo/empty-retrieval' | python3 -m json.tool
```

打开看板查看指标变红，再到管理台审计 Tab 查看对应 `trace_id`。

## 3. 已知问题 / Tech debt

| ID | 问题 | 影响 | 建议 |
|----|------|------|------|
| I1 | FAQ 检索仍为关键词规则，非向量检索 | 召回有限 | 后续可换 embedding，不影响事故闭环叙事 |
| I2 | 成本估算为示意单价，非账单级 | 看板成本仅供趋势 | 接入真实 usage 计价表 |
| I3 | `docs/dev-deploy-test.md` 等旧文档仍提及 `MOCK_LLM` | 文档漂移 | 后续扫一遍更新 |
| I4 | Showcase 与 CoAgent 同进程部署 | 简单，但扩展性一般 | 需要时可拆独立进程，仍走 OTLP |
| I5 | 空检索默认每次 promote | 演示友好，生产可能过噪 | 可加连续 N 次阈值（决策文档已预留） |
| I6 | `generate_with_retry` 在 stub 下被直接替换为单次 stub | 单测不覆盖重试 | live_llm / 专项测试覆盖 |

## 4. 验证结果（实现当次）

- `DEMO_MODE=true python -m pytest tests/ -m "not live_llm"` → **78 passed, 1 deselected**
- 含 `tests/test_showcase_faq.py`（看板、空检索 promote、正常问答 stub）

## 5. 非目标回顾

未做：向量库、飞书、独立 git 仓、完整 OTLP protobuf Collector（与决策一致）。
