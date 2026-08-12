# Adopt OpenTelemetry as the trajectory contract for Inline Observer

CoAgent will observe real Agents as a continuous consumer of trajectories, but the primary wire format is OpenTelemetry (OTLP + GenAI/Agent semantic conventions), not a proprietary step API or an inline LLM/tool proxy.

This keeps instrumentation portable across frameworks, lets existing OTel/Langfuse-style exporters feed CoAgent, and preserves today's Playbook/scoring path by promoting detected anomalies into `AgentEvent` incidents.

**Considered options:** proprietary emit SDK only; traffic-proxying gateway; vendor-only Trace APIs as the sole ingest path.
