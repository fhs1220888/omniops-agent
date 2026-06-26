import asyncio

from fastapi.testclient import TestClient

from app.main import app
from app.services.approval_service import ApprovalService, approval_service
from app.tools.gateway import HumanApprovalRequired, execute_tool_via_gateway


client = TestClient(app)


def _state() -> dict:
    return {
        "incident_id": "INC-APPROVAL",
        "policy_records": [],
    }


async def _executor(**kwargs) -> dict:
    return {"executed": True}


def test_approval_request_creation() -> None:
    service = ApprovalService()

    request = service.create_request(
        incident_id="INC-1",
        tool_name="restart_service",
        arguments={"service": "order-service"},
        risk_level="high",
        reason="Tool requires human approval.",
    )

    assert request.status == "pending"
    assert request.approval_id.startswith("APR-")
    assert service.get(request.approval_id) == request


def test_approve_request() -> None:
    service = ApprovalService()
    request = service.create_request(
        incident_id="INC-1",
        tool_name="restart_service",
        arguments={},
        risk_level="high",
        reason="review",
    )

    approved = service.approve(request.approval_id, reviewer="alice", reason="safe")

    assert approved.status == "approved"
    assert approved.reviewer == "alice"
    assert approved.decision_reason == "safe"
    assert approved.reviewed_at is not None


def test_reject_request() -> None:
    service = ApprovalService()
    request = service.create_request(
        incident_id="INC-1",
        tool_name="execute_sql",
        arguments={},
        risk_level="high",
        reason="review",
    )

    rejected = service.reject(request.approval_id, reviewer="bob", reason="too risky")

    assert rejected.status == "rejected"
    assert rejected.reviewer == "bob"
    assert rejected.decision_reason == "too risky"


def test_high_risk_tool_creates_pending_approval() -> None:
    approval_service.reset()

    try:
        asyncio.run(
            execute_tool_via_gateway(
                tool_name="restart_service",
                arguments={"service": "order-service"},
                incident_state=_state(),
                executor=_executor,
            )
        )
    except HumanApprovalRequired as exc:
        request = approval_service.get(exc.approval_id)
        assert request is not None
        assert request.status == "pending"
        assert request.tool_name == "restart_service"
    else:
        raise AssertionError("restart_service should require approval")


def test_high_risk_tool_is_not_executed_before_approval() -> None:
    approval_service.reset()
    executed = False

    async def executor(**kwargs) -> dict:
        nonlocal executed
        executed = True
        return {"executed": True}

    try:
        asyncio.run(
            execute_tool_via_gateway(
                tool_name="execute_sql",
                arguments={"sql": "select 1"},
                incident_state=_state(),
                executor=executor,
            )
        )
    except HumanApprovalRequired:
        pass
    else:
        raise AssertionError("execute_sql should require approval")

    assert executed is False


def test_pending_approvals_api() -> None:
    approval_service.reset()
    request = approval_service.create_request(
        incident_id="INC-API",
        tool_name="restart_service",
        arguments={"service": "order-service"},
        risk_level="high",
        reason="Tool requires human approval.",
    )

    pending_response = client.get("/api/approvals/pending")
    assert pending_response.status_code == 200
    assert any(
        item["approval_id"] == request.approval_id
        for item in pending_response.json()
    )

    approve_response = client.post(
        f"/api/approvals/{request.approval_id}/approve",
        json={"reviewer": "alice", "reason": "approved for demo"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"


def test_demo_high_risk_tool_returns_approval_required() -> None:
    approval_service.reset()

    response = client.post("/api/demo/high-risk-tool")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "approval_required"
    assert payload["approval_id"].startswith("APR-")
    assert approval_service.get(payload["approval_id"]) is not None
