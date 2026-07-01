"""Knowledge base retriever."""

from __future__ import annotations

from app.core.config import Settings
from app.knowledge.embeddings import LocalHashEmbedding
from app.knowledge.schemas import RetrievedKnowledge
from app.knowledge.store import LocalJsonVectorStore


class KnowledgeRetriever:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.store = LocalJsonVectorStore(
            data_dir=self.settings.rag_data_dir,
            collection=self.settings.rag_collection,
            embedding=LocalHashEmbedding(self.settings.embedding_dim),
            backend=self.settings.rag_backend,
        )

    def search(self, query: str, top_k: int | None = None) -> list[RetrievedKnowledge]:
        if not self.settings.rag_enabled:
            return []
        limit = top_k if top_k is not None else self.settings.rag_top_k
        if limit <= 0:
            return []
        return self.store.search(query, limit)

    def status(self) -> dict:
        return {
            "rag_enabled": self.settings.rag_enabled,
            "backend": self.settings.rag_backend,
            "collection": self.settings.rag_collection,
            "data_dir": self.settings.rag_data_dir,
            "docs_dir": self.settings.rag_docs_dir,
            **self.store.status(),
        }
