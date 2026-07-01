"""Knowledge base schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    id: str
    path: str
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeChunk(BaseModel):
    id: str
    document_id: str
    path: str
    title: str
    content: str
    chunk_index: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedKnowledge(BaseModel):
    id: str
    title: str
    path: str
    content: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)
