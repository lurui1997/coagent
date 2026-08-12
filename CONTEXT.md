# CoAgent

Agent 上线后的运行态运维与事故处置上下文：观察 Agent 行为、判定事故、给出可解释的处置边界。

## Language

**Inline Observer**:
CoAgent 作为常驻消费者持续接收 Agent 运行轨迹，在本地完成异常检测，并打开事故处置入口；不要求代理每一笔 LLM/工具调用。
_Avoid_: Incident Bridge（仅收事故候选事件）, 把 CoAgent 做成强制流量代理

**Telemetry Contract**:
Agent 侧以 OpenTelemetry（OTLP）及 GenAI/Agent 语义约定输出 spans/metrics；这是 Trajectory 的主交换格式。
_Avoid_: 自研逐步 JSON 协议作为主契约, 厂商私有 Trace API 作为唯一入口

**Trajectory**:
一次 Agent 运行中按时间顺序排列的可观察步骤序列，在实现上对应一组关联的 OTel spans（模型调用、工具调用、检索、成本等）。
_Avoid_: Trace（外部观测平台产品名）, log dump, 会话全文

**AgentEvent**:
当前仓库已实现的稀疏事故事件契约（type / symptom / error / log_snippet 等），由检测器从 Trajectory 提升而来，用于触发处置流水线。
_Avoid_: 把 Trajectory 或原始 OTel span 直接叫作 Event

**First Agent (R1)**:
仓库内演示 Agent：`cs-bot`、`rag-bot`、`content-bot`，作为 Inline Observer 的首个接入目标。
_Avoid_: 未具名的「真实生产 Agent」当作已完成接入
