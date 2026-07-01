# Service Unhealthy Diagnosis Skill

## Purpose

Guide an agent through diagnosing application-level unhealthy or HTTP 503 responses.

## When To Use

Use this skill when symptoms mention service unhealthy, health check failure, readiness issue, HTTP 503, or degraded service health.

## Inputs

- Incident title, service, and symptom.
- Prometheus 503 rate and health signals.
- Loki service unhealthy logs.
- Tempo traces when available.

## Required Evidence

- Prometheus: 503 rate or health failure signal.
- Loki: `service_unhealthy` event and reason.
- Tempo: optional failed request span.

## Tools To Use

- `query_metrics`
- `query_logs`
- `query_traces` when trace evidence exists

## Reasoning Steps

1. Confirm the service is returning 503 while the process may still be up.
2. Inspect logs for unhealthy reason.
3. Check dependency health, readiness/liveness, and resource pressure.
4. Use traces only if they clarify request path impact.
5. If only generic symptom exists, mark evidence insufficient.

## Output Contract

Return a service unhealthy RCA only when metrics or logs support the 503/unhealthy diagnosis.

## Guardrails

- Do not confuse application-level unhealthy with container crash unless Kubernetes evidence exists.
- Do not recommend restart without policy approval.
- Live evidence must ground the RCA.

## Example

When metrics show 503s and logs contain `service_unhealthy`, diagnose application-level unhealthy response and recommend checking dependencies and readiness conditions.
