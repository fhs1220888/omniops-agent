from app.harness.config import HarnessConfig
from app.harness.policy import HarnessPolicy


def _config(require_evidence_for_report: bool = True) -> HarnessConfig:
    return HarnessConfig(
        llm_mode="real",
        tools_mode="real",
        observability_backend="prometheus_loki_tempo",
        fake_llm_enabled=False,
        fake_tools_enabled=False,
        max_agent_steps=None,
        require_evidence_for_report=require_evidence_for_report,
    )


def test_low_risk_tool_is_allowed() -> None:
    policy = HarnessPolicy(_config())

    assert policy.allow_tool("query_logs", {}) is True


def test_high_risk_tool_requires_human_approval() -> None:
    policy = HarnessPolicy(_config())

    assert policy.allow_tool("restart_service", {}) is False
    assert policy.require_human_approval("restart_service", {}) is True


def test_critical_or_unknown_tool_is_not_allowed() -> None:
    policy = HarnessPolicy(_config())

    assert policy.allow_tool("delete_database", {}) is False
    assert policy.allow_tool("unknown_tool", {}) is False
    assert policy.require_human_approval("delete_database", {}) is False


def test_zero_evidence_report_is_not_allowed_when_evidence_required() -> None:
    policy = HarnessPolicy(_config(require_evidence_for_report=True))

    assert policy.allow_report(evidence_count=0, failed_tools=[]) is False
    assert policy.allow_report(evidence_count=1, failed_tools=[]) is True


def test_failed_tools_are_reflected_in_policy_summary() -> None:
    policy = HarnessPolicy(_config())

    summary = policy.summary()

    assert summary["failed_tools_included_in_result"] is True
    assert summary["zero_evidence_behavior"] == "mark_evidence_insufficient"
    assert summary["real_mode_fake_tool_fallback_allowed"] is False
