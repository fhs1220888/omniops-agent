"""Knowledge base APIs for RAG runbook retrieval."""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

from app.core.config import Settings
from app.knowledge.ingestion import ingest_knowledge_base
from app.knowledge.retriever import KnowledgeRetriever

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class KnowledgeIngestRequest(BaseModel):
    reset: bool = False


@router.get("/status")
def knowledge_status() -> dict:
    settings = Settings.from_env()
    retriever = KnowledgeRetriever(settings)
    return retriever.status()


@router.post("/search")
def search_knowledge(payload: KnowledgeSearchRequest) -> dict:
    settings = Settings.from_env()
    results = KnowledgeRetriever(settings).search(payload.query, payload.top_k)
    return {
        "query": payload.query,
        "rag_enabled": settings.rag_enabled,
        "results": [item.model_dump() for item in results],
    }


@router.post("/ingest")
def ingest_knowledge(payload: KnowledgeIngestRequest) -> dict:
    settings = Settings.from_env()
    stats = ingest_knowledge_base(reset=payload.reset, settings=settings)
    return {"rag_enabled": settings.rag_enabled, **stats}
