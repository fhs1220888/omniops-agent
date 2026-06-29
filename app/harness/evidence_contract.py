"""Evidence contract for tool outputs entering the harness."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvidenceContract(BaseModel):
    source: str
    tool: str
    service: str | None = None
    empty: bool
    error: str | None = None
    items: list[dict] = Field(default_factory=list)
