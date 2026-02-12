"""Automatic spec validators."""

from spectra.constitution.validators.completeness import validate_spec_completeness
from spectra.constitution.validators.structure import validate_structure_completeness

__all__ = [
    "validate_structure_completeness",
    "validate_spec_completeness",
]
