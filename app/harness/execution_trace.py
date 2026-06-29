"""Harness execution trace contract."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class HarnessExecutionTrace(BaseModel):
    incident_id: str | None = None
    agent_steps: list[dict] = Field(default_factory=list)
    tool_calls: list[dict] = Field(default_factory=list)
    evidence_items: list[dict] = Field(default_factory=list)
    failed_tools: list[str] = Field(default_factory=list)
    started_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    finished_at: str | None = None
