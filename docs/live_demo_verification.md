# Live Demo Verification

This document records the latest successful live observability verification for OmniOps Agent.

## Docker Services

The live stack was started with:

```bash
docker compose -f deploy/docker-compose.observability.yml up -d
```

Verified running services:

- `prometheus` on `9090`
- `loki` on `3100`
- `tempo` on `3200`
- `grafana` on `3000`
- `otel-collector` on `4317/4318`
- `order-service` on `8002`

## Generated Traffic

Traffic was generated with:

```bash
uv run python scripts/generate_demo_traffic.py
```

Observed output:

```json
{
  "request_count": 33,
  "status_counts": {
    "/checkout:200": 20,
    "/checkout/slow:200": 5,
    "/checkout/error:503": 4,
    "/checkout/redis-timeout:504": 4
  }
}
```

## Live Backend Check

The live backend check was run with:

```bash
uv run python scripts/run_live_demo_check.py
```

Observed result:

```json
{
  "live_real_mode": true,
  "prometheus": {
    "reachable": true,
    "up": true,
    "result_count": 1
  },
  "loki": {
    "reachable": true,
    "log_count": 34
  },
  "tempo": {
    "reachable": true,
    "found": true
  }
}
```

## Runtime Status

Runtime status was checked with:

```bash
uv run python scripts/check_runtime_status.py
```

Observed result:

```json
{
  "fake_llm_enabled": false,
  "fake_tools_enabled": false,
  "llm_mode": "real",
  "tools_mode": "real",
  "observability_backend": "prometheus_loki_tempo",
  "prometheus_reachable": true,
  "loki_reachable": true,
  "tempo_reachable": true
}
```

## Smoke Diagnosis

The live diagnosis smoke test was run with:

```bash
uv run python scripts/smoke_real_observability.py
```

Observed result:

```json
{
  "executed_tools": ["logs", "metrics", "traces"],
  "tool_sources": ["loki", "prometheus", "tempo"],
  "evidence_count": 3,
  "failed_tools": [],
  "root_cause": "Redis connection pool exhaustion in order-service.",
  "confidence": 0.87
}
```

## Pytest

Latest test result:

```text
63 passed, 3 skipped, 1 warning
```

The skipped tests are live integration tests that only run when `RUN_REAL_OBSERVABILITY_TESTS=true`.

## Current Limitations

- The live demo depends on Docker and local ports `3000`, `3100`, `3200`, `4317`, `4318`, `8002`, and `9090`.
- Tempo lookup depends on `trace_id` being present in Loki logs.
- Production environments may use different Prometheus metric names, Loki labels, Tempo trace formats, and service naming conventions.
- `.env` must be configured manually with a real `LLM_API_KEY`; `.env.live.example` intentionally does not contain secrets.
