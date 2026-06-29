"""Harness-level configuration derived from application settings."""

from __future__ import annotations

from pydantic import BaseModel

from app.core.config import Settings
from app.services.runtime_status import get_runtime_status


class HarnessConfig(BaseModel):
    llm_mode: str
    tools_mode: str
    observability_backend: str
    fake_llm_enabled: bool
    fake_tools_enabled: bool
    max_agent_steps: int | None = None
    require_evidence_for_report: bool = True

    @classmethod
    def from_settings(
        cls,
        settings: Settings | None = None,
        *,
        max_agent_steps: int | None = None,
        require_evidence_for_report: bool = True,
    ) -> "HarnessConfig":
        runtime_status = get_runtime_status(settings)
        return cls(
            llm_mode=runtime_status["llm_mode"],
            tools_mode=runtime_status["tools_mode"],
            observability_backend=runtime_status["observability_backend"],
            fake_llm_enabled=runtime_status["fake_llm_enabled"],
            fake_tools_enabled=runtime_status["fake_tools_enabled"],
            max_agent_steps=max_agent_steps,
            require_evidence_for_report=require_evidence_for_report,
        )

    @property
    def live_observability_enabled(self) -> bool:
        return (
            not self.fake_tools_enabled
            and self.observability_backend == "prometheus_loki_tempo"
        )
