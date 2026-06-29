"""Runtime facade for the OmniOps Agent Harness."""

from __future__ import annotations

from app.harness.config import HarnessConfig
from app.harness.policy import HarnessPolicy
from app.harness.result import HarnessResult
from app.services.runtime_status import get_runtime_status


HARNESS_CAPABILITIES = [
    "multi_agent_orchestration",
    "tool_governance",
    "observability_connectors",
    "evidence_tracking",
    "reflection",
    "runtime_status",
    "live_demo_verification",
]


class OmniOpsHarnessRuntime:
    def __init__(self, config: HarnessConfig, policy: HarnessPolicy) -> None:
        self.config = config
        self.policy = policy

    def describe(self) -> dict:
        return {
            "name": "OmniOps Agent Harness",
            "capabilities": HARNESS_CAPABILITIES,
        }

    def validate_runtime(self) -> dict:
        status = get_runtime_status()
        real_mode_fake_fallback_allowed = False
        return {
            **self.describe(),
            **status,
            "real_mode_fake_fallback_allowed": real_mode_fake_fallback_allowed,
            "evidence_policy": self.policy.summary(),
        }

    def summarize_result(self, diagnosis_result: dict) -> HarnessResult:
        root_cause_analysis = _as_dict(diagnosis_result.get("root_cause_analysis"))
        evidence = diagnosis_result.get("evidence_items") or diagnosis_result.get("evidence") or []
        failed_tools = _failed_tool_names(diagnosis_result.get("failed_tools", []))
        evidence_count = len(evidence)
        return HarnessResult(
            root_cause=root_cause_analysis.get("root_cause"),
            confidence=root_cause_analysis.get("confidence"),
            evidence_count=evidence_count,
            executed_tools=list(diagnosis_result.get("executed_tools", [])),
            failed_tools=failed_tools,
            tool_sources=_tool_sources(diagnosis_result),
            evidence_sufficient=self.policy.allow_report(evidence_count, failed_tools),
        )


def _as_dict(value: object) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {}


def _failed_tool_names(items: list) -> list[str]:
    names: list[str] = []
    for item in items:
        data = _as_dict(item)
        name = data.get("tool_name")
        if name:
            names.append(str(name))
    return names


def _tool_sources(diagnosis_result: dict) -> list[str]:
    sources: list[str] = []
    for item in diagnosis_result.get("evidence", []):
        data = _as_dict(item)
        source = data.get("source")
        if source and source not in sources:
            sources.append(str(source))
    for item in diagnosis_result.get("evidence_items", []):
        data = _as_dict(item)
        source = data.get("source")
        if source and source not in sources:
            sources.append(str(source))
    return sources
