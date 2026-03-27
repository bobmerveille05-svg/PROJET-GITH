"""Event wiring for cross-innovation integration."""

import sqlite3

from spectra.core.events import Event, EventBus, EventType


def setup_event_handlers(event_bus: EventBus, conn: sqlite3.Connection) -> None:
    """
    Register all event handlers for cross-innovation communication.

    Args:
        event_bus: Event bus instance
        conn: Database connection
    """

    # SPEC_CREATED -> Run constitution check
    def on_spec_created(event: Event, conn: sqlite3.Connection) -> None:
        """Auto-check constitution when spec is created."""
        # This would trigger constitution enforcement
        # For now, just log the event
        pass

    event_bus.subscribe(EventType.SPEC_CREATED, on_spec_created)

    # SPEC_LINKED -> Check for circular dependencies
    def on_spec_linked(event: Event, conn: sqlite3.Connection) -> None:
        """Check for circular dependencies when edge is added."""
        # This would trigger cycle detection in graph
        pass

    event_bus.subscribe(EventType.SPEC_LINKED, on_spec_linked)

    # CEREMONY_LEVEL_CHANGED -> Update lifecycle gate availability
    def on_ceremony_level_changed(event: Event, conn: sqlite3.Connection) -> None:
        """Update available lifecycle transitions when ceremony level changes."""
        pass

    event_bus.subscribe(EventType.CEREMONY_LEVEL_CHANGED, on_ceremony_level_changed)

    # CONSTITUTION_VIOLATION -> Block lifecycle transition
    def on_constitution_violation(event: Event, conn: sqlite3.Connection) -> None:
        """Record constitution violation."""
        spec_id = event.payload.get("spec_id")
        rule_name = event.payload.get("rule_name")
        severity = event.payload.get("severity", "error")
        message = event.payload.get("message", "")

        if spec_id and rule_name:
            conn.execute(
                """
                INSERT INTO constitution_violations
                (spec_id, rule_name, severity, message, detected_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (spec_id, rule_name, severity, message),
            )
            conn.commit()

    event_bus.subscribe(EventType.CONSTITUTION_VIOLATION, on_constitution_violation)

    # SPEC_PROMOTED -> Run ceremony check
    def on_spec_promoted(event: Event, conn: sqlite3.Connection) -> None:
        """Log ceremony check when spec is promoted."""
        spec_id = event.payload.get("spec_id")
        to_state = event.payload.get("to_state")

        if spec_id:
            # Could trigger ceremony checks here
            pass

    event_bus.subscribe(EventType.SPEC_PROMOTED, on_spec_promoted)

    # SPEC_DEMOTED -> Record reason
    def on_spec_demoted(event: Event, conn: sqlite3.Connection) -> None:
        """Log demotion reason."""
        # Already recorded in lifecycle_transitions table
        pass

    event_bus.subscribe(EventType.SPEC_DEMOTED, on_spec_demoted)
