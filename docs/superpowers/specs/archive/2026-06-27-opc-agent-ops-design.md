# OPC Agent Ops 设计规格说明

> **⚠️ 已归档。** 已合并为 Final：[coagent-design-spec.md](../coagent-design-spec.md)

**日期：** 2026-06-27  
**状态：** 已合并至 v3  
**产品工作名：** AgentPulse（可改名）  
**与 CoAgent 关系：** **独立产品线** — CoAgent v2 服务 Hackathon（企业 SRE on-call）；本文档服务 OPC 订阅创业

---

## 1. 一句话

> 帮 OPC 在 **3 分钟内** 知道：哪个 Agent 出了问题、花了多少钱、下一步点哪里修。

**客户买到的不是「Agent Ops 平台」，是每月 ¥99 的「Agent 值班通知 + 处置建议」。**

---

## 2. 目标客户（OPC）

| 属性 | 描述 |
|------|------|
| 谁 | 一人公司：独立开发者、小微工作室、超级个体 |
| 规模 | 日常运行 **3–15 个** Agent/自动化（n8n、Make、自研脚本、OpenAI Assistant、Cursor 自动化等） |
| 痛点 | Agent 静默失败、LLM 费用失控、出错后不知道哪一步挂了、没有统一看板 |
| 不是什么 | 没有 on-call 轮值、没有 K8s/Grafana、没有 SRE 团队 |

---

## 3. 付费动作（¥99/月 必须交付）

### 3.1 核心动作（MVP 唯一承诺）

**「Agent 异常 → 5 分钟内推送到你的 IM → 带错误摘要 + 修复建议 + 一键重试链接」**

拆解为可验收行为：

| # | 动作 | 验收标准 |
|---|------|----------|
| A1 | **接入** | 用户 10 分钟内接好 1 条 webhook（n8n/自研/常见平台） |
| A2 | **监控** | 面板显示：今日运行次数、失败次数、LLM 估算成本 |
| A3 | **告警** | 失败或超预算阈值 → 飞书/企业微信/邮件（三选一 MVP） |
| A4 | **解读** | 告警消息含：失败步骤、最近日志摘要、LLM 生成的 1–3 条修复建议 |
| A5 | **重试** | 消息内一键链接触发用户配置的 retry webhook |

**不承诺（v1 不做）：** 自动修、Multi-Agent 编排、企业 CMDB、把握度评分三因子（那是 CoAgent 企业线）。

### 3.2 与 CoAgent 的差异

| | CoAgent（Hackathon） | AgentPulse（OPC） |
|---|---------------------|-------------------|
| 场景 | P1  infra 告警 | Agent/workflow 运行失败 |
| Buyer | SRE 团队 | OPC 个体 |
| 价格 | 企业议价 | ¥99/月 |
| 核心 | 把握度评分 + runbook | 失败通知 + 修复建议 + 重试 |
| 数据 | Mock metrics/CMDB | 用户 webhook 日志 + 可选 LLM usage |

---

## 4. 产品边界（YAGNI）

### 4.1 v1 范围内

- 单租户 Admin 页（运行面板 + 告警历史）
- Webhook 接入：`POST /events` 接收 run_start / run_fail / run_ok / cost_report
- 规则引擎：失败即告警；可选日成本 > ¥X 告警
- LLM 层：仅对 **失败事件** 生成修复建议（真实调用，非模板）
- 通知通道：飞书 OR 邮件（MVP 二选一，建议飞书与 CoAgent 复用 SDK 经验）
- 订阅：Stripe/ LemonSqueezy/ 国内支付（Hackathon 后可接）

### 4.2 v1 范围外

- 多 Agent 编排、可视化 workflow 编辑器
- 企业 SSO、多租户、权限体系
- 与 CoAgent SRE 场景共用 playbook
- 「Agent Ops」全栈平台叙事

---

## 5. 事件模型（Webhook）

```json
{
  "event_id": "evt-001",
  "agent_id": "content-bot",
  "agent_name": "小红书发文 Bot",
  "type": "run_fail",
  "ts": "2026-06-27T14:00:00+08:00",
  "error": "OpenAI rate limit 429",
  "log_snippet": "... last 500 chars ...",
  "cost_yuan_today": 12.5,
  "retry_webhook": "https://user.app/hooks/retry/content-bot"
}
```

支持 `type`：`run_ok` | `run_fail` | `run_start` | `cost_report`

---

## 6. 告警消息模板（IM）

```
🔴 Agent 失败 | content-bot
━━━━━━━━━━━━━━━━
错误：OpenAI rate limit 429
今日成本：¥12.5 / 预算 ¥20
━━━━━━━━━━━━━━━━
建议：
1. 等待 60s 后重试
2. 切换 backup API key
3. 降低 batch 大小
[一键重试] [打开面板]
```

LLM 生成「建议」三条；**失败时不伪造成功态**。

---

## 7. Admin 面板（OPC 版，极简 2 Tab）

### Tab 1 — 今日面板

- Agent 列表：名称、今日次数、失败数、成本  
- 最近 10 条事件 timeline  

### Tab 2 — 设置

- Webhook URL + secret  
- 通知通道（飞书 webhook / 邮件）  
- 日成本预算阈值  
- Retry 模板  

---

## 8. 商业模式（印钞机规格）

| | 内容 |
|---|------|
| **Input** | OPC 配置 webhook + 通知渠道；平台提供告警 + LLM 解读 |
| **Output** | 异常 5 分钟内可达 + 可执行下一步 |
| **定价** | ¥99/月（单用户，最多 10 个 agent_id） |
| **利润款（后续）** | ¥999/月：无限 agent + 电话/短信 + 自动重试 + 周报 |
| **价差** | 10x，符合引流/利润款结构 |

**Layer 1→2 任务：** 找到 **10 个 OPC** 愿意接 webhook 试用 → **1 个** 付 ¥99。

---

## 9. 获客（冷启动，零渠道）

不做大盘流量。顺序：

1. **Dogfood** — 自己的 3 个 automation 接入  
2. **同温层** — 独立开发者社群发「我做了个 Agent 挂了通知工具」  
3. **对标** — n8n 社区、V2EX、即刻 AI 独立开发者  
4. **钩子** — 免费 tier：1 agent + 邮件告警；¥99 加飞书 + LLM 建议  

**禁止：** 在 OPC 没验证前做企业 SRE 销售。

---

## 10. MVP 成功标准

- [ ] 用户 10 分钟内接好 webhook，面板能看到事件  
- [ ] 模拟 `run_fail`，5 分钟内 IM 收到带 LLM 建议的消息  
- [ ] 一键 retry 链接触发用户 URL  
- [ ] 1 个非本人 OPC 愿意连续用 7 天  
- [ ] 1 笔 ¥99 真实付款（Layer 2）

---

## 11. 48h 与创业节奏

| 阶段 | 时间 | 重点 |
|------|------|------|
| Hackathon | 现在 | **只做 CoAgent v2**，赢比赛 |
| Week 1 后 | 3–5 天 | AgentPulse MVP：webhook + 面板 + 飞书 + LLM 建议 |
| Week 2 | | 自己 dogfood + 找 5 个试用 |
| Week 3–4 | | 第一笔 ¥99 |

**不要 Hackathon 48h 内双线作战。**

---

## 12. 开放问题

1. 产品名：AgentPulse / OpsBell / 其他  
2. 国内支付接入时机  
3. LLM 成本：¥99 是否含 LLM 额度 cap  

---

## 13. 诊断备忘（dbs-diagnosis）

- 「Agent Ops」已落地为：**失败告警 + 成本可视 + LLM 修复建议 + 重试**  
- 印钞机待验证：需第一笔 ¥99，不是 spec  
- 与 CoAgent 分线正确：Hackathon 叙事 ≠ OPC 订阅  
