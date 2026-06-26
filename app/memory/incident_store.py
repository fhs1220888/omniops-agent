"""Local JSON incident memory with simple keyword-overlap recall."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.models.incident import HistoricalIncident, SimilarIncident

DEFAULT_STORE_PATH = Path("data/incident_memory.json")


SEED_INCIDENTS = [
    HistoricalIncident(
        incident_id="HIST-REDIS-001",
        title="OrderService Redis pool exhaustion caused checkout latency",
        service="order-service",
        symptoms=[
            "P95 latency increased during checkout",
            "RedisTimeoutException in order-service logs",
            "Redis connections reached pool limit",
        ],
        root_cause="Redis connection pool exhaustion after a config change lowered maxTotal.",
        recommended_actions=[
            "Restore Redis maxTotal to the last known safe value.",
            "Add alerts for Redis pool saturation.",
            "Review config changes before deployment.",
        ],
        tags=["redis", "latency", "checkout", "connection-pool"],
    ),
    HistoricalIncident(
        incident_id="HIST-MYSQL-001",
        title="PaymentService slow query increased payment latency",
        service="payment-service",
        symptoms=[
            "Payment latency spiked",
            "Slow SQL query found in logs",
            "Database CPU increased",
        ],
        root_cause="Missing composite index on payment_order lookup query.",
        recommended_actions=[
            "Add the missing composite index.",
            "Verify slow query count drops.",
        ],
        tags=["mysql", "slow-query", "payment", "latency"],
    ),
    HistoricalIncident(
        incident_id="HIST-CONFIG-001",
        title="InventoryService bad config delayed stock updates",
        service="inventory-service",
        symptoms=[
            "Inventory update latency increased",
            "Inventory updates delayed",
            "Connection retries increased after deploy",
        ],
        root_cause="Bad deploy configuration reduced downstream connection capacity.",
        recommended_actions=[
            "Rollback the bad configuration.",
            "Monitor inventory update latency until it returns to baseline.",
        ],
        tags=["bad-config", "inventory", "latency"],
    ),
]


class IncidentStore:
    def __init__(self, path: Path | str = DEFAULT_STORE_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_all(SEED_INCIDENTS)

    def list_incidents(self) -> list[HistoricalIncident]:
        with self.path.open("r", encoding="utf-8") as file:
            raw_items = json.load(file)
        return [HistoricalIncident.model_validate(item) for item in raw_items]

    def store_resolved_incident(self, incident: HistoricalIncident) -> HistoricalIncident:
        incidents = self.list_incidents()
        incidents = [item for item in incidents if item.incident_id != incident.incident_id]
        incidents.append(incident)
        self._write_all(incidents)
        return incident

    def find_similar(
        self,
        *,
        title: str,
        service: str,
        symptoms: list[str],
        limit: int = 3,
    ) -> list[SimilarIncident]:
        query_tokens = _tokenize(" ".join([title, service, *symptoms]))
        scored: list[SimilarIncident] = []
        for incident in self.list_incidents():
            incident_tokens = _tokenize(
                " ".join(
                    [
                        incident.title,
                        incident.service,
                        *incident.symptoms,
                        incident.root_cause,
                        *incident.tags,
                    ]
                )
            )
            score = len(query_tokens & incident_tokens)
            if score <= 0:
                continue
            scored.append(
                SimilarIncident(
                    **incident.model_dump(),
                    similarity_score=score,
                )
            )
        return sorted(
            scored,
            key=lambda item: (-item.similarity_score, item.incident_id),
        )[:limit]

    def _write_all(self, incidents: list[HistoricalIncident]) -> None:
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                [incident.model_dump() for incident in incidents],
                file,
                indent=2,
                sort_keys=True,
            )


def _tokenize(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 2
    }
