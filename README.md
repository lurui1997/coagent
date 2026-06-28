# CoAgent

ToB Agent Ops Copilot — Hackathon 项目。

**设计规格（唯一实施基线）：** [docs/superpowers/specs/coagent-design-spec.md](docs/superpowers/specs/coagent-design-spec.md)  
**开发部署测试：** [docs/dev-deploy-test.md](docs/dev-deploy-test.md)  
**任务追踪：** [TODOS.md](TODOS.md)

## 快速开始

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
MOCK_LLM=true DEMO_MODE=true uvicorn app.main:app --reload --port 8000
```

打开 http://localhost:8000/ → Tab2 触发 S1/S2/S3 Demo。

## 本地 Claude Agent（真实接入）

三个 Agent 位于 `agents/`，通过 `POST /events` 接入 CoAgent 流水线：

| Agent | 场景 | 触发条件 |
|-------|------|----------|
| `cs-bot` | S1 限流 | Claude 返回 429 / rate limit |
| `rag-bot` | S2 空检索 | 本地 FAQ 无匹配片段 |
| `content-bot` | S3 超预算 | 日累计成本 > `CONTENT_BUDGET_YUAN_DAILY` |

**启动 CoAgent 后：**

```bash
# simulate：上报预置场景（无需 Claude，验证接入）
bash scripts/test_agents.sh

# live：调用本地 claude/tclaude CLI
python3 -m agents.cli run cs-bot --mode live --query "我的订单什么时候发货"
python3 -m agents.cli run rag-bot --mode live --query "完全不存在的冷门问题"
python3 -m agents.cli run content-bot --mode live --task "618 海报" --template longform
python3 -m agents.cli cost content-bot          # 查看日累计
python3 -m agents.cli cost content-bot --reset  # 重置累计（测试用）

# HTTP API
curl http://localhost:8000/agents/content-bot/cost
curl -X POST http://localhost:8000/agents/content-bot/run \
  -H 'Content-Type: application/json' \
  -d '{"mode":"live","task":"618海报","template":"longform"}'
```

FAQ 检索规则见 `data/agent_kb/RETRIEVAL.md`；content-bot 按 Token×模板倍率累计成本，超 `CONTENT_BUDGET_YUAN_DAILY` 自动上报 S3。

环境变量：`COAGENT_PUBLIC_URL`、`CLAUDE_BIN`、`CONTENT_BUDGET_YUAN_DAILY`、`CONTENT_COST_PER_1K_TOKENS`。

## 官网

静态营销站点位于 `website/`，与管理台分离部署：

```bash
# 本地预览（任选其一）
python3 -m http.server 3000 --directory website
# 或
npx serve website
```

浏览器打开 http://localhost:3000/

```bash
bash scripts/run_tests.sh -q
# 或: .venv/bin/python3 -m pytest tests/ -m "not live_llm" -q
bash scripts/demo.sh
```