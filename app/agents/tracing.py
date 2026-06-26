"""Small helpers for local AgentOps tracing."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from time import perf_counter

from app.agents.state import IncidentState
from app.models.agent_trace import AgentTrace


def trace_sync_agent(
    agent_name: str,
    summary: str,
    func: Callable[[IncidentState], dict],
) -> Callable[[IncidentState], dict]:
    def wrapped(state: IncidentState) -> dict:
        started_at = datetime.now(UTC)
        started_perf = perf_counter()
        try:
            update = func(state)
            return {
                **update,
                "agent_traces": [
                    *state["agent_traces"],
                    _trace(agent_name, started_at, started_perf, "success", summary),
                ],
            }
        except Exception:
            return {
                "agent_traces": [
                    *state["agent_traces"],
                    _trace(agent_name, started_at, started_perf, "failed", summary),
                ],
            }

    return wrapped


def trace_async_agent(
    agent_name: str,
    summary: str,
    func: Callable[[IncidentState], Awaitable[dict]],
) -> Callable[[IncidentState], Awaitable[dict]]:
    async def wrapped(state: IncidentState) -> dict:
        started_at = datetime.now(UTC)
        started_perf = perf_counter()
        try:
            update = await func(state)
            return {
                **update,
                "agent_traces": [
                    *state["agent_traces"],
                    _trace(agent_name, started_at, started_perf, "success", summary),
                ],
            }
        except Exception:
            trace = _trace(agent_name, started_at, started_perf, "failed", summary)
            return {
                "agent_traces": [*state["agent_traces"], trace],
            }

    return wrapped


def _trace(
    agent_name: str,
    started_at: datetime,
    started_perf: float,
    status: str,
    summary: str,
) -> dict:
    return AgentTrace(
        agent_name=agent_name,
        started_at=started_at,
        finished_at=datetime.now(UTC),
        duration_ms=round((perf_counter() - started_perf) * 1000, 3),
        status=status,
        summary=summary,
    ).model_dump()
