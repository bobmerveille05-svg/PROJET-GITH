"""Data models for spec lifecycle management."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SpecState(Enum):
    """Lifecycle states for specs."""

    DRAFT = "DRAFT"
    SPECIFIED = "SPECIFIED"
    IMPLEMENTING = "IMPLEMENTING"
    VALIDATING = "VALIDATING"
    COMPLETE = "COMPLETE"
    ARCHIVED = "ARCHIVED"


# Valid state transitions
TRANSITIONS: dict[SpecState, set[SpecState]] = {
    SpecState.DRAFT: {SpecState.SPECIFIED, SpecState.ARCHIVED},
    SpecState.SPECIFIED: {SpecState.IMPLEMENTING, SpecState.DRAFT, SpecState.ARCHIVED},
    SpecState.IMPLEMENTING: {SpecState.VALIDATING, SpecState.SPECIFIED, SpecState.ARCHIVED},
    SpecState.VALIDATING: {SpecState.COMPLETE, SpecState.IMPLEMENTING, SpecState.ARCHIVED},
    SpecState.COMPLETE: {SpecState.ARCHIVED, SpecState.VALIDATING},
    SpecState.ARCHIVED: set(),  # Cannot transition out of archived
}

# Minimum ceremony level required to enter each state
STATE_CEREMONY_GATES: dict[SpecState, int] = {
    SpecState.DRAFT: 0,  # EXPLORE
    SpecState.SPECIFIED: 2,  # DRAFT ceremony level
    SpecState.IMPLEMENTING: 2,  # DRAFT ceremony level
    SpecState.VALIDATING: 3,  # SPECIFIED ceremony level
    SpecState.COMPLETE: 4,  # VALIDATED ceremony level
    SpecState.ARCHIVED: 0,  # No gate for archiving
}


@dataclass
class Transition:
    """Represents a lifecycle state transition."""

    spec_id: str
    from_state: SpecState
    to_state: SpecState
    actor: str
    reason: str = ""
    timestamp: datetime = None

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for serialization."""
        return {
            "spec_id": self.spec_id,
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "actor": self.actor,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }
