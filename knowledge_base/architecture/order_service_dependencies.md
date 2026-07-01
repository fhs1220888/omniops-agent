# Order Service Dependencies

## Symptoms

- Checkout failures can originate inside order-service or one of its dependencies.

## Signals in Metrics

- `order-service` exposes request count, status, and duration metrics.
- Endpoint labels identify checkout paths.

## Signals in Logs

- Structured logs include service, endpoint, event, level, and trace ID.
- Dependency fields identify services such as `payment-service`.

## Signals in Traces

- OpenTelemetry traces show checkout spans and dependency spans.
- Important spans include Redis cart reads, MySQL order lookup, and payment-service calls.

## Diagnosis Steps

1. Use Prometheus to confirm endpoint impact.
2. Use Loki to identify event names and dependency fields.
3. Use Tempo to find the slowest or failed span.
4. Map the failing span to the owning service.

## Mitigation

- Mitigate the confirmed dependency or code path.
- Do not infer root cause from architecture alone.

## When to Escalate

- Escalate to the dependency owner when trace evidence points outside order-service.
