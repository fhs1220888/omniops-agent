"""MCP-style lightweight Tool Gateway."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from time import perf_counter

from app.agents.state import IncidentState
from app.models.incident import ToolPolicyRecord
from app.models.tool_trace import ToolCallTrace
from app.services.approval_service import approval_service
from app.tools.policy import evaluate_tool_call
from app.tools.registry import get_tool_spec


class ToolDenied(RuntimeError):
    def __init__(
        self,
        tool_name: str,
        reason: str,
        record: ToolPolicyRecord,
        tool_trace: ToolCallTrace,
    ) -> None:
        super().__init__(reason)
        self.tool_name = tool_name
        self.reason = reason
        self.record = record
        self.tool_trace = tool_trace


class HumanApprovalRequired(RuntimeError):
    def __init__(
        self,
        tool_name: str,
        reason: str,
        record: ToolPolicyRecord,
        tool_trace: ToolCallTrace,
        approval_id: str,
    ) -> None:
        super().__init__(reason)
        self.tool_name = tool_name
        self.reason = reason
        self.record = record
        self.tool_trace = tool_trace
        self.approval_id = approval_id


class ToolGatewayTimeout(TimeoutError):
    def __init__(
        self,
        tool_name: str,
        reason: str,
        record: ToolPolicyRecord,
        tool_trace: ToolCallTrace,
    ) -> None:
        super().__init__(reason)
        self.tool_name = tool_name
        self.reason = reason
        self.record = record
        self.tool_trace = tool_trace


async def execute_tool_via_gateway(
    tool_name: str,
    arguments: dict,
    incident_state: IncidentState,
    executor: Callable[..., Awaitable[dict]],
    timeout_seconds: float | None = None,
) -> dict:
    started = perf_counter()
    policy = evaluate_tool_call(tool_name, arguments, incident_state)
    spec = get_tool_spec(tool_name)
    effective_timeout = (
        timeout_seconds
        if timeout_seconds is not None
        else spec.timeout_seconds if spec is not None else 0
    )

    if policy.decision == "deny":
        record = _record(
            tool_name=tool_name,
            policy_decision="deny",
            risk_level=policy.risk_level,
            started=started,
            status="denied",
            error=policy.reason,
        )
        raise ToolDenied(tool_name, policy.reason, record, _trace_from_record(record))

    if policy.decision == "review":
        approval_request = approval_service.create_request(
            incident_id=str(incident_state.get("incident_id", "unknown")),
            tool_name=tool_name,
            arguments=arguments,
            risk_level=policy.risk_level,
            reason=policy.reason,
        )
        record = _record(
            tool_name=tool_name,
            policy_decision="review",
            risk_level=policy.risk_level,
            started=started,
            status="review_required",
            error=policy.reason,
        )
        raise HumanApprovalRequired(
            tool_name,
            policy.reason,
            record,
            _trace_from_record(record),
            approval_request.approval_id,
        )

    try:
        result = await asyncio.wait_for(
            executor(**arguments),
            timeout=effective_timeout,
        )
    except TimeoutError as exc:
        record = _record(
            tool_name=tool_name,
            policy_decision="allow",
            risk_level=policy.risk_level,
            started=started,
            status="timeout",
            error=f"{tool_name} timed out after {effective_timeout} seconds.",
        )
        raise ToolGatewayTimeout(
            tool_name,
            record.error or "Tool timed out.",
            record,
            _trace_from_record(record),
        ) from exc
    except Exception as exc:
        record = _record(
            tool_name=tool_name,
            policy_decision="allow",
            risk_level=policy.risk_level,
            started=started,
            status="failed",
            error=str(exc),
        )
        exc.gateway_trace = _trace_from_record(record)
        exc.gateway_record = record
        raise

    record = _record(
        tool_name=tool_name,
        policy_decision="allow",
        risk_level=policy.risk_level,
        started=started,
        status="completed",
    )
    return {
        "result": result,
        "policy_record": record.model_dump(),
        "tool_trace": _trace_from_record(record).model_dump(),
    }


def _record(
    *,
    tool_name: str,
    policy_decision: str,
    risk_level: str,
    started: float,
    status: str,
    error: str | None = None,
) -> ToolPolicyRecord:
    return ToolPolicyRecord(
        tool_name=tool_name,
        policy_decision=policy_decision,
        risk_level=risk_level,
        latency_ms=round((perf_counter() - started) * 1000, 3),
        status=status,
        error=error,
    )


def _trace_from_record(record: ToolPolicyRecord) -> ToolCallTrace:
    return ToolCallTrace(
        tool_name=record.tool_name,
        policy_decision=record.policy_decision,
        risk_level=record.risk_level,
        duration_ms=record.latency_ms,
        status=record.status,
        error=record.error,
    )
