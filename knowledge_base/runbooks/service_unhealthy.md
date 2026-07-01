# Service Unhealthy Runbook

## Symptoms

- Order service returns HTTP 503.
- Health or readiness behavior is degraded at the application level.
- The container may remain running even though application health is poor.

## Signals in Metrics

- 503 rate increases for `/checkout/unhealthy`.
- Service `up` may still be true because the container is alive.

## Signals in Logs

- Structured logs include `event=service_unhealthy`.
- Logs include a `reason` field.
- Error type may be `ServiceUnhealthy`.

## Signals in Traces

- Trace evidence may be optional for application-level health failures.
- Failed spans can confirm request path impact.

## Diagnosis Steps

1. Confirm the service is still running but returning 503.
2. Inspect Loki logs for the unhealthy reason.
3. Check dependency health budgets and readiness conditions.
4. Confirm this is not a container crash or Kubernetes restart loop.

## Mitigation

- Remove unhealthy instances from traffic.
- Restore dependency health or relax readiness only if safe.
- Restart service only after approval if policy requires it.

## When to Escalate

- Escalate to platform on-call for readiness or routing issues.
- Escalate to service owner for application-level health state.
