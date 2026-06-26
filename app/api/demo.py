"""Demo API routes for high-risk tool approval behavior."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import HTTPException

from app.services.benchmark_service import list_scenarios, run_benchmark, run_scenario
from app.tools.gateway import HumanApprovalRequired, execute_tool_via_gateway

router = APIRouter(prefix="/demo", tags=["demo"])


async def _restart_service_executor(**kwargs) -> dict:
    return {"restarted": True, "arguments": kwargs}


@router.post("/high-risk-tool")
async def request_high_risk_tool() -> dict:
    state = {
        "incident_id": "DEMO-HIGH-RISK",
        "policy_records": [],
    }
    try:
        await execute_tool_via_gateway(
            tool_name="restart_service",
            arguments={"service": "order-service"},
            incident_state=state,
            executor=_restart_service_executor,
        )
    except HumanApprovalRequired as exc:
        return {
            "status": "approval_required",
            "approval_id": exc.approval_id,
            "tool_name": exc.tool_name,
            "reason": exc.reason,
        }

    return {"status": "executed"}


@router.get("/scenarios")
def get_demo_scenarios() -> list[dict]:
    return list_scenarios()


@router.post("/run/{scenario_name}")
def run_demo_scenario(scenario_name: str) -> dict:
    try:
        return run_scenario(scenario_name).model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/benchmark")
def get_demo_benchmark() -> dict:
    return run_benchmark().model_dump()
