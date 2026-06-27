# CoAgent 核心创新点

**日期：** 2026-06-27  
**来源：** 基于 [coagent-design-spec.md](./coagent-design-spec.md) §1.5 提炼  
**状态：** 摘要文档

---

## 一句话定位

**ToB Agent Ops Copilot**：Agent 出错或烧钱时，不只告诉你「挂了」，而是沿因果链推一跳，给出带证据链、把握度和处置边界的方案。

> Agent 出错或烧钱时，90 秒内拿到「该信什么、该做什么、有多把握」——带 Decision Score 的 Agent Ops Copilot。

---

## 创新叙事重心

CoAgent 的核心创新不在「告警 + LLM 写建议」，而在 **Agent Ops 层的可验证因果处置闭环**。

| 叙事层级 | 评委感知 | 创新性 |
|----------|----------|--------|
| ❌ 弱 | 「又一个 Agent 监控/告警工具」 | 低 |
| ⚠️ 中 | 「LLM 帮写 runbook」 | 中 |
| ✅ **CoAgent 主线** | **「Agent 异常 → 因果一跳 → Decision Score 可验证 → Human-in-loop 处置 → 飞轮复盘」** | **高** |

---

## 五大核心创新

### 1. 因果一跳（Causal One-Hop），而非 log join

不是像 Datadog / Azure SRE Agent 那样做 infra 变更关联，而是在 **Agent 运行态** 做 Playbook 约束下的因果推理：

| 场景 | 因果一跳 | 处置边界 |
|------|----------|----------|
| **S1 限流** | 流量↑ → 429 → 客服不可用 | 可 Retry 🟢 |
| **S2 空检索** | 索引 lag → 空检索 → 幻觉答复 | 不能盲 Retry 🟡 |
| **S3 超预算** | 发布/流量 → Token↑ → 超预算 | 必须升级止血 🔴 |

前沿差异在 **因果 + 拓扑**，不在单纯 join。CoAgent 的「因果」落在 **Agent 运行态层**。

### 2. Decision Score：可验证推理，非 LLM 自报 confidence

三因子公式：

```
total = round(100 × (0.35×D + 0.35×P + 0.30×C))
```

| 因子 | 含义 |
|------|------|
| **D** data_completeness | 数据完备度（字段、log、tools 成功率） |
| **P** playbook_match | 手册匹配度（symptom/type vs Ops 标签） |
| **C** reasoning_consistency | 推理一致性（hypothesis/steps vs error/log 规则） |

输出 🟢🟡🔴 分级，直接回答 **「敢不敢动」**——针对运维场景 **零幻觉容忍**，Decision Score 是主要差异抓手。

| total | grade | 动作 |
|-------|-------|------|
| ≥80 | executable 🟢 | 建议按步骤执行（人工确认高风险） |
| 60–79 | needs_confirmation 🟡 | 请负责人确认 |
| <60 | escalate 🔴 | @oncall / Admin 强调升级 |

### 3. Human-in-loop 的处置边界

Score 不是装饰，而是 **动作权限**：

- **S1 🟢**：Score 85，可一键 Retry —— **敢动手**
- **S2 🟡**：Score 70，不建议 Retry，需改知识库 —— **不敢盲动**
- **S3 🔴**：Score 54，高风险步骤不可自动执行，须升级 @ —— **必须升级**

同一套 `run_fail` 事件，S1 能 Retry、S2 不能——Score 定义「敢不敢动」的边界。

### 4. 过程可审计 + 反馈飞轮

- Admin SSE timeline + SQLite incident 全链路留痕
- 👍/👎 反馈驱动 Ops 手册与 prompt 迭代
- 解决企业 **「说不清当时建议了什么、谁批准的」** 的复盘痛点

价值递进：

```
听见异常 → 获得处置建议 → 评估把握程度 → 团队复盘迭代
   │              │                │              │
 告警+面板      LLM+Retry        Decision Score    飞轮+@升级
```

### 5. 赛道切口：填补「Agent 运行态 Ops」真空

PagerDuty 管 infra，不管 Agent 运行态；通用 Chatbot 不管 **Ops 决策与置信度**。

| 现成路线 | 做什么 | CoAgent 差异 |
|----------|--------|--------------|
| Azure SRE Agent / Rootly / Harness | 变更 + 遥测 **关联**，根因+置信度 | 不做 infra 变更归因；做 **Agent Ops 层因果 + Score 可验证** |
| Datadog / 通用 APM | 告警 → 调查 → 「什么变了」 | 聚焦 **LLM Agent 失败/成本**，非通用 infra |
| 飞书/邮件 Webhook 通知器 | 挂了提醒 | 有 **推理链 + Score + 飞轮**，不是通知 |
| 通用 Chatbot Copilot | 自然语言问答 | **事件驱动 Playbook + 结构化处置 + 审计** |

**CoAgent 占用的真空：**  
**「运维 AI 应用本身」+ 「零幻觉可解释处置」** — 与 LLMOps 哨兵方向同构，Decision Score 是差异抓手。

---

## Pitch 必讲「三件套」

1. **跨信号 Agent Ops 推理** — 不是 log join，是 Playbook 约束下的因果链
2. **每步可验证** — Decision Score 分解，评委可追问公式
3. **处置可闭环** — 建议 + 把握度 + Retry/升级，全程留痕

---

## 与竞品一句话（Q&A 备用）

| 他们 | 我们 |
|------|------|
| 管服务器 / 5xx | 管 **Agent 失败、质量、成本** |
| 告警 + 建议 | **Score 可验证 + 审计闭环** |
| SaaS 吃数据 | **本地部署，日志不出域** |

---

## 总结

CoAgent 的创新内核：

> **Agent 异常 → 因果一跳 → Decision Score 可验证 → Human-in-loop 处置 → 飞轮复盘**

同一套代码，叙事从「又一个 Agent 监控工具」上移到 **「带把握度的 Agent Ops 因果处置 Copilot」**——Decision Score 三因子 + 三场景（敢动手 → 不敢盲动 → 必须升级）是 Demo 与答辩的主线。

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [coagent-design-spec.md](./coagent-design-spec.md) | Hackathon 唯一实施基线 |
| [idea.md](../../../idea.md) | 方向收敛 / 切口定位参考 |
