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

```bash
python -m pytest tests/ -m "not live_llm" -q
bash scripts/demo.sh
```