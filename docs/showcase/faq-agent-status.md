# Showcase FAQ Agent — 实现状态与问题

**日期：** 2026-08-13  
**对照决策：** [faq-agent-decisions.md](./faq-agent-decisions.md)

## 1. 已交付

| 项 | 路径 / 入口 | 说明 |
|----|-------------|------|
| 决策文档 | `docs/showcase/faq-agent-decisions.md` | D1–D7 锁定 |
| Showcase 包 | `showcase/faq_agent/` | FAQ 检索、真实 LLM 作答、指标、OTLP 提升 |
| 量化看板 | http://localhost:8000/showcase/faq/ | 请求量 / 空检索率 / 幻觉风险 / 延迟 / 成本 / 事故数 |
| 空检索演示 | `POST /showcase/faq/demo/empty-retrieval` | 强制空检索并 promote 到 CoAgent |
| 拆除生产 Mock | `app/llm/client.py`、`app/config.py` | 无 `MOCK_LLM`；缺 Key 直接报错 |
| 管理台企业视觉 | `web/static/enterprise-tokens.css` | 与 Showcase 共用浅色工作台 |
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

打开看板查看空检索率，再到管理台 **审计复盘** 打开对应 `trace_id` 详情（详情面板在日志上方）。

也可在 **处置工作台** 直接点 S1 / S2 / S3，对比「可执行 / 需确认 / 须升级」边界。

## 3. 已知问题 / Tech debt

| ID | 问题 | 影响 | 建议 |
|----|------|------|------|
| I1 | FAQ 检索仍为关键词规则，非向量检索 | 召回有限 | 后续可换 embedding，不影响事故闭环叙事 |
| I2 | 成本估算为示意单价，非账单级 | 看板成本仅供趋势 | 接入真实 usage 计价表 |
| I4 | Showcase 与 CoAgent 同进程部署 | 简单，扩展性一般 | 需要时可拆独立进程，仍走 OTLP |
| I5 | 空检索默认每次 promote | 演示友好，生产可能过噪 | 可加连续 N 次阈值（决策文档已预留） |
| I6 | `generate_with_retry` 在 stub 下被直接替换为单次 stub | 单测不覆盖重试 | live_llm / 专项测试覆盖 |
| I7 | 诊断流水线偶发 `PIPELINE_TIMEOUT_S` 超时 | Showcase 提升事故可能显示「失败」 | 已落库明确超时文案；可加大超时或缩短 ReAct 步数 |

已关闭：I3（`docs/dev-deploy-test.md` Mock 漂移）— 已随文档刷新更正。

## 4. 验证结果

- `PYTHONPATH=. pytest tests/ -m "not live_llm"` — 以当前 `main` 为准本地执行
- 含 `tests/test_showcase_faq.py`、`tests/test_audit_detail_nav.py`、`tests/test_pipeline_failure.py`

## 5. 非目标回顾

未做：向量库、飞书、独立 git 仓、完整 OTLP protobuf Collector（与决策一致）。
