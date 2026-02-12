"""Delta absorption for intent graph changes."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

import networkx as nx


class ChangeType(Enum):
    """Types of changes in the graph."""

    NODE_ADDED = "node_added"
    NODE_REMOVED = "node_removed"
    NODE_MODIFIED = "node_modified"
    EDGE_ADDED = "edge_added"
    EDGE_REMOVED = "edge_removed"


@dataclass
class Change:
    """Represents a change between two graph states."""

    change_type: ChangeType
    entity: str  # "node" or "edge"
    details: dict[str, Any]

    def __str__(self) -> str:
        """Human-readable change description."""
        if self.entity == "node":
            node_id = self.details.get("id", "unknown")
            if self.change_type == ChangeType.NODE_ADDED:
                return f"Added spec: {node_id}"
            elif self.change_type == ChangeType.NODE_REMOVED:
                return f"Removed spec: {node_id}"
            elif self.change_type == ChangeType.NODE_MODIFIED:
                return f"Modified spec: {node_id}"
        elif self.entity == "edge":
            source = self.details.get("source", "?")
            target = self.details.get("target", "?")
            edge_type = self.details.get("edge_type", "?")
            if self.change_type == ChangeType.EDGE_ADDED:
                return f"Added edge: {source} -> {target} ({edge_type})"
            elif self.change_type == ChangeType.EDGE_REMOVED:
                return f"Removed edge: {source} -> {target} ({edge_type})"
        return f"{self.change_type.value}: {self.details}"


def absorb_changes(old_graph: nx.DiGraph, new_graph: nx.DiGraph) -> list[Change]:
    """
    Detect changes between two graph states.

    Args:
        old_graph: Previous graph state
        new_graph: New graph state

    Returns:
        List of changes detected
    """
    changes: list[Change] = []

    old_nodes = set(old_graph.nodes())
    new_nodes = set(new_graph.nodes())

    # Detect node changes
    added_nodes = new_nodes - old_nodes
    removed_nodes = old_nodes - new_nodes
    common_nodes = old_nodes & new_nodes

    for node_id in added_nodes:
        changes.append(
            Change(
                change_type=ChangeType.NODE_ADDED,
                entity="node",
                details={"id": node_id, **dict(new_graph.nodes[node_id])},
            )
        )

    for node_id in removed_nodes:
        changes.append(
            Change(
                change_type=ChangeType.NODE_REMOVED,
                entity="node",
                details={"id": node_id, **dict(old_graph.nodes[node_id])},
            )
        )

    # Check for modified nodes
    for node_id in common_nodes:
        old_attrs = dict(old_graph.nodes[node_id])
        new_attrs = dict(new_graph.nodes[node_id])

        if old_attrs != new_attrs:
            # Find what changed
            modified_fields = {}
            for key in set(old_attrs.keys()) | set(new_attrs.keys()):
                old_val = old_attrs.get(key)
                new_val = new_attrs.get(key)
                if old_val != new_val:
                    modified_fields[key] = {"old": old_val, "new": new_val}

            changes.append(
                Change(
                    change_type=ChangeType.NODE_MODIFIED,
                    entity="node",
                    details={"id": node_id, "modified_fields": modified_fields},
                )
            )

    # Detect edge changes
    old_edges = set(old_graph.edges(data=True))
    new_edges = set(new_graph.edges(data=True))

    # Convert to comparable format (source, target, edge_type)
    def edge_key(edge: tuple[str, str, dict[str, Any]]) -> tuple[str, str, str]:
        return (edge[0], edge[1], edge[2].get("edge_type", ""))

    old_edge_keys = {edge_key(e): e for e in old_edges}
    new_edge_keys = {edge_key(e): e for e in new_edges}

    added_edge_keys = set(new_edge_keys.keys()) - set(old_edge_keys.keys())
    removed_edge_keys = set(old_edge_keys.keys()) - set(new_edge_keys.keys())

    for edge_key_tuple in added_edge_keys:
        edge = new_edge_keys[edge_key_tuple]
        changes.append(
            Change(
                change_type=ChangeType.EDGE_ADDED,
                entity="edge",
                details={
                    "source": edge[0],
                    "target": edge[1],
                    "edge_type": edge[2].get("edge_type", "unknown"),
                    "weight": edge[2].get("weight", 1.0),
                },
            )
        )

    for edge_key_tuple in removed_edge_keys:
        edge = old_edge_keys[edge_key_tuple]
        changes.append(
            Change(
                change_type=ChangeType.EDGE_REMOVED,
                entity="edge",
                details={
                    "source": edge[0],
                    "target": edge[1],
                    "edge_type": edge[2].get("edge_type", "unknown"),
                    "weight": edge[2].get("weight", 1.0),
                },
            )
        )

    return changes


def summarize_changes(changes: list[Change]) -> dict[str, int]:
    """
    Summarize changes by type.

    Args:
        changes: List of changes

    Returns:
        Dictionary mapping change type to count
    """
    summary: dict[str, int] = {}
    for change in changes:
        key = change.change_type.value
        summary[key] = summary.get(key, 0) + 1
    return summary
