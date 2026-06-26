"""Human approval API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.approval import ApprovalRequest
from app.services.approval_service import approval_service

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalDecision(BaseModel):
    reviewer: str
    reason: str


@router.get("/pending", response_model=list[ApprovalRequest])
def list_pending_approvals() -> list[ApprovalRequest]:
    return approval_service.list_pending()


@router.post("/{approval_id}/approve", response_model=ApprovalRequest)
def approve_request(approval_id: str, payload: ApprovalDecision) -> ApprovalRequest:
    try:
        return approval_service.approve(approval_id, payload.reviewer, payload.reason)
    except KeyError:
        raise HTTPException(status_code=404, detail="Approval request not found")


@router.post("/{approval_id}/reject", response_model=ApprovalRequest)
def reject_request(approval_id: str, payload: ApprovalDecision) -> ApprovalRequest:
    try:
        return approval_service.reject(approval_id, payload.reviewer, payload.reason)
    except KeyError:
        raise HTTPException(status_code=404, detail="Approval request not found")
