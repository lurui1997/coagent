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

**Real LLM Only**:
本项目运行与演示路径必须调用真实 LLM API；禁止以 Mock 响应冒充模型输出。
_Avoid_: MOCK_LLM 演示捷径, 内置 MOCK_RESPONSES 作为默认可运行路径

**Showcase Packaging**:
Showcase 以本仓独立包 `showcase/faq_agent` 交付：自有 FAQ、运行入口、metrics 与看板；经 OTLP 接入 CoAgent，不与黑客松 demo bot 混为一谈。
_Avoid_: 把 Showcase 逻辑塞进 `agents/rag_bot.py` 作为唯一形态; 另起独立 git 仓库作为第一版
