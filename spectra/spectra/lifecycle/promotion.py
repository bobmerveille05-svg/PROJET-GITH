"""Spec promotion and demotion with gates."""

import sqlite3
from typing import Any, Optional

from spectra.ceremony.enforcer import CeremonyEnforcer
from spectra.ceremony.models import CeremonyLevel
from spectra.constitution.engine import ConstitutionEngine
from spectra.constitution.schema import ConstitutionConfig
from spectra.core.events import Event, EventBus, EventType
from spectra.core.exceptions import CeremonyError, ConstitutionViolation, LifecycleError
from spectra.lifecycle.models import STATE_CEREMONY_GATES, SpecState, Transition
from spectra.lifecycle.state_machine import LifecycleStateMachine


class LifecyclePromoter:
    """Handles spec promotion and demotion with ceremony and constitution gates."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        event_bus: EventBus,
        ceremony_enforcer: CeremonyEnforcer,
        constitution_engine: ConstitutionEngine,
    ) -> None:
        """
        Initialize promoter.

        Args:
            conn: Database connection
            event_bus: Event bus for notifications
            ceremony_enforcer: Ceremony gate enforcer
            constitution_engine: Constitution rule engine
        """
        self._conn = conn
        self._event_bus = event_bus
        self._ceremony_enforcer = ceremony_enforcer
        self._constitution_engine = constitution_engine

    def promote(
        self,
        spec_id: str,
        spec_data: dict[str, Any],
        actor: str,
        reason: str = "",
        constitution: Optional[ConstitutionConfig] = None,
    ) -> Transition:
        """
        Promote spec to next state in forward progression.

        Args:
            spec_id: Spec ID
            spec_data: Spec metadata
            actor: User or system performing promotion
            reason: Reason for promotion
            constitution: Optional constitution for validation

        Returns:
            Transition record

        Raises:
            LifecycleError: If transition is invalid
            CeremonyError: If ceremony gates not met
            ConstitutionViolation: If constitution rules violated
        """
        current_state_str = spec_data.get("lifecycle_state", "DRAFT")
        current_state = SpecState(current_state_str)

        # Get next state
        state_machine = LifecycleStateMachine(current_state)
        next_state = state_machine.get_next_forward_state()

        if next_state is None:
            raise LifecycleError(
                f"Cannot promote from {current_state.value} - no forward state available"
            )

        # Validate transition
        if not state_machine.can_transition_to(next_state):
            raise LifecycleError(
                f"Invalid transition from {current_state.value} to {next_state.value}"
            )

        # Check ceremony gate
        required_level = STATE_CEREMONY_GATES.get(next_state, 0)
        target_ceremony_level = CeremonyLevel(required_level)

        if not self._ceremony_enforcer.can_proceed(spec_data, target_ceremony_level):
            blockers = self._ceremony_enforcer.get_blockers(spec_data, target_ceremony_level)
            blocker_msgs = [f"- {b.check_name}: {b.details}" for b in blockers]
            raise CeremonyError(
                f"Cannot promote to {next_state.value}: ceremony requirements not met\n"
                + "\n".join(blocker_msgs)
            )

        # Check constitution if provided
        if constitution:
            results = self._constitution_engine.enforce(spec_data, constitution)
            if self._constitution_engine.has_violations(results, constitution.settings.strict_mode):
                violations = self._constitution_engine.get_violations(results)
                violation_msgs = [f"- {v.rule_name}: {v.message}" for v in violations]
                raise ConstitutionViolation(
                    f"Cannot promote to {next_state.value}: constitution violations\n"
                    + "\n".join(violation_msgs)
                )

        # Perform transition
        transition = Transition(
            spec_id=spec_id,
            from_state=current_state,
            to_state=next_state,
            actor=actor,
            reason=reason or f"Promoted to {next_state.value}",
        )

        # Update spec state
        self._conn.execute(
            "UPDATE specs SET lifecycle_state = ? WHERE id = ?",
            (next_state.value, spec_id),
        )

        # Record transition
        self._record_transition(transition)

        # Emit event
        self._event_bus.emit(
            Event(
                event_type=EventType.SPEC_PROMOTED,
                source="lifecycle.promotion",
                payload={
                    "spec_id": spec_id,
                    "from_state": current_state.value,
                    "to_state": next_state.value,
                    "actor": actor,
                },
            )
        )

        self._conn.commit()

        return transition

    def demote(
        self,
        spec_id: str,
        spec_data: dict[str, Any],
        actor: str,
        reason: str,
    ) -> Transition:
        """
        Demote spec to previous state.

        Args:
            spec_id: Spec ID
            spec_data: Spec metadata
            actor: User or system performing demotion
            reason: Reason for demotion (required)

        Returns:
            Transition record

        Raises:
            LifecycleError: If transition is invalid or reason not provided
        """
        if not reason:
            raise LifecycleError("Reason required for demotion")

        current_state_str = spec_data.get("lifecycle_state", "DRAFT")
        current_state = SpecState(current_state_str)

        # Determine previous state (reverse of typical progression)
        previous_state_map: dict[SpecState, SpecState] = {
            SpecState.SPECIFIED: SpecState.DRAFT,
            SpecState.IMPLEMENTING: SpecState.SPECIFIED,
            SpecState.VALIDATING: SpecState.IMPLEMENTING,
            SpecState.COMPLETE: SpecState.VALIDATING,
        }

        previous_state = previous_state_map.get(current_state)
        if previous_state is None:
            raise LifecycleError(
                f"Cannot demote from {current_state.value} - no previous state"
            )

        # Validate transition
        state_machine = LifecycleStateMachine(current_state)
        if not state_machine.can_transition_to(previous_state):
            raise LifecycleError(
                f"Invalid transition from {current_state.value} to {previous_state.value}"
            )

        # Perform transition
        transition = Transition(
            spec_id=spec_id,
            from_state=current_state,
            to_state=previous_state,
            actor=actor,
            reason=reason,
        )

        # Update spec state
        self._conn.execute(
            "UPDATE specs SET lifecycle_state = ? WHERE id = ?",
            (previous_state.value, spec_id),
        )

        # Record transition
        self._record_transition(transition)

        # Emit event
        self._event_bus.emit(
            Event(
                event_type=EventType.SPEC_DEMOTED,
                source="lifecycle.promotion",
                payload={
                    "spec_id": spec_id,
                    "from_state": current_state.value,
                    "to_state": previous_state.value,
                    "actor": actor,
                    "reason": reason,
                },
            )
        )

        self._conn.commit()

        return transition

    def _record_transition(self, transition: Transition) -> None:
        """Record transition to database."""
        self._conn.execute(
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
