# Downstream Timeout Diagnosis Skill

## Purpose

Guide an agent through diagnosing downstream API timeout incidents, especially payment-service timeout during checkout.

## When To Use

Use this skill when symptoms mention downstream timeout, payment-service, dependency failure, 504 responses, or external API latency.

## Inputs

- Incident title, service, and symptom.
- Prometheus metrics for 504 rate and latency.
- Loki logs with dependency fields.
- Tempo spans for downstream calls.

## Required Evidence

- Prometheus: 504 rate and latency spike.
- Loki: `downstream_timeout` or `dependency=payment-service`.
- Tempo: `payment-service.call` span slow or error.

## Tools To Use

- `query_metrics`
- `query_logs`
- `query_traces`

## Reasoning Steps

1. Confirm the failing endpoint and 504 rate.
2. Verify logs identify a downstream dependency such as payment-service.
3. Inspect traces for slow or failed `payment-service.call` spans.
4. Consider retry storms, timeout budget, downstream saturation, or circuit breaker behavior.
5. If only this skill matches but live evidence is empty, mark evidence insufficient.

## Output Contract

Return a downstream timeout RCA only when live evidence links the error to a dependency. Include dependency name, evidence IDs, confidence, and mitigation.

## Guardrails

- Do not blame payment-service unless logs or traces identify it.
- Skills and runbooks are guidance only.
- Evidence gaps must be listed as limitations.

## Example

When metrics show 504s, logs show `dependency=payment-service`, and traces show `payment-service.call` slow/error, diagnose a downstream payment-service timeout.
