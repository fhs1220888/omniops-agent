# Downstream Timeout Runbook

## Symptoms

- Checkout requests fail with HTTP 504.
- The failing dependency is `payment-service`.
- User-facing payment authorization may time out.

## Signals in Metrics

- Request count increases for `/checkout/downstream-timeout`.
- 504 rate increases for `order-service`.
- P95 latency increases while requests wait for the dependency.

## Signals in Logs

- Structured logs include `event=downstream_timeout`.
- Logs include `dependency=payment-service`.
- Error type may be `DownstreamTimeout`.

## Signals in Traces

- Tempo includes a span named `payment-service.call`.
- The dependency span has error status or `error=true`.

## Diagnosis Steps

1. Confirm the failing endpoint and HTTP 504 rate.
2. Verify Loki logs identify `payment-service`.
3. Inspect Tempo for long `payment-service.call` spans.
4. Check whether payment-service has its own saturation or deploy event.

## Mitigation

- Fail over payment traffic if a healthy dependency instance exists.
- Increase timeout budget only if downstream latency is temporary and safe.
- Apply circuit breaking or graceful degradation for checkout.

## When to Escalate

- Escalate to payment-service on-call when dependency spans are the bottleneck.
- Escalate to platform on-call if network or service discovery is suspected.
