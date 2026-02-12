"""Tests for lifecycle state machine."""

import pytest

from spectra.core.exceptions import LifecycleError
from spectra.lifecycle.models import TRANSITIONS, SpecState
from spectra.lifecycle.state_machine import (
    LifecycleStateMachine,
    get_available_transitions,
    validate_transition,
)


class TestValidateTransition:
    """Test transition validation logic."""

    def test_valid_transition_draft_to_specified(self):
        """DRAFT can transition to SPECIFIED."""
        assert validate_transition(SpecState.DRAFT, SpecState.SPECIFIED) is True

    def test_valid_transition_specified_to_implementing(self):
        """SPECIFIED can transition to IMPLEMENTING."""
        assert validate_transition(SpecState.SPECIFIED, SpecState.IMPLEMENTING) is True

    def test_valid_transition_implementing_to_validating(self):
        """IMPLEMENTING can transition to VALIDATING."""
        assert validate_transition(SpecState.IMPLEMENTING, SpecState.VALIDATING) is True

    def test_valid_transition_validating_to_complete(self):
        """VALIDATING can transition to COMPLETE."""
        assert validate_transition(SpecState.VALIDATING, SpecState.COMPLETE) is True

    def test_valid_transition_any_to_archived(self):
        """Any state can transition to ARCHIVED."""
        for state in SpecState:
            if state != SpecState.ARCHIVED:
                assert validate_transition(state, SpecState.ARCHIVED) is True

    def test_invalid_transition_draft_to_implementing(self):
        """DRAFT cannot skip to IMPLEMENTING."""
        assert validate_transition(SpecState.DRAFT, SpecState.IMPLEMENTING) is False

    def test_invalid_transition_draft_to_complete(self):
        """DRAFT cannot jump to COMPLETE."""
        assert validate_transition(SpecState.DRAFT, SpecState.COMPLETE) is False

    def test_invalid_transition_from_archived(self):
        """Cannot transition out of ARCHIVED state."""
        assert validate_transition(SpecState.ARCHIVED, SpecState.DRAFT) is False
        assert validate_transition(SpecState.ARCHIVED, SpecState.SPECIFIED) is False
        assert validate_transition(SpecState.ARCHIVED, SpecState.COMPLETE) is False

    def test_backward_transition_specified_to_draft(self):
        """Can demote from SPECIFIED back to DRAFT."""
        assert validate_transition(SpecState.SPECIFIED, SpecState.DRAFT) is True

    def test_backward_transition_implementing_to_specified(self):
        """Can demote from IMPLEMENTING back to SPECIFIED."""
        assert validate_transition(SpecState.IMPLEMENTING, SpecState.SPECIFIED) is True

    def test_backward_transition_validating_to_implementing(self):
        """Can demote from VALIDATING back to IMPLEMENTING."""
        assert validate_transition(SpecState.VALIDATING, SpecState.IMPLEMENTING) is True

    def test_backward_transition_complete_to_validating(self):
        """Can demote from COMPLETE back to VALIDATING."""
        assert validate_transition(SpecState.COMPLETE, SpecState.VALIDATING) is True


class TestGetAvailableTransitions:
    """Test getting available transitions."""

    def test_draft_available_transitions(self):
        """DRAFT can go to SPECIFIED or ARCHIVED."""
        available = get_available_transitions(SpecState.DRAFT)
        assert SpecState.SPECIFIED in available
        assert SpecState.ARCHIVED in available
        assert len(available) == 2

    def test_specified_available_transitions(self):
        """SPECIFIED can go to IMPLEMENTING, DRAFT, or ARCHIVED."""
        available = get_available_transitions(SpecState.SPECIFIED)
        assert SpecState.IMPLEMENTING in available
        assert SpecState.DRAFT in available
        assert SpecState.ARCHIVED in available
        assert len(available) == 3

    def test_archived_has_no_transitions(self):
        """ARCHIVED state has no outgoing transitions."""
        available = get_available_transitions(SpecState.ARCHIVED)
        assert len(available) == 0


class TestLifecycleStateMachine:
    """Test state machine class."""

    def test_initialization(self):
        """State machine initializes with given state."""
        sm = LifecycleStateMachine(SpecState.DRAFT)
        assert sm.current_state == SpecState.DRAFT

    def test_can_transition_to_valid_state(self):
        """Can transition to valid target state."""
        sm = LifecycleStateMachine(SpecState.DRAFT)
        assert sm.can_transition_to(SpecState.SPECIFIED) is True

    def test_cannot_transition_to_invalid_state(self):
        """Cannot transition to invalid target state."""
        sm = LifecycleStateMachine(SpecState.DRAFT)
        assert sm.can_transition_to(SpecState.IMPLEMENTING) is False

    def test_get_next_states(self):
        """Get all valid next states."""
        sm = LifecycleStateMachine(SpecState.DRAFT)
        next_states = sm.get_next_states()
        assert SpecState.SPECIFIED in next_states
        assert SpecState.ARCHIVED in next_states

    def test_successful_transition(self):
        """Transition updates current state."""
        sm = LifecycleStateMachine(SpecState.DRAFT)
        sm.transition(SpecState.SPECIFIED)
        assert sm.current_state == SpecState.SPECIFIED

    def test_invalid_transition_raises_error(self):
        """Invalid transition raises LifecycleError."""
        sm = LifecycleStateMachine(SpecState.DRAFT)
        with pytest.raises(LifecycleError, match="Cannot transition from DRAFT to IMPLEMENTING"):
            sm.transition(SpecState.IMPLEMENTING)

    def test_multiple_transitions(self):
        """Can chain multiple valid transitions."""
        sm = LifecycleStateMachine(SpecState.DRAFT)
        sm.transition(SpecState.SPECIFIED)
        sm.transition(SpecState.IMPLEMENTING)
        sm.transition(SpecState.VALIDATING)
        sm.transition(SpecState.COMPLETE)
        assert sm.current_state == SpecState.COMPLETE

    def test_transition_to_archived_is_final(self):
        """Transitioning to ARCHIVED is irreversible."""
        sm = LifecycleStateMachine(SpecState.COMPLETE)
        sm.transition(SpecState.ARCHIVED)
        assert sm.current_state == SpecState.ARCHIVED

        # Cannot transition out
        with pytest.raises(LifecycleError):
            sm.transition(SpecState.DRAFT)

    def test_get_forward_path_from_draft(self):
        """Forward path from DRAFT shows typical progression."""
        sm = LifecycleStateMachine(SpecState.DRAFT)
        path = sm.get_forward_path()
        assert path == [
            SpecState.SPECIFIED,
            SpecState.IMPLEMENTING,
            SpecState.VALIDATING,
            SpecState.COMPLETE,
        ]

    def test_get_forward_path_from_implementing(self):
        """Forward path from IMPLEMENTING shows remaining states."""
        sm = LifecycleStateMachine(SpecState.IMPLEMENTING)
        path = sm.get_forward_path()
        assert path == [SpecState.VALIDATING, SpecState.COMPLETE]

    def test_get_forward_path_from_complete(self):
        """Forward path from COMPLETE is empty."""
        sm = LifecycleStateMachine(SpecState.COMPLETE)
        path = sm.get_forward_path()
        assert path == []

    def test_get_next_forward_state(self):
        """Get immediate next state in forward progression."""
        sm = LifecycleStateMachine(SpecState.DRAFT)
        next_state = sm.get_next_forward_state()
        assert next_state == SpecState.SPECIFIED

    def test_get_next_forward_state_at_end(self):
        """Get next forward state returns None at end."""
        sm = LifecycleStateMachine(SpecState.COMPLETE)
        next_state = sm.get_next_forward_state()
        assert next_state is None


class TestTransitionSymmetry:
    """Test that transitions are properly defined and symmetric where appropriate."""

    def test_all_states_have_transition_definitions(self):
        """Every state has an entry in TRANSITIONS."""
        for state in SpecState:
            assert state in TRANSITIONS

    def test_forward_and_backward_transitions_match(self):
        """If A->B is valid, B->A might be valid (demotion)."""
        # SPECIFIED -> IMPLEMENTING is valid
        assert validate_transition(SpecState.SPECIFIED, SpecState.IMPLEMENTING)
        # IMPLEMENTING -> SPECIFIED is valid (demotion)
        assert validate_transition(SpecState.IMPLEMENTING, SpecState.SPECIFIED)

    def test_archived_state_is_terminal(self):
        """ARCHIVED state has empty transitions set."""
        assert TRANSITIONS[SpecState.ARCHIVED] == set()

    def test_no_self_transitions(self):
        """States cannot transition to themselves."""
        for state in SpecState:
            assert state not in TRANSITIONS[state]
