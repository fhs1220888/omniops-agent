"""Harness-level diagnosis result summary."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HarnessResult(BaseModel):
    root_cause: str | None = None
    confidence: float | None = None
    evidence_count: int
    executed_tools: list[str] = Field(default_factory=list)
    failed_tools: list[str] = Field(default_factory=list)
    tool_sources: list[str] = Field(default_factory=list)
    evidence_sufficient: bool
