"""NetworkX-based graph query engine."""

from typing import Optional

import networkx as nx

from spectra.intent_graph.models import Edge, EdgeType, ImpactReport, IntentNode


class IntentGraphEngine:
    """Graph query and analysis engine using NetworkX."""

    def __init__(self) -> None:
        """Initialize empty graph."""
        self._graph: nx.DiGraph = nx.DiGraph()

    def build_graph(self, nodes: list[IntentNode], edges: list[Edge]) -> nx.DiGraph:
        """
        Construct NetworkX graph from nodes and edges.

        Args:
            nodes: List of spec nodes
            edges: List of graph edges

        Returns:
            NetworkX directed graph
        """
        self._graph = nx.DiGraph()

        # Add nodes with attributes
        for node in nodes:
            self._graph.add_node(
                node.id,
                name=node.name,
                intent=node.intent,
                ceremony_level=node.ceremony_level,
                lifecycle_state=node.lifecycle_state,
                trust_score=node.trust_score,
                metadata=node.metadata,
            )

        # Add edges with attributes
        for edge in edges:
            # Only add edge if both nodes exist
            if edge.source_id in self._graph and edge.target_id in self._graph:
                self._graph.add_edge(
                    edge.source_id,
                    edge.target_id,
                    edge_type=edge.edge_type.value,
                    weight=edge.weight,
                )

        return self._graph

    def get_dependencies(self, spec_id: str, transitive: bool = True) -> list[str]:
        """
        Get upstream dependencies of a spec.

        Args:
            spec_id: Spec ID
            transitive: Include transitive dependencies

        Returns:
            List of dependency spec IDs
        """
        if spec_id not in self._graph:
            return []

        if not transitive:
            # Direct dependencies only (outgoing DEPENDS_ON edges)
            deps = []
            for _, target, data in self._graph.out_edges(spec_id, data=True):
                if data.get("edge_type") == EdgeType.DEPENDS_ON.value:
                    deps.append(target)
            return deps

        # Transitive dependencies using DFS
        deps = set()
        visited = set()

        def dfs(node_id: str) -> None:
            if node_id in visited:
                return
            visited.add(node_id)

            for _, target, data in self._graph.out_edges(node_id, data=True):
                if data.get("edge_type") == EdgeType.DEPENDS_ON.value:
                    deps.add(target)
                    dfs(target)

        dfs(spec_id)
        return list(deps)

    def get_dependents(self, spec_id: str, transitive: bool = True) -> list[str]:
        """
        Get downstream dependents of a spec (who depends on this).

        Args:
            spec_id: Spec ID
            transitive: Include transitive dependents

        Returns:
            List of dependent spec IDs
        """
        if spec_id not in self._graph:
            return []

        if not transitive:
            # Direct dependents only (incoming DEPENDS_ON edges)
            deps = []
            for source, _, data in self._graph.in_edges(spec_id, data=True):
                if data.get("edge_type") == EdgeType.DEPENDS_ON.value:
                    deps.append(source)
            return deps

        # Transitive dependents using reverse DFS
        deps = set()
        visited = set()

        def dfs(node_id: str) -> None:
            if node_id in visited:
                return
            visited.add(node_id)

            for source, _, data in self._graph.in_edges(node_id, data=True):
                if data.get("edge_type") == EdgeType.DEPENDS_ON.value:
                    deps.add(source)
                    dfs(source)

        dfs(spec_id)
        return list(deps)

    def impact_analysis(self, spec_id: str) -> ImpactReport:
        """
        Analyze what specs would be affected by changing this spec.

        Args:
            spec_id: Spec ID to analyze

        Returns:
            Impact analysis report
        """
        direct = self.get_dependents(spec_id, transitive=False)
        transitive = self.get_dependents(spec_id, transitive=True)

        # Remove direct dependents from transitive list
        transitive_only = [dep for dep in transitive if dep not in direct]

        return ImpactReport(
            spec_id=spec_id,
            direct_dependents=direct,
            transitive_dependents=transitive_only,
        )

    def detect_cycles(self) -> list[list[str]]:
        """
        Find circular dependencies in the graph.

        Returns:
            List of cycles, where each cycle is a list of spec IDs
        """
        try:
            cycles = list(nx.simple_cycles(self._graph))
            return cycles
        except Exception:
            return []

    def topological_sort(self) -> list[str]:
        """
        Get specs in topological order (implementation order).

        Returns:
            List of spec IDs in topological order

        Raises:
            ValueError: If graph contains cycles
        """
        try:
            return list(nx.topological_sort(self._graph))
        except nx.NetworkXError as e:
            raise ValueError(f"Cannot sort graph with cycles: {e}")

    def subgraph(self, root_id: str, max_depth: Optional[int] = None) -> nx.DiGraph:
        """
        Extract subgraph starting from root node.

        Args:
            root_id: Root node ID
            max_depth: Maximum depth to traverse (None for unlimited)

        Returns:
            Subgraph as NetworkX DiGraph
        """
        if root_id not in self._graph:
            return nx.DiGraph()

        if max_depth is None:
            # Get all reachable nodes
            reachable = nx.descendants(self._graph, root_id)
            reachable.add(root_id)
            return self._graph.subgraph(reachable).copy()

        # BFS with depth limit
        nodes_at_depth: dict[str, int] = {root_id: 0}
        queue = [(root_id, 0)]
        visited = {root_id}

        while queue:
            node, depth = queue.pop(0)

            if depth >= max_depth:
                continue

            for _, target in self._graph.out_edges(node):
                if target not in visited:
                    visited.add(target)
                    nodes_at_depth[target] = depth + 1
                    queue.append((target, depth + 1))

        return self._graph.subgraph(visited).copy()

    def get_refinement_chain(self, spec_id: str) -> list[str]:
        """
        Get the refinement chain for a spec (following REFINES edges).

        Args:
            spec_id: Spec ID

        Returns:
            List of spec IDs from most abstract to most refined
        """
        chain = [spec_id]
        current = spec_id

        # Follow REFINES edges backwards (incoming)
        while True:
            refined_by = None
            for source, _, data in self._graph.in_edges(current, data=True):
                if data.get("edge_type") == EdgeType.REFINES.value:
                    refined_by = source
                    break

            if refined_by and refined_by not in chain:
                chain.insert(0, refined_by)
                current = refined_by
            else:
                break

        return chain

    def get_enabled_specs(self, spec_id: str) -> list[str]:
        """
        Get specs that would be enabled by completing this spec.

        Args:
            spec_id: Spec ID

        Returns:
            List of enabled spec IDs
        """
        enabled = []
        for _, target, data in self._graph.out_edges(spec_id, data=True):
            if data.get("edge_type") == EdgeType.ENABLES.value:
                enabled.append(target)
        return enabled

    def get_conflicts(self, spec_id: str) -> list[str]:
        """
        Get specs that conflict with this spec.

        Args:
            spec_id: Spec ID

        Returns:
            List of conflicting spec IDs
        """
        conflicts = []

        # Outgoing conflicts
        for _, target, data in self._graph.out_edges(spec_id, data=True):
            if data.get("edge_type") == EdgeType.CONFLICTS_WITH.value:
                conflicts.append(target)

        # Incoming conflicts (bidirectional relationship)
        for source, _, data in self._graph.in_edges(spec_id, data=True):
            if data.get("edge_type") == EdgeType.CONFLICTS_WITH.value:
                conflicts.append(source)

        return list(set(conflicts))

    def get_graph_stats(self) -> dict[str, int]:
        """
        Get graph statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "total_nodes": self._graph.number_of_nodes(),
            "total_edges": self._graph.number_of_edges(),
            "connected_components": nx.number_weakly_connected_components(self._graph),
            "has_cycles": len(self.detect_cycles()) > 0,
        }
