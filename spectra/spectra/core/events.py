"""Event bus for cross-innovation communication."""

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class EventType(Enum):
    """Types of events in the system."""

    # Spec events
    SPEC_CREATED = "spec_created"
    SPEC_UPDATED = "spec_updated"
    SPEC_DELETED = "spec_deleted"
    SPEC_LINKED = "spec_linked"
    SPEC_UNLINKED = "spec_unlinked"

    # Lifecycle events
    SPEC_PROMOTED = "spec_promoted"
    SPEC_DEMOTED = "spec_demoted"
    STATE_CHANGED = "state_changed"

    # Ceremony events
    CEREMONY_LEVEL_CHANGED = "ceremony_level_changed"
    CEREMONY_CHECK_RUN = "ceremony_check_run"
    CEREMONY_GATE_BLOCKED = "ceremony_gate_blocked"

    # Constitution events
    CONSTITUTION_LOADED = "constitution_loaded"
    CONSTITUTION_VIOLATION = "constitution_violation"
    RULE_EVALUATED = "rule_evaluated"

    # Conflict events (Phase 2)
    CONFLICT_DETECTED = "conflict_detected"
    CONFLICT_RESOLVED = "conflict_resolved"

    # Agent events (Phase 2)
    AGENT_TASK_STARTED = "agent_task_started"
    AGENT_TASK_COMPLETED = "agent_task_completed"
    AGENT_TASK_FAILED = "agent_task_failed"

    # Feedback events (Phase 3)
    FEEDBACK_GENERATED = "feedback_generated"
    FEEDBACK_APPLIED = "feedback_applied"

    # Test events (Phase 3)
    SPEC_TEST_RUN = "spec_test_run"
    SPEC_TEST_PASSED = "spec_test_passed"
    SPEC_TEST_FAILED = "spec_test_failed"

    # Metrics events (Phase 3)
    METRICS_CALCULATED = "metrics_calculated"
    METRIC_THRESHOLD_EXCEEDED = "metric_threshold_exceeded"

    # Drift events (Phase 4)
    DRIFT_DETECTED = "drift_detected"
    DRIFT_RESOLVED = "drift_resolved"

    # Rewind events (Phase 4)
    SNAPSHOT_CREATED = "snapshot_created"
    REWIND_EXECUTED = "rewind_executed"

    # Trust events (Phase 4)
    TRUST_SCORE_UPDATED = "trust_score_updated"
    TRUST_THRESHOLD_CHANGED = "trust_threshold_changed"


@dataclass
class Event:
    """Represents a system event."""

    event_type: EventType
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "source": self.source,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }


EventHandler = Callable[[Event, sqlite3.Connection], None]


class EventBus:
    """
    Synchronous event bus for cross-module communication.

    All events are dispatched immediately to registered handlers
    and persisted to the events table.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        """
        Initialize event bus.

        Args:
            conn: Database connection for event persistence
        """
        self._conn = conn
        self._handlers: dict[EventType, list[EventHandler]] = {}

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Register a handler for an event type.

        Args:
            event_type: Type of event to handle
            handler: Callable that accepts (Event, Connection)
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def emit(self, event: Event) -> None:
        """
        Dispatch event to all subscribers and persist to database.

        Args:
            event: Event to dispatch
        """
        # Persist event
        self._persist_event(event)

        # Dispatch to handlers
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event, self._conn)
            except Exception as e:
                # Log error but don't fail the event dispatch
                print(f"Error in event handler: {e}")

    def _persist_event(self, event: Event) -> None:
        """Save event to events table."""
        try:
            self._conn.execute(
                """
                INSERT INTO events (id, event_type, source, payload, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.event_type.value,
                    event.source,
                    json.dumps(event.payload),
                    event.created_at.isoformat(),
                ),
            )
            self._conn.commit()
        except sqlite3.Error as e:
            print(f"Failed to persist event: {e}")

    def history(
        self, event_type: Optional[EventType] = None, limit: int = 100
    ) -> list[Event]:
        """
        Query persisted events.

        Args:
            event_type: Filter by event type (None for all)
            limit: Maximum number of events to return

        Returns:
            List of events in reverse chronological order
        """
        if event_type is None:
            cursor = self._conn.execute(
                """
                SELECT id, event_type, source, payload, created_at
                FROM events
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
        else:
            cursor = self._conn.execute(
                """
                SELECT id, event_type, source, payload, created_at
                FROM events
                WHERE event_type = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (event_type.value, limit),
            )

        events = []
        for row in cursor.fetchall():
            events.append(
                Event(
                    id=row["id"],
                    event_type=EventType(row["event_type"]),
                    source=row["source"],
                    payload=json.loads(row["payload"]) if row["payload"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            )

        return events
