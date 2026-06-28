# CoAgent 开发 · 部署 · 测试文档

**版本：** 2026-06-28  
**设计基线：** [coagent-design-spec.md](./superpowers/specs/coagent-design-spec.md)  
**官网：** http://www.aikipedia.cn/coagent/

---

## 1. 项目概述

CoAgent 是面向企业的 **Agent 运维助手**,实现统一处置流水线:

```
事件接入 → 场景路由 → 处置手册+工具 → 大模型根因推理 → 把握度评分 → 分级处置 · 审计留痕
```

### 1.1 已实现功能（P0 + Ultra 基础）

| 模块 | 状态 | 说明 |
|------|------|------|
| `POST /events` | ✅ | Webhook 接入,10 分钟 `event_id` 幂等 |
| 管理台三 Tab | ✅ | Tab1 总览 · Tab2 处置工作台 · Tab3 审计复盘 |
| ReAct 诊断 Agent | ✅ | 默认 `DIAGNOSTIC_AGENT=true`,失败回退 legacy LLM 路径 |
| SSE 时间线 | ✅ | incident_started → tool ×3 → llm → score → completed |
| 3 处置手册 | ✅ | S1 限流 / S2 空检索 / S3 超预算 |
| 把握度评分 | ✅ | D/P/C 三因子 + 🟢🟡🔴 分级;`DEMO_MODE` 仅 clamp C |
| Mock / 真 LLM | ✅ | 无 API Key 或 `MOCK_LLM=true` 可完整演示 |
| 飞书 S1 | 📅 | 代码骨架 `feishu_im.py`;**尚未对接真实 API**,无 `FEISHU_*` 时仅 mock `channel_sync` |
| 本地 Agent 接入 | ✅ | cs-bot / rag-bot / content-bot → `/events` |
| Ultra 面板 | ✅ | 知识图谱 · 相似事故 · What-if · Team-plan |
| 回放 / 审计 | ✅ | 只读重放 SSE,不调 LLM;JSON/CSV 导出 |
| 反馈飞轮 | ✅ | Tab3 👍/👎 统计 |
| 测试套件 | ✅ | 18 个 pytest 文件,`-m "not live_llm"` |

---

## 2. 环境要求

| 依赖 | 版本 |
|------|------|
| Python | 3.11+（已在 3.14 验证） |
| pip | 最新 |
| curl |演示脚本需要 |

---

## 3. 本地开发

### 3.1 克隆

```bash
git clone <repo-url> coagent
cd coagent
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
| `LLM_API_KEY` | 生产/真 LLM 时 | OpenAI 兼容 API Key;空则自动 mock |
| `LLM_BASE_URL` | 否 | 默认 `https://api.openai.com/v1` |
| `LLM_MODEL` | 否 | 默认 `gpt-4o-mini` |
| `LLM_TIMEOUT_S` | 否 | 默认 **15**（代码默认,`.env.example` 可写 60） |
| `PIPELINE_TIMEOUT_S` | 否 | 整条链超时,默认 **30** |
| `MOCK_LLM` | 否 | `true` 强制内置 mock 响应 |
| `DEMO_MODE` | 否 | `true` 时对 C 因子做区间校正（演示稳定） |
| `DIAGNOSTIC_AGENT` | 否 | 默认 `true`,ReAct 工具调用路径 |
| `DIAGNOSTIC_MAX_STEPS` | 否 | ReAct 最大步数,默认 8 |
| `FEISHU_*` | 否 | **规划中**;配置后仍待联调,当前跳过真实发送 |
| `COAGENT_PUBLIC_URL` | 否 | 预留 retry_webhook 基址 |
| `COAGENT_URL` | Agent 侧 | `agents/` 客户端上报地址,默认 localhost:8000 |
| `CLAUDE_BIN` | live Agent | 本地 claude/tclaude CLI |
| `CONTENT_BUDGET_YUAN_DAILY` | content-bot | 日预算,默认 20 元 |

**黑客松演示 推荐：**

```env
MOCK_LLM=true
DEMO_MODE=true
```

### 3.4 启动开发服务器

```bash
source .venv/bin/activate
MOCK_LLM=true DEMO_MODE=true uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问:

- **管理台**（FastAPI 渲染 `web/`）: http://localhost:8000/
- **营销站**（静态 `website/`）: `python3 -m http.server 3000 --directory website`
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

---

## 4. 项目结构

```
coagent/
├── app/
│   ├── main.py              # FastAPI 入口 + 管理台页面 /
│   ├── orchestrator.py      # 编排:幂等 → 路由 → 诊断/LLM → 评分 → 通道
│   ├── diagnostic_agent.py  # ReAct 诊断（默认路径）
│   ├── router.py            # (type, symptom) → playbook_id
│   ├── config.py            # 环境配置
│   ├── db.py                # SQLite 持久化
│   ├── sse.py               # SSE 广播
│   ├── api/                 # events, admin, agents, demo
│   ├── playbooks/engine.py  # 处置手册 + mock 工具
│   ├── llm/client.py        # Async LLM + mock
│   ├── scoring/scorer.py    # 把握度评分 D/P/C
│   ├── channels/feishu_im.py
│   ├── correction/          # 纠偏建议
│   ├── ultra/               # 图谱 / 相似 / what-if / team
│   └── models/
├── agents/                  # cs-bot, rag-bot, content-bot CLI
├── web/                     # 管理台模板与静态资源（非 website/）
├── website/                 # 营销官网静态页
├── data/
│   ├── ops_playbooks.json   # Playbook 唯一配置源
│   ├── agents.json
│   ├── scenarios/s1|s2|s3.json
│   └── agent_kb/            # RAG FAQ
├── tests/
├── scripts/                 # demo.sh, run_tests.sh, test_agents.sh 等
└── docs/diagrams/           # 架构 HTML（流水线自动循环高亮）
```

---

## 5. API 速查

### 5.1 事件与 Agent

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/events` | Webhook 事件上报 |
| GET | `/agents` | 列出 cs-bot / rag-bot / content-bot |
| POST | `/agents/{id}/run` | live 或 simulate 运行 Agent |
| POST | `/agents/retry/cs-bot` | Claude 重试（Agent 侧,非飞书） |
| GET | `/agents/content-bot/cost` | content-bot 日累计成本 |
| POST | `/agents/content-bot/cost/reset` | 重置日累计（测试） |

### 5.2 管理台

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/admin/trigger/{s1\|s2\|s3}` | 演示触发场景 |
| GET | `/admin/incidents` | 事故列表 |
| GET | `/admin/incidents/{trace_id}` | 详情（含纠偏建议） |
| GET | `/admin/incidents/{trace_id}/stream` | SSE 实时流 |
| POST | `/admin/incidents/{trace_id}/feedback` | 👍/👎 反馈 |
| GET | `/admin/stats` | 飞轮统计 |
| POST | `/admin/replay/{trace_id}` | 只读回放 |
| GET | `/admin/audit/export` | JSON 或 `?format=csv` |
| POST | `/demo/retry/{agent_id}` | **模拟**重试（管理台 UI 用） |

### 5.3 Ultra（Tab2 面板）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/ultra/graph` | 全局知识图谱 |
| GET | `/admin/ultra/graph/agent/{id}` | Agent 子图 |
| GET | `/admin/ultra/incidents/{trace_id}/similar` | 相似事故 |
| POST | `/admin/ultra/incidents/{trace_id}/what-if` | 参数推演重算评分 |
| GET | `/admin/ultra/incidents/{trace_id}/team-plan` | 团队编排计划 |

---

## 6. 测试

### 6.1 单元 / 集成测试（默认，无 LLM）

```bash
bash scripts/run_tests.sh -q
# 或
MOCK_LLM=true DEMO_MODE=true python -m pytest tests/ -m "not live_llm" -v
```

**覆盖范围：**

| 测试文件 | 覆盖 |
|----------|------|
| `test_playbook_engine.py` | Router + JSON + mock tools |
| `test_scoring.py` | D/P/C + clamp + 分级区间 |
| `test_idempotency.py` | event_id 10min 幂等 |
| `test_diagnostic_agent.py` | ReAct 诊断路径 |
| `test_ultra.py` | 图谱 / similar / what-if |
| `test_agents_api.py` | `/agents` HTTP 接入 |
| `test_replay.py` | SSE 只读重放 |
| `test_audit_export.py` | 审计导出 |
| `test_feishu_im.py` | 飞书卡片构建 |
| `test_llm_integration.py` | 完整流水线（含 live_llm marker） |

> 运行 `bash scripts/run_tests.sh -q` 验证;具体用例数见 pytest 输出。

### 6.2 真大模型 集成测试

```bash
export LLM_API_KEY=sk-...
export MOCK_LLM=false
python -m pytest tests/ -m live_llm -v
```

### 6.3 本地部署演示 验证

**步骤 1：** 启动服务

```bash
MOCK_LLM=true DEMO_MODE=true uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**步骤 2：** 运行演示脚本

```bash
bash scripts/demo.sh
```

**预期输出：**

| 场景 | 评分 | Grade |
|------|-------|-------|
| S1 限流 | 87 | 可执行 🟢 |
| S2 空检索 | 72 | 需确认 🟡 |
| S3 超预算 | 58 | 需升级 🔴 |

**步骤 3：** 浏览器验证

1. Tab2 **处置工作台** → 触发 S1/S2/S3,查看 SSE 时间线与决策面板
2. Tab2 Ultra 区 → 知识图谱 / 相似事故 / What-if
3. Tab3 **审计复盘** → 👎 反馈、审计日志 JSON/CSV 导出
4. S1 🟢 可一键重试（调用 `/demo/retry/cs-bot` 模拟链）

**步骤 4：** 手动 API 验证

```bash
# 事件回调 接入
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d @data/scenarios/s1.json

#模拟重试
curl -X POST http://localhost:8000/demo/retry/cs-bot

# 幂等验证（同 event_id 10min 内）
curl -X POST http://localhost:8000/admin/trigger/s1
# 第二次应返回 {"status":"duplicate",...}
```

### 6.4 评分校准

```bash
bash scripts/calibrate_scores.sh s1 10
# 产出 data/calibration/s1.json
```

> 注意:固定 `event_id` 的 POST 在 10min 内会幂等 duplicate;批量采样需换 `event_id`。

---

## 7. 部署

### 7.1 单机部署（黑客松 / 私有化）

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

### 7.4 Nginx 反向代理（生产必看）

**常见展示异常原因：**

1. **HTML 未更新** — 服务器仍是旧 `admin.html`（页面出现「Hackathon Demo」文案）
2. **CSS 被缓存** — 浏览器/nginx 缓存了旧版 `/static/style.css`（有 HTML 无卡片样式）
3. **`/static` 未转发** — nginx 把 `/static` 指到空目录，返回 404 或非 CSS 内容

**推荐配置**（全部转发给 uvicorn，由 FastAPI 提供静态文件）：

```nginx
server {
    listen 80;
    server_name www.aikipedia.cn aikipedia.cn;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # 禁止 nginx 缓存 HTML（静态资源由 uvicorn 带 ?v= 长期缓存）
        proxy_no_cache 1;
        proxy_cache_bypass 1;
    }
}
```

**不要**单独 `alias /static` 到旧目录，除非你能保证与代码同步更新。

**部署更新步骤：**

```bash
# 方式一：一键脚本（在服务器项目目录执行）
bash scripts/deploy_server.sh

# 方式二：手动
cd /path/to/coagent
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt -q
pkill -f 'uvicorn app.main:app' || true
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 >> coagent.log 2>&1 &
```

**部署后验证：**

```bash
bash scripts/verify_deploy.sh http://www.aikipedia.cn
```

模板已对 `style.css` / `theme.js` / `htmx` 附加 `?v=mtime` 版本号；htmx 已内置到 `web/static/vendor/`，不依赖 unpkg CDN。

---

## 8. 验收清单（对照 Spec §15）

- [x] S1/S2/S3 事件回调 与 管理台 触发均可闭环
- [x] 标签页一 Agent 列表 + 实时推送时间线
- [x] 大模型 reasoning_chain / steps（模拟 或真 LLM）
- [x] S1/S2/S3 评分 区间与 标签页三 渲染规则
- [x] 标签页三 展示评分 总分 + 三因子 + 分级
- [x] S1 `channel_sync` 占位（飞书未对接,mock-msg-id）
- [x] Tab3 反馈更新统计
- [x] L0 不伪造；回放 只读可用
- [x] event_id 10min 幂等
- [x] `POST /demo/retry/{agent_id}` 可达
- [x] DEMO_MODE 下 C 区间校正 披露
- [x] `pytest tests/ -m "not live_llm"` 通过

---

## 9. 常见问题

**Q: 触发场景返回 duplicate？**  
A: 10 分钟内相同 `event_id` 幂等保护。删除 `coagent.db` 重启服务，或修改 scenario JSON 中的 `event_id`。

**Q: 评分 不在预期区间？**  
A: 调整 `data/ops_playbooks.json` 中的 `consistency_区间校正` / `consistency_rules`，运行 `评分校准.sh` 验证。

**Q: 无大模型 API Key 能演示 吗？**  
A: 可以。设置 `MOCK_LLM=true`，使用内置三场景模拟 响应。

**Q: 飞书卡片没收到？**  
A: **当前版本未对接飞书 API**。流水线仍会记录 `channel_sync` 事件（`mock-msg-id`）;配置 `FEISHU_*` 后需完成联调方可真实发送。处置请在管理台 Tab2 完成。

---

## 10. 后续 P1（未实现）

- S1 飞书 IM 卡片真实发送 + Retry 联调
- S2/S3 飞书卡片
- 飞书文档时间线
- 运维手册 检索增强
- 真实 Agent 事件回调 接入

详见 [TODOS.md](../TODOS.md)。
