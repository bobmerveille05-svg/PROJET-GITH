"""SQLite database management and schema migrations."""

import sqlite3
from pathlib import Path
from typing import Any, Optional

from spectra.core.exceptions import DatabaseError

# Database schema version
SCHEMA_VERSION = 1


def get_connection(db_path: Path) -> sqlite3.Connection:
    """
    Create or return SQLite connection with proper settings.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Database connection

    Raises:
        DatabaseError: If connection fails
    """
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))

        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys=ON")

        # Set row factory for dict-like access
        conn.row_factory = sqlite3.Row

        return conn
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to connect to database: {e}")


def run_migrations(conn: sqlite3.Connection) -> None:
    """
    Create all tables from schema (forward-compatible for all phases).

    Args:
        conn: Database connection

    Raises:
        DatabaseError: If migration fails
    """
    try:
        # Create schema version table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Check current schema version
        cursor = conn.execute("SELECT MAX(version) FROM schema_version")
        current_version = cursor.fetchone()[0]

        if current_version is not None and current_version >= SCHEMA_VERSION:
            return  # Already up to date

        # Specs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS specs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                intent TEXT NOT NULL,
                ceremony_level INTEGER NOT NULL DEFAULT 0,
                lifecycle_state TEXT NOT NULL DEFAULT 'DRAFT',
                trust_score REAL DEFAULT 0.5,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Edges table for graph relationships
        conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                edge_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source_id, target_id, edge_type),
                FOREIGN KEY (source_id) REFERENCES specs(id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES specs(id) ON DELETE CASCADE
            )
        """)

        # Lifecycle transitions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lifecycle_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spec_id TEXT NOT NULL,
                from_state TEXT NOT NULL,
                to_state TEXT NOT NULL,
                actor TEXT,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spec_id) REFERENCES specs(id) ON DELETE CASCADE
            )
        """)

        # Events table for event bus persistence
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                payload TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Ceremony checks table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ceremony_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spec_id TEXT NOT NULL,
                check_name TEXT NOT NULL,
                passed BOOLEAN NOT NULL,
                details TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spec_id) REFERENCES specs(id) ON DELETE CASCADE
            )
        """)

        # Constitution violations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS constitution_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spec_id TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT,
                details TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spec_id) REFERENCES specs(id) ON DELETE CASCADE
            )
        """)

        # Conflicts table (Phase 2)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conflicts (
                id TEXT PRIMARY KEY,
                spec_a_id TEXT NOT NULL,
                spec_b_id TEXT NOT NULL,
                conflict_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (spec_a_id) REFERENCES specs(id) ON DELETE CASCADE,
                FOREIGN KEY (spec_b_id) REFERENCES specs(id) ON DELETE CASCADE
            )
        """)

        # Agent tasks table (Phase 2)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_tasks (
                id TEXT PRIMARY KEY,
                spec_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                input_data TEXT,
                output_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (spec_id) REFERENCES specs(id) ON DELETE CASCADE
            )
        """)

        # Feedback loops table (Phase 3)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback_loops (
                id TEXT PRIMARY KEY,
                spec_id TEXT NOT NULL,
                loop_type TEXT NOT NULL,
                observation TEXT,
                recommendation TEXT,
                applied BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spec_id) REFERENCES specs(id) ON DELETE CASCADE
            )
        """)

        # Spec test results table (Phase 3)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS spec_test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spec_id TEXT NOT NULL,
                test_name TEXT NOT NULL,
                passed BOOLEAN NOT NULL,
                output TEXT,
                run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spec_id) REFERENCES specs(id) ON DELETE CASCADE
            )
        """)

        # Metrics snapshots table (Phase 3)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spec_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spec_id) REFERENCES specs(id) ON DELETE CASCADE
            )
        """)

        # Drift detections table (Phase 4)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS drift_detections (
                id TEXT PRIMARY KEY,
                spec_id TEXT NOT NULL,
                drift_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spec_id) REFERENCES specs(id) ON DELETE CASCADE
            )
        """)

        # Snapshots table for temporal rewind (Phase 4)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id TEXT PRIMARY KEY,
                spec_id TEXT NOT NULL,
                snapshot_data TEXT NOT NULL,
                snapshot_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spec_id) REFERENCES specs(id) ON DELETE CASCADE
            )
        """)

        # Trust score history table (Phase 4)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trust_score_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spec_id TEXT NOT NULL,
                trust_score REAL NOT NULL,
                factors TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spec_id) REFERENCES specs(id) ON DELETE CASCADE
            )
        """)

        # Create indexes for performance
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_specs_name ON specs(name)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_specs_state ON specs(lifecycle_state)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_specs_ceremony ON specs(ceremony_level)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_lifecycle_spec ON lifecycle_transitions(spec_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_conflicts_specs ON conflicts(spec_a_id, spec_b_id)"
        )

        # Record schema version
        conn.execute(
            "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
            (SCHEMA_VERSION,),
        )

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Migration failed: {e}")


def execute_query(
    conn: sqlite3.Connection,
    sql: str,
    params: Optional[tuple[Any, ...]] = None,
) -> sqlite3.Cursor:
    """
    Execute SQL query with error handling.

    Args:
        conn: Database connection
        sql: SQL query string
        params: Query parameters

    Returns:
        Query cursor

    Raises:
        DatabaseError: If query fails
    """
    try:
        if params is None:
            return conn.execute(sql)
        else:
            return conn.execute(sql, params)
    except sqlite3.Error as e:
        raise DatabaseError(f"Query execution failed: {e}")
