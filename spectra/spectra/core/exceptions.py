"""Exception hierarchy for Spectra."""


class SpectraError(Exception):
    """Base exception for all Spectra errors."""

    pass


class ConfigError(SpectraError):
    """Raised when there are configuration issues."""

    pass


class DatabaseError(SpectraError):
    """Raised when SQLite operations fail."""

    pass


class ValidationError(SpectraError):
    """Raised when model or schema validation fails."""

    pass


class LifecycleError(SpectraError):
    """Raised when invalid state transitions are attempted."""

    pass


class CeremonyError(SpectraError):
    """Raised when ceremony gate violations occur."""

    pass


class ConstitutionViolation(SpectraError):
    """Raised when rule enforcement fails."""

    pass


class ConflictError(SpectraError):
    """Raised when semantic conflict issues are detected."""

    pass


class GraphError(SpectraError):
    """Raised when intent graph operations fail."""

    pass
