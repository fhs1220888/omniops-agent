# OmniOps Agent Harness Design

## What Is An Agent Harness?

An Agent Harness is the engineering layer that makes an agent reliable enough to operate beyond a prompt demo. It controls how a model is invoked, which tools can run, how evidence is collected, how failures are represented, and how the final result is validated.

In OmniOps, the model is the LLM used by report generation. The harness is the system around it.

## OmniOps Harness Components

- Planner: selects logs, metrics, traces, and memory based on incident attributes.
- Tool Gateway: applies allow/review/deny policy before tool execution.
- Observability providers: connect fake tools, file observability, or live Prometheus/Loki/Tempo.
- Evidence contract: requires each tool path to expose source, empty/error state, and evidence items.
- Skill registry: loads Markdown reusable diagnosis skills and injects selected guidance into report generation.
- Execution trace: unifies agent traces, tool traces, evidence, and failures.
- Reflection: checks whether evidence is sufficient and optionally requests another investigation round.
- Runtime status: exposes whether the system is fake, file-backed, or live real mode.
- Evaluation scripts: verify runtime mode, live backend data, and smoke diagnosis.

## Capability Matrix

| Capability | Current Status | Notes |
| --- | --- | --- |
| Multi-agent orchestration | Implemented | Planner, triage, investigation, reflection, report |
| Dynamic tool routing | Implemented | Planner-selected logs, metrics, traces, memory |
| Tool governance | Implemented | Low-risk allow, high-risk approval, critical deny |
| Human approval | Implemented | In-memory approval workflow and API |
| Async investigation | Implemented | Concurrent selected tools with timeout isolation |
| Evidence tracking | Implemented | Evidence items and in-memory evidence graph |
| AgentOps tracing | Implemented | Agent and tool timelines in diagnosis output |
| Fake mode | Implemented | Deterministic tests and offline demos |
| File observability mode | Implemented | Replay exported JSON logs, metrics, traces |
| Live observability mode | Implemented | Prometheus, Loki, Tempo providers |
| Runtime verification | Implemented | `/api/runtime/status`, `/api/harness/status`, scripts |
| Durable persistence | Not implemented | Intentionally out of scope for local MVP |

## Implemented Harness Contracts

`app/harness/config.py`

- derives harness mode from existing application settings
- does not duplicate environment parsing
- identifies fake, file, and live observability mode

`app/harness/policy.py`

- reuses existing Tool Gateway policy
- exposes simple `allow_tool`, `require_human_approval`, and `allow_report` methods
- records that real mode fake fallback is not allowed

`app/harness/execution_trace.py`

- describes the unified trace shape for incident id, agent steps, tool calls, evidence, failures, and timing

`app/harness/evidence_contract.py`

- describes the expected evidence payload from tools and providers

`app/harness/result.py`

- summarizes root cause, confidence, evidence count, executed tools, failed tools, tool sources, and sufficiency

`app/harness/runtime.py`

- exposes harness capabilities
- validates runtime mode
- converts diagnosis results into a harness-level result summary

## Why This Is Not A Chatbot

A chatbot can answer questions without proving where the answer came from. OmniOps requires:

- planned tool selection
- policy-gated execution
- source-specific evidence
- explicit missing evidence
- failed tool visibility
- live runtime mode checks
- benchmark and smoke verification

The LLM is constrained by the harness. It should produce an RCA only from evidence, and live mode must not invent logs, metrics, or traces when backends are empty.

## Current Limitations

- Harness models are a contract layer and do not yet replace every internal response model.
- Runtime state is local and in-memory.
- Approval requests are not durable.
- Production observability auth, TLS, tenant headers, and custom schemas are not implemented.
- Provider query templates are intentionally minimal and should be tuned for each production stack.

## Future Extensions

- Kubernetes provider for events, pod status, and deployment history.
- Datadog provider for metrics, logs, and APM traces.
- CloudWatch provider for AWS-native logs and metrics.
- MCP adapters routed through the Tool Gateway.
- Durable execution trace storage.
- Richer benchmark suites with noisy and ambiguous incidents.
