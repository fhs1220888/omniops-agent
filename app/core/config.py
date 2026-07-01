"""Application settings for the Week 2 MVP."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
ObservabilityBackend = Literal["fake", "file", "prometheus_loki_tempo"]


class Settings(BaseModel):
    app_name: str = "OmniOps Agent"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    llm_provider: str = "openai-compatible"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    use_fake_llm: bool = True
    use_fake_tools: bool = True
    observability_backend: ObservabilityBackend = "fake"
    observability_data_file: str = ""
    prometheus_url: str = "http://localhost:9090"
    loki_url: str = "http://localhost:3100"
    tempo_url: str = "http://localhost:3200"
    rag_enabled: bool = False
    rag_backend: str = "local_chroma"
    rag_collection: str = "omniops_runbooks"
    rag_data_dir: str = ".chroma"
    rag_docs_dir: str = "knowledge_base"
    rag_top_k: int = 3
    embedding_provider: str = "local"
    embedding_dim: int = 384
    skills_enabled: bool = True
    skills_dir: str = "skills"
    skills_top_k: int = 3

    @classmethod
    def from_env(cls) -> "Settings":
        env_values = _read_dotenv(ENV_FILE)
        return cls(
            llm_provider=_env("LLM_PROVIDER", "openai-compatible", env_values),
            llm_base_url=_env("LLM_BASE_URL", "https://api.openai.com/v1", env_values),
            llm_api_key=_env("LLM_API_KEY", "", env_values),
            llm_model=_env("LLM_MODEL", "gpt-4o-mini", env_values),
            use_fake_llm=_read_bool("USE_FAKE_LLM", default=True, env_values=env_values),
            use_fake_tools=_read_bool("USE_FAKE_TOOLS", default=True, env_values=env_values),
            observability_backend=_env("OBSERVABILITY_BACKEND", "fake", env_values),
            observability_data_file=_env("OBSERVABILITY_DATA_FILE", "", env_values),
            prometheus_url=_env("PROMETHEUS_URL", "http://localhost:9090", env_values),
            loki_url=_env("LOKI_URL", "http://localhost:3100", env_values),
            tempo_url=_env("TEMPO_URL", "http://localhost:3200", env_values),
            rag_enabled=_read_bool("RAG_ENABLED", default=False, env_values=env_values),
            rag_backend=_env("RAG_BACKEND", "local_chroma", env_values),
            rag_collection=_env("RAG_COLLECTION", "omniops_runbooks", env_values),
            rag_data_dir=_env("RAG_DATA_DIR", ".chroma", env_values),
            rag_docs_dir=_env("RAG_DOCS_DIR", "knowledge_base", env_values),
            rag_top_k=int(_env("RAG_TOP_K", "3", env_values)),
            embedding_provider=_env("EMBEDDING_PROVIDER", "local", env_values),
            embedding_dim=int(_env("EMBEDDING_DIM", "384", env_values)),
            skills_enabled=_read_bool("SKILLS_ENABLED", default=True, env_values=env_values),
            skills_dir=_env("SKILLS_DIR", "skills", env_values),
            skills_top_k=int(_env("SKILLS_TOP_K", "3", env_values)),
        )


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _env(name: str, default: str, env_values: dict[str, str]) -> str:
    return os.getenv(name) or env_values.get(name, default)


def _read_bool(name: str, default: bool, env_values: dict[str, str]) -> bool:
    value = os.getenv(name) or env_values.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


settings = Settings.from_env()
