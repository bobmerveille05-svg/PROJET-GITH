"""Tests for event bus."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from spectra.core.database import get_connection, run_migrations
from spectra.core.events import Event, EventBus, EventType


@pytest.fixture
def db_conn():
    """Create temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = get_connection(db_path)
        run_migrations(conn)
        yield conn
        conn.close()


def test_event_creation():
    """Test Event creation."""
    event = Event(
        event_type=EventType.SPEC_CREATED,
        source="test",
        payload={"spec_id": "test-123"},
    )

    assert event.event_type == EventType.SPEC_CREATED
    assert event.source == "test"
    assert event.payload["spec_id"] == "test-123"
    assert event.id is not None
    assert event.created_at is not None


def test_event_bus_subscribe_and_emit(db_conn):
    """Test subscribing to and emitting events."""
    event_bus = EventBus(db_conn)
    handler_called = []

    def test_handler(event: Event, conn: sqlite3.Connection) -> None:
        handler_called.append(event.event_type)

    event_bus.subscribe(EventType.SPEC_CREATED, test_handler)

    event = Event(
        event_type=EventType.SPEC_CREATED,
        source="test",
        payload={"spec_id": "test-123"},
    )

    event_bus.emit(event)

    assert EventType.SPEC_CREATED in handler_called


def test_event_bus_history(db_conn):
    """Test querying event history."""
    event_bus = EventBus(db_conn)

    # Emit some events
    for i in range(3):
        event = Event(
            event_type=EventType.SPEC_CREATED,
            source="test",
            payload={"spec_id": f"test-{i}"},
        )
        event_bus.emit(event)

    # Query history
    history = event_bus.history(EventType.SPEC_CREATED, limit=10)

    assert len(history) == 3
    assert all(e.event_type == EventType.SPEC_CREATED for e in history)


def test_event_bus_multiple_handlers(db_conn):
    """Test multiple handlers for same event."""
    event_bus = EventBus(db_conn)
    handler1_called = []
    handler2_called = []

    def handler1(event: Event, conn: sqlite3.Connection) -> None:
        handler1_called.append(True)

    def handler2(event: Event, conn: sqlite3.Connection) -> None:
        handler2_called.append(True)

    event_bus.subscribe(EventType.SPEC_CREATED, handler1)
    event_bus.subscribe(EventType.SPEC_CREATED, handler2)

    event = Event(
        event_type=EventType.SPEC_CREATED,
        source="test",
    )
    event_bus.emit(event)

    assert len(handler1_called) == 1
    assert len(handler2_called) == 1
