from app.rag.graph_store import EvidenceGraph


def test_evidence_graph_node_insertion() -> None:
    graph = EvidenceGraph()

    node = graph.add_node("service:order-service", "Service", "order-service")

    exported = graph.export_graph()
    assert node.node_id == "service:order-service"
    assert exported["nodes"][0]["node_type"] == "Service"


def test_evidence_graph_edge_insertion_and_neighbor_lookup() -> None:
    graph = EvidenceGraph()
    graph.add_node("log:redis-timeout", "LogPattern", "RedisTimeoutException")
    graph.add_node("hypothesis:redis", "LogPattern", "redis_pool_exhaustion")
    graph.add_edge("log:redis-timeout", "hypothesis:redis", "supports")

    neighbors = graph.get_neighbors("log:redis-timeout")
    exported = graph.export_graph()

    assert [node.node_id for node in neighbors] == ["hypothesis:redis"]
    assert exported["edges"] == [
        {
            "source_id": "log:redis-timeout",
            "target_id": "hypothesis:redis",
            "edge_type": "supports",
        }
    ]
