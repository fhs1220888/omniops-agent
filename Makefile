.PHONY: test live-up live-down live-traffic live-check live-demo

test:
	uv run pytest -q

live-up:
	docker compose -f deploy/docker-compose.observability.yml up -d

live-down:
	docker compose -f deploy/docker-compose.observability.yml down

live-traffic:
	uv run python scripts/generate_demo_traffic.py

live-check:
	uv run python scripts/run_live_demo_check.py
	uv run python scripts/check_runtime_status.py
	uv run python scripts/smoke_real_observability.py

live-demo:
	bash scripts/demo_live.sh
