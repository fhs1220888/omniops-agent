"""Incident APIs backed by fake in-memory data for the Week 1.5 MVP."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.agents.graph import run_incident_diagnosis
from app.memory.incident_store import IncidentStore
from app.models.incident import (
    HistoricalIncident,
    Incident,
    IncidentCreate,
    IncidentDiagnosis,
    IncidentResponse,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


_INCIDENTS: dict[str, IncidentResponse] = {}
_INCIDENT_STORE = IncidentStore()


@router.post("", response_model=IncidentResponse, status_code=201)
def create_incident(payload: IncidentCreate) -> IncidentResponse:
    incident = IncidentResponse(
        id=f"INC-{uuid4().hex[:8].upper()}",
        title=payload.title,
        service=payload.service,
        severity=payload.severity,
        description=payload.description,
        status="created",
    )
    _INCIDENTS[incident.id] = incident
    return incident


@router.get("/history", response_model=list[HistoricalIncident])
def list_incident_history() -> list[HistoricalIncident]:
    return _INCIDENT_STORE.list_incidents()


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str) -> IncidentResponse:
    return _get_incident_or_404(incident_id)


@router.post("/{incident_id}/analyze", response_model=IncidentResponse)
def analyze_incident(incident_id: str) -> IncidentResponse:
    return _diagnose_and_update(incident_id, include_legacy_analysis=True)


@router.post("/{incident_id}/diagnose", response_model=IncidentDiagnosis)
def diagnose_incident(incident_id: str) -> IncidentDiagnosis:
    return _diagnose_and_update(incident_id).diagnosis


@router.post("/{incident_id}/resolve", response_model=HistoricalIncident)
def resolve_incident(incident_id: str) -> HistoricalIncident:
    incident = _get_incident_or_404(incident_id)
    if incident.diagnosis is None:
        incident = _diagnose_and_update(incident_id)

    diagnosis = incident.diagnosis
    resolved = HistoricalIncident(
        incident_id=incident.id,
        title=incident.title,
        service=incident.service,
        symptoms=[item.summary for item in diagnosis.evidence],
        root_cause=diagnosis.root_cause_analysis.root_cause,
        recommended_actions=[
            action.description for action in diagnosis.recommended_actions
        ],
        tags=_derive_tags(incident.service, diagnosis.root_cause_analysis.root_cause),
    )
    incident.status = "completed"
    _INCIDENTS[incident.id] = incident
    return _INCIDENT_STORE.store_resolved_incident(resolved)


def _diagnose_and_update(
    incident_id: str,
    include_legacy_analysis: bool = False,
) -> IncidentResponse:
    incident = _get_incident_or_404(incident_id)
    incident.status = "running"
    diagnosis = run_incident_diagnosis(
        Incident(
            id=incident.id,
            title=incident.title,
            service=incident.service,
            severity=incident.severity,
            description=incident.description,
            status="running",
            created_at=incident.created_at,
        )
    )
    incident.diagnosis = diagnosis
    if include_legacy_analysis:
        incident.analysis = diagnosis.model_dump()
    incident.status = "completed"
    _INCIDENTS[incident.id] = incident
    return incident


def _get_incident_or_404(incident_id: str) -> IncidentResponse:
    incident = _INCIDENTS.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


def _derive_tags(service: str, root_cause: str) -> list[str]:
    words = {service}
    lower_root_cause = root_cause.lower()
    for keyword in ["redis", "mysql", "latency", "timeout"]:
        if keyword in lower_root_cause:
            words.add(keyword)
    return sorted(words)
