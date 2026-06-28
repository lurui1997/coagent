# CoAgent 开发 · 部署 · 测试文档

**版本：** 2026-06-27  
**分支：** `feature/coagent-p0-impl`  
**设计基线：** [coagent-design-spec.md](./superpowers/specs/coagent-design-spec.md)

---

## 1. 项目概述

CoAgent 是 面向企业的 **Agent 运维助手**，实现事件回调接入 → 场景路由 → 处置手册 →大模型推理 → 把握度评分 → 管理台/飞书 的完整闭环。

### 1.1 已实现 P0 功能

| 模块 | 状态 | 说明 |
|------|------|------|
| `POST /events` | ✅ | 事件回调 接入，10 分钟 event_id 幂等 |
| 管理台 四 Tab | ✅ | Agent/时间线、场景触发、把握度评分、飞轮 |
| 实时推送时间线 | ✅ | 故障事件_started → tool → 大模型 → 评分 → completed |
| 3 处置手册 | ✅ | S1 限流 / S2 空检索 / S3 超预算 |
| 把握度评分 | ✅ | 数据·手册·推理 三因子 + 🟢🟡🔴 分级 |
| 模拟大模型 | ✅ | 无 API Key 时可完整演示 |
| 飞书 S1 | ✅ | 未配置时 mock 模式 |
| 回放 | ✅ | 只读重放时间线，不调大模型 |
| 反馈飞轮 | ✅ | 标签页四 👍/👎 统计 |
| 测试套件 | ✅ | 19 项（不含 live_llm） |

---

## 2. 环境要求

| 依赖 | 版本 |
|------|------|
| Python | 3.11+（已在 3.14 验证） |
| pip | 最新 |
| curl |演示脚本需要 |

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
| `LLM_API_KEY` | 生产/真大模型 时 | OpenAI 兼容 API Key |
| `LLM_BASE_URL` | 否 | 默认 `https://api.openai.com/v1` |
| `LLM_MODEL` | 否 | 默认 `gpt-4o-mini` |
| `MOCK_LLM` | 否 | `true` 时使用内置模拟 响应 |
| `DEMO_MODE` | 否 | `true` 时对 C 因子做 区间校正（演示稳定） |
| `FEISHU_*` | 否 | 飞书卡片；未配置则 mock |

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

访问：

- 管理台 面板：http://localhost:8000/
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

---

## 4. 项目结构

```
coagent/
├── app/
│   ├── main.py              # FastAPI 入口 + 管理台 页面
│   ├── orchestrator.py      # 事件编排主流程
│   ├── router.py            # (type, symptom) → playbook_id
│   ├── config.py            # 环境配置
│   ├── db.py                # SQLite 持久化
│   ├── sse.py               # 实时推送 事件广播
│   ├── api/                 # REST 端点
│   ├── playbooks/engine.py  #处置手册引擎
│   ├── llm/client.py        # Async 大模型 + 模拟
│   ├── scoring/scorer.py    # 把握度评分 数据·手册·推理
│   ├── channels/feishu_im.py
│   └── models/              # Pydantic 模型
├── web/
│   ├── templates/admin.html # 管理台 四 Tab UI
│   └── static/style.css
├── data/
│   ├── ops_playbooks.json   # 处置手册 唯一配置源
│   ├── agents.json
│   └── scenarios/s1|s2|s3.json
├── tests/                   # pytest 测试
├── scripts/
│   ├── demo.sh              # 5 分钟演示 自动化
│   └── 评分校准.sh  # 评分 校准
└── requirements.txt
```

---

## 5. API 速查

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/events` | 事件回调 上报 |
| POST | `/admin/trigger/{s1\|s2\|s3}` | 演示 触发场景 |
| GET | `/admin/故障事件s` | Incident 列表 |
| GET | `/admin/故障事件s/{trace_id}` | Incident 详情 |
| GET | `/admin/故障事件s/{trace_id}/stream` | 实时推送 实时流 |
| POST | `/admin/故障事件s/{trace_id}/feedback?rating=up\|down` | 反馈 |
| GET | `/admin/stats` | 飞轮统计 |
| POST | `/admin/replay/{trace_id}` | 只读回放 |
| POST | `/demo/retry/{agent_id}` |模拟重试 |

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
| `test_scoring.py` | 数据·手册·推理 + 区间校正 + 分级 区间 |
| `test_idempotency.py` | event_id 10min 幂等 |
| `test_replay.py` | 实时推送 只读重放 |
| `test_llm_integration.py` | 完整 流水线 + feedback + retry |

**最新验证结果（2026-06-27）：** 19 passed, 0 failed

> 注意：若 shell 环境设置了 `PYTEST_ADDOPTS` 导致 0 tests collected，请使用：
> `env -i PATH="$PWD/.venv/bin:/usr/bin:/bin" HOME="$HOME" PYTHONPATH="$PWD" python -m pytest tests/ -m "not live_llm" -v`

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

1. 打开 http://localhost:8000/?tab=2 → 点击触发 S1/S2/S3
2. 标签页一 查看 实时推送时间线 滚动
3. 标签页三 查看 把握度评分三因子 + 重试/升级差异化 UI
4. 标签页四 提交 👎 反馈，确认统计更新

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

### 6.4 评分 校准

```bash
bash scripts/评分校准.sh s1 10
# 产出 data/calibration/s1.json
```

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
    }
}
```

**不要**单独 `alias /static` 到旧目录，除非你能保证与代码同步更新。

**部署更新步骤：**

```bash
cd /path/to/coagent
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt -q
# 重启服务（systemd / supervisor / 手动）
pkill -f 'uvicorn app.main:app' || true
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 >> coagent.log 2>&1 &
# 可选：重载 nginx
sudo nginx -s reload
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
- [x] S1 飞书 mock + 重试
- [x] S3升级态展示
- [x] 标签页四 反馈更新统计
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
A: 配置 `FEISHU_APP_ID/SECRET/CHAT_ID`；未配置时系统 mock 发送，管理台 面板仍完整可用。

---

## 10. 后续 P1（未实现）

- S2/S3 飞书卡片
- 飞书文档时间线
- 运维手册 检索增强
- 真实 Agent 事件回调 接入

详见 [TODOS.md](../TODOS.md)。
