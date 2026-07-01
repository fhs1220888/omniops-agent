# Incident Response Process

## Symptoms

- A service has customer-visible errors, latency, or degraded health.
- Alerts or user reports indicate production impact.

## Signals in Metrics

- Error rate, latency, traffic, and saturation should be checked first.

## Signals in Logs

- Logs should be filtered by service, endpoint, error type, and trace ID.

## Signals in Traces

- Traces should identify slow or failing dependency spans.

## Diagnosis Steps

1. Confirm impact and affected service.
2. Gather metrics, logs, and traces for the same time window.
3. Identify whether evidence is sufficient.
4. Use runbooks as guidance, not as live facts.
5. Record root cause, confidence, and recommended actions.

## Mitigation

- Prefer reversible mitigations.
- Require human approval for high-risk operational actions.
- Verify the customer-facing symptom improves.

## When to Escalate

- Escalate when evidence is insufficient, impact is broad, or mitigation requires risky changes.
