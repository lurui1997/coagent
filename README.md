<div align="center">

# CoAgent

### AI Agent 事故指挥官(Agent Incident Commander)

**面向 AI Agent 进入生产后的运行事故 —— 运行失败、质量异常、成本失控,CoAgent 提供异常发现、根因诊断、风险决策、受控处置与审计复盘的一体化闭环。**

![赛道](https://img.shields.io/badge/赛道-ToB%20AI%20Agent-2563eb)
![定位](https://img.shields.io/badge/定位-Agent%20运行态%20Ops-7c3aed)
![后端](https://img.shields.io/badge/Backend-FastAPI%20·%20SSE%20·%20SQLite-059669)
![推理](https://img.shields.io/badge/推理-真实%20LLM%20·%20Pydantic%20契约-ea580c)
![License](https://img.shields.io/badge/License-MIT-64748b)

🌐 **官网**:`website/` · 🏗 **架构图**:[docs/diagrams/coagent-architecture.html](docs/diagrams/coagent-architecture.html) · 🎬 **完整录屏**:[docs/demos/](docs/demos/)

<br />

![CoAgent 演示](docs/demos/coagent-demo.gif)

*事故触发 → 根因诊断 → Decision Score 风险分级 → 飞书处置 → 结果验证的完整闭环*

</div>

---

### ⚡ 三句话看懂 CoAgent

- 🧠 **可解释的 Decision Score** —— 用「数据完整度 × Playbook 匹配 × 推理一致性」给出 0–100 风险分和 🟢🟡🔴 分级,让值班人 3 秒决定动不动、还敢反驳它。
- 💬 **飞书原生处置台** —— 把复杂诊断变成 IM 里可确认、可升级的处置卡片,非原作者(FDE / 值班人 / 客户 IT)也能安全拍板。
- 🔁 **越用越准的飞轮** —— 每次人工反馈与处置结果回流,持续校准处置手册、风险规则与提示词。

<details>
<summary><b>📖 目录</b></summary>

- [它解决什么问题](#它解决什么问题)
- [核心能力](#核心能力)
- [创新点](#创新点)
- [系统架构](#系统架构) · [Decision Score](#decision-score可解释的风险评分)
- [三场景](#三场景)
- [快速开始](#快速开始)
- [本地 Claude Agent(真实接入)](#本地-claude-agent真实接入)
- [进阶能力](#进阶能力)
- [官网](#官网) · [测试](#测试) · [License](#license)

</details>

## 它解决什么问题

**AI Agent 做 demo 都挺好,一上线就翻车 —— 而出事那一刻,没人敢拍板。**

- **62%** 企业已试验 Agent,但近 2/3 尚未规模化(McKinsey 2025);**仅 21%** 具备成熟治理(Deloitte 2026)。
- Gartner 预测:到 **2027 年底,超 40%** 的 agentic AI 项目会因成本上升、价值不清、风险失控被取消。
- 卡住的不是模型不够聪明,是**出事时没人知道该怎么办**:慢(爬日志)、靠老师傅、不留痕、不敢动。

CoAgent 聚焦 Agent「上线之后」的运行态 Ops,把出事那一刻的**处置决策**做成产品:

| 痛点场景 | 真实例子 | 当前处理的问题 |
|---|---|---|
| **运行异常难诊断** | 客服 Agent 大促并发翻倍触发 API 429,失败率 38% | 需跨监控/Trace/配置排查,依赖原工程师 |
| **质量问题难发现** | RAG Agent 索引延迟,空检索率 35%,仍返回幻觉答案 | 基础设施指标正常,盲目重试无解 |
| **成本失控难止损** | 内容 Agent 长文模板使 Token 增长 180%,超日预算 | 只看到超支,不知该限流、降级还是暂停 |
| **处置风险难判断** | 需在重试/降级/暂停间选择,但不清楚动作影响 | 缺风险依据与权限边界,易误操作或延误 |

> **谁会用:Agent 出岔子时,得去拍板「动还是不动」的那个人** —— Agent 交付团队(FDE)、企业 AI 平台与 SRE、接手第三方 Agent 的客户 IT。

## 核心能力

CoAgent 围绕 Agent 事故处理全过程,提供从发现到沉淀的完整能力链:

| 能力 | 回答的问题 | 说明 |
|---|---|---|
| **事故识别** | 发生了什么? | 接入运行事件与指标,将失败/质量/成本异常识别为 Agent 事故 |
| **根因诊断** | 为什么发生? | 汇总日志、指标、配置与处置手册,形成根因假设、影响判断与证据链 |
| **风险决策** | 要不要动? | 按 Decision Score 风险分级,输出可执行 / 需确认 / 必须升级 |
| **IM 协同** | 如何及时触达? | 飞书推送事故证据、风险等级与建议动作,支持确认、升级与结果同步 |
| **受控处置** | 应该怎么动? | 提供重试/降级/暂停/升级建议,高风险动作经人工审批 |
| **结果验证** | 处置是否有效? | 记录结果并对比前后指标,判断恢复或继续升级 |
| **审计复盘** | 谁做了什么? | 保存并回放证据、建议、审批、动作与结果,支持责任追溯 |
| **反馈飞轮** | 如何越用越准? | 基于人工反馈与历史事故,持续完善处置手册、风险规则与提示词 |

> 当前版本以处置建议、人工审批与模拟执行验证流程,**不声称自动修复生产系统**。

## 创新点

> 创新不在单个新技术,而在针对 Agent 事故场景形成的**决策与处置机制**。

| 创新点 | 核心机制 | 与现有方案的差异 |
|---|---|---|
| **Agent 原生事故模型** | 将失败/质量/成本统一为事故,关联版本、工具调用、业务影响与责任人 | 观测工具以 Trace/Eval 为中心;CoAgent 以需处置的事故为中心 |
| **风险分级的处置合同** | 把证据、反证、动作风险、可逆性、审批要求组合为执行边界 | 多数产品给评分/建议;CoAgent 让风险判断直接约束动作权限与审批 |
| **面向非原作者的 IM 处置** | 把复杂诊断转成飞书中可理解、可确认、可升级的处置卡片 | 多数产品服务开发者、在控制台调查;CoAgent 让 FDE/值班人也能安全决策 |
| **结果验证驱动的学习飞轮** | 记录前后指标、人工决策、动作与恢复结果,反馈回流校准 | 现有流程常止于告警/修复建议;CoAgent 以「是否恢复」作为事故闭环终点 |

> **一句话:把 Agent 事故判断转化为一份有证据、有风险边界、有审批权限、有验证标准的「处置合同」,让非原作者也能安全执行。**

## 系统架构

```
Webhook 事件  →  Scenario Router  →  Playbook Engine  →  真实 LLM 诊断  →  Decision Score
     →  Admin 主控台(SSE timeline)  →  飞书 IM 处置卡片  →  人工反馈  →  飞轮统计 / 校准
```

一个 `POST /events` webhook 接入,事件经场景路由命中 Playbook(`data/ops_playbooks.json` 单一配置源),交由**真实 LLM** 生成经 Pydantic 契约校验的结构化诊断,产出可解释的 **Decision Score**;值班人在 Admin 或飞书卡片上当场处置,反馈回流形成校准飞轮。完整架构见 [docs/diagrams/coagent-architecture.html](docs/diagrams/coagent-architecture.html)。

### Decision Score:可解释的风险评分

总分由三因子加权,分级即处置权限:

```
总分 = 100 × ( 0.35·数据完整度 D + 0.35·Playbook匹配 P + 0.30·推理一致性 C )
```

| 分级 | 含义 | 处置边界 |
|---|---|---|
| 🟢 **可执行** | 证据充分、把握高 | 可直接处置(如人工 Retry) |
| 🟡 **需确认** | 有不确定性 | 需人工确认后处置 |
| 🔴 **升级** | 高风险 / 证据弱 | 必须升级负责人,不自动执行 |

> 三因子(D/P/C)与一致性原始值全部持久化,UI 同时显示原始与校准值;`DEMO_MODE` 仅对一致性因子做有界校准并明确披露(`clamp_applied`),绝不篡改 LLM 文本。

## 三场景

| 场景 | 触发事件 | 因果一跳 | 目标 Score | 处置边界 |
|------|------|----------|------------|----------|
| **S1** 客服 API 限流 | `run_fail/rate_limit` | 并发↑ → 429 → 客服不可用 | 82–88 🟢 | 人工 Retry |
| **S2** RAG 空检索 | `run_fail/empty_retrieval` | 索引 lag → 空检索 → 错误回答 | 65–75 🟡 | 确认后改库 |
| **S3** 日成本超预算 | `cost_report/over_budget` | 模板/流量↑ → Token↑ → 超预算 | 50–58 🔴 | 升级负责人 |

## 快速开始

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
MOCK_LLM=true DEMO_MODE=true uvicorn app.main:app --reload --port 8000
```

打开 http://localhost:8000/ → Tab2 触发 S1/S2/S3 Demo。

## 本地 Claude Agent(真实接入)

三个 Agent 位于 `agents/`,通过 `POST /events` 接入 CoAgent 流水线:

| Agent | 场景 | 触发条件 |
|-------|------|----------|
| `cs-bot` | S1 限流 | Claude 返回 429 / rate limit |
| `rag-bot` | S2 空检索 | 本地 FAQ 无匹配片段 |
| `content-bot` | S3 超预算 | 日累计成本 > `CONTENT_BUDGET_YUAN_DAILY` |

**启动 CoAgent 后:**

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

FAQ 检索规则见 `data/agent_kb/RETRIEVAL.md`;content-bot 按 Token×模板倍率累计成本,超 `CONTENT_BUDGET_YUAN_DAILY` 自动上报 S3。

环境变量:`COAGENT_PUBLIC_URL`、`CLAUDE_BIN`、`CONTENT_BUDGET_YUAN_DAILY`、`CONTENT_COST_PER_1K_TOKENS`。

## 进阶能力

`app/ultra/` 在 P0 闭环之上提供面向规模化运维的增强能力:

| 能力 | 端点 | 说明 |
|---|---|---|
| **知识图谱** | `GET /graph`、`/graph/agent/{id}` | 事故、Agent、工具、责任人的关联视图 |
| **相似事故检索** | `GET /incidents/{trace_id}/similar` | 拉出历史相似事故辅助决策 |
| **What-if 推演** | `POST /incidents/{trace_id}/what-if` | 处置动作的影响预演 |
| **团队编排** | `GET /incidents/{trace_id}/team-plan` | 跨角色协同处置计划 |
| **审计导出 / Replay** | `GET /audit/export`、`POST /replay/{trace_id}` | 只读回放历史 SSE/SQLite,不调用 LLM 或飞书 |

## 官网

静态营销站点位于 `website/`,与管理台分离部署:

```bash
# 本地预览（任选其一）
python3 -m http.server 3000 --directory website
# 或
npx serve website
```

浏览器打开 http://localhost:3000/

## 测试

```bash
bash scripts/run_tests.sh -q
# 或: .venv/bin/python3 -m pytest tests/ -m "not live_llm" -q
bash scripts/demo.sh
```

## License

[MIT](LICENSE)

---

<div align="center">
<sub>CoAgent · 2026 黑客松项目(微软孵化器 × 小宿科技 · ToB AI Agent 赛道)</sub>
</div>
