"""Runtime status API for demo verification."""

from __future__ import annotations

from fastapi import APIRouter

from app.services.runtime_status import get_runtime_status

router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/status")
def runtime_status() -> dict:
    return get_runtime_status()
