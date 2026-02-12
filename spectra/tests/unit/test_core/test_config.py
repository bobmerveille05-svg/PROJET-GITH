"""Tests for core configuration."""

import tempfile
from pathlib import Path

import pytest

from spectra.core.config import (
    SpectraConfig,
    ensure_project_dirs,
    find_project_root,
    load_config,
    save_config,
)
from spectra.core.exceptions import ConfigError


def test_spectra_config_initialization():
    """Test SpectraConfig initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        config = SpectraConfig(project_root=project_root)

        assert config.project_root == project_root
        assert config.spectra_dir == project_root / ".spectra"
        assert config.db_path == project_root / ".spectra" / "db" / "spectra.db"
        assert config.active_constitution_profile == "balanced"
        assert config.default_ceremony_level == 1


def test_ensure_project_dirs():
    """Test directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        ensure_project_dirs(project_root)

        assert (project_root / ".spectra").exists()
        assert (project_root / ".spectra" / "specs").exists()
        assert (project_root / ".spectra" / "snapshots").exists()
        assert (project_root / ".spectra" / "db").exists()


def test_save_and_load_config():
    """Test config persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        ensure_project_dirs(project_root)

        # Create and save config
        config = SpectraConfig(project_root=project_root)
        config.active_constitution_profile = "strict"
        config.default_ceremony_level = 3
        save_config(config)

        # Load and verify
        loaded_config = load_config(project_root)
        assert loaded_config.active_constitution_profile == "strict"
        assert loaded_config.default_ceremony_level == 3


def test_find_project_root():
    """Test project root detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        ensure_project_dirs(project_root)

        # Should find root from subdirectory
        subdir = project_root / "subdir" / "nested"
        subdir.mkdir(parents=True)

        found_root = find_project_root(subdir)
        assert found_root == project_root


def test_find_project_root_not_found():
    """Test project root detection when not in a project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_project_dir = Path(tmpdir)
        found_root = find_project_root(non_project_dir)
        assert found_root is None


def test_load_config_not_found():
    """Test loading config when not in a project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_project_dir = Path(tmpdir)
        with pytest.raises(ConfigError, match="Not in a Spectra project"):
            load_config(non_project_dir)
