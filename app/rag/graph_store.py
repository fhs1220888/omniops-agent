"""Pure Python in-memory Evidence Graph."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

NodeType = Literal["Service", "Metric", "LogPattern", "TraceSpan", "Memory"]
EdgeType = Literal["supports", "caused_by", "related_to"]


class EvidenceGraphNode(BaseModel):
    node_id: str
    node_type: NodeType
    label: str
    metadata: dict[str, str | int | float] = {}


class EvidenceGraphEdge(BaseModel):
    source_id: str
    target_id: str
    edge_type: EdgeType


class EvidenceGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, EvidenceGraphNode] = {}
        self._edges: list[EvidenceGraphEdge] = []

    def add_node(
        self,
        node_id: str,
        node_type: NodeType,
        label: str,
        metadata: dict[str, str | int | float] | None = None,
    ) -> EvidenceGraphNode:
        node = EvidenceGraphNode(
            node_id=node_id,
            node_type=node_type,
            label=label,
            metadata=metadata or {},
        )
        self._nodes[node_id] = node
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
    ) -> EvidenceGraphEdge:
        edge = EvidenceGraphEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
        )
        if edge not in self._edges:
            self._edges.append(edge)
        return edge

    def get_neighbors(self, node_id: str) -> list[EvidenceGraphNode]:
        neighbor_ids = {
            edge.target_id
            for edge in self._edges
            if edge.source_id == node_id and edge.target_id in self._nodes
        }
        neighbor_ids.update(
            edge.source_id
            for edge in self._edges
            if edge.target_id == node_id and edge.source_id in self._nodes
        )
        return [self._nodes[neighbor_id] for neighbor_id in sorted(neighbor_ids)]

    def export_graph(self) -> dict[str, list[dict]]:
        return {
            "nodes": [node.model_dump() for node in self._nodes.values()],
            "edges": [edge.model_dump() for edge in self._edges],
        }
