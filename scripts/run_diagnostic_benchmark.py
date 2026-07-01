"""Run live diagnostic coverage scenarios through the OmniOps API."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from statistics import mean
from typing import Any

import httpx


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SCENARIO_FILE = ROOT / "data" / "diagnostic_scenarios.json"
OMNIOPS_URL = os.getenv("OMNIOPS_URL", "http://localhost:8001").rstrip("/")
REAL_TOOL_SOURCES = {"loki", "prometheus", "tempo"}

from app.core.config import Settings  # noqa: E402


def main() -> int:
    settings = Settings.from_env()
    try:
        runtime = _get_runtime_status()
    except httpx.HTTPError:
        print(
            "Please start OmniOps API first: "
            "uv run uvicorn app.main:app --reload --port 8001",
            file=sys.stderr,
        )
        return 1

    if not _is_live_observability_mode(runtime):
        print(
            "Runtime is not live real observability mode. Required: "
            "USE_FAKE_TOOLS=false and OBSERVABILITY_BACKEND=prometheus_loki_tempo",
            file=sys.stderr,
        )
        print(json.dumps(runtime, indent=2, sort_keys=True), file=sys.stderr)
        return 1

    scenarios = _load_scenarios()
    results = [_run_scenario(scenario) for scenario in scenarios]
    passed = sum(1 for item in results if item["passed"])
    confidence_values = [
        item["confidence"]
        for item in results
        if isinstance(item.get("confidence"), int | float)
    ]
    summary = {
        "scenario_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "average_confidence": round(mean(confidence_values), 3)
        if confidence_values
        else None,
        "all_tool_sources_real": all(
            source in REAL_TOOL_SOURCES
            for item in results
            for source in item["tool_sources"]
        ),
        "rag_enabled": settings.rag_enabled,
        "skills_enabled": settings.skills_enabled,
        "average_retrieved_knowledge_count": round(
            mean(item["retrieved_knowledge_count"] for item in results),
            3,
        )
        if results
        else 0,
        "average_selected_skill_count": round(
            mean(item["selected_skill_count"] for item in results),
            3,
        )
        if results
        else 0,
        "scenarios": results,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["failed"] == 0 else 1


def _get_runtime_status() -> dict:
    response = httpx.get(f"{OMNIOPS_URL}/api/runtime/status", timeout=3.0)
    response.raise_for_status()
    return response.json()


def _is_live_observability_mode(runtime: dict) -> bool:
    return (
        runtime.get("tools_mode") == "real"
        and runtime.get("fake_tools_enabled") is False
        and runtime.get("observability_backend") == "prometheus_loki_tempo"
    )


def _load_scenarios() -> list[dict]:
    return json.loads(SCENARIO_FILE.read_text(encoding="utf-8"))


def _run_scenario(scenario: dict) -> dict:
    incident = _create_incident(scenario)
    diagnosis = _diagnose_incident(incident["id"])
    evidence = diagnosis.get("evidence", [])
    report_markdown = diagnosis.get("report_markdown", "")
    root_cause = diagnosis.get("root_cause_analysis", {}).get("root_cause")
    confidence = diagnosis.get("root_cause_analysis", {}).get("confidence")
    evidence_count = _non_empty_evidence_count(evidence)
    matched_keywords = _matched_keywords(
        scenario.get("expected_root_cause_keywords", []),
        diagnosis,
    )
    insufficient_ok = (
        evidence_count == 0
        or "evidence insufficient" in report_markdown.lower()
        or "insufficient evidence" in report_markdown.lower()
        or "no evidence" in report_markdown.lower()
    )
    if scenario.get("expect_evidence_insufficient"):
        passed = insufficient_ok
    else:
        passed = bool(matched_keywords) and evidence_count > 0
    return {
        "scenario_id": scenario["id"],
        "executed_tools": diagnosis.get("executed_tools", []),
        "tool_sources": sorted({item.get("source") for item in evidence if item.get("source")}),
        "evidence_count": evidence_count,
        "failed_tools": diagnosis.get("failed_tools", []),
        "root_cause": root_cause,
        "confidence": confidence,
        "retrieved_knowledge_count": len(diagnosis.get("retrieved_knowledge", [])),
        "selected_skill_count": len(diagnosis.get("selected_skills", [])),
        "selected_skills": [
            item.get("id")
            for item in diagnosis.get("selected_skills", [])
            if item.get("id")
        ],
        "matched_expected_keywords": matched_keywords,
        "passed": passed,
    }


def _create_incident(scenario: dict) -> dict:
    payload = {
        "title": scenario["title"],
        "service": scenario["service"],
        "severity": "high",
        "description": scenario["symptom"],
    }
    response = httpx.post(
        f"{OMNIOPS_URL}/api/incidents",
        json=payload,
        timeout=5.0,
    )
    response.raise_for_status()
    return response.json()


def _diagnose_incident(incident_id: str) -> dict:
    response = httpx.post(
        f"{OMNIOPS_URL}/api/incidents/{incident_id}/diagnose",
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def _non_empty_evidence_count(evidence: list[dict]) -> int:
    return sum(1 for item in evidence if str(item.get("metadata", {}).get("empty")) != "True")


def _matched_keywords(keywords: list[str], diagnosis: dict) -> list[str]:
    haystack = json.dumps(diagnosis, ensure_ascii=False).lower()
    return [keyword for keyword in keywords if keyword.lower() in haystack]


if __name__ == "__main__":
    sys.exit(main())
