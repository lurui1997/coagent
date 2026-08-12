# Showcase FAQ Agent

企业 FAQ 切口：真实 LLM 问答 + 量化看板 + 空检索质量事故接入 CoAgent。

## 本地

```bash
set -a && source .env && set +a   # 需要 LLM_API_KEY（DeepSeek）
uvicorn app.main:app --reload --port 8000
open http://127.0.0.1:8000/showcase/faq/
```

空检索事故演示：

```bash
curl -X POST 'http://127.0.0.1:8000/showcase/faq/demo/empty-retrieval'
```

生产路径无 Mock LLM。完整 5 分钟价值演示见仓库 [README Quickstart](../../README.md#quickstart)。

## 文档

- [docs/showcase/README.md](../../docs/showcase/README.md)
- [docs/showcase/faq-agent-decisions.md](../../docs/showcase/faq-agent-decisions.md)
- [docs/showcase/faq-agent-status.md](../../docs/showcase/faq-agent-status.md)
