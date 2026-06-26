"""Evidence models for explainability and local graph construction."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

EvidenceSource = Literal["log", "metric", "trace", "memory"]


class EvidenceItem(BaseModel):
    evidence_id: str
    source: EvidenceSource
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
