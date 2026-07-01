"""Markdown loader and chunker for diagnostic knowledge documents."""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.knowledge.schemas import KnowledgeChunk, KnowledgeDocument


def load_markdown_documents(docs_dir: Path | str) -> list[KnowledgeDocument]:
    root = Path(docs_dir)
    if not root.exists():
        return []
    documents = []
    for path in sorted(root.rglob("*.md")):
        content = path.read_text(encoding="utf-8")
        relative = path.relative_to(root.parent).as_posix()
        documents.append(
            KnowledgeDocument(
                id=_stable_id(relative),
                path=relative,
                title=_title_from_markdown(content, path),
                content=content,
                metadata={
                    "path": relative,
                    "category": path.parent.name,
                    "filename": path.name,
                },
            )
        )
    return documents


def chunk_documents(
    documents: list[KnowledgeDocument],
    *,
    chunk_size: int = 1000,
    overlap: int = 120,
) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for document in documents:
        parts = _semantic_parts(document.content)
        buffer = ""
        chunk_index = 0
        for part in parts:
            candidate = f"{buffer}\n\n{part}".strip() if buffer else part
            if len(candidate) <= chunk_size:
                buffer = candidate
                continue
            if buffer:
                chunks.append(_chunk(document, buffer, chunk_index))
                chunk_index += 1
                buffer = _tail(buffer, overlap)
            buffer = f"{buffer}\n\n{part}".strip() if buffer else part
            while len(buffer) > chunk_size:
                chunks.append(_chunk(document, buffer[:chunk_size], chunk_index))
                chunk_index += 1
                buffer = _tail(buffer[:chunk_size], overlap) + buffer[chunk_size:]
        if buffer:
            chunks.append(_chunk(document, buffer, chunk_index))
    return chunks


def _title_from_markdown(content: str, path: Path) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return path.stem.replace("_", " ").title()


def _semantic_parts(content: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    for line in content.splitlines():
        if line.startswith("#") and current:
            parts.append("\n".join(current).strip())
            current = [line]
        elif not line.strip() and current:
            current.append(line)
            parts.append("\n".join(current).strip())
            current = []
        else:
            current.append(line)
    if current:
        parts.append("\n".join(current).strip())
    return [part for part in parts if part]


def _chunk(document: KnowledgeDocument, content: str, chunk_index: int) -> KnowledgeChunk:
    return KnowledgeChunk(
        id=f"{document.id}:{chunk_index}",
        document_id=document.id,
        path=document.path,
        title=document.title,
        content=content.strip(),
        chunk_index=chunk_index,
        metadata={**document.metadata, "chunk_index": chunk_index},
    )


def _tail(text: str, overlap: int) -> str:
    return text[-overlap:] if overlap > 0 else ""


def _stable_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]
