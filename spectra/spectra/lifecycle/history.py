"""Lifecycle transition history and audit trail."""

import sqlite3
from datetime import datetime
from typing import Optional

from spectra.lifecycle.models import SpecState, Transition


def record_transition(conn: sqlite3.Connection, transition: Transition) -> None:
    """
    Persist transition to lifecycle_transitions table.

    Args:
        conn: Database connection
        transition: Transition to record
    """
    conn.execute(
        """
        INSERT INTO lifecycle_transitions (spec_id, from_state, to_state, actor, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            transition.spec_id,
            transition.from_state.value,
            transition.to_state.value,
            transition.actor,
            transition.reason,
            transition.timestamp.isoformat(),
        ),
    )
    conn.commit()


def get_history(conn: sqlite3.Connection, spec_id: str) -> list[Transition]:
    """
    Query transition history for a spec.

    Args:
        conn: Database connection
        spec_id: Spec ID

    Returns:
        List of transitions in chronological order
    """
    cursor = conn.execute(
        """
        SELECT spec_id, from_state, to_state, actor, reason, timestamp
        FROM lifecycle_transitions
        WHERE spec_id = ?
        ORDER BY timestamp ASC
        """,
        (spec_id,),
    )

    transitions: list[Transition] = []
    for row in cursor.fetchall():
        transitions.append(
            Transition(
                spec_id=row["spec_id"],
                from_state=SpecState(row["from_state"]),
                to_state=SpecState(row["to_state"]),
                actor=row["actor"],
                reason=row["reason"] or "",
                timestamp=datetime.fromisoformat(row["timestamp"]),
            )
        )

    return transitions


def get_current_state(conn: sqlite3.Connection, spec_id: str) -> Optional[SpecState]:
    """
    Get current lifecycle state from spec record.

    Args:
        conn: Database connection
        spec_id: Spec ID

    Returns:
        Current state or None if spec not found
    """
    cursor = conn.execute(
        "SELECT lifecycle_state FROM specs WHERE id = ?",
        (spec_id,),
    )

    row = cursor.fetchone()
    if row:
        return SpecState(row["lifecycle_state"])
    return None


def get_transition_count(conn: sqlite3.Connection, spec_id: str) -> int:
    """
    Get number of transitions for a spec.

    Args:
        conn: Database connection
        spec_id: Spec ID

    Returns:
        Transition count
    """
    cursor = conn.execute(
        "SELECT COUNT(*) as count FROM lifecycle_transitions WHERE spec_id = ?",
        (spec_id,),
    )
    row = cursor.fetchone()
    return row["count"] if row else 0


def get_time_in_state(conn: sqlite3.Connection, spec_id: str, state: SpecState) -> float:
    """
    Calculate total time spec has spent in a given state (in days).

    Args:
        conn: Database connection
        spec_id: Spec ID
        state: State to measure

    Returns:
        Time in days
    """
    transitions = get_history(conn, spec_id)

    total_seconds = 0.0
    current_state_start: Optional[datetime] = None

    for transition in transitions:
        # Check if entering the target state
        if transition.to_state == state:
            current_state_start = transition.timestamp

        # Check if leaving the target state
        elif transition.from_state == state and current_state_start:
            duration = (transition.timestamp - current_state_start).total_seconds()
            total_seconds += duration
            current_state_start = None

    # If still in the state, count time until now
    if current_state_start:
        duration = (datetime.utcnow() - current_state_start).total_seconds()
        total_seconds += duration

    return total_seconds / 86400  # Convert to days
