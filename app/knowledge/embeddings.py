"""Deterministic local embeddings for CI-stable vector search."""

from __future__ import annotations

import hashlib
import math
import re


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_./-]+")


class LocalHashEmbedding:
    def __init__(self, dim: int = 384) -> None:
        if dim <= 0:
            raise ValueError("embedding dim must be positive")
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for token in _tokens(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        return _normalize(vector)


class OpenAIEmbedding:
    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError(
            "OpenAI embeddings are reserved for a future optional integration. "
            "Use EMBEDDING_PROVIDER=local for the current implementation."
        )


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 8) for value in vector]
