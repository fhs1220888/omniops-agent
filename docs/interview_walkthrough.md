# Interview Walkthrough

## 30 Second Project Introduction

OmniOps is an observability-driven Agent Harness for multi-agent incident diagnosis and RCA. It takes an incident, plans which evidence sources to inspect, queries logs, metrics, traces, and memory through policy-gated tools, builds an evidence graph, reflects on evidence sufficiency, and generates a root cause report.

The project is not a chatbot. It is a structured incident workflow with tool governance, runtime verification, evidence contracts, and live Prometheus/Loki/Tempo integration.

## 2 Minute Architecture Walkthrough

Start with the workflow:

```text
planner -> triage -> async investigation -> Tool Gateway -> Evidence Graph -> reflection -> report
```

Then explain the layers:

- FastAPI exposes incident, demo, approval, runtime, and harness APIs.
- LangGraph coordinates planner, triage, investigation, reflection, and report agents.
- The planner selects only the needed tools.
- Investigation runs selected tools concurrently and isolates failures/timeouts.
- Tool Gateway enforces allow/review/deny policy before execution.
- Observability providers support fake, file, and live Prometheus/Loki/Tempo modes.
- Evidence items and an evidence graph make the RCA explainable.
- The Agent Harness layer describes config, policy, evidence contracts, execution trace, and result summaries.

## How To Prove It Is Not Fake Data

Run live mode:

```env
USE_FAKE_LLM=false
USE_FAKE_TOOLS=false
OBSERVABILITY_BACKEND=prometheus_loki_tempo
```

Then show:

- `/api/runtime/status` reports `tools_mode=real`.
- `/api/harness/status` reports fake tool fallback is not allowed.
- `scripts/run_live_demo_check.py` finds `order-service` metrics in Prometheus, logs in Loki, and traces in Tempo.
- `scripts/smoke_real_observability.py` reports tool sources `["loki", "prometheus", "tempo"]`.

If a backend is empty or unreachable, tools return explicit `empty` or `error` evidence. They do not switch to generated fake data.

## How To Explain Agent Harness

The LLM is the model. The harness is the engineering control plane around it.

OmniOps Harness responsibilities:

- configuration and runtime mode detection
- planner-driven tool selection
- policy-gated tool execution
- evidence contract enforcement
- execution tracing
- evidence sufficiency checks
- result summarization
- live demo verification

This makes the project closer to an agent platform slice than a prompt wrapper.

## What Failure Types Can It Diagnose?

OmniOps is aimed at microservice runtime failures. The current live demo and diagnostic benchmark cover:

- Redis timeout and connection pool exhaustion
- Downstream payment-service timeout
- Database slow query and missing index signal
- Application exception and HTTP 500 spike
- Service unhealthy response and HTTP 503
- Latency spike
- Evidence insufficient handling for unknown services

The multi-agent value is not one `if` branch per failure. The value is the RCA workflow: planner-driven evidence collection, policy-gated tools, logs/metrics/traces correlation, evidence graph construction, reflection on sufficiency, and report generation. In real mode, tools do not fall back to fake data, so if the evidence is empty the system must surface that limitation instead of guessing.

## Current Limitations

- Local JSON and in-memory state instead of durable storage.
- Approval requests are not persisted.
- Provider query templates are minimal and should be tuned for real production metrics and labels.
- No production auth, tenant headers, TLS, or RBAC for observability backends yet.
- No real Kubernetes, Datadog, CloudWatch, or MCP integrations yet.

## Future Extensions

- Kubernetes event and rollout provider.
- Datadog and CloudWatch observability providers.
- Durable trace and incident storage.
- MCP adapters routed through the Tool Gateway.
- Richer benchmark scenarios with noisy and ambiguous evidence.
