# OmniOps Agent Benchmark Report

- Scenario count: 4
- RCA accuracy: 1.0
- Evidence precision: 1.0
- Average duration ms: 0.324
- Average agent count: 5.0
- Average tool count: 2.5

## redis_timeout

- Root cause: Redis connection pool exhaustion in order-service.
- Expected root cause: Redis connection pool exhaustion in order-service.
- Confidence: 0.87
- RCA correct: True
- Evidence precision: 1.0

### Evidence
- evidence-metric-latency-spike
- evidence-trace-redis-bottleneck

### Tool timeline
- query_metrics:completed:0.093ms
- query_traces:completed:0.141ms

### Agent timeline
- planner:success:0.068ms
- triage:success:0.01ms
- investigation:success:0.256ms
- reflection:success:0.005ms
- report:success:0.372ms

## mysql_slow_query

- Root cause: Missing database index caused slow payment_order queries in payment-service.
- Expected root cause: Missing database index caused slow payment_order queries in payment-service.
- Confidence: 0.84
- RCA correct: True
- Evidence precision: 1.0

### Evidence
- evidence-log-mysql-slow-query
- evidence-metric-mysql-db-latency
- evidence-trace-mysql-query-bottleneck
- memory-HIST-CONFIG-001
- memory-HIST-MYSQL-001
- memory-HIST-REDIS-001

### Tool timeline
- query_logs:completed:0.098ms
- query_metrics:completed:0.146ms
- query_traces:completed:0.187ms
- query_memory:completed:0.276ms

### Agent timeline
- planner:success:0.077ms
- triage:success:0.011ms
- investigation:success:0.447ms
- reflection:success:0.007ms
- report:success:0.452ms

## kafka_lag

- Root cause: Inventory consumer processing lag delayed stock updates.
- Expected root cause: Inventory consumer processing lag delayed stock updates.
- Confidence: 0.8
- RCA correct: True
- Evidence precision: 1.0

### Evidence
- evidence-log-kafka-consumer-lag
- memory-HIST-CONFIG-001
- memory-HIST-MYSQL-001
- memory-HIST-REDIS-001

### Tool timeline
- query_logs:completed:0.086ms
- query_memory:completed:0.174ms

### Agent timeline
- planner:success:0.074ms
- triage:success:0.011ms
- investigation:success:0.3ms
- reflection:success:0.007ms
- report:success:0.342ms

## bad_config_deploy

- Root cause: Bad configuration deploy reduced connection capacity for order-service.
- Expected root cause: Bad configuration deploy reduced connection capacity for order-service.
- Confidence: 0.82
- RCA correct: True
- Evidence precision: 1.0

### Evidence
- evidence-log-bad-config-deploy
- memory-HIST-CONFIG-001
- memory-HIST-MYSQL-001
- memory-HIST-REDIS-001

### Tool timeline
- query_logs:completed:0.096ms
- query_memory:completed:0.184ms

### Agent timeline
- planner:success:0.063ms
- triage:success:0.01ms
- investigation:success:0.31ms
- reflection:success:0.004ms
- report:success:0.305ms
