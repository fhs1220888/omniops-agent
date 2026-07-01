"""OmniOps Agent Harness status API."""

from __future__ import annotations

from fastapi import APIRouter

from app.harness.config import HarnessConfig
from app.harness.policy import HarnessPolicy
from app.harness.runtime import OmniOpsHarnessRuntime
from app.services.runtime_status import get_runtime_status

router = APIRouter(prefix="/harness", tags=["harness"])


@router.get("/status")
def harness_status() -> dict:
    config = HarnessConfig.from_settings()
    policy = HarnessPolicy(config)
    runtime = OmniOpsHarnessRuntime(config, policy)
    runtime_status = get_runtime_status()
    return {
        **runtime.describe(),
        "llm_mode": config.llm_mode,
        "tools_mode": config.tools_mode,
        "observability_backend": config.observability_backend,
        "observability_profile": runtime_status["observability_profile"],
        "live_backend_reachability": {
            "prometheus": runtime_status["prometheus_reachable"],
            "loki": runtime_status["loki_reachable"],
            "tempo": runtime_status["tempo_reachable"],
        },
        "fake_llm_enabled": config.fake_llm_enabled,
        "fake_tools_enabled": config.fake_tools_enabled,
        "evidence_policy": policy.summary(),
    }
