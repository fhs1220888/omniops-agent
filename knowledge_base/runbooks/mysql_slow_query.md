# MySQL Slow Query Runbook

## Symptoms

- Checkout latency increases while requests may still return HTTP 200.
- Slow order lookup queries dominate checkout latency.
- The suspected issue is a missing composite index.

## Signals in Metrics

- P95 latency increases for checkout endpoints.
- Error rate may remain low if the service degrades but still succeeds.

## Signals in Logs

- Structured logs include `event=db_slow_query`.
- Logs include `db=mysql`.
- Logs include `query_name=checkout_order_lookup`.
- Logs may include `suspected_issue=missing_composite_index`.

## Signals in Traces

- Tempo includes `mysql.checkout_order_lookup`.
- Trace attributes include `db.system=mysql`.
- Trace attributes include query name or SQL statement metadata.

## Diagnosis Steps

1. Confirm latency increase in Prometheus.
2. Confirm MySQL slow query signatures in Loki.
3. Inspect Tempo for `mysql.checkout_order_lookup`.
4. Check query plan and index coverage for checkout order lookup.

## Mitigation

- Add or restore the missing composite index.
- Reduce query cardinality or add pagination if needed.
- Cache read-heavy lookup data when safe.

## When to Escalate

- Escalate to database owner if query plans changed unexpectedly.
- Escalate to service owner if application query shape changed.
