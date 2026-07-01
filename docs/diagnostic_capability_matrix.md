# Diagnostic Capability Matrix

OmniOps currently focuses on microservice runtime diagnosis. It correlates logs, metrics, traces, policy metadata, and evidence sufficiency to produce RCA output for common service failure modes.

| Scenario | Metrics Evidence | Logs Evidence | Trace Evidence | Expected RCA | Status |
| --- | --- | --- | --- | --- | --- |
| Redis timeout | 504 / latency | `redis_timeout` | Redis span | Redis pool timeout | Supported |
| Downstream timeout | 504 / latency | `downstream_timeout` | `payment-service.call` span | Payment dependency timeout | Supported |
| DB slow query | p95 latency | `db_slow_query` | `mysql.checkout_order_lookup` span | Missing index / slow query | Supported |
| App exception | 500 rate | stack/error log | failed span | Application exception | Supported |
| Service unhealthy | 503 / up | `service_unhealthy` | optional | Unhealthy response | Supported |
| Latency spike | p95 latency | optional | slow checkout span | Slow path / latency bottleneck | Supported |
| Evidence insufficient | empty | empty | empty | Insufficient evidence | Supported |

## Live Evidence Path

All supported live scenarios are triggered by real `order-service` HTTP requests. The service emits:

- Prometheus metrics through `/metrics`
- structured logs pushed to Loki with `service=order-service`
- OpenTelemetry traces exported through the OTel Collector to Tempo

The Agent tools query Prometheus, Loki, and Tempo. In live mode they do not fall back to fake data.

## Knowledge Guidance Path

RAG retrieves matching runbooks and SOPs from `knowledge_base/`. This helps the Report Agent explain diagnosis steps and mitigation options, but it is not counted as real-time evidence. A runbook match cannot override empty logs, metrics, or traces.

## Skill Guidance Path

Skills under `skills/**/SKILL.md` guide reusable diagnosis behavior. They describe required evidence, reasoning steps, output contracts, and guardrails for each failure type. Skills do not execute tools and do not count as evidence.

## What This Covers

This is microservice runtime diagnosis, not a universal AIOps engine. The current coverage is strongest for request-path failures where logs, metrics, and traces expose the symptom:

- dependency timeout
- database slow query
- application exception
- service-level unhealthy response
- latency spike
- missing or empty evidence

## Current Non-Goals

- Kubernetes `OOMKilled` and `CrashLoopBackOff` require a future Kubernetes provider.
- Deployment/config change correlation requires a future `ChangeProvider`.
- Cloud provider incidents require Datadog, CloudWatch, or vendor-specific providers.
- The benchmark uses keyword matching for RCA validation; it is not a formal semantic evaluation system.
