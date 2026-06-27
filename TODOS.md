# CoAgent TODOS

工程评审（`/plan-eng-review`，2026-06-27）遗留与赛后项。  
**实施基线：** [docs/superpowers/specs/coagent-design-spec.md](docs/superpowers/specs/coagent-design-spec.md)（含 §18）

---

## P0 — Hackathon 前

### TODO-1：同步 gstack design doc → Agent Ops 叙事

- **What：** 更新 `~/.gstack/projects/lurui1997-coagent/drulu-main-design-20260627-135144.md`：顶部 **Superseded by coagent-design-spec.md**；Problem / Demo 场景改为 cs-bot / rag-bot / content-bot（Agent Ops），删除 v2 infra 场景引用。
- **Why：** office-hours 文档仍为 APPROVED + infra 叙事，与 Final Spec 分叉，Pitch 易自相矛盾。
- **Pros：** 单一叙事源；context-restore / gstack 不再注入错误场景。
- **Cons：** 文件在 `~/.gstack/`，不在 repo 内，需手动或通过 gstack 工具同步。
- **Context：** 工程评审 Issue 1 → 决策 **1A**。Repo 内 Spec §0 已注明 superseded。
- **Depends on：** 无
- **Status：** pending

### TODO-2：实现 CoAgent P0 代码基线

- **What：** 按 Spec §4–§18 实现 FastAPI + PlaybookEngine + Score + Admin 四 Tab + S1 飞书 + 测试。
- **Why：** 仓库当前零应用代码，§15 验收全部未满足。
- **Pros：** Hackathon 可 Demo。
- **Cons：** Solo 48h 时间紧，严格跟 §12 时间线。
- **Context：** 评审 Implementation Tasks T1–T5（见 `~/.gstack/projects/lurui1997-coagent/tasks-eng-review-*.jsonl`）。
- **Depends on：** Spec §18 已写回（done）
- **Status：** pending

### TODO-3：`data/ops_playbooks.json` 初始数据

- **What：** 创建三 playbook JSON 条目（S1/S2/S3），含 `tool_mocks`、`consistency_rules`、`consistency_clamp`、`expected_score`。
- **Why：** PlaybookEngine 单一配置源（评审 7B）。
- **Pros：** 改场景不调 Python；与 calibrate 同源。
- **Cons：** 需与 `data/scenarios/s*.json` 字段对齐。
- **Context：** Spec §6、§3.3–§3.5。
- **Depends on：** TODO-2
- **Status：** pending

---

## P1 — Hackathon 后 / 可选

### TODO-4：S2/S3 飞书卡片同步

- **What：** 扩展 `channels/feishu_im.py` 支持 S2 🟡、S3 🔴 @升级卡片。
- **Why：** Spec §2.2 P1；当前 Admin 为主。
- **Status：** deferred

### TODO-5：真实 Agent 平台 Webhook 接入

- **What：** 替换 mock `POST /events` 为客户的 Agent 运行时上报。
- **Why：** 赛后产品化第一步（Spec §16）。
- **Status：** deferred

### TODO-6：Ops 手册 RAG

- **What：** `search_ops_playbook` 从静态 JSON 升级为向量检索。
- **Why：** 企业手册规模化（Spec §16）。
- **Status：** deferred

### TODO-7：商业化与定价文档

- **What：** 单独文档，不在本 Spec（Spec §16 已声明）。
- **Status：** deferred

---

## 已完成

- [x] **Spec §18 写回** — 2026-06-27 工程评审 12 条决策合并入 `coagent-design-spec.md`
- [x] **TODOS.md 创建** — 本文件
