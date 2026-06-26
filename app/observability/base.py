"""Shared observability provider interface."""

from __future__ import annotations

from typing import Protocol


class ObservabilityProvider(Protocol):
    def query_logs(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        ...

    def query_metrics(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        ...

    def query_traces(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        ...
