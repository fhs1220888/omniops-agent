from app.knowledge.embeddings import LocalHashEmbedding
from app.knowledge.loader import chunk_documents, load_markdown_documents
from app.knowledge.store import LocalJsonVectorStore


def test_vector_store_search_finds_redis_runbook(tmp_path) -> None:
    documents = load_markdown_documents("knowledge_base")
    chunks = chunk_documents(documents)
    store = LocalJsonVectorStore(
        data_dir=tmp_path / "index",
        collection="test",
        embedding=LocalHashEmbedding(dim=64),
    )

    store.add_chunks(chunks)
    results = store.search("redis timeout checkout 504", top_k=3)

    assert results
    assert any("Redis Timeout" in item.title for item in results)
    assert store.status()["chunk_count"] == len(chunks)
