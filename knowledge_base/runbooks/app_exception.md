# Application Exception Runbook

## Symptoms

- Checkout returns HTTP 500.
- Error rate spikes without a clear downstream timeout.
- Users see checkout failures immediately.

## Signals in Metrics

- `order_service_requests_total` shows 500 responses.
- Error rate percentage increases for `order-service`.

## Signals in Logs

- Structured logs include `event=application_exception`.
- Logs include `exception_type`.
- Logs include `error_message`.

## Signals in Traces

- The checkout span is marked error.
- The failing span may have `error=true`.

## Diagnosis Steps

1. Confirm HTTP 500 rate and affected endpoint.
2. Inspect exception type and error message in Loki.
3. Correlate trace ID from logs to the failed Tempo trace.
4. Check recent code paths and deployments touching checkout.

## Mitigation

- Roll back the faulty release if a recent deploy caused the spike.
- Patch the null or invalid state handling.
- Add regression tests for the failing code path.

## When to Escalate

- Escalate to order-service owner for code-level exceptions.
- Escalate to incident commander if user impact is broad.
