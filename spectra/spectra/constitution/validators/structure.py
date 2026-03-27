"""Structure completeness validator."""

from typing import Any


def validate_structure_completeness(spec_data: dict[str, Any]) -> list[str]:
    """
    Validate that structure section is complete.

    Args:
        spec_data: Spec metadata

    Returns:
        List of validation issues (empty if valid)
    """
    issues: list[str] = []

    structure = spec_data.get("structure")

    if not structure:
        issues.append("Missing structure section")
        return issues

    if not isinstance(structure, dict):
        issues.append("Structure must be a dictionary")
        return issues

    # Check for at least one of: files, modules, components
    has_files = "files" in structure and isinstance(structure["files"], list)
    has_modules = "modules" in structure and isinstance(structure["modules"], list)
    has_components = "components" in structure and isinstance(
        structure["components"], list
    )

    if not (has_files or has_modules or has_components):
        issues.append(
            "Structure should contain at least one of: files, modules, components"
        )

    # Validate files are non-empty strings
    if has_files:
        files = structure["files"]
        for i, file_path in enumerate(files):
            if not isinstance(file_path, str) or not file_path.strip():
                issues.append(f"Invalid file path at index {i}")

    return issues
