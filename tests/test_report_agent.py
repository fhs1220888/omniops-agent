from app.agents.report_agent import generate_rca_from_state
from app.agents.state import IncidentState


class FailingLLMClient:
    def diagnose(self, prompt: str) -> dict:
        raise RuntimeError("simulated upstream failure")


def test_report_agent_falls_back_to_fake_rca_when_llm_fails() -> None:
    state: IncidentState = {
        "incident_id": "INC-FALLBACK",
        "title": "OrderService checkout latency",
        "service": "order-service",
        "severity": "high",
        "status": "running",
        "time_window": {"start": "2026-06-23T00:00:00Z", "end": "2026-06-23T00:30:00Z"},
        "affected_services": ["order-service"],
        "investigation_plan": {
            "objectives": ["Measure latency impact."],
            "required_tools": ["logs", "metrics", "traces", "memory"],
            "reasoning": "test fixture",
        },
        "investigation_steps": ["planner:selected_tools"],
        "executed_tools": ["logs", "metrics", "traces", "memory"],
        "skipped_tools": [],
        "reflection_decision": "sufficient",
        "reflection_reason": "test fixture",
        "replanning_requested": False,
        "additional_tools": [],
        "investigation_round": 1,
        "max_investigation_rounds": 2,
        "tool_timings": [],
        "failed_tools": [],
        "policy_records": [],
        "denied_tools": [],
        "approval_required_tools": [],
        "total_investigation_duration_ms": 0,
        "evidence": [
            {
                "id": "evidence-log-redis-timeout",
                "source": "fake_logs",
                "type": "log_pattern",
                "summary": "Redis timeout errors increased.",
                "metadata": {"service": "order-service", "error_count": 42},
            },
            {
                "id": "evidence-metric-latency-spike",
                "source": "fake_metrics",
                "type": "metric_anomaly",
                "summary": "P95 latency and Redis connection usage spiked.",
                "metadata": {"service": "order-service", "p95_latency_ms": 2400},
            },
            {
                "id": "evidence-trace-redis-bottleneck",
                "source": "fake_traces",
                "type": "trace_bottleneck",
                "summary": "Slow traces wait on Redis.",
                "metadata": {"service": "order-service", "slowest_span_ms": 1850},
            },
        ],
        "evidence_items": [],
        "evidence_graph": {"nodes": [], "edges": []},
        "findings": [],
        "tool_observations": [],
        "agent_traces": [],
        "tool_traces": [],
        "similar_incidents": [],
        "root_cause_analysis": None,
        "recommended_actions": [],
        "report_markdown": None,
    }

    root_cause, actions = generate_rca_from_state(state, client=FailingLLMClient())

    assert root_cause.root_cause == "Redis connection pool exhaustion in order-service."
    assert root_cause.supporting_evidence_ids == [
        "evidence-log-redis-timeout",
        "evidence-metric-latency-spike",
        "evidence-trace-redis-bottleneck",
    ]
    assert len(actions) == 3
