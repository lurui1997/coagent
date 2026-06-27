# CoAgent 开发 · 部署 · 测试文档

**版本：** 2026-06-27  
**分支：** `feature/coagent-p0-impl`  
**设计基线：** [coagent-design-spec.md](./superpowers/specs/coagent-design-spec.md)

---

## 1. 项目概述

CoAgent 是 ToB **Agent Ops Copilot**，实现 Webhook 事件接入 → Scenario Router → Playbook → LLM 推理 → Decision Score → Admin/飞书 的完整闭环。

### 1.1 已实现 P0 功能

| 模块 | 状态 | 说明 |
|------|------|------|
| `POST /events` | ✅ | Webhook 接入，10 分钟 event_id 幂等 |
| Admin 四 Tab | ✅ | Agent/Timeline、场景触发、Decision、飞轮 |
| SSE Timeline | ✅ | incident_started → tool → LLM → Score → completed |
| 3 Playbook | ✅ | S1 限流 / S2 空检索 / S3 超预算 |
| Decision Score | ✅ | D/P/C 三因子 + 🟢🟡🔴 分级 |
| Mock LLM | ✅ | 无 API Key 时可完整 Demo |
| 飞书 S1 | ✅ | 未配置时 mock 模式 |
| Replay | ✅ | 只读重放 timeline，不调 LLM |
| 反馈飞轮 | ✅ | Tab4 👍/👎 统计 |
| 测试套件 | ✅ | 19 项（不含 live_llm） |

---

## 2. 环境要求

| 依赖 | 版本 |
|------|------|
| Python | 3.11+（已在 3.14 验证） |
| pip | 最新 |
| curl | Demo 脚本需要 |

---

## 3. 本地开发

### 3.1 克隆与分支

```bash
git clone <repo-url> coagent
cd coagent
git checkout feature/coagent-p0-impl
```

### 3.2 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3.3 配置环境变量

```bash
cp .env.example .env
```

| 变量 | 必填 | 说明 |
|------|------|------|
| `LLM_API_KEY` | 生产/真 LLM 时 | OpenAI 兼容 API Key |
| `LLM_BASE_URL` | 否 | 默认 `https://api.openai.com/v1` |
| `LLM_MODEL` | 否 | 默认 `gpt-4o-mini` |
| `MOCK_LLM` | 否 | `true` 时使用内置 Mock 响应 |
| `DEMO_MODE` | 否 | `true` 时对 C 因子做 clamp（Demo 稳定） |
| `FEISHU_*` | 否 | 飞书卡片；未配置则 mock |

**Hackathon Demo 推荐：**

```env
MOCK_LLM=true
DEMO_MODE=true
```

### 3.4 启动开发服务器

```bash
source .venv/bin/activate
MOCK_LLM=true DEMO_MODE=true uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：

- Admin 面板：http://localhost:8000/
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

---

## 4. 项目结构

```
coagent/
├── app/
│   ├── main.py              # FastAPI 入口 + Admin 页面
│   ├── orchestrator.py      # 事件编排主流程
│   ├── router.py            # (type, symptom) → playbook_id
│   ├── config.py            # 环境配置
│   ├── db.py                # SQLite 持久化
│   ├── sse.py               # SSE 事件广播
│   ├── api/                 # REST 端点
│   ├── playbooks/engine.py  # PlaybookEngine
│   ├── llm/client.py        # Async LLM + Mock
│   ├── scoring/scorer.py    # Decision Score D/P/C
│   ├── channels/feishu_im.py
│   └── models/              # Pydantic 模型
├── web/
│   ├── templates/admin.html # Admin 四 Tab UI
│   └── static/style.css
├── data/
│   ├── ops_playbooks.json   # Playbook 唯一配置源
│   ├── agents.json
│   └── scenarios/s1|s2|s3.json
├── tests/                   # pytest 测试
├── scripts/
│   ├── demo.sh              # 5 分钟 Demo 自动化
│   └── calibrate_scores.sh  # Score 校准
└── requirements.txt
```

---

## 5. API 速查

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/events` | Webhook 上报 |
| POST | `/admin/trigger/{s1\|s2\|s3}` | Demo 触发场景 |
| GET | `/admin/incidents` | Incident 列表 |
| GET | `/admin/incidents/{trace_id}` | Incident 详情 |
| GET | `/admin/incidents/{trace_id}/stream` | SSE 实时流 |
| POST | `/admin/incidents/{trace_id}/feedback?rating=up\|down` | 反馈 |
| GET | `/admin/stats` | 飞轮统计 |
| POST | `/admin/replay/{trace_id}` | 只读 Replay |
| POST | `/demo/retry/{agent_id}` | Mock Retry |

---

## 6. 测试

### 6.1 单元 / 集成测试（默认，无 LLM）

```bash
source .venv/bin/activate
MOCK_LLM=true DEMO_MODE=true python -m pytest tests/ -m "not live_llm" -v
```

**覆盖范围：**

| 测试文件 | 覆盖 |
|----------|------|
| `test_playbook_engine.py` | Router + JSON 配置 + mock tools |
| `test_scoring.py` | D/P/C + clamp + grade 区间 |
| `test_idempotency.py` | event_id 10min 幂等 |
| `test_replay.py` | SSE 只读重放 |
| `test_llm_integration.py` | 完整 pipeline + feedback + retry |

**最新验证结果（2026-06-27）：** 19 passed, 0 failed

> 注意：若 shell 环境设置了 `PYTEST_ADDOPTS` 导致 0 tests collected，请使用：
> `env -i PATH="$PWD/.venv/bin:/usr/bin:/bin" HOME="$HOME" PYTHONPATH="$PWD" python -m pytest tests/ -m "not live_llm" -v`

### 6.2 真 LLM 集成测试

```bash
export LLM_API_KEY=sk-...
export MOCK_LLM=false
python -m pytest tests/ -m live_llm -v
```

### 6.3 本地部署 Demo 验证

**步骤 1：** 启动服务

```bash
MOCK_LLM=true DEMO_MODE=true uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**步骤 2：** 运行 Demo 脚本

```bash
bash scripts/demo.sh
```

**预期输出：**

| 场景 | Score | Grade |
|------|-------|-------|
| S1 限流 | 87 | executable 🟢 |
| S2 空检索 | 72 | needs_confirmation 🟡 |
| S3 超预算 | 58 | escalate 🔴 |

**步骤 3：** 浏览器验证

1. 打开 http://localhost:8000/?tab=2 → 点击触发 S1/S2/S3
2. Tab1 查看 SSE Timeline 滚动
3. Tab3 查看 Decision Score 三因子 + Retry/升级差异化 UI
4. Tab4 提交 👎 反馈，确认统计更新

**步骤 4：** 手动 API 验证

```bash
# Webhook 接入
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d @data/scenarios/s1.json

# Mock Retry
curl -X POST http://localhost:8000/demo/retry/cs-bot

# 幂等验证（同 event_id 10min 内）
curl -X POST http://localhost:8000/admin/trigger/s1
# 第二次应返回 {"status":"duplicate",...}
```

### 6.4 Score 校准

```bash
bash scripts/calibrate_scores.sh s1 10
# 产出 data/calibration/s1.json
```

---

## 7. 部署

### 7.1 单机部署（Hackathon / 私有化）

```bash
# 生产环境建议使用真 LLM
cp .env.example .env
# 编辑 .env 填入 LLM_API_KEY、FEISHU_* 等

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

### 7.2 Docker（可选扩展）

当前 P0 未包含 Dockerfile，可按以下模板添加：

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.3 数据持久化

- SQLite 文件：项目根目录 `coagent.db`（可通过 `DATABASE_PATH` 环境变量扩展）
- 配置数据：`data/ops_playbooks.json`（改场景无需改 Python）
- 校准产出：`data/calibration/`

---

## 8. 验收清单（对照 Spec §15）

- [x] S1/S2/S3 Webhook 与 Admin 触发均可闭环
- [x] Tab1 Agent 列表 + SSE timeline
- [x] LLM reasoning_chain / steps（Mock 或真 LLM）
- [x] S1/S2/S3 Score 区间与 Tab3 渲染规则
- [x] Tab3 展示 Score 总分 + 三因子 + grade
- [x] S1 飞书 mock + Retry
- [x] S3 升级态展示
- [x] Tab4 反馈更新统计
- [x] L0 不伪造；Replay 只读可用
- [x] event_id 10min 幂等
- [x] `POST /demo/retry/{agent_id}` 可达
- [x] DEMO_MODE 下 C clamp 披露
- [x] `pytest tests/ -m "not live_llm"` 通过

---

## 9. 常见问题

**Q: 触发场景返回 duplicate？**  
A: 10 分钟内相同 `event_id` 幂等保护。删除 `coagent.db` 重启服务，或修改 scenario JSON 中的 `event_id`。

**Q: Score 不在预期区间？**  
A: 调整 `data/ops_playbooks.json` 中的 `consistency_clamp` / `consistency_rules`，运行 `calibrate_scores.sh` 验证。

**Q: 无 LLM API Key 能 Demo 吗？**  
A: 可以。设置 `MOCK_LLM=true`，使用内置三场景 Mock 响应。

**Q: 飞书卡片没收到？**  
A: 配置 `FEISHU_APP_ID/SECRET/CHAT_ID`；未配置时系统 mock 发送，Admin 面板仍完整可用。

---

## 10. 后续 P1（未实现）

- S2/S3 飞书卡片
- 飞书文档时间线
- Ops 手册 RAG
- 真实 Agent Webhook 接入

详见 [TODOS.md](../TODOS.md)。
