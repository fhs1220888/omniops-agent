# Latency Spike Diagnosis Skill

## Purpose

Guide an agent through diagnosing latency spikes without an obvious error spike.

## When To Use

Use this skill when symptoms mention latency spike, p95/p99 increase, slow checkout, degraded performance, or requests completing slowly.

## Inputs

- Incident title, service, and symptom.
- Prometheus latency metrics.
- Loki slow request logs when present.
- Tempo trace spans.

## Required Evidence

- Prometheus: p95 or p99 latency increase.
- Loki: slow request signal if available.
- Tempo: slowest span identifying bottleneck path.

## Tools To Use

- `query_metrics`
- `query_traces`
- `query_logs` if slow logs exist

## Reasoning Steps

1. Confirm p95/p99 latency changed from baseline.
2. Inspect traces to identify the slowest span.
3. Use logs to check for slow path warnings or dependency hints.
4. Distinguish dependency latency from local service execution.
5. If traces and metrics are empty, mark evidence insufficient.

## Output Contract

Return a latency RCA with the suspected bottleneck span and supporting evidence IDs.

## Guardrails

- Do not overclaim root cause if only latency metric exists.
- Do not invent a dependency without trace or log evidence.
- Skills are methodology, not evidence.

## Example

When p95 latency rises and Tempo shows a slow MySQL or payment-service span, identify that span as the bottleneck and recommend targeted mitigation.
