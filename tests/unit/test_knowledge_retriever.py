from app.core.config import Settings
from app.knowledge.embeddings import LocalHashEmbedding
from app.knowledge.ingestion import ingest_knowledge_base
from app.knowledge.retriever import KnowledgeRetriever


def test_retriever_returns_empty_when_disabled(tmp_path) -> None:
    settings = Settings(
        rag_enabled=False,
        rag_data_dir=str(tmp_path / "missing"),
        embedding_dim=64,
    )

    assert KnowledgeRetriever(settings).search("redis timeout") == []


def test_retriever_returns_empty_when_index_missing(tmp_path) -> None:
    settings = Settings(
        rag_enabled=True,
        rag_data_dir=str(tmp_path / "missing"),
        embedding_dim=64,
    )

    assert KnowledgeRetriever(settings).search("redis timeout") == []


def test_retriever_searches_ingested_index(tmp_path) -> None:
    settings = Settings(
        rag_enabled=True,
        rag_data_dir=str(tmp_path / "index"),
        rag_docs_dir="knowledge_base",
        embedding_dim=64,
    )

    stats = ingest_knowledge_base(reset=True, settings=settings)
    results = KnowledgeRetriever(settings).search("redis timeout checkout 504", top_k=3)

    assert stats["chunk_count"] >= stats["document_count"]
    assert results
    assert any("Redis Timeout" in item.title for item in results)
