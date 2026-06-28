# CoAgent 选题文档

> 产品定位：面向生产环境的 **AI Agent 事故识别、风险决策与受控处置助手（Agent Incident Commander）**。
>
> 市场判断截至：2026-06-28。

## 产品价值

### 1. 一句话价值

> **CoAgent 是面向 AI Agent 进入生产环境后的运行事故场景（运行失败、质量异常、成本失控），提供异常发现、根因诊断、风险决策、受控处置和审计复盘能力的产品。**

### 2. 目标用户

核心用户是 Agent 事故发生后负责判断、审批或执行处置的人。

少量、低风险且由原开发者直接维护的 Agent 不是优先用户。

| 目标用户 | 典型例子 | 核心需求 |
|---|---|---|
| **Agent 交付团队** | FDE（前线部署工程师）、AI 解决方案商、系统集成商 | 用少量人力维护多个客户的 Agent |
| **企业 AI 平台与运维团队** | 电商、金融、SaaS 企业的 AI 平台负责人和 SRE | 保障线上 Agent 稳定，控制业务与成本风险 |
| **客户 IT 或业务负责人** | 接手第三方 Agent 的客户方人员 | 看懂处置依据并完成审批或升级 |

### 3. 痛点场景

Agent 事故的核心痛点是：**运行异常难诊断、质量问题难发现、成本失控难止损、处置风险难判断**。

| 痛点场景 | 具体例子 | 当前处理方式的问题 | 价值指标 | 对应能力 |
|---|---|---|---|---|
| **运行异常难诊断** | [API 限流]客服 Agent：大促并发翻倍触发 API 429，失败率达 38% | 需跨监控、Trace 和配置排查，并依赖原工程师决策 | 初步诊断时间↓、MTTR↓ | 多信号汇总、根因诊断、证据链、处置手册匹配 |
| **质量问题难发现** | [空检索]RAG Agent：知识库索引延迟，空检索率达 35%，仍返回幻觉答案 | 基础设施指标正常，盲目重试无法解决问题 | 质量异常发现时间↓、错误影响范围↓ | 质量指标监测、跨信号关联、质量事故识别、无效重试拦截 |
| **成本失控难止损** | [Token 超支]内容 Agent：长文模板使 Token 用量增长 180%，超过日预算 | 只能看到超支，无法判断该限流、降级还是暂停 | 止损时间↓、超预算金额↓ | Token 与成本监测、损失估算、风险分级、限流/降级/暂停建议 |
| **处置风险难判断** | [高风险处置]客服 Agent：需要在重试、降级和暂停中选择，但不清楚动作影响 | 缺少风险依据和权限边界，容易误操作或延误处置 | 决策时间↓、误操作率↓ | 风险评分、处置分级、人工审批、结果验证 |

## 当前市场格局

**AI Agent 试验已广泛展开，但规模化生产与运行治理仍处于早期；市场上的观测、评测、SRE 和安全工具虽在快速完善，能力仍分散在不同产品中，尚未形成面向事故责任人的统一处置闭环。**

### 1. 需求侧：Agent 试验广泛，运行治理滞后，规模化生产受阻

- **62% 已试验 Agent，近 2/3 尚未规模化 AI。** 企业兴趣已形成，但生产落地仍处早期（McKinsey，2025）。
- **仅 21% 具备成熟的 Agent 治理。** 调查覆盖 24 个国家、3,235 名企业与 IT 负责人（Deloitte，2026）。
- **超 40% 的 Agentic AI 项目预计被取消。** 主要原因是成本上升、价值不清和风险控制不足（Gartner，2027 年底预测）。

### 2. 供应侧：单点工具逐步成熟，但完整处置闭环仍靠拼接

现有产品组合能够覆盖 **Agent 事故识别 → 风险决策 → 受控处置 → 结果验证** 的大部分功能，但需要企业自行完成数据统一、规则配置、执行适配和跨系统审计。市场缺口不是“没有能力”，而是缺少低集成成本、Agent 原生的一体化处置闭环。

| 能力层 | 阶段 | 当前市场已提供的能力 | 代表产品 |
|---|:---:|---|---|
| **感知与评测层** | **较成熟** | Trace、指标监控、在线评测、异常告警 | LangSmith、Langfuse、Arize Phoenix、Braintrust、Datadog Agent Observability |
| **诊断与决策层** | **成长期** | 问题聚类、根因调查、关联证据、修复建议 | Galileo、Datadog、Rootly |
| **控制与执行层** | **早期** | Guardrail、策略阻断、Runbook 和基础设施修复 | Galileo、Cisco AI Defense、Snyk Evo、Rootly |
| **协同与治理层** | **分化** | On-call、事故协作、人工审批、留痕复盘 | PagerDuty、Rootly、飞书/Slack + 人工 Runbook |

### 3. 市场结论

**Agent 试验已普及，但规模化生产仍受治理能力制约；市场已有各类单点工具，却缺少低集成成本、Agent 原生的事故处置闭环。CoAgent 的机会不在创造新能力，而在将事故识别、风险决策、受控处置和结果验证整合为一个产品。**

## 能力说明

### 1. 核心能力

CoAgent 围绕 Agent 事故处理过程，提供从发现问题到复盘沉淀的完整能力链。

| 核心能力 | 回答的问题 | 能力说明 |
|---|---|---|
| **事故识别** | 发生了什么？ | 接入运行事件与指标，将运行失败、质量异常和成本失控识别为 Agent 事故 |
| **根因诊断** | 为什么发生？ | 汇总日志、指标、配置和处置手册，形成根因假设、影响判断与证据链 |
| **风险决策** | 要不要动？ | 根据数据、手册和推理依据进行风险分级，输出可执行、需确认或必须升级 |
| **IM 协同** | 如何及时触达并协作？ | 通过飞书等 IM 推送事故证据、风险等级和建议动作，支持确认、升级与结果同步 |
| **受控处置** | 应该怎么动？ | 提供重试、降级、暂停或升级建议，通过人工审批控制高风险动作 |
| **结果验证** | 处置是否有效？ | 记录处置结果并对比前后指标，判断事故是否恢复或需要继续升级 |
| **审计复盘** | 谁做了什么？ | 保存并回放证据、建议、审批、动作和结果，支持责任追溯与事故复盘 |
| **反馈飞轮** | 如何越用越准？ | 基于人工反馈和历史事故，持续完善处置手册、风险规则与提示词 |

> 当前版本以处置建议、人工审批和模拟执行验证流程，不声称能够自动修复生产系统。

### 2. 创新点提炼

CoAgent 的创新不在单个新技术，而在针对 Agent 事故场景形成新的决策与处置机制。

| 创新点 | 核心机制 | 与现有方案的差异 |
|---|---|---|
| **Agent 原生事故模型** | 将运行失败、质量异常和成本失控统一为 Agent 事故，并关联版本、工具调用、业务影响和责任人 | 现有观测工具通常以 Trace、Session 或 Eval 为中心；CoAgent 以需要处置的事故为中心 |
| **风险分级的处置合同** | 将证据、反证、动作风险、可逆性和审批要求组合为明确的执行边界：可执行、需确认或必须升级 | 现有产品多提供评分、建议或策略阻断；CoAgent 让风险判断直接约束动作权限和审批流程 |
| **面向非原作者的 IM 处置** | 将复杂诊断转化为飞书等 IM 中可理解、可确认、可升级的处置卡片 | 现有产品主要服务开发者并在控制台完成调查；CoAgent 服务 FDE、值班人和客户 IT，使非原作者也能安全决策 |
| **结果验证驱动的学习飞轮** | 记录事故前后指标、人工决策、执行动作和恢复结果，并用反馈持续完善处置手册与风险规则 | 现有流程常止于告警或修复建议；CoAgent 将“是否恢复”作为事故闭环终点和后续学习依据 |

> **核心创新：将 Agent 事故判断转化为一份有证据、有风险边界、有审批权限、有验证标准的处置合同，让非原作者也能安全执行。**

## 参考资料

- [McKinsey — The state of AI in 2025](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai/)
- [Deloitte — State of AI in the Enterprise 2026](https://www.deloitte.com/us/en/what-we-do/capabilities/applied-artificial-intelligence/content/state-of-ai-in-the-enterprise.html)
- [Gartner — Over 40% of agentic AI projects will be canceled by end of 2027](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027)
- [LangSmith — Evaluation and online monitoring](https://docs.langchain.com/langsmith/evaluation)
- [Galileo — Agent Reliability Platform](https://galileo.ai/agent-reliability)
- [Datadog — Agent Observability](https://docs.datadoghq.com/llm_observability/)
- [Cisco — AI Defense](https://www.cisco.com/site/us/en/products/security/ai-defense/index.html)
- [Snyk — Evo Agentic Development Security](https://snyk.io/evo/agentic-development-security/)
- [OpenTelemetry — GenAI Observability](https://opentelemetry.io/blog/2026/genai-observability/)
