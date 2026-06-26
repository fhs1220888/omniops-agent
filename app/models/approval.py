"""Human approval models for high-risk tool calls."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ApprovalStatus = Literal["pending", "approved", "rejected"]


class ApprovalRequest(BaseModel):
    approval_id: str
    incident_id: str
    tool_name: str
    arguments: dict[str, Any]
    risk_level: Literal["low", "medium", "high", "critical"]
    reason: str
    status: ApprovalStatus = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reviewed_at: datetime | None = None
    reviewer: str | None = None
    decision_reason: str | None = None
