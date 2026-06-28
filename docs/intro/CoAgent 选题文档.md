# CoAgent 选题文档

> 产品定位：面向生产环境的 **AI Agent 事故决策与受控处置助手（Agent Incident Commander）**。
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

### 2. 供应侧：能力沿事故生命周期分布在四层【待修改】

| 能力层 | 阶段 | 当前市场已提供的能力 | 尚未解决的问题 | 代表产品 |
|---|:---:|---|---|---|
| **感知与评测层** | **较成熟** | Trace、指标监控、在线评测、异常告警 | 信号仍按 Trace、质量和成本分散，难以统一识别业务事故 | LangSmith、Langfuse、Arize Phoenix、Braintrust、Datadog Agent Observability |
| **诊断与决策层** | **成长期** | 问题聚类、根因调查、关联证据、修复建议 | 诊断偏开发者视角，缺少反证、动作风险和可执行边界 | Galileo、Datadog、Rootly |
| **控制与执行层** | **早期** | Guardrail、策略阻断、Runbook 和基础设施修复 | 擅长阻断或修基础设施，Agent 事故后的审批、受控执行和结果验证仍不完整 | Galileo、Cisco AI Defense、Snyk Evo、Rootly |
| **协同与治理层** | **分化** | On-call、事故协作、人工审批、留痕复盘 | Agent 证据、人工决策、执行动作和恢复结果尚未形成统一责任链 | PagerDuty、Rootly、飞书/Slack + 人工 Runbook |

当前市场已覆盖“看见、分析、阻断、协作”等单点能力，但尚未贯通 **Agent 事故识别 → 风险决策 → 受控处置 → 结果验证**；企业仍需组合多层产品并依赖人工衔接，需求侧的诊断、止损和决策问题因此没有被完整解决。

### 3. 市场结论【待修改】

市场不存在“完全没人提供能力”的真空。领先产品已经从 **只提供 Trace** 快速扩展到 **诊断、建议、Guardrail 和自动调查**；同时，OpenTelemetry 正在标准化模型调用、工具调用与 Token 等 GenAI 遥测，基础采集能力会进一步商品化。

**执行层也不是蓝海。** Galileo、Cisco 和 Snyk 已提供运行时引导或阻断，通用 AI SRE 产品也在提供自动调查和基础设施修复。相对空白不在“能不能执行”，而在 **Agent 事故发生后，能否针对失败、质量和成本问题，结合风险分级、人工审批与结果验证完成受控处置**。

真正尚未被充分占据的位置是：**以 Agent 事故为第一对象，以值班人和交付负责人为第一用户，把证据、反证、动作风险、人工批准、执行结果与审计记录组织成一个处置闭环。** 这不是单点功能空白，而是产品对象、用户角色和工作流的空白。

## 创新点：CoAgent 与竞品差在哪里【待修改】

CoAgent 的创新不是“告警后让大模型写一段建议”，也不是发明新的 Trace、置信度或 Human-in-the-loop，而是把已有能力重组为 **Agent 事故现场的可验证、可控、可追责处置系统**。

| 创新点 | 竞品常见做法 | CoAgent 的差异 |
|---|---|---|
| **Incident-first，而非 Trace-first** | 从 Trace、Session、指标或 Eval 进入问题调查 | 将失败、质量和成本异常统一为一个 Agent Incident，直接呈现业务影响、证据、反证、责任人与待决策动作 |
| **服务非原作者，而非只服务开发者** | 帮助 Prompt/Agent 工程师定位和调试 | 面向接手客户 Agent 的 IT、交付值班人和业务负责人，让不了解实现细节的人也能在几分钟内做决定 |
| **风险分级的处置合同，而非一条“置信度”** | 展示评分、洞察或推荐修复，是否执行仍靠人自行判断；Guardrail 则侧重规则阻断 | 综合证据充分度、反证、动作可逆性、影响半径和权限要求，将动作明确分为 **可执行 / 需确认 / 必须升级**；评分直接约束动作权限 |
| **IM 原生责任闭环，而非把用户带回控制台** | 在控制台分析，向 IM 推送通知 | 在飞书中同时给出证据、建议、风险与按钮，完成批准、反对、升级和结果回写，适配中国企业真实值班协作方式 |
| **结果验证与审计，而非止于“给建议”** | 生成诊断或修复建议，反馈主要回流到评测数据 | 把“谁批准—执行了什么—指标是否恢复—避免了多少损失”写入同一时间线，使每次事故可复盘、可追责并能沉淀为下一次处置依据 |
| **Agent 原生三类事故统一处置** | APM 管运行错误，Eval 管质量，FinOps 管成本，安全产品管危险动作 | 在同一责任模型下处理 **运行失败、质量异常、成本失控**，避免值班人跨四套系统拼接结论 |

### 最核心的差异【待修改】

> **Galileo、LangSmith 和 Datadog 更擅长告诉工程师“Agent 发生了什么、为什么”；Cisco 和 Snyk 更擅长判断“这个动作能不能执行”；CoAgent 要解决的是“事故已经发生，现在谁该基于什么证据、以什么权限做哪个动作，并如何证明处置有效”。**

因此，CoAgent 的护城河不能只建立在 Decision Score 公式上。真正需要验证和积累的是：Agent 事故模型、企业处置手册、风险与权限策略、IM 协作入口，以及“事故—决策—动作—结果”形成的组织经验数据。

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
