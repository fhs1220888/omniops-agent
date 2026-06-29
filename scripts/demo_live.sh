#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_FILE="deploy/docker-compose.observability.yml"
OMNIOPS_URL="${OMNIOPS_URL:-http://localhost:8001}"

wait_for_url() {
  local name="$1"
  local url="$2"
  local max_attempts="${3:-60}"
  local attempt=1

  printf 'Waiting for %s at %s' "$name" "$url"
  while [ "$attempt" -le "$max_attempts" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      printf '\n%s is ready.\n' "$name"
      return 0
    fi
    printf '.'
    sleep 2
    attempt=$((attempt + 1))
  done

  printf '\n%s did not become ready in time.\n' "$name" >&2
  return 1
}

require_omniops() {
  if ! curl -fsS "$OMNIOPS_URL/api/runtime/status" >/dev/null 2>&1; then
    cat >&2 <<MSG
OmniOps API is not reachable at $OMNIOPS_URL.

Please start OmniOps API first:
uv run uvicorn app.main:app --reload --port 8001

Also make sure .env is configured for live mode:
USE_FAKE_LLM=false
USE_FAKE_TOOLS=false
OBSERVABILITY_BACKEND=prometheus_loki_tempo
MSG
    return 1
  fi
}

echo "== OmniOps live observability demo =="
echo "Project: $ROOT_DIR"

echo
echo "== Starting observability stack =="
docker compose -f "$COMPOSE_FILE" up -d

echo
echo "== Waiting for services =="
wait_for_url "Prometheus" "http://localhost:9090/-/ready"
wait_for_url "Loki" "http://localhost:3100/ready"
wait_for_url "Tempo" "http://localhost:3200/ready"
wait_for_url "order-service" "http://localhost:8002/health"

echo
echo "== Generating real order-service traffic =="
uv run python scripts/generate_demo_traffic.py

echo
echo "== Checking OmniOps API =="
require_omniops

echo
echo "== Checking live backend data =="
uv run python scripts/run_live_demo_check.py

echo
echo "== Checking runtime mode =="
uv run python scripts/check_runtime_status.py

echo
echo "== Running live smoke diagnosis =="
uv run python scripts/smoke_real_observability.py

cat <<'MSG'

== Summary ==
Live demo completed.
- order-service generated real traffic.
- Prometheus, Loki, and Tempo were queried.
- OmniOps runtime status and smoke diagnosis were checked.

Expected live mode:
- fake_llm_enabled=false
- fake_tools_enabled=false
- tools_mode=real
- observability_backend=prometheus_loki_tempo
- tool_sources include loki, prometheus, tempo
MSG
