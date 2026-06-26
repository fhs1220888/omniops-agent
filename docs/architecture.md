# Architecture

OmniOps Agent is a local-first incident diagnosis system. It models the shape of an enterprise agent platform without requiring production infrastructure. The current implementation uses FastAPI, LangGraph, deterministic fake tools, local JSON memory, and pure Python explainability structures.

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

The live mode is the only direct backend mode:

```env
USE_FAKE_LLM=false
USE_FAKE_TOOLS=false
OBSERVABILITY_BACKEND=prometheus_loki_tempo
```

Provider failures and empty responses are preserved as evidence metadata. The system does not silently fall back to fake data in file or live mode.

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
- Docker
- frontend
- vector database
- Neo4j
- LangSmith

This keeps the project easy to run, easy to test, and focused on agent engineering mechanics before infrastructure expansion.
