"""Incident and diagnosis schemas for the local MVP."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.agent_trace import AgentTrace
from app.models.evidence import EvidenceItem as ExplainableEvidenceItem
from app.models.tool_trace import ToolCallTrace

IncidentSeverity = Literal["low", "medium", "high", "critical"]
IncidentStatus = Literal["created", "running", "completed", "failed"]
EvidenceType = Literal["log_pattern", "metric_anomaly", "trace_bottleneck"]
ActionType = Literal["investigate", "mitigate", "verify"]
SupportedTool = Literal["logs", "metrics", "traces", "memory"]


class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, examples=["OrderService P95 latency spike"])
    service: str = Field(default="order-service")
    severity: IncidentSeverity = "medium"
    description: str | None = None


class Incident(BaseModel):
    id: str
    title: str
    service: str
    severity: IncidentSeverity
    status: IncidentStatus = "created"
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EvidenceItem(BaseModel):
    id: str
    source: str
    type: EvidenceType
    summary: str
    metadata: dict[str, str | int | float]


class ToolObservation(BaseModel):
    tool_name: str
    source: str
    summary: str
    raw: dict[str, object]


class AgentFinding(BaseModel):
    agent_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str
    findings: list[str]
    evidence_ids: list[str] = Field(default_factory=list)
    next_suggestion: str | None = None
    risk_level: Literal["low", "medium", "high"] = "low"


class RecommendedAction(BaseModel):
    action_type: ActionType
    description: str
    owner: str
    priority: Literal["low", "medium", "high"]


class RootCauseAnalysis(BaseModel):
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    impact: str
    supporting_evidence_ids: list[str]


class HistoricalIncident(BaseModel):
    incident_id: str
    title: str
    service: str
    symptoms: list[str]
    root_cause: str
    recommended_actions: list[str]
    tags: list[str] = Field(default_factory=list)


class SimilarIncident(HistoricalIncident):
    similarity_score: int


class InvestigationPlan(BaseModel):
    objectives: list[str]
    required_tools: list[SupportedTool]
    reasoning: str


class ToolTiming(BaseModel):
    tool_name: SupportedTool
    started_at: datetime
    finished_at: datetime
    duration_ms: float


class FailedTool(BaseModel):
    tool_name: SupportedTool
    error_message: str
    timeout: bool = False


class ToolPolicyRecord(BaseModel):
    tool_name: str
    policy_decision: Literal["allow", "review", "deny"]
    risk_level: Literal["low", "medium", "high", "critical"]
    latency_ms: float
    status: Literal["allowed", "completed", "denied", "review_required", "failed", "timeout"]
    error: str | None = None


class ApprovalRequiredTool(BaseModel):
    tool_name: str
    reason: str
    approval_id: str | None = None


class DeniedTool(BaseModel):
    tool_name: str
    reason: str


class IncidentDiagnosis(BaseModel):
    incident_id: str
    status: Literal["completed"]
    affected_services: list[str]
    investigation_plan: InvestigationPlan
    investigation_steps: list[str]
    executed_tools: list[SupportedTool]
    skipped_tools: list[SupportedTool]
    reflection_decision: Literal["sufficient", "need_more_evidence"] | None = None
    reflection_reason: str | None = None
    replanning_requested: bool = False
    additional_tools: list[SupportedTool] = Field(default_factory=list)
    investigation_round: int = 0
    max_investigation_rounds: int = 2
    tool_timings: list[ToolTiming] = Field(default_factory=list)
    failed_tools: list[FailedTool] = Field(default_factory=list)
    policy_records: list[ToolPolicyRecord] = Field(default_factory=list)
    denied_tools: list[DeniedTool] = Field(default_factory=list)
    approval_required_tools: list[ApprovalRequiredTool] = Field(default_factory=list)
    total_investigation_duration_ms: float = 0
    evidence: list[EvidenceItem]
    evidence_items: list[ExplainableEvidenceItem] = Field(default_factory=list)
    evidence_graph: dict[str, list[dict]] = Field(default_factory=dict)
    agent_traces: list[AgentTrace] = Field(default_factory=list)
    tool_traces: list[ToolCallTrace] = Field(default_factory=list)
    findings: list[AgentFinding]
    similar_incidents: list[SimilarIncident] = Field(default_factory=list)
    root_cause_analysis: RootCauseAnalysis
    recommended_actions: list[RecommendedAction]
    report_markdown: str


class IncidentResponse(Incident):
    diagnosis: IncidentDiagnosis | None = None
    analysis: dict[str, object] | None = None
