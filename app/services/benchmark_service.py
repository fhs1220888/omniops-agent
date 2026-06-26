"""Deterministic demo benchmark runner."""

from __future__ import annotations

from pathlib import Path
from statistics import mean
from tempfile import TemporaryDirectory

from pydantic import BaseModel

from app.agents.graph import run_incident_diagnosis_with_store
from app.demo.faults import SCENARIOS
from app.demo.ground_truth import GROUND_TRUTH, ScenarioGroundTruth
from app.memory.incident_store import IncidentStore
from app.models.incident import Incident, IncidentDiagnosis


class BenchmarkScenarioResult(BaseModel):
    scenario_name: str
    root_cause: str
    expected_root_cause: str
    rca_correct: bool
    evidence_precision: float
    duration_ms: float
    agent_count: int
    tool_count: int
    confidence: float
    evidence: list[str]
    report_markdown: str
    evidence_graph: dict[str, list[dict]]
    reflection_decision: str | None
    replanning_requested: bool
    investigation_round: int
    denied_tools: list[dict]
    approval_required_tools: list[dict]
    tool_timeline: list[str]
    agent_timeline: list[str]


class BenchmarkSummary(BaseModel):
    scenario_count: int
    rca_accuracy: float
    evidence_precision: float
    average_duration_ms: float
    average_agent_count: float
    average_tool_count: float
    report_path: str
    results: list[BenchmarkScenarioResult]


def list_scenarios() -> list[dict]:
    return [factory() for factory in SCENARIOS.values()]


def run_scenario(scenario_name: str) -> BenchmarkScenarioResult:
    scenario = _get_scenario(scenario_name)
    ground_truth = GROUND_TRUTH[scenario_name]
    diagnosis = _diagnose_scenario(scenario)
    return _score_scenario(scenario_name, diagnosis, ground_truth)


def run_benchmark(report_path: Path | str = "benchmark_report.md") -> BenchmarkSummary:
    results = [run_scenario(name) for name in SCENARIOS]
    summary = BenchmarkSummary(
        scenario_count=len(results),
        rca_accuracy=round(mean(1.0 if item.rca_correct else 0.0 for item in results), 3),
        evidence_precision=round(mean(item.evidence_precision for item in results), 3),
        average_duration_ms=round(mean(item.duration_ms for item in results), 3),
        average_agent_count=round(mean(item.agent_count for item in results), 3),
        average_tool_count=round(mean(item.tool_count for item in results), 3),
        report_path=str(report_path),
        results=results,
    )
    Path(report_path).write_text(_render_markdown_report(summary), encoding="utf-8")
    return summary


def _get_scenario(scenario_name: str) -> dict:
    try:
        return SCENARIOS[scenario_name]()
    except KeyError as exc:
        raise ValueError(f"Unknown scenario: {scenario_name}") from exc


def _diagnose_scenario(scenario: dict) -> IncidentDiagnosis:
    incident = Incident(**scenario["incident"])
    with TemporaryDirectory() as tmpdir:
        store = IncidentStore(Path(tmpdir) / "incident_memory.json")
        return run_incident_diagnosis_with_store(incident, store)


def _score_scenario(
    scenario_name: str,
    diagnosis: IncidentDiagnosis,
    ground_truth: ScenarioGroundTruth,
) -> BenchmarkScenarioResult:
    actual_evidence = {
        item.id for item in diagnosis.evidence
    } | {
        item.evidence_id for item in diagnosis.evidence_items
    }
    expected_evidence = set(ground_truth.expected_evidence)
    matched_evidence = actual_evidence & expected_evidence
    precision = (
        len(matched_evidence) / len(expected_evidence)
        if expected_evidence
        else 1.0
    )
    return BenchmarkScenarioResult(
        scenario_name=scenario_name,
        root_cause=diagnosis.root_cause_analysis.root_cause,
        expected_root_cause=ground_truth.expected_root_cause,
        rca_correct=_root_cause_matches_scenario(
            scenario_name,
            diagnosis.root_cause_analysis.root_cause,
        ),
        evidence_precision=round(precision, 3),
        duration_ms=diagnosis.total_investigation_duration_ms,
        agent_count=len(diagnosis.agent_traces),
        tool_count=len(diagnosis.tool_traces),
        confidence=diagnosis.root_cause_analysis.confidence,
        evidence=sorted(actual_evidence),
        report_markdown=diagnosis.report_markdown,
        evidence_graph=diagnosis.evidence_graph,
        reflection_decision=diagnosis.reflection_decision,
        replanning_requested=diagnosis.replanning_requested,
        investigation_round=diagnosis.investigation_round,
        denied_tools=[item.model_dump() for item in diagnosis.denied_tools],
        approval_required_tools=[
            item.model_dump() for item in diagnosis.approval_required_tools
        ],
        tool_timeline=[
            f"{trace.tool_name}:{trace.status}:{trace.duration_ms}ms"
            for trace in diagnosis.tool_traces
        ],
        agent_timeline=[
            f"{trace.agent_name}:{trace.status}:{trace.duration_ms}ms"
            for trace in diagnosis.agent_traces
        ],
    )


def _root_cause_matches_scenario(scenario_name: str, root_cause: str) -> bool:
    text = root_cause.lower()
    positive_terms = {
        "redis_timeout": ["redis", "connection", "pool", "timeout"],
        "mysql_slow_query": ["mysql", "database", "index", "payment_order", "query"],
        "kafka_lag": ["consumer", "lag", "inventory", "stock"],
        "bad_config_deploy": ["config", "deploy", "connection", "capacity"],
    }[scenario_name]
    blocked_terms = {
        "redis_timeout": ["mysql", "kafka"],
        "mysql_slow_query": ["redis", "kafka"],
        "kafka_lag": ["redis", "mysql"],
        "bad_config_deploy": ["mysql", "kafka"],
    }[scenario_name]
    return (
        sum(1 for term in positive_terms if term in text) >= 2
        and not any(term in text for term in blocked_terms)
    )


def _render_markdown_report(summary: BenchmarkSummary) -> str:
    lines = [
        "# OmniOps Agent Benchmark Report",
        "",
        f"- Scenario count: {summary.scenario_count}",
        f"- RCA accuracy: {summary.rca_accuracy}",
        f"- Evidence precision: {summary.evidence_precision}",
        f"- Average duration ms: {summary.average_duration_ms}",
        f"- Average agent count: {summary.average_agent_count}",
        f"- Average tool count: {summary.average_tool_count}",
        "",
    ]
    for result in summary.results:
        lines.extend(
            [
                f"## {result.scenario_name}",
                "",
                f"- Root cause: {result.root_cause}",
                f"- Expected root cause: {result.expected_root_cause}",
                f"- Confidence: {result.confidence}",
                f"- RCA correct: {result.rca_correct}",
                f"- Evidence precision: {result.evidence_precision}",
                "",
                "### Evidence",
                *[f"- {item}" for item in result.evidence],
                "",
                "### Tool timeline",
                *[f"- {item}" for item in result.tool_timeline],
                "",
                "### Agent timeline",
                *[f"- {item}" for item in result.agent_timeline],
                "",
            ]
        )
    return "\n".join(lines)
