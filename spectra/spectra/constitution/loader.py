"""Constitution file loading and merging."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError as PydanticValidationError

from spectra.constitution.schema import ConstitutionConfig
from spectra.core.exceptions import ConfigError, ValidationError


def load_constitution(path: Path) -> ConstitutionConfig:
    """
    Load constitution from YAML file.

    Args:
        path: Path to constitution YAML file

    Returns:
        Parsed constitution config

    Raises:
        ValidationError: If YAML is invalid or doesn't match schema
    """
    if not path.exists():
        raise ValidationError(f"Constitution file not found: {path}")

    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML in constitution file: {e}")
    except IOError as e:
        raise ValidationError(f"Failed to read constitution file: {e}")

    if not isinstance(data, dict):
        raise ValidationError("Constitution file must contain a dictionary")

    try:
        return ConstitutionConfig(**data)
    except PydanticValidationError as e:
        raise ValidationError(f"Constitution schema validation failed: {e}")


def merge_constitutions(
    base: ConstitutionConfig, overlay: ConstitutionConfig
) -> ConstitutionConfig:
    """
    Merge two constitutions, with overlay taking precedence.

    Rules with the same name in overlay replace rules in base.

    Args:
        base: Base constitution
        overlay: Constitution to overlay

    Returns:
        Merged constitution config
    """
    # Start with base rules
    merged_rules = {rule.name: rule for rule in base.rules}

    # Overlay rules (replace or add)
    for rule in overlay.rules:
        merged_rules[rule.name] = rule

    # Create merged config
    return ConstitutionConfig(
        profile=overlay.profile or base.profile,
        description=overlay.description or base.description,
        rules=list(merged_rules.values()),
        settings=overlay.settings,  # Overlay settings take precedence
    )


def get_active_constitution(
    project_config: dict[str, str | int | None]
) -> Optional[ConstitutionConfig]:
    """
    Load the active constitution based on project config.

    Args:
        project_config: Project configuration dictionary

    Returns:
        Active constitution or None if not found
    """
    from spectra.core.config import find_project_root

    project_root = find_project_root()
    if not project_root:
        raise ConfigError("Not in a Spectra project")

    # Get active profile from config
    active_profile = project_config.get("active_constitution_profile", "balanced")

    # Try to load constitution file
    constitution_path = project_root / ".spectra" / "constitution.yaml"

    if not constitution_path.exists():
        # Fall back to built-in profile
        return load_builtin_profile(str(active_profile))

    try:
        return load_constitution(constitution_path)
    except ValidationError:
        # Fall back to built-in profile
        return load_builtin_profile(str(active_profile))


def load_builtin_profile(profile_name: str) -> ConstitutionConfig:
    """
    Load a built-in constitution profile.

    Args:
        profile_name: Name of profile (strict, balanced, rapid)

    Returns:
        Constitution config

    Raises:
        ValidationError: If profile not found
    """
    if profile_name == "strict":
        from spectra.constitution.profiles.strict import get_strict_constitution
        return get_strict_constitution()
    elif profile_name == "balanced":
        from spectra.constitution.profiles.balanced import get_balanced_constitution
        return get_balanced_constitution()
    elif profile_name == "rapid":
        from spectra.constitution.profiles.rapid import get_rapid_constitution
        return get_rapid_constitution()
    else:
        raise ValidationError(f"Unknown constitution profile: {profile_name}")
