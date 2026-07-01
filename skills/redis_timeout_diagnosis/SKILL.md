# Redis Timeout Diagnosis Skill

## Purpose

Guide an agent through diagnosing Redis timeout, Redis connection pool exhaustion, or checkout 504 incidents.

## When To Use

Use this skill when the incident mentions Redis, Redis timeout, connection pool exhaustion, checkout 504, or cart read/write latency.

## Inputs

- Incident title, service, severity, and symptom.
- Prometheus metrics for request count, status, latency, and endpoint impact.
- Loki logs for Redis timeout events.
- Tempo traces for Redis spans.

## Required Evidence

- Prometheus: 504 rate, p95 latency, endpoint metrics.
- Loki: `redis_timeout`, `RedisTimeoutException`, or pool exhaustion signal.
- Tempo: Redis span slow, failed, or dominant in request duration.

## Tools To Use

- `query_metrics`
- `query_logs`
- `query_traces`

## Reasoning Steps

1. Check whether Loki contains Redis timeout or pool exhaustion logs.
2. Check whether Prometheus shows 504 responses or latency spike for the same service.
3. Check whether Tempo shows Redis spans as slow or failed.
4. Increase confidence when logs, metrics, and traces agree on Redis.
5. If only this skill or a runbook matches but live evidence is empty, mark evidence insufficient.

## Output Contract

Return an RCA only when live evidence supports Redis timeout. Include confidence, supporting evidence IDs, impact, and mitigations.

## Guardrails

- Skills are reusable reasoning guidance, not real-time evidence.
- Do not infer Redis root cause from this skill alone.
- If logs, metrics, and traces are empty, report evidence insufficient.

## Example

When logs include `RedisTimeoutException`, metrics show 504 responses, and traces show a slow Redis span, diagnose Redis timeout or connection pool exhaustion and recommend checking pool size, timeout configuration, Redis latency, and recent config changes.
