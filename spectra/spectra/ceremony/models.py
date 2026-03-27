"""Data models for adaptive ceremony."""

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any, Callable, Optional


class CeremonyLevel(IntEnum):
    """Ceremony levels from most flexible to most rigorous."""

    EXPLORE = 0  # Free-form ideation
    SKETCH = 1  # Basic intent defined
    DRAFT = 2  # Structure + initial tests
    SPECIFIED = 3  # Complete spec + review
    VALIDATED = 4  # CI passing + docs
    LOCKED = 5  # Formal approval required


class ChangeCategory(Enum):
    """Categories of change based on risk and scope."""

    PATCH = "patch"  # Tiny fix, minimal risk
    MINOR = "minor"  # Small change, localized impact
    STANDARD = "standard"  # Normal feature or change
    MAJOR = "major"  # Large change, significant impact
    CRITICAL = "critical"  # System-wide, high risk


@dataclass
class CeremonyCheck:
    """Represents a single ceremony requirement check."""

    name: str
    description: str
    required_at_level: CeremonyLevel
    check_fn: Callable[[dict[str, Any]], bool]


@dataclass
class CeremonyResult:
    """Result of running a ceremony check."""

    check_name: str
    passed: bool
    current_level: CeremonyLevel
    details: str = ""

    def __str__(self) -> str:
        """Human-readable result."""
        status = "✓" if self.passed else "✗"
        return f"{status} {self.check_name}: {self.details}"
