"""Run one incident diagnosis using the configured observability backend."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agents.graph import run_incident_diagnosis  # noqa: E402
from app.models.incident import Incident  # noqa: E402


def main() -> None:
    service = os.getenv("SMOKE_SERVICE", "order-service")
    title = os.getenv("SMOKE_TITLE", f"{service} latency investigation")
    description = os.getenv(
        "SMOKE_DESCRIPTION",
        "Smoke test using the configured observability backend.",
    )
    diagnosis = run_incident_diagnosis(
        Incident(
            id="SMOKE-REAL-OBSERVABILITY",
            title=title,
            service=service,
            severity="high",
            description=description,
        )
    )
    output = {
        "executed_tools": diagnosis.executed_tools,
        "tool_sources": sorted({item.source for item in diagnosis.evidence}),
        "empty_results": [
            {
                "evidence_id": item.id,
                "source": item.source,
                "error": item.metadata.get("error"),
            }
            for item in diagnosis.evidence
            if item.metadata.get("empty") == "True"
        ],
        "failed_tools": [item.model_dump() for item in diagnosis.failed_tools],
        "root_cause": diagnosis.root_cause_analysis.root_cause,
        "confidence": diagnosis.root_cause_analysis.confidence,
        "evidence_count": len(diagnosis.evidence),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
