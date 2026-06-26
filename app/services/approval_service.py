"""In-memory approval request service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.approval import ApprovalRequest


class ApprovalService:
    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}

    def create_request(
        self,
        *,
        incident_id: str,
        tool_name: str,
        arguments: dict,
        risk_level: str,
        reason: str,
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            approval_id=f"APR-{uuid4().hex[:8].upper()}",
            incident_id=incident_id,
            tool_name=tool_name,
            arguments=_safe_arguments(arguments),
            risk_level=risk_level,
            reason=reason,
        )
        self._requests[request.approval_id] = request
        return request

    def approve(self, approval_id: str, reviewer: str, reason: str) -> ApprovalRequest:
        request = self._get_or_raise(approval_id)
        request.status = "approved"
        request.reviewed_at = datetime.now(UTC)
        request.reviewer = reviewer
        request.decision_reason = reason
        self._requests[approval_id] = request
        return request

    def reject(self, approval_id: str, reviewer: str, reason: str) -> ApprovalRequest:
        request = self._get_or_raise(approval_id)
        request.status = "rejected"
        request.reviewed_at = datetime.now(UTC)
        request.reviewer = reviewer
        request.decision_reason = reason
        self._requests[approval_id] = request
        return request

    def get(self, approval_id: str) -> ApprovalRequest | None:
        return self._requests.get(approval_id)

    def list_pending(self) -> list[ApprovalRequest]:
        return [
            request
            for request in self._requests.values()
            if request.status == "pending"
        ]

    def reset(self) -> None:
        self._requests.clear()

    def _get_or_raise(self, approval_id: str) -> ApprovalRequest:
        request = self.get(approval_id)
        if request is None:
            raise KeyError(f"Approval request not found: {approval_id}")
        return request


def _safe_arguments(arguments: dict) -> dict:
    safe: dict = {}
    for key, value in arguments.items():
        if key == "state" and isinstance(value, dict):
            safe[key] = {
                "incident_id": value.get("incident_id"),
                "service": value.get("service"),
                "severity": value.get("severity"),
            }
        elif isinstance(value, str | int | float | bool | type(None)):
            safe[key] = value
        elif isinstance(value, dict):
            safe[key] = _safe_arguments(value)
        else:
            safe[key] = str(value)
    return safe


approval_service = ApprovalService()
