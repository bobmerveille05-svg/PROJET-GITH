"""Spectra - Intent-driven development orchestration system."""

__version__ = "0.1.0"
__author__ = "Spectra Contributors"

from spectra.core.config import SpectraConfig, find_project_root, load_config
from spectra.core.exceptions import SpectraError

__all__ = [
    "__version__",
    "__author__",
    "SpectraConfig",
    "find_project_root",
    "load_config",
    "SpectraError",
]
