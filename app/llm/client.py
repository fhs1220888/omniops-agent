"""LLM client abstraction for fake and OpenAI-compatible real mode."""

from __future__ import annotations

import json
from typing import Protocol

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.models.incident import RecommendedAction, RootCauseAnalysis


class LLMClientError(RuntimeError):
    """Raised when the configured LLM client cannot produce usable output."""


class RCAJsonResult(BaseModel):
    root_cause_analysis: RootCauseAnalysis
    recommended_actions: list[RecommendedAction]


class LLMClient(Protocol):
    def diagnose(self, prompt: str) -> dict:
        """Return an RCA JSON-compatible dictionary."""


class FakeLLMClient:
    """Deterministic local LLM substitute used by tests and default local runs."""

    def diagnose(self, prompt: str) -> dict:
        incident_text = _incident_text_from_prompt(prompt)
        if "consumer lag" in incident_text or "stock update" in incident_text:
            return _fake_rca_payload(
                root_cause="Inventory consumer processing lag delayed stock updates.",
                confidence=0.8,
                impact="Inventory updates were delayed while consumer lag accumulated.",
                evidence_ids=[
                    "evidence-log-redis-timeout",
                    "memory-HIST-CONFIG-001",
                ],
                actions=[
                    {
                        "action_type": "mitigate",
                        "description": "Scale or unblock inventory consumers.",
                        "owner": "inventory-service",
                        "priority": "high",
                    },
                    {
                        "action_type": "verify",
                        "description": "Monitor consumer lag and stock update latency until stable.",
                        "owner": "service-oncall",
                        "priority": "medium",
                    },
                ],
            )
        if "bad config" in incident_text or "configuration deploy" in incident_text:
            return _fake_rca_payload(
                root_cause="Bad configuration deploy reduced connection capacity for order-service.",
                confidence=0.82,
                impact="Order service requests saw connection-related failures after deploy.",
                evidence_ids=[
                    "evidence-log-redis-timeout",
                    "memory-HIST-REDIS-001",
                ],
                actions=[
                    {
                        "action_type": "mitigate",
                        "description": "Rollback the bad configuration.",
                        "owner": "platform-oncall",
                        "priority": "high",
                    },
                    {
                        "action_type": "investigate",
                        "description": "Add a pre-deploy configuration validation check.",
                        "owner": "order-service",
                        "priority": "medium",
                    },
                ],
            )
        if "mysql" in incident_text or "payment_order" in incident_text:
            return _fake_rca_payload(
                root_cause="Missing database index caused slow payment_order queries in payment-service.",
                confidence=0.84,
                impact="Payment requests experienced elevated database latency.",
                evidence_ids=[
                    "evidence-log-redis-timeout",
                    "evidence-metric-latency-spike",
                    "evidence-trace-redis-bottleneck",
                ],
                actions=[
                    {
                        "action_type": "mitigate",
                        "description": "Add the missing composite index for payment_order lookups.",
                        "owner": "payment-service",
                        "priority": "high",
                    },
                    {
                        "action_type": "verify",
                        "description": "Verify database latency and payment P95 latency return to baseline.",
                        "owner": "service-oncall",
                        "priority": "high",
                    },
                ],
            )
        return {
            "root_cause_analysis": {
                "root_cause": "Redis connection pool exhaustion in order-service.",
                "confidence": 0.87,
                "impact": "Checkout requests experienced elevated latency and timeout errors.",
                "supporting_evidence_ids": [
                    "evidence-log-redis-timeout",
                    "evidence-metric-latency-spike",
                    "evidence-trace-redis-bottleneck",
                ],
            },
            "recommended_actions": [
                {
                    "action_type": "mitigate",
                    "description": "Restore the Redis connection pool limit to the last known safe value.",
                    "owner": "platform-oncall",
                    "priority": "high",
                },
                {
                    "action_type": "verify",
                    "description": "Confirm P95 latency returns below 250ms and Redis timeout logs stop.",
                    "owner": "service-oncall",
                    "priority": "high",
                },
                {
                    "action_type": "investigate",
                    "description": "Review the deploy/configuration change that reduced Redis pool capacity.",
                    "owner": "order-service",
                    "priority": "medium",
                },
            ],
        }


def _fake_rca_payload(
    *,
    root_cause: str,
    confidence: float,
    impact: str,
    evidence_ids: list[str],
    actions: list[dict],
) -> dict:
    return {
        "root_cause_analysis": {
            "root_cause": root_cause,
            "confidence": confidence,
            "impact": impact,
            "supporting_evidence_ids": evidence_ids,
        },
        "recommended_actions": actions,
    }


def _incident_text_from_prompt(prompt: str) -> str:
    try:
        payload = json.loads(prompt.split("\n\n", 1)[1])
    except (IndexError, json.JSONDecodeError):
        return prompt.lower()
    incident = payload.get("incident", {})
    if not isinstance(incident, dict):
        return prompt.lower()
    return " ".join(
        str(incident.get(field, ""))
        for field in ["id", "title", "service", "severity", "time_window"]
    ).lower()


class OpenAICompatibleLLMClient:
    """Minimal client for OpenAI-compatible chat completions APIs."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 20.0,
    ) -> None:
        if not base_url:
            raise LLMClientError("LLM_BASE_URL is required for real LLM mode.")
        if not api_key:
            raise LLMClientError("LLM_API_KEY is required for real LLM mode.")
        if not model:
            raise LLMClientError("LLM_MODEL is required for real LLM mode.")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def diagnose(self, prompt: str) -> dict:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an incident diagnosis engine. "
                            "Return only valid JSON matching the requested schema."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMClientError("LLM response did not contain chat message content.") from exc
        return _parse_json_object(content)


def build_llm_client(settings: Settings | None = None) -> LLMClient:
    config = settings or Settings.from_env()
    if config.use_fake_llm:
        return FakeLLMClient()
    if config.llm_provider != "openai-compatible":
        raise LLMClientError(f"Unsupported LLM_PROVIDER: {config.llm_provider}")
    return OpenAICompatibleLLMClient(
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        model=config.llm_model,
    )


def validate_rca_json(payload: dict) -> RCAJsonResult:
    try:
        return RCAJsonResult.model_validate(payload)
    except ValidationError as exc:
        raise LLMClientError("LLM RCA JSON failed schema validation.") from exc


def _parse_json_object(content: str) -> dict:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMClientError("LLM response content was not valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise LLMClientError("LLM response JSON must be an object.")
    return parsed
