import json
import asyncio

from app.agents.investigation_agent import execute_selected_tools
from app.tools.log_tools import query_logs
from app.tools.metric_tools import query_metrics
from app.tools.trace_tools import query_traces


def test_file_backed_observability_tools(monkeypatch, tmp_path) -> None:
    data_file = tmp_path / "observability.json"
    data_file.write_text(
        json.dumps(
            {
                "logs": [
                    {
                        "service": "checkout-service",
                        "level": "error",
                        "error_type": "PaymentTimeout",
                        "message": "payment provider timed out",
                    }
                ],
                "metrics": [
                    {
                        "service": "checkout-service",
                        "name": "p95_latency_ms",
                        "value": 1750,
                    },
                    {
                        "service": "checkout-service",
                        "name": "error_rate_percent",
                        "value": 6.2,
                    },
                ],
                "traces": [
                    {
                        "service": "checkout-service",
                        "span": "checkout-service -> payment-provider charge",
                        "duration_ms": 1420,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("USE_FAKE_TOOLS", "false")
    monkeypatch.setenv("OBSERVABILITY_BACKEND", "file")
    monkeypatch.setenv("OBSERVABILITY_DATA_FILE", str(data_file))

    logs = query_logs("checkout-service", None)
    metrics = query_metrics("checkout-service", None)
    traces = query_traces("checkout-service", None)

    assert logs["evidence_id"] == "evidence-log-file-checkout-service"
    assert logs["top_error"] == "PaymentTimeout"
    assert metrics["evidence_id"] == "evidence-metric-file-checkout-service"
    assert metrics["p95_latency_ms"] == 1750
    assert metrics["error_rate_percent"] == 6.2
    assert traces["evidence_id"] == "evidence-trace-file-checkout-service"
    assert traces["slowest_span"] == "checkout-service -> payment-provider charge"


def test_file_backed_observability_runs_through_investigation(monkeypatch, tmp_path) -> None:
    data_file = tmp_path / "observability.json"
    data_file.write_text(
        json.dumps(
            {
                "logs": [
                    {
                        "service": "checkout-service",
                        "level": "error",
                        "error_type": "PaymentTimeout",
                        "message": "payment provider timed out",
                    }
                ],
                "metrics": [
                    {
                        "service": "checkout-service",
                        "name": "p95_latency_ms",
                        "value": 1750,
                    },
                    {
                        "service": "checkout-service",
                        "name": "error_rate_percent",
                        "value": 6.2,
                    },
                ],
                "traces": [
                    {
                        "service": "checkout-service",
                        "span": "checkout-service -> payment-provider charge",
                        "duration_ms": 1420,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("USE_FAKE_TOOLS", "false")
    monkeypatch.setenv("OBSERVABILITY_BACKEND", "file")
    monkeypatch.setenv("OBSERVABILITY_DATA_FILE", str(data_file))

    state = {
        "incident_id": "INC-REAL-DATA",
        "title": "CheckoutService payment provider latency",
        "service": "checkout-service",
        "severity": "high",
        "description": "Use exported observability records for diagnosis.",
        "status": "running",
        "time_window": None,
        "affected_services": ["checkout-service"],
        "investigation_plan": {
            "objectives": ["collect external evidence"],
            "required_tools": ["logs", "metrics", "traces"],
            "reasoning": "test external observability provider",
        },
        "investigation_steps": [],
        "executed_tools": [],
        "skipped_tools": ["memory"],
        "reflection_decision": None,
        "reflection_reason": None,
        "replanning_requested": False,
        "additional_tools": [],
        "investigation_round": 0,
        "max_investigation_rounds": 2,
        "tool_timings": [],
        "failed_tools": [],
        "policy_records": [],
        "denied_tools": [],
        "approval_required_tools": [],
        "total_investigation_duration_ms": 0,
        "evidence": [],
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

    result = asyncio.run(execute_selected_tools(state))

    assert result["executed_tools"] == ["logs", "metrics", "traces"]
    assert [item["id"] for item in result["evidence"]] == [
        "evidence-log-file-checkout-service",
        "evidence-metric-file-checkout-service",
        "evidence-trace-file-checkout-service",
    ]
    assert result["failed_tools"] == []
    assert len(result["tool_traces"]) == 3
