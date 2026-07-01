"""Ingest markdown runbooks into the local knowledge vector store."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.knowledge.ingestion import ingest_knowledge_base  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    print(json.dumps(ingest_knowledge_base(reset=args.reset), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
