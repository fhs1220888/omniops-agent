"""Knowledge base ingestion."""

from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from app.knowledge.embeddings import LocalHashEmbedding
from app.knowledge.loader import chunk_documents, load_markdown_documents
from app.knowledge.store import LocalJsonVectorStore


def ingest_knowledge_base(
    docs_dir: Path | str | None = None,
    data_dir: Path | str | None = None,
    *,
    reset: bool = False,
    settings: Settings | None = None,
) -> dict:
    config = settings or Settings.from_env()
    docs_path = Path(docs_dir or config.rag_docs_dir)
    data_path = Path(data_dir or config.rag_data_dir)
    embedding = LocalHashEmbedding(config.embedding_dim)
    store = LocalJsonVectorStore(
        data_dir=data_path,
        collection=config.rag_collection,
        embedding=embedding,
        backend=config.rag_backend,
    )
    if reset:
        store.reset()
    documents = load_markdown_documents(docs_path)
    chunks = chunk_documents(documents)
    status = store.add_chunks(chunks)
    return {
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "backend": status["backend"],
        "collection": status["collection"],
        "data_dir": status["data_dir"],
    }
