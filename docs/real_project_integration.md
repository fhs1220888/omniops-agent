# Real Project Integration

OmniOps can be connected to real Prometheus, Loki, and Tempo backends as a read-only RCA copilot.

## Recommended Mode

```env
USE_FAKE_TOOLS=false
OBSERVABILITY_BACKEND=prometheus_loki_tempo
OBSERVABILITY_PROFILE=spring_boot_micrometer
PROMETHEUS_URL=http://your-prometheus:9090
LOKI_URL=http://your-loki:3100
TEMPO_URL=http://your-tempo:3200
```

Use `USE_FAKE_LLM=false` when you want real LLM RCA generation. Keep destructive tools disabled or approval-gated.

## Observability Profiles

Profiles live in:

```text
config/observability_profiles/
```

Current profiles:

- `demo_order_service`
- `generic`
- `spring_boot_micrometer`
- `fastapi_prometheus`

A profile configures:

- Prometheus metric names
- Prometheus service, endpoint, and status labels
- Loki service label
- Loki trace ID fields
- Tempo trace ID source

## How To Choose A Profile

Use `demo_order_service` for the local demo stack.

Use `spring_boot_micrometer` if your service emits common Micrometer metrics:

```text
http_server_requests_seconds_count
http_server_requests_seconds_bucket
```

Use `fastapi_prometheus` if your FastAPI service uses common HTTP metrics:

```text
http_requests_total
http_request_duration_seconds_bucket
```

Use `generic` as a template when labels and metric names are close to conventional names.

## How To Add A Profile

1. Copy `config/observability_profiles/generic.yaml`.
2. Rename it, for example `my_company.yaml`.
3. Update metric names and labels:
   - `request_count_metric`
   - `latency_bucket_metric`
   - `service_label`
   - `endpoint_label`
   - `status_label`
4. Update Loki label and trace ID fields.
5. Set:
   `OBSERVABILITY_PROFILE=my_company`
6. Run tests and smoke checks.

## Check Service Labels

Prometheus:

```promql
up
```

Look for the label that identifies your service, such as `service`, `application`, `app`, or `job`.

Loki:

```logql
{service="your-service"}
```

If this returns no logs, check whether the label is named `app`, `job`, `container`, or `namespace`.

## Check Metric Names

Common Prometheus metric names:

- `http_requests_total`
- `http_request_duration_seconds_bucket`
- `http_server_requests_seconds_count`
- `http_server_requests_seconds_bucket`

The profile should match the metrics actually scraped in your Prometheus.

## Check Trace IDs

OmniOps retrieves trace IDs from Loki logs and then queries Tempo.

Logs should include one of:

- `trace_id`
- `traceId`
- `traceID`
- `traceid`

If trace IDs are missing, Tempo evidence may be empty even when logs and metrics exist.

## Runtime Verification

```bash
uv run python scripts/check_runtime_status.py
```

Expected live mode:

```json
{
  "tools_mode": "real",
  "observability_backend": "prometheus_loki_tempo",
  "observability_profile": "spring_boot_micrometer",
  "fake_tools_enabled": false
}
```

## API

```text
GET /api/observability/profile
GET /api/observability/profiles
```

## Safety Boundary

Use OmniOps first as a read-only RCA copilot:

- query observability backends
- retrieve runbooks
- select markdown skills
- generate RCA and actions

Do not directly auto-remediate production services until authentication, audit logging, approval workflows, and rollback controls are production-ready.
