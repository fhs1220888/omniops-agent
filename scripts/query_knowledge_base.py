"""Query the local knowledge vector store."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import Settings  # noqa: E402
from app.knowledge.retriever import KnowledgeRetriever  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=None)
    args = parser.parse_args()
    settings = Settings.from_env().model_copy(update={"rag_enabled": True})
    results = KnowledgeRetriever(settings).search(args.query, args.top_k)
    output = {
        "query": args.query,
        "results": [
            {
                "title": item.title,
                "path": item.path,
                "score": item.score,
                "snippet": item.content[:300],
            }
            for item in results
        ],
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
