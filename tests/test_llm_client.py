import pytest

from app.llm.client import FakeLLMClient, LLMClientError, validate_rca_json


def test_fake_llm_client_returns_valid_rca_json() -> None:
    payload = FakeLLMClient().diagnose("diagnose this incident")

    result = validate_rca_json(payload)

    assert result.root_cause_analysis.root_cause == (
        "Redis connection pool exhaustion in order-service."
    )
    assert result.root_cause_analysis.confidence == 0.87
    assert len(result.recommended_actions) == 3
    assert result.recommended_actions[0].action_type == "mitigate"


def test_validate_rca_json_rejects_invalid_payload() -> None:
    invalid_payload = {
        "root_cause_analysis": {
            "root_cause": "Missing confidence and impact fields.",
            "supporting_evidence_ids": [],
        },
        "recommended_actions": [],
    }

    with pytest.raises(LLMClientError):
        validate_rca_json(invalid_payload)
