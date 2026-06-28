# CoAgent 选题文档

> 产品定位：面向生产环境的 **AI Agent 事故决策与受控处置助手（Agent Incident Commander）**。
>
> 市场判断截至：2026-06-28。

## 产品价值

### 1. 一句话价值

> **CoAgent 是面向 AI Agent 进入生产环境后的运行事故场景（运行失败、质量异常、成本失控），提供异常发现、根因诊断、风险决策、受控处置和审计复盘能力的产品。**

### 2. 目标用户

核心用户不是 Agent 的普通使用者，而是事故发生后 **必须判断“动不动、怎么动、谁来承担风险”的责任人**。

| 目标用户 | 典型例子 | 为什么需要 CoAgent |
|---|---|---|
| **Agent 交付负责人和交付值班人** | 为十几家客户交付客服 Agent、RAG 知识库助手的 AI 解决方案团队或系统集成商 | 项目交付后原开发者已经撤场，团队需要用较少人力同时处理多个客户的线上异常 |
| **企业 AI 平台负责人和 SRE/运维值班人员** | 电商、金融或 SaaS 企业中，负责线上客服 Agent、营销 Agent、内部流程 Agent 稳定性的团队 | Agent 已接入真实业务，运行失败、答复质量下降或成本异常会直接影响客户、收入和预算 |
| **接手 Agent 的客户 IT 或业务负责人** | 没有参与 Agent 开发，却需要批准重试、暂停任务、切换模型或升级处理的客户方人员 | 不了解实现细节，单看日志和 Trace 难以判断动作风险，需要能解释、能反驳、能审批的决策依据 |

个人自用或低风险的内部实验 Agent 不是优先用户：这类场景通常可以由开发者直接重启或调试，尚未形成稳定的事故责任和采购需求。

### 3. 痛点场景

Agent 事故的共同难点不是“看不到报错”，而是 **看到异常后仍不知道该不该动，以及动错了由谁负责**。

| 痛点场景 | 具体例子 | 当前处理方式的问题 | CoAgent 提供的价值 |
|---|---|---|---|
| **运行失败：告警有了，但不知道能否立即重试** | 大促期间客服 Agent 并发从 5 提升到 10，触发模型 API 429，5 分钟内失败 47 次、失败率达到 38% | 值班人需要跨监控、Trace 和配置系统找证据，再等待熟悉系统的工程师判断是重试、降并发还是换 Key | 汇总影响、配置变化、错误证据和处置手册，给出“可执行 / 需确认 / 必须升级”的动作边界 |
| **质量异常：系统没宕机，但正在持续答错** | RAG 知识库索引落后一天，空检索率从 5% 升到 35%，Agent 仍正常返回内容，却开始产生幻觉答复和客诉 | 基础设施监控显示正常；盲目重试不能解决索引问题，反而继续把错误答案发给客户 | 将检索质量、索引版本和业务反馈关联为质量事故，明确禁止无效重试，并要求修复知识库后再执行 |
| **成本失控：没有报错，却在持续烧钱** | 新增长文模板后，内容 Agent 日 Token 升至 120 万、增长 180%，成本超过预算 | 成本平台能显示超支，但无法判断该限流、切换模型、暂停批任务还是继续观察，也不清楚谁有权批准 | 估算继续运行的损失，结合影响范围和动作可逆性分级，触发负责人确认或升级审批 |
| **责任断裂：处置完成后无法还原决策过程** | 事故群里有人建议重试、有人临时改配置，恢复后说不清谁批准了什么、哪个动作真正有效 | 建议散落在聊天记录中，监控、执行和审批相互分离，复盘依赖口述，也无法沉淀为下一次的处置依据 | 在同一时间线记录证据、反证、建议、批准人、执行动作和恢复结果，形成可审计、可复用的事故经验 |

## 当前市场格局

### 1. 需求侧：Agent 加速进入生产，运行治理没有同步成熟

- **采用在加速。** McKinsey 2025 年全球调查显示，62% 的受访组织已至少开始试验 AI Agent，但近三分之二尚未在企业范围规模化。这意味着大量 Agent 正处于从试验走向生产、运行问题集中暴露的阶段。
- **治理明显滞后。** Deloitte 2026 年对 3,235 名企业与 IT 负责人的调查显示，只有 21% 的企业具备成熟的自主 Agent 治理模型；多数企业仍缺少清晰的人工审批边界、实时异常监控和完整审计链。
- **失败代价已经从“答错一次”扩大为业务事故。** Agent 会调用工具、访问系统并持续消耗 Token，一次异常可能造成服务中断、错误操作、客户流失、数据风险或成本放大。Gartner 预计，到 2027 年底，超过 40% 的 Agentic AI 项目会因成本上升、价值不清或风险控制不足而被取消。
- **真正缺的是事故时刻的决策能力。** 企业已经能采集 Trace、错误率、延迟和 Token，但事故发生后仍要由人跨多个系统拼证据、找原作者、判断是否重试或回滚，再到群里完成审批和留痕。需求正从“看见 Agent 怎么运行”上移到“出事后如何安全地处置”。

因此，CoAgent 对应的不是一个凭空出现的新预算，而是 LLM Observability、APM/SRE、Incident Management、AI Security 与 FinOps 等现有预算交叉处正在形成的 **Agent 运行事故治理需求**。

### 2. 供应侧：能力已经存在，但分散在不同产品层

| 能力层 | 代表产品 | 当前市场已提供的能力 | 相对 CoAgent 目标场景的缺口 |
|---|---|---|---|
| **Agent 可观测与评测** | LangSmith、Langfuse、Arize Phoenix、Braintrust、Datadog Agent Observability | Trace、会话与工具调用还原，错误/延迟/Token/成本监控，在线评测、异常发现和告警 | 产品主对象通常是 Trace、Session 或 Eval，主要帮助开发者发现和调试问题；事故责任人仍需自行完成处置判断与协同 |
| **Agent Reliability 一体化** | Galileo | Graph/Timeline、持续评测、问题洞察、原因说明、关联证据、修复建议和实时 Guardrail | 是最接近的直接竞品，说明“诊断 + 建议 + 阻断”已不是市场空白；其公开产品重心仍是帮助工程团队构建、调试和保护 Agent，而非围绕值班人组织事故审批、责任和结果验证 |
| **通用 APM、AI SRE 与事故管理** | Datadog、Rootly、PagerDuty | 基础设施与应用告警、根因调查、On-call、Runbook、事故协作和修复建议 | 通用事故流程成熟，但对 Agent 的轨迹、工具选择、回答质量、Token 成本等运行语义不够原生；Datadog 等厂商正在快速补齐这部分能力 |
| **Agent 运行时安全** | Cisco AI Defense、Snyk Evo | 发现 Agent/工具资产，按策略检测、引导或阻断越权工具调用、提示词注入和数据泄露 | 解决的是“动作是否安全”，不以失败、质量下降或成本失控后的业务处置为核心 |
| **人工拼接方案** | 监控告警 + Trace 平台 + 飞书/Slack + 人工 Runbook | 工具齐全、组合灵活，是多数团队当前最现实的处理方式 | 信息分散、依赖原作者和老师傅，处置慢；建议、批准、执行与结果没有统一责任链 |

### 3. 市场结论

市场不存在“完全没人提供能力”的真空。领先产品已经从 **只提供 Trace** 快速扩展到 **诊断、建议、Guardrail 和自动调查**；同时，OpenTelemetry 正在标准化模型调用、工具调用与 Token 等 GenAI 遥测，基础采集能力会进一步商品化。

真正尚未被充分占据的位置是：**以 Agent 事故为第一对象，以值班人和交付负责人为第一用户，把证据、反证、动作风险、人工批准、执行结果与审计记录组织成一个处置闭环。** 这不是单点功能空白，而是产品对象、用户角色和工作流的空白。

## 创新点：CoAgent 与竞品差在哪里

CoAgent 的创新不是“告警后让大模型写一段建议”，也不是发明新的 Trace、置信度或 Human-in-the-loop，而是把已有能力重组为 **Agent 事故现场的可验证、可控、可追责处置系统**。

| 创新点 | 竞品常见做法 | CoAgent 的差异 |
|---|---|---|
| **Incident-first，而非 Trace-first** | 从 Trace、Session、指标或 Eval 进入问题调查 | 将失败、质量和成本异常统一为一个 Agent Incident，直接呈现业务影响、证据、反证、责任人与待决策动作 |
| **服务非原作者，而非只服务开发者** | 帮助 Prompt/Agent 工程师定位和调试 | 面向接手客户 Agent 的 IT、交付值班人和业务负责人，让不了解实现细节的人也能在几分钟内做决定 |
| **风险分级的处置合同，而非一条“置信度”** | 展示评分、洞察或推荐修复，是否执行仍靠人自行判断；Guardrail 则侧重规则阻断 | 综合证据充分度、反证、动作可逆性、影响半径和权限要求，将动作明确分为 **可执行 / 需确认 / 必须升级**；评分直接约束动作权限 |
| **IM 原生责任闭环，而非把用户带回控制台** | 在控制台分析，向 IM 推送通知 | 在飞书中同时给出证据、建议、风险与按钮，完成批准、反对、升级和结果回写，适配中国企业真实值班协作方式 |
| **结果验证与审计，而非止于“给建议”** | 生成诊断或修复建议，反馈主要回流到评测数据 | 把“谁批准—执行了什么—指标是否恢复—避免了多少损失”写入同一时间线，使每次事故可复盘、可追责并能沉淀为下一次处置依据 |
| **Agent 原生三类事故统一处置** | APM 管运行错误，Eval 管质量，FinOps 管成本，安全产品管危险动作 | 在同一责任模型下处理 **运行失败、质量异常、成本失控**，避免值班人跨四套系统拼接结论 |

### 最核心的差异

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
