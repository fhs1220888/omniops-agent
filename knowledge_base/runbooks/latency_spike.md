# Checkout Latency Spike Runbook

## Symptoms

- Checkout P95 latency increases.
- Requests may still succeed.
- Users experience slow checkout instead of immediate errors.

## Signals in Metrics

- Prometheus p95 latency increases for checkout endpoints.
- Error rate may remain low.

## Signals in Logs

- Logs may show slow path warnings.
- Logs may not include a direct exception.

## Signals in Traces

- Tempo shows one or more slow spans dominating request duration.
- Slow spans identify whether latency is from Redis, MySQL, payment-service, or local execution.

## Diagnosis Steps

1. Confirm P95 latency increase in Prometheus.
2. Inspect traces to identify the slowest span.
3. Use logs to confirm whether slow path warnings align with trace IDs.
4. Avoid guessing dependency root cause if traces are empty.

## Mitigation

- Mitigate the slowest confirmed dependency or code path.
- Add caching, reduce blocking work, or tune timeout budgets.
- Verify latency returns to baseline.

## When to Escalate

- Escalate to service owner if local code path is slow.
- Escalate to dependency owner if traces identify a downstream bottleneck.
