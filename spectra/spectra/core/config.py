"""Configuration management for Spectra projects."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from spectra.core.exceptions import ConfigError


@dataclass
class SpectraConfig:
    """Project configuration for Spectra."""

    project_root: Path
    spectra_dir: Path = field(init=False)
    db_path: Path = field(init=False)
    active_constitution_profile: str = "balanced"
    default_ceremony_level: int = 1
    editor: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize derived paths."""
        self.spectra_dir = self.project_root / ".spectra"
        self.db_path = self.spectra_dir / "db" / "spectra.db"

    def to_dict(self) -> dict[str, str | int | None]:
        """Convert config to dictionary for serialization."""
        return {
            "active_constitution_profile": self.active_constitution_profile,
            "default_ceremony_level": self.default_ceremony_level,
            "editor": self.editor,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | int | None], project_root: Path) -> "SpectraConfig":
        """Create config from dictionary."""
        return cls(
            project_root=project_root,
            active_constitution_profile=str(
                data.get("active_constitution_profile", "balanced")
            ),
            default_ceremony_level=int(data.get("default_ceremony_level", 1)),
            editor=data.get("editor") if data.get("editor") else None,
        )


def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Walk up directories looking for .spectra/ directory.

    Args:
        start_path: Directory to start search from (default: current directory)

    Returns:
        Path to project root, or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # Walk up the directory tree
    while True:
        spectra_dir = current / ".spectra"
        if spectra_dir.exists() and spectra_dir.is_dir():
            return current

        parent = current.parent
        if parent == current:
            # Reached filesystem root
            return None

        current = parent


def load_config(project_root: Optional[Path] = None) -> SpectraConfig:
    """
    Load configuration from .spectra/config.yaml.

    Args:
        project_root: Project root directory (will auto-detect if None)

    Returns:
        Loaded configuration

    Raises:
        ConfigError: If project root not found or config is invalid
    """
    if project_root is None:
        project_root = find_project_root()
        if project_root is None:
            raise ConfigError(
                "Not in a Spectra project. Run 'spectra init' to initialize."
            )

    config_path = project_root / ".spectra" / "config.yaml"

    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in config file: {e}")
    except IOError as e:
        raise ConfigError(f"Failed to read config file: {e}")

    return SpectraConfig.from_dict(data, project_root)


def save_config(config: SpectraConfig) -> None:
    """
    Save configuration to .spectra/config.yaml.

    Args:
        config: Configuration to save

    Raises:
        ConfigError: If save fails
    """
    config_path = config.spectra_dir / "config.yaml"

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)
    except IOError as e:
        raise ConfigError(f"Failed to write config file: {e}")


def ensure_project_dirs(project_root: Path) -> None:
    """
    Create all required .spectra/ subdirectories.

    Args:
        project_root: Project root directory
    """
    dirs = [
        project_root / ".spectra",
        project_root / ".spectra" / "specs",
        project_root / ".spectra" / "snapshots",
        project_root / ".spectra" / "db",
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
