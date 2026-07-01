from app.knowledge.embeddings import LocalHashEmbedding


def test_local_embedding_is_deterministic() -> None:
    embedding = LocalHashEmbedding(dim=32)

    first = embedding.embed("redis timeout checkout 504")
    second = embedding.embed("redis timeout checkout 504")

    assert first == second
    assert len(first) == 32
    assert any(value != 0 for value in first)


def test_local_embedding_normalizes_vectors() -> None:
    vector = LocalHashEmbedding(dim=32).embed("mysql slow query missing index")

    norm = sum(value * value for value in vector) ** 0.5

    assert round(norm, 6) == 1.0
