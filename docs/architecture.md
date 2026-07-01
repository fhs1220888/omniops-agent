# Architecture

OmniOps Agent is a local-first incident diagnosis system. It models the shape of an enterprise agent platform without requiring production infrastructure. The current implementation uses FastAPI, LangGraph, deterministic fake tools, local JSON memory, and pure Python explainability structures.

## Harness Layer

The `app/harness/` package describes the system as an Agent Harness. It is a lightweight contract layer over the existing workflow rather than a replacement for LangGraph or the Tool Gateway.

The harness includes:

- `HarnessConfig`: derives LLM mode, tools mode, observability backend, and evidence requirements from `app/core/config.py`.
- `HarnessPolicy`: exposes tool allow/review/deny behavior and report evidence sufficiency rules while reusing the existing Tool Gateway policy.
- `HarnessExecutionTrace`: describes agent steps, tool calls, evidence items, failures, and timing as one trace contract.
- `EvidenceContract`: documents the required shape for tool evidence: source, tool, service, empty, error, and items.
- `HarnessResult`: summarizes root cause, confidence, evidence count, executed tools, failed tools, tool sources, and evidence sufficiency.
- `OmniOpsHarnessRuntime`: describes harness capabilities, validates runtime mode, and summarizes diagnosis results.

The status endpoint `GET /api/harness/status` combines harness identity, capabilities, runtime mode, live backend reachability, and evidence policy. It reuses the existing runtime status service instead of duplicating backend probes.

## Harness vs Agent vs Tool

- Harness: the orchestration boundary. It owns contracts for configuration, policy, evidence, execution trace, runtime status, and result summaries.
- Agent: a workflow node with a specific responsibility, such as planner, triage, investigation, reflection, or report.
- Tool: an external or local capability called by the investigation layer, such as logs, metrics, traces, memory, or high-risk operational tools.

The LLM is not the harness. It is one model used by the report agent after the harness has gathered and constrained evidence.

## RAG Knowledge Layer

The RAG Knowledge Base lives in `app/knowledge/`. It stores long-term diagnostic knowledge:

- runbooks
- SOPs
- historical RCA notes
- architecture documents

It does not store live logs, metrics, or traces. Live runtime evidence still comes from Prometheus, Loki, and Tempo.

The first implementation uses deterministic local embeddings and a lightweight JSON vector index under `.chroma/`. The configured backend name is `local_chroma`; this gives the project a local vector retrieval boundary without introducing pgvector or a heavy external service.

Report generation uses retrieved knowledge as guidance only. The RCA guardrail remains:

- real-time evidence determines root cause
- retrieved runbooks can guide diagnosis and mitigation
- runbooks are not treated as live facts
- if evidence is empty, the report must say evidence is insufficient

## Skill Layer

The `skills/**/SKILL.md` files define reusable agent behavior. Skills are Markdown prompt/workflow packages, not tools and not live evidence.

The Skill layer includes:

- `app/skills/loader.py`: loads `skills/**/SKILL.md`
- `app/skills/registry.py`: exposes skill metadata and lookup
- `app/skills/selector.py`: deterministically selects relevant skills
- `app/api/skills.py`: exposes skill status, selection, and content APIs

Skills guide Report Agent behavior by describing required evidence, reasoning steps, output contracts, and guardrails. They do not execute actions. They do not replace Prometheus, Loki, Tempo, or RAG runbooks.

The Report Agent includes selected skill excerpts in the prompt while preserving the evidence-first rule:

- live evidence determines root cause
- RAG runbooks are operational knowledge
- skills are diagnosis methodology
- if evidence is insufficient, say evidence insufficient

## Real Mode Anti-Fallback Guarantees

The harness and provider layer preserve the same rule: real mode must not silently fall back to fake data.

The live real mode is:

```env
USE_FAKE_LLM=false
USE_FAKE_TOOLS=false
OBSERVABILITY_BACKEND=prometheus_loki_tempo
```

When live mode is enabled:

- fake tools are disabled by configuration
- providers return explicit empty/error payloads for backend failures
- evidence count can be zero, but the report must mark evidence insufficient
- failed tools remain visible in the final result
- `/api/runtime/status` and `/api/harness/status` expose whether fake tools are enabled

## Future Harness Extensions

The harness boundary is intended to make new backends and tool systems additive:

- Kubernetes: add providers or tools for events, pod status, deployment history, and rollout metadata.
- Datadog: add metrics, logs, and trace providers behind the same evidence contract.
- CloudWatch: add AWS logs and metrics providers with service naming normalization.
- PagerDuty or incident systems: add incident enrichment while preserving the same `HarnessResult`.
- MCP-style adapters: map external MCP tools through the existing Tool Gateway policy.

Production integration should customize metric names, Loki labels, Tempo trace lookup, authentication, tenant headers, TLS, and service naming conventions without changing the core agent workflow.

## LangGraph Workflow

The diagnosis graph is defined in `app/agents/graph.py`.

```text
planner -> triage -> investigate -> report
```

The graph state is an `IncidentState` dictionary. It carries incident metadata, selected tools, execution metadata, evidence, traces, policy records, approval records, and final RCA output.

The nodes are:

- `planner`: selects investigation tools.
- `triage`: sets affected service and time window.
- `investigate`: runs selected tools concurrently.
- `report`: builds the final RCA report.

Agent tracing wraps each node and records:

- agent name
- start and finish timestamps
- duration
- status
- summary

## Planner

The planner is deterministic. It chooses from:

- `logs`
- `metrics`
- `traces`
- `memory`

Routing examples:

- latency issue -> `metrics + traces`
- pod crash -> `logs + memory`
- database timeout -> `logs + metrics + traces + memory`
- consumer lag demo -> `logs + memory`
- bad config demo -> `logs + memory`

The planner records:

- investigation objectives
- required tools
- reasoning
- skipped tools

## Async Investigation

The investigation node runs selected tools concurrently with `asyncio.gather`.

Each tool execution is isolated:

- one tool can fail without failing the whole diagnosis
- one tool can time out without blocking other evidence
- successful tools still contribute evidence

The state records:

- executed tools
- failed tools
- skipped tools
- per-tool timings
- total investigation duration
- tool traces
- policy records

## Tool Gateway

All tool execution goes through `app/tools/gateway.py`.

The gateway evaluates policy before execution. It handles:

- policy decision
- timeout
- execution errors
- metadata records
- tool call traces
- approval request creation for high-risk tools

Current read-only observability tools:

- `query_logs`
- `query_metrics`
- `query_traces`
- `query_memory`

The observability tool layer has three modes:

- `USE_FAKE_TOOLS=true`: generated deterministic demo data, used by tests and demos.
- `USE_FAKE_TOOLS=false` with `OBSERVABILITY_BACKEND=file`: file-backed observability records from `OBSERVABILITY_DATA_FILE`.
- `USE_FAKE_TOOLS=false` with `OBSERVABILITY_BACKEND=prometheus_loki_tempo`: live Prometheus, Loki, and Tempo queries.

Mode 1: fake tools.

- Purpose: unit tests, deterministic demos, offline development.
- Source: local deterministic generators.
- Fallback behavior: this is the fallback mode, selected explicitly through configuration.

Mode 2: file observability.

- Purpose: replay exported real observability records without running vendor backends.
- Source: JSON file with `logs`, `metrics`, and `traces`.
- Fallback behavior: missing records produce explicit empty evidence; the system does not switch to generated fake data.

Mode 3: live observability.

- Purpose: interview demo and local integration with real backend APIs.
- Source: Prometheus HTTP API, Loki HTTP API, and Tempo HTTP API.
- Fallback behavior: backend failures become `empty`/`error` evidence records; the system does not switch to generated fake data.

The live mode is the only direct backend mode:

```env
USE_FAKE_LLM=false
USE_FAKE_TOOLS=false
OBSERVABILITY_BACKEND=prometheus_loki_tempo
```

Provider failures and empty responses are preserved as evidence metadata. The system does not silently fall back to fake data in file or live mode.

## Local Live Demo Stack

The local live demo uses `deploy/docker-compose.observability.yml`:

- `order-service` produces real HTTP traffic, structured logs, Prometheus metrics, and OpenTelemetry traces.
- Prometheus scrapes `order-service:/metrics`.
- `order-service` pushes structured logs to Loki with `service=order-service` and `trace_id` fields.
- OpenTelemetry Collector receives OTLP traces from `order-service` and forwards them to Tempo.
- OmniOps queries Prometheus, Loki, and Tempo through the live observability provider.

This keeps fake data out of the live demo path while preserving fake mode for unit tests and deterministic demos.

Production integration usually requires adapting:

- Prometheus metric names, such as request counters, error counters, and latency histograms.
- Loki labels, especially the service label used by `{service="..."}` queries.
- Tempo trace ID extraction from logs and trace payload shape.
- Service naming conventions across metrics, logs, traces, incidents, and deployment metadata.
- Authentication, TLS, tenant headers, and network routing for production observability backends.

Current high-risk or blocked tools:

- `restart_service`
- `execute_sql`
- `read_env_vars`
- `delete_database`

## Policy: Allow, Review, Deny

Policy lives in `app/tools/policy.py`.

Rules:

- unknown tool -> deny
- critical tool -> deny
- approval-required tool -> review
- low-risk read-only tool -> allow
- max calls per incident is enforced from tool metadata

Policy records are included in diagnosis output and the report.

## Human Approval

High-risk tools do not execute immediately.

When policy returns `review`, the gateway creates an in-memory `ApprovalRequest` through `ApprovalService` and raises `HumanApprovalRequired`.

Approval APIs:

- `GET /api/approvals/pending`
- `POST /api/approvals/{approval_id}/approve`
- `POST /api/approvals/{approval_id}/reject`

The demo endpoint `POST /api/demo/high-risk-tool` attempts `restart_service` and returns an approval ID instead of executing the tool.

## AgentOps Tracing

Agent traces are defined in `app/models/agent_trace.py`.

Each graph node records:

- `agent_name`
- `started_at`
- `finished_at`
- `duration_ms`
- `status`
- `summary`

Tool traces are defined in `app/models/tool_trace.py`.

Each gateway call records:

- `tool_name`
- `policy_decision`
- `risk_level`
- `duration_ms`
- `status`
- `error`

These traces appear in both the diagnosis response and report markdown.

## Evidence Graph

The evidence graph lives in `app/rag/graph_store.py`.

It is an in-memory Python graph with:

Node types:

- `Service`
- `Metric`
- `LogPattern`
- `TraceSpan`
- `Memory`

Edge types:

- `supports`
- `caused_by`
- `related_to`

Functions:

- `add_node()`
- `add_edge()`
- `get_neighbors()`
- `export_graph()`

Tool results become normalized evidence items and evidence graph nodes. Example relation:

```text
RedisTimeoutException -> supports -> redis_pool_exhaustion
redis_pool_exhaustion -> caused_by -> order-service
```

The graph is exported as a plain dictionary in diagnosis output. There is no Neo4j, database, vector DB, or external graph service.

## Report Generation

The report includes:

- root cause
- recommended actions
- evidence summary
- confidence scores
- missing evidence
- policy decisions
- approval-required tools
- denied tools
- agent timeline
- tool timeline

The RCA JSON can come from a real OpenAI-compatible API when configured, but tests force fake mode.

## Benchmark Suite

The benchmark service runs deterministic demo scenarios:

- `redis_timeout`
- `mysql_slow_query`
- `kafka_lag`
- `bad_config_deploy`

Metrics:

- RCA accuracy
- evidence precision
- average duration
- average agent count
- average tool count

The benchmark writes `benchmark_report.md`.

## Current Constraints

The implementation intentionally avoids:

- PostgreSQL
- Redis
- Kafka runtime
- vector database
- Neo4j
- LangSmith

The project includes a Docker Compose stack only for the local live observability demo. Core OmniOps state remains local and lightweight.
