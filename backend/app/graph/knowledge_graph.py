from __future__ import annotations

from typing import Any

import networkx as nx


class ComplianceKnowledgeGraph:
    def __init__(self) -> None:
        self.graph = nx.MultiDiGraph()

    def add_entity(self, entity_id: str, entity_type: str, **attrs: Any) -> None:
        self.graph.add_node(entity_id, entity_type=entity_type, **attrs)

    def add_relation(self, source: str, target: str, relation: str, **attrs: Any) -> None:
        self.graph.add_edge(source, target, relation=relation, **attrs)

    def detect_high_risk_paths(self) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for u, v, data in self.graph.edges(data=True):
            if data.get("relation") in {"transfers_to_third_country", "stores_sensitive_data"}:
                findings.append({"source": u, "target": v, "relation": data.get("relation"), "risk": "High"})
        return findings

    def to_visual_payload(self) -> dict[str, list[dict[str, Any]]]:
        nodes = [{"id": node, **attrs} for node, attrs in self.graph.nodes(data=True)]
        edges = [{"source": u, "target": v, **data} for u, v, data in self.graph.edges(data=True)]
        return {"nodes": nodes, "edges": edges}
