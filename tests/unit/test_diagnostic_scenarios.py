import json
from pathlib import Path


SCENARIO_FILE = Path("data/diagnostic_scenarios.json")


def test_diagnostic_scenarios_file_exists() -> None:
    assert SCENARIO_FILE.exists()


def test_diagnostic_scenarios_have_required_fields() -> None:
    scenarios = json.loads(SCENARIO_FILE.read_text(encoding="utf-8"))

    assert len(scenarios) >= 7
    for scenario in scenarios:
        assert scenario["id"]
        assert scenario["title"]
        assert scenario["service"]
        assert scenario["symptom"]
        assert scenario["expected_tools"]
        assert scenario["expected_root_cause_keywords"]


def test_evidence_insufficient_scenario_exists() -> None:
    scenarios = json.loads(SCENARIO_FILE.read_text(encoding="utf-8"))

    insufficient = [
        scenario
        for scenario in scenarios
        if scenario.get("expect_evidence_insufficient") is True
    ]

    assert len(insufficient) == 1
    assert insufficient[0]["id"] == "evidence_insufficient"
    assert insufficient[0]["service"] == "unknown-service"
