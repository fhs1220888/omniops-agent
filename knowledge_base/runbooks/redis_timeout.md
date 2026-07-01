# Redis Timeout Runbook

## Symptoms

- Checkout requests return HTTP 504.
- Loki logs contain `RedisTimeoutException` or `redis_timeout`.
- Users report cart or checkout delays.

## Signals in Metrics

- `order_service_requests_total` shows 504 responses for `/checkout/redis-timeout`.
- P95 checkout latency rises above the normal budget.
- Redis connection pool usage may reach the configured limit.

## Signals in Logs

- Structured logs include `event=redis_timeout`.
- `error_type=RedisTimeoutException`.
- The affected service should be `order-service`.

## Signals in Traces

- Slow spans wait on Redis cart reads.
- Redis dependency spans dominate request duration.

## Diagnosis Steps

1. Confirm HTTP 504 rate and latency increase in Prometheus.
2. Confirm Redis timeout signatures in Loki.
3. Inspect Tempo spans for Redis wait time.
4. Compare the incident window with recent configuration changes.

## Mitigation

- Temporarily increase Redis connection pool capacity.
- Roll back recent pool or timeout configuration changes.
- Reduce checkout concurrency if Redis saturation is severe.

## When to Escalate

- Escalate to the platform on-call if Redis saturation affects multiple services.
- Escalate to the order-service owner if only checkout traffic is affected.
