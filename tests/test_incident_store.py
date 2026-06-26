from app.memory.incident_store import IncidentStore
from app.models.incident import HistoricalIncident


def test_store_resolved_incident(tmp_path) -> None:
    store = IncidentStore(tmp_path / "incidents.json")
    incident = HistoricalIncident(
        incident_id="INC-RESOLVED",
        title="OrderService Redis timeout",
        service="order-service",
        symptoms=["RedisTimeoutException", "P95 latency spike"],
        root_cause="Redis connection pool exhaustion.",
        recommended_actions=["Restore pool size."],
        tags=["redis", "latency"],
    )

    stored = store.store_resolved_incident(incident)
    incidents = store.list_incidents()

    assert stored.incident_id == "INC-RESOLVED"
    assert any(item.incident_id == "INC-RESOLVED" for item in incidents)


def test_find_similar_uses_keyword_overlap(tmp_path) -> None:
    store = IncidentStore(tmp_path / "incidents.json")

    similar = store.find_similar(
        title="Checkout latency from Redis timeouts",
        service="order-service",
        symptoms=[
            "RedisTimeoutException appeared in logs",
            "Redis connections reached pool limit",
        ],
    )

    assert len(similar) == 3
    assert similar[0].incident_id == "HIST-REDIS-001"
    assert similar[0].similarity_score > similar[1].similarity_score
