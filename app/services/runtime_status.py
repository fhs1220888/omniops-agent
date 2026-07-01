"""Runtime mode and backend reachability checks."""

from __future__ import annotations

import httpx

from app.core.config import Settings


def get_runtime_status(settings: Settings | None = None) -> dict:
    config = settings or Settings.from_env()
    live_backend = (
        not config.use_fake_tools
        and config.observability_backend == "prometheus_loki_tempo"
    )
    return {
        "llm_mode": "fake" if config.use_fake_llm else "real",
        "tools_mode": _tools_mode(config),
        "observability_backend": config.observability_backend,
        "observability_profile": config.observability_profile,
        "prometheus_reachable": _reachable(config.prometheus_url, "/-/ready")
        if live_backend
        else False,
        "loki_reachable": _reachable(config.loki_url, "/ready")
        if live_backend
        else False,
        "tempo_reachable": _reachable(config.tempo_url, "/ready")
        if live_backend
        else False,
        "fake_tools_enabled": config.use_fake_tools,
        "fake_llm_enabled": config.use_fake_llm,
    }


def _tools_mode(config: Settings) -> str:
    if config.use_fake_tools:
        return "fake"
    if config.observability_backend == "file":
        return "file"
    return "real"


def _reachable(base_url: str, path: str) -> bool:
    if not base_url:
        return False
    try:
        response = httpx.get(f"{base_url.rstrip('/')}{path}", timeout=1.5)
        return 200 <= response.status_code < 500
    except Exception:
        return False
