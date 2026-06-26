"""Agent execution trace models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

AgentExecutionStatus = Literal["running", "success", "failed"]


class AgentTrace(BaseModel):
    agent_name: str
    started_at: datetime
    finished_at: datetime
    duration_ms: float
    status: AgentExecutionStatus
    summary: str
