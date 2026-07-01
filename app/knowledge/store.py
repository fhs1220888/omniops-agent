"""Local vector store for knowledge chunks.

The default backend is named local_chroma for configuration compatibility, but
the implementation is a lightweight JSON vector store to keep CI stable.
"""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Any

from app.knowledge.embeddings import LocalHashEmbedding
from app.knowledge.schemas import KnowledgeChunk, RetrievedKnowledge


class LocalJsonVectorStore:
    def __init__(
        self,
        *,
        data_dir: Path | str,
        collection: str,
        embedding: LocalHashEmbedding,
        backend: str = "local_chroma",
    ) -> None:
        self.data_dir = Path(data_dir)
        self.collection = collection
        self.embedding = embedding
        self.backend = backend
        self.index_path = self.data_dir / "index.json"

    def add_chunks(self, chunks: list[KnowledgeChunk]) -> dict:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        records = [
            {
                "chunk": chunk.model_dump(),
                "embedding": self.embedding.embed(chunk.content),
            }
            for chunk in chunks
        ]
        self.index_path.write_text(
            json.dumps(
                {
                    "backend": self.backend,
                    "collection": self.collection,
                    "records": records,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return self.status()

    def search(self, query: str, top_k: int) -> list[RetrievedKnowledge]:
        if not self.index_path.exists():
            return []
        payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        query_embedding = self.embedding.embed(query)
        scored = []
        for record in payload.get("records", []):
            score = _cosine(query_embedding, record.get("embedding", []))
            scored.append((score, record["chunk"]))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            RetrievedKnowledge(
                id=chunk["id"],
                title=chunk["title"],
                path=chunk["path"],
                content=chunk["content"],
                score=round(score, 4),
                metadata=chunk.get("metadata", {}),
            )
            for score, chunk in scored[:top_k]
        ]

    def reset(self) -> None:
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)

    def status(self) -> dict[str, Any]:
        payload = _read_payload(self.index_path)
        records = payload.get("records", [])
        document_ids = {
            record.get("chunk", {}).get("document_id")
            for record in records
            if record.get("chunk", {}).get("document_id")
        }
        return {
            "backend": self.backend,
            "collection": self.collection,
            "data_dir": str(self.data_dir),
            "index_exists": self.index_path.exists(),
            "document_count": len(document_ids),
            "chunk_count": len(records),
        }


def _read_payload(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    length = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(length))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
