"""Similar incident recall node."""

from __future__ import annotations

import asyncio

from app.agents.state import IncidentState
from app.memory.incident_store import IncidentStore


async def recall_similar_incidents(
    state: IncidentState,
    store: IncidentStore | None = None,
) -> dict:
    await asyncio.sleep(0)
    incident_store = store or IncidentStore()
    symptoms = [item["summary"] for item in state["evidence"]]
    similar_incidents = incident_store.find_similar(
        title=state["title"],
        service=state["service"],
        symptoms=symptoms,
        limit=3,
    )
    return {
        "similar_incidents": [
            incident.model_dump() for incident in similar_incidents
        ],
        "executed_tools": [*state["executed_tools"], "memory"],
        "investigation_steps": [*state["investigation_steps"], "memory:find_similar"],
    }
