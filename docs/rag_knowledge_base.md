# RAG Knowledge Base

OmniOps includes a lightweight RAG Knowledge Base for long-term diagnostic guidance.

## What It Stores

- Runbooks
- SOPs
- Historical RCA notes
- Architecture documents

## What It Does Not Store

- Live logs
- Live metrics
- Live traces

Prometheus, Loki, and Tempo remain the live evidence layer. RAG is the knowledge layer.

## Current Backend

The first implementation uses:

- backend name: `local_chroma`
- storage path: `.chroma/index.json`
- embedding provider: deterministic local hashing
- default embedding dimension: `384`

This avoids pgvector and external embedding APIs. It also keeps local tests and GitHub Actions stable. The store boundary can later be replaced by ChromaDB, Qdrant, Milvus, or another vector database.

## Configuration

```env
RAG_ENABLED=false
RAG_BACKEND=local_chroma
RAG_COLLECTION=omniops_runbooks
RAG_DATA_DIR=.chroma
RAG_DOCS_DIR=knowledge_base
RAG_TOP_K=3
EMBEDDING_PROVIDER=local
EMBEDDING_DIM=384
```

Live demos may set:

```env
RAG_ENABLED=true
```

If RAG is disabled, retrieval returns an empty list. If the index is missing, retrieval also returns an empty list. RCA should continue.

## Ingestion

```bash
uv run python scripts/ingest_knowledge_base.py --reset
```

The script loads markdown files from `knowledge_base/**/*.md`, chunks them, embeds them, and persists the local vector index.

## Query

```bash
uv run python scripts/query_knowledge_base.py "redis timeout checkout 504"
```

The output includes title, path, score, and snippet for the top matches.

## API

```text
GET  /api/knowledge/status
POST /api/knowledge/search
POST /api/knowledge/ingest
```

## Report Agent Contract

The Report Agent may include retrieved knowledge in the RCA prompt as:

```text
Retrieved Runbook Guidance
```

Guardrails:

- Real-time evidence determines root cause.
- Retrieved runbooks guide diagnosis and mitigation.
- Do not infer root cause from runbooks if live evidence is empty.
- If evidence is insufficient, say evidence insufficient.
