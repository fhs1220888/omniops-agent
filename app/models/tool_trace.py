"""Tool call trace models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ToolCallTrace(BaseModel):
    tool_name: str
    policy_decision: Literal["allow", "review", "deny"]
    risk_level: Literal["low", "medium", "high", "critical"]
    duration_ms: float
    status: Literal["completed", "denied", "review_required", "failed", "timeout"]
    error: str | None = None
