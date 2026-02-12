"""Dual persistence layer: YAML files + SQLite database."""

import json
import sqlite3
from pathlib import Path
from typing import Optional

import yaml

from spectra.core.exceptions import DatabaseError, GraphError, ValidationError
from spectra.intent_graph.models import Edge, EdgeType, IntentNode
from spectra.intent_graph.parser import extract_links, parse_spec_yaml


class SpecStore:
    """
    Manages dual persistence of specs: YAML files + SQLite index.

    YAML files are the source of truth, SQLite is for fast queries.
    """

    def __init__(self, conn: sqlite3.Connection, specs_dir: Path) -> None:
        """
        Initialize spec store.

        Args:
            conn: Database connection
            specs_dir: Directory for YAML spec files
        """
        self._conn = conn
        self._specs_dir = specs_dir
        self._specs_dir.mkdir(parents=True, exist_ok=True)

    def create_spec(self, node: IntentNode, yaml_content: str) -> None:
        """
        Create a new spec (write YAML + insert into DB).

        Args:
            node: Spec node to create
            yaml_content: YAML content to write

        Raises:
            GraphError: If spec already exists
            DatabaseError: If database insert fails
            ValidationError: If file write fails
        """
        # Check if spec already exists
        cursor = self._conn.execute(
            "SELECT id FROM specs WHERE id = ? OR name = ?", (node.id, node.name)
        )
        if cursor.fetchone():
            raise GraphError(f"Spec already exists: {node.id} or {node.name}")

        # Write YAML file
        yaml_path = self._specs_dir / f"{node.id}.yaml"
        try:
            with open(yaml_path, "w") as f:
                f.write(yaml_content)
        except IOError as e:
            raise ValidationError(f"Failed to write spec file: {e}")

        # Insert into database
        try:
            self._conn.execute(
                """
                INSERT INTO specs (id, name, intent, ceremony_level, lifecycle_state,
                                   trust_score, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node.id,
                    node.name,
                    node.intent,
                    node.ceremony_level,
                    node.lifecycle_state,
                    node.trust_score,
                    json.dumps(node.metadata),
                    node.created_at.isoformat(),
                ),
            )
            self._conn.commit()
        except sqlite3.Error as e:
            # Rollback and delete YAML file
            yaml_path.unlink(missing_ok=True)
            raise DatabaseError(f"Failed to create spec: {e}")

        # Extract and create edges
        edges = extract_links(yaml_content)
        for edge in edges:
            try:
                self.create_edge(edge)
            except Exception:
                # Non-fatal: edge targets might not exist yet
                pass

    def get_spec(self, spec_id: str) -> Optional[IntentNode]:
        """
        Get spec by ID from database.

        Args:
            spec_id: Spec ID

        Returns:
            IntentNode or None if not found
        """
        cursor = self._conn.execute(
            """
            SELECT id, name, intent, ceremony_level, lifecycle_state,
                   trust_score, metadata, created_at
            FROM specs
            WHERE id = ?
            """,
            (spec_id,),
        )
        row = cursor.fetchone()
        if row:
            return IntentNode.from_db_row(row)
        return None

    def get_spec_by_name(self, name: str) -> Optional[IntentNode]:
        """
        Get spec by name from database.

        Args:
            name: Spec name

        Returns:
            IntentNode or None if not found
        """
        cursor = self._conn.execute(
            """
            SELECT id, name, intent, ceremony_level, lifecycle_state,
                   trust_score, metadata, created_at
            FROM specs
            WHERE name = ?
            """,
            (name,),
        )
        row = cursor.fetchone()
        if row:
            return IntentNode.from_db_row(row)
        return None

    def get_spec_yaml(self, spec_id: str) -> str:
        """
        Read YAML file for a spec.

        Args:
            spec_id: Spec ID

        Returns:
            YAML content as string

        Raises:
            GraphError: If spec not found
        """
        yaml_path = self._specs_dir / f"{spec_id}.yaml"
        if not yaml_path.exists():
            raise GraphError(f"Spec file not found: {spec_id}")

        try:
            with open(yaml_path, "r") as f:
                return f.read()
        except IOError as e:
            raise GraphError(f"Failed to read spec file: {e}")

    def update_spec(self, node: IntentNode, yaml_content: str) -> None:
        """
        Update existing spec (update YAML + DB).

        Args:
            node: Updated spec node
            yaml_content: Updated YAML content

        Raises:
            GraphError: If spec not found
            DatabaseError: If update fails
        """
        # Verify spec exists
        if not self.get_spec(node.id):
            raise GraphError(f"Spec not found: {node.id}")

        # Update YAML file
        yaml_path = self._specs_dir / f"{node.id}.yaml"
        try:
            with open(yaml_path, "w") as f:
                f.write(yaml_content)
        except IOError as e:
            raise ValidationError(f"Failed to write spec file: {e}")

        # Update database
        try:
            self._conn.execute(
                """
                UPDATE specs
                SET name = ?, intent = ?, ceremony_level = ?, lifecycle_state = ?,
                    trust_score = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    node.name,
                    node.intent,
                    node.ceremony_level,
                    node.lifecycle_state,
                    node.trust_score,
                    json.dumps(node.metadata),
                    node.id,
                ),
            )
            self._conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update spec: {e}")

        # Rebuild edges
        self._conn.execute("DELETE FROM edges WHERE source_id = ?", (node.id,))
        edges = extract_links(yaml_content)
        for edge in edges:
            try:
                self.create_edge(edge)
            except Exception:
                pass

    def delete_spec(self, spec_id: str) -> None:
        """
        Delete spec (remove YAML + DB record).

        Args:
            spec_id: Spec ID to delete

        Raises:
            GraphError: If spec not found
        """
        # Verify spec exists
        if not self.get_spec(spec_id):
            raise GraphError(f"Spec not found: {spec_id}")

        # Delete YAML file
        yaml_path = self._specs_dir / f"{spec_id}.yaml"
        yaml_path.unlink(missing_ok=True)

        # Delete from database (cascades to edges)
        try:
            self._conn.execute("DELETE FROM specs WHERE id = ?", (spec_id,))
            self._conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to delete spec: {e}")

    def list_specs(
        self,
        state_filter: Optional[str] = None,
        level_filter: Optional[int] = None,
    ) -> list[IntentNode]:
        """
        List all specs with optional filters.

        Args:
            state_filter: Filter by lifecycle state
            level_filter: Filter by ceremony level

        Returns:
            List of IntentNodes
        """
        query = """
            SELECT id, name, intent, ceremony_level, lifecycle_state,
                   trust_score, metadata, created_at
            FROM specs
            WHERE 1=1
        """
        params: list[str | int] = []

        if state_filter:
            query += " AND lifecycle_state = ?"
            params.append(state_filter)

        if level_filter is not None:
            query += " AND ceremony_level = ?"
            params.append(level_filter)

        query += " ORDER BY created_at DESC"

        cursor = self._conn.execute(query, params)
        return [IntentNode.from_db_row(row) for row in cursor.fetchall()]

    def create_edge(self, edge: Edge) -> None:
        """
        Create a graph edge.

        Args:
            edge: Edge to create

        Raises:
            DatabaseError: If edge creation fails
        """
        try:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO edges (source_id, target_id, edge_type, weight)
                VALUES (?, ?, ?, ?)
                """,
                (edge.source_id, edge.target_id, edge.edge_type.value, edge.weight),
            )
            self._conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create edge: {e}")

    def delete_edge(self, source_id: str, target_id: str, edge_type: Optional[EdgeType] = None) -> None:
        """
        Delete a graph edge.

        Args:
            source_id: Source spec ID
            target_id: Target spec ID
            edge_type: Optional edge type filter

        Raises:
            DatabaseError: If deletion fails
        """
        try:
            if edge_type:
                self._conn.execute(
                    "DELETE FROM edges WHERE source_id = ? AND target_id = ? AND edge_type = ?",
                    (source_id, target_id, edge_type.value),
                )
            else:
                self._conn.execute(
                    "DELETE FROM edges WHERE source_id = ? AND target_id = ?",
                    (source_id, target_id),
                )
            self._conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to delete edge: {e}")

    def get_edges(
        self, spec_id: str, direction: str = "outgoing"
    ) -> list[Edge]:
        """
        Get edges for a spec.

        Args:
            spec_id: Spec ID
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of edges
        """
        edges: list[Edge] = []

        if direction in ("outgoing", "both"):
            cursor = self._conn.execute(
                "SELECT source_id, target_id, edge_type, weight FROM edges WHERE source_id = ?",
                (spec_id,),
            )
            edges.extend([Edge.from_db_row(row) for row in cursor.fetchall()])

        if direction in ("incoming", "both"):
            cursor = self._conn.execute(
                "SELECT source_id, target_id, edge_type, weight FROM edges WHERE target_id = ?",
                (spec_id,),
            )
            edges.extend([Edge.from_db_row(row) for row in cursor.fetchall()])

        return edges

    def get_all_edges(self) -> list[Edge]:
        """
        Get all edges in the graph.

        Returns:
            List of all edges
        """
        cursor = self._conn.execute(
            "SELECT source_id, target_id, edge_type, weight FROM edges"
        )
        return [Edge.from_db_row(row) for row in cursor.fetchall()]
