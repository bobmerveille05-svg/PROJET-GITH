"""Graph visualization and output formatting."""

from typing import Optional

import networkx as nx
from rich.table import Table
from rich.tree import Tree

from spectra.intent_graph.models import Edge, IntentNode


def to_ascii_tree(
    graph: nx.DiGraph, root_id: Optional[str] = None, max_depth: int = 5
) -> str:
    """
    Generate terminal-friendly tree representation.

    Args:
        graph: NetworkX graph
        root_id: Root node to start from (None for all roots)
        max_depth: Maximum depth to display

    Returns:
        ASCII tree as string
    """
    if graph.number_of_nodes() == 0:
        return "(empty graph)"

    # Find root nodes (nodes with no incoming edges) if no root specified
    if root_id is None:
        roots = [n for n in graph.nodes() if graph.in_degree(n) == 0]
        if not roots:
            # If there are cycles, just pick the first node
            roots = [list(graph.nodes())[0]]
    else:
        roots = [root_id]

    lines: list[str] = []

    def build_tree(node_id: str, prefix: str = "", depth: int = 0) -> None:
        if depth > max_depth:
            return

        # Get node data
        node_data = graph.nodes.get(node_id, {})
        name = node_data.get("name", node_id)
        state = node_data.get("lifecycle_state", "?")
        level = node_data.get("ceremony_level", "?")

        lines.append(f"{prefix}{name} [{state}, L{level}]")

        # Get children (outgoing edges)
        children = list(graph.successors(node_id))

        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            child_prefix = prefix + ("└── " if is_last else "├── ")
            continuation_prefix = prefix + ("    " if is_last else "│   ")

            # Get edge type
            edge_data = graph.get_edge_data(node_id, child, {})
            edge_type = edge_data.get("edge_type", "")
            edge_label = f" ({edge_type})" if edge_type else ""

            lines.append(f"{child_prefix}{edge_label}")
            build_tree(child, continuation_prefix, depth + 1)

    for root in roots:
        build_tree(root)
        lines.append("")  # Blank line between trees

    return "\n".join(lines)


def to_dot(graph: nx.DiGraph) -> str:
    """
    Generate DOT format for Graphviz rendering.

    Args:
        graph: NetworkX graph

    Returns:
        DOT format string
    """
    lines = ["digraph intent_graph {"]
    lines.append("  rankdir=TB;")
    lines.append("  node [shape=box, style=rounded];")
    lines.append("")

    # Add nodes
    for node_id in graph.nodes():
        node_data = graph.nodes[node_id]
        name = node_data.get("name", node_id)
        state = node_data.get("lifecycle_state", "?")
        level = node_data.get("ceremony_level", "?")

        label = f"{name}\\n[{state}, L{level}]"
        lines.append(f'  "{node_id}" [label="{label}"];')

    lines.append("")

    # Add edges
    for source, target, data in graph.edges(data=True):
        edge_type = data.get("edge_type", "")
        label = edge_type.replace("_", " ").title()
        color = _get_edge_color(edge_type)

        lines.append(
            f'  "{source}" -> "{target}" [label="{label}", color="{color}"];'
        )

    lines.append("}")
    return "\n".join(lines)


def _get_edge_color(edge_type: str) -> str:
    """Get color for edge type."""
    colors = {
        "depends_on": "blue",
        "refines": "green",
        "enables": "purple",
        "conflicts_with": "red",
    }
    return colors.get(edge_type, "black")


def to_rich_table(nodes: list[IntentNode], edges: list[Edge]) -> Table:
    """
    Generate Rich table for terminal display.

    Args:
        nodes: List of spec nodes
        edges: List of graph edges

    Returns:
        Rich Table object
    """
    table = Table(title="Intent Graph")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="bright_white")
    table.add_column("State", style="yellow")
    table.add_column("Level", justify="center")
    table.add_column("Trust", justify="center")
    table.add_column("Dependencies", style="dim")

    # Build dependency map
    dep_map: dict[str, list[str]] = {}
    for edge in edges:
        if edge.edge_type.value == "depends_on":
            if edge.source_id not in dep_map:
                dep_map[edge.source_id] = []
            dep_map[edge.source_id].append(edge.target_id)

    # Add rows
    for node in nodes:
        deps = dep_map.get(node.id, [])
        dep_str = ", ".join(deps[:3])
        if len(deps) > 3:
            dep_str += f" +{len(deps) - 3} more"

        table.add_row(
            node.id[:8],
            node.name,
            node.lifecycle_state,
            str(node.ceremony_level),
            f"{node.trust_score:.1f}",
            dep_str or "-",
        )

    return table


def to_rich_tree(graph: nx.DiGraph, root_id: Optional[str] = None) -> Tree:
    """
    Generate Rich Tree for terminal display.

    Args:
        graph: NetworkX graph
        root_id: Root node to start from (None for all roots)

    Returns:
        Rich Tree object
    """
    if graph.number_of_nodes() == 0:
        tree = Tree("(empty graph)")
        return tree

    # Find root nodes if no root specified
    if root_id is None:
        roots = [n for n in graph.nodes() if graph.in_degree(n) == 0]
        if not roots:
            roots = [list(graph.nodes())[0]]
    else:
        roots = [root_id]

    main_tree = Tree("Intent Graph")

    def build_tree(node_id: str, parent_tree: Tree, visited: set[str]) -> None:
        if node_id in visited:
            return
        visited.add(node_id)

        # Get node data
        node_data = graph.nodes.get(node_id, {})
        name = node_data.get("name", node_id)
        state = node_data.get("lifecycle_state", "?")
        level = node_data.get("ceremony_level", "?")

        label = f"[cyan]{name}[/cyan] [[yellow]{state}[/yellow], L{level}]"
        node_tree = parent_tree.add(label)

        # Get children
        for child in graph.successors(node_id):
            edge_data = graph.get_edge_data(node_id, child, {})
            edge_type = edge_data.get("edge_type", "")

            child_data = graph.nodes.get(child, {})
            child_name = child_data.get("name", child)
            child_state = child_data.get("lifecycle_state", "?")
            child_level = child_data.get("ceremony_level", "?")

            child_label = f"[dim]{edge_type}[/dim] → [cyan]{child_name}[/cyan] [[yellow]{child_state}[/yellow], L{child_level}]"

            if child not in visited:
                child_tree = node_tree.add(child_label)
                build_tree(child, node_tree, visited)
            else:
                # Already visited (cycle or shared dependency)
                node_tree.add(f"{child_label} [dim](seen)[/dim]")

    for root in roots:
        visited: set[str] = set()
        build_tree(root, main_tree, visited)

    return main_tree
