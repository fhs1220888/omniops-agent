from pathlib import Path

from app.knowledge.loader import chunk_documents, load_markdown_documents


def test_markdown_loader_loads_runbooks() -> None:
    documents = load_markdown_documents(Path("knowledge_base"))

    titles = {document.title for document in documents}

    assert "Redis Timeout Runbook" in titles
    assert "MySQL Slow Query Runbook" in titles
    assert len(documents) >= 8


def test_chunk_documents_returns_at_least_one_chunk_per_document() -> None:
    documents = load_markdown_documents(Path("knowledge_base"))
    chunks = chunk_documents(documents, chunk_size=500, overlap=80)

    assert len(chunks) >= len(documents)
    assert all(chunk.content for chunk in chunks)
    assert all(chunk.path.endswith(".md") for chunk in chunks)
