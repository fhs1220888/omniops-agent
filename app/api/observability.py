"""Observability profile APIs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.config import Settings
from app.observability.profile import (
    ObservabilityProfileError,
    list_observability_profiles,
    load_observability_profile,
)

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/profile")
def current_observability_profile() -> dict:
    settings = Settings.from_env()
    try:
        profile = load_observability_profile(settings=settings)
    except ObservabilityProfileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return profile.model_dump()


@router.get("/profiles")
def observability_profiles() -> dict:
    return {"profiles": list_observability_profiles()}
