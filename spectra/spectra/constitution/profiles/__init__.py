"""Built-in constitution profiles."""

from spectra.constitution.profiles.balanced import get_balanced_constitution
from spectra.constitution.profiles.rapid import get_rapid_constitution
from spectra.constitution.profiles.strict import get_strict_constitution

__all__ = [
    "get_strict_constitution",
    "get_balanced_constitution",
    "get_rapid_constitution",
]
