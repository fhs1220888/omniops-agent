"""Knowledge base retrieval for long-term diagnostic guidance."""

from app.knowledge.ingestion import ingest_knowledge_base
from app.knowledge.retriever import KnowledgeRetriever
from app.knowledge.schemas import KnowledgeChunk, KnowledgeDocument, RetrievedKnowledge

__all__ = [
    "KnowledgeChunk",
    "KnowledgeDocument",
    "KnowledgeRetriever",
    "RetrievedKnowledge",
    "ingest_knowledge_base",
]
