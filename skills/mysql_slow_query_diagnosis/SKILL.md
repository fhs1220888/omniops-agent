# MySQL Slow Query Diagnosis Skill

## Purpose

Guide an agent through diagnosing database slow query or missing index incidents.

## When To Use

Use this skill when symptoms mention MySQL, database latency, slow query, missing index, checkout order lookup, or degraded latency without immediate errors.

## Inputs

- Incident title, service, and symptom.
- Prometheus latency and endpoint metrics.
- Loki database slow query logs.
- Tempo MySQL query spans.

## Required Evidence

- Prometheus: p95 latency increase.
- Loki: `db_slow_query`, `query_name`, or `missing_composite_index`.
- Tempo: `mysql.checkout_order_lookup` span slow.

## Tools To Use

- `query_metrics`
- `query_logs`
- `query_traces`

## Reasoning Steps

1. Confirm p95 or p99 latency increase.
2. Check logs for slow query event, query name, and suspected index issue.
3. Inspect traces for MySQL span duration.
4. Recommend EXPLAIN plan, index validation, query optimization, and connection pool checks.
5. If live database evidence is missing, mark evidence insufficient.

## Output Contract

Return a DB slow query RCA only when logs, metrics, or traces support it. Include query name when available.

## Guardrails

- Do not infer a missing index solely from this skill.
- Do not treat runbook guidance as live database evidence.
- State missing logs, metrics, or traces explicitly.

## Example

When logs show `db_slow_query`, metrics show p95 latency, and traces show `mysql.checkout_order_lookup`, diagnose slow query or missing index signal.
