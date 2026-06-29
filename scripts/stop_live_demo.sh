#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_FILE="deploy/docker-compose.observability.yml"

if [ "${1:-}" = "--volumes" ]; then
  docker compose -f "$COMPOSE_FILE" down -v
else
  docker compose -f "$COMPOSE_FILE" down
fi
