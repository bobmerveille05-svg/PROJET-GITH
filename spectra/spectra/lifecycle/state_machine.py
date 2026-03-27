"""State machine for lifecycle transitions."""

from typing import Optional

from spectra.core.exceptions import LifecycleError
from spectra.lifecycle.models import TRANSITIONS, SpecState


def validate_transition(current_state: SpecState, target_state: SpecState) -> bool:
    """
    Check if a state transition is valid.

    Args:
        current_state: Current lifecycle state
        target_state: Target lifecycle state

    Returns:
        True if transition is allowed
    """
    allowed_transitions = TRANSITIONS.get(current_state, set())
    return target_state in allowed_transitions


def get_available_transitions(current_state: SpecState) -> set[SpecState]:
    """
    Get available target states from current state.

    Args:
        current_state: Current lifecycle state

    Returns:
        Set of valid target states
    """
    return TRANSITIONS.get(current_state, set())


class LifecycleStateMachine:
    """Wraps lifecycle transition logic with validation."""

    def __init__(self, current_state: SpecState) -> None:
        """
        Initialize state machine.

        Args:
            current_state: Initial state
        """
        self._current_state = current_state

    @property
    def current_state(self) -> SpecState:
        """Get current state."""
        return self._current_state

    def can_transition_to(self, target_state: SpecState) -> bool:
        """
        Check if transition to target state is allowed.

        Args:
            target_state: Target state

        Returns:
            True if transition is valid
        """
        return validate_transition(self._current_state, target_state)

    def get_next_states(self) -> set[SpecState]:
        """
        Get all valid next states.

        Returns:
            Set of possible target states
        """
        return get_available_transitions(self._current_state)

    def transition(self, target_state: SpecState) -> None:
        """
        Perform state transition.

        Args:
            target_state: State to transition to

        Raises:
            LifecycleError: If transition is invalid
        """
        if not self.can_transition_to(target_state):
            raise LifecycleError(
                f"Cannot transition from {self._current_state.value} to {target_state.value}"
            )

        self._current_state = target_state

    def get_forward_path(self) -> list[SpecState]:
        """
        Get typical forward progression path from current state.

        Returns:
            List of states in forward order
        """
        # Define typical forward paths
        forward_paths: dict[SpecState, list[SpecState]] = {
            SpecState.DRAFT: [SpecState.SPECIFIED, SpecState.IMPLEMENTING, SpecState.VALIDATING, SpecState.COMPLETE],
            SpecState.SPECIFIED: [SpecState.IMPLEMENTING, SpecState.VALIDATING, SpecState.COMPLETE],
            SpecState.IMPLEMENTING: [SpecState.VALIDATING, SpecState.COMPLETE],
            SpecState.VALIDATING: [SpecState.COMPLETE],
            SpecState.COMPLETE: [],
            SpecState.ARCHIVED: [],
        }

        return forward_paths.get(self._current_state, [])

    def get_next_forward_state(self) -> Optional[SpecState]:
        """
        Get the next state in typical forward progression.

        Returns:
            Next state or None if at end
        """
        path = self.get_forward_path()
        return path[0] if path else None
