"""YAML spec parsing and edge extraction."""

from pathlib import Path
from typing import Any

import yaml

from spectra.core.exceptions import ValidationError
from spectra.intent_graph.models import Edge, EdgeType, IntentNode


def parse_spec_yaml(yaml_content: str) -> IntentNode:
    """
    Parse YAML string to IntentNode.

    Args:
        yaml_content: YAML string content

    Returns:
        Parsed IntentNode

    Raises:
        ValidationError: If YAML is invalid or missing required fields
    """
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML: {e}")

    if not isinstance(data, dict):
        raise ValidationError("YAML must be a dictionary")

    # Validate required fields
    required_fields = ["id", "name", "intent"]
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")

    # Extract metadata from all non-standard fields
    metadata_keys = [
        "structure",
        "acceptance",
        "review",
        "notes",
        "risk",
        "dependencies",
        "links",
    ]
    metadata: dict[str, Any] = {}
    for key in metadata_keys:
        if key in data:
            metadata[key] = data[key]

    return IntentNode(
        id=str(data["id"]),
        name=str(data["name"]),
        intent=str(data["intent"]),
        ceremony_level=int(data.get("ceremony_level", 0)),
        lifecycle_state=str(data.get("lifecycle_state", "DRAFT")),
        trust_score=float(data.get("trust_score", 0.5)),
        metadata=metadata,
    )


def parse_spec_file(path: Path) -> IntentNode:
    """
    Read and parse a spec file.

    Args:
        path: Path to YAML spec file

    Returns:
        Parsed IntentNode

    Raises:
        ValidationError: If file cannot be read or parsed
    """
    try:
        with open(path, "r") as f:
            content = f.read()
        return parse_spec_yaml(content)
    except IOError as e:
        raise ValidationError(f"Failed to read spec file: {e}")


def extract_links(yaml_content: str) -> list[Edge]:
    """
    Extract graph edges from spec YAML.

    Looks for:
    - dependencies.depends_on -> DEPENDS_ON edges
    - dependencies.refines -> REFINES edges
    - dependencies.enables -> ENABLES edges
    - links.conflicts_with -> CONFLICTS_WITH edges

    Args:
        yaml_content: YAML string content

    Returns:
        List of Edge objects
    """
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError:
        return []

    if not isinstance(data, dict):
        return []

    edges: list[Edge] = []
    source_id = str(data.get("id", ""))

    if not source_id:
        return edges

    # Extract dependency links
    dependencies = data.get("dependencies", {})
    if isinstance(dependencies, dict):
        # depends_on links
        depends_on = dependencies.get("depends_on", [])
        if isinstance(depends_on, list):
            for target in depends_on:
                edges.append(
                    Edge(
                        source_id=source_id,
                        target_id=str(target),
                        edge_type=EdgeType.DEPENDS_ON,
                    )
                )

        # refines links
        refines = dependencies.get("refines")
        if refines:
            edges.append(
                Edge(
                    source_id=source_id,
                    target_id=str(refines),
                    edge_type=EdgeType.REFINES,
                )
            )

        # enables links
        enables = dependencies.get("enables", [])
        if isinstance(enables, list):
            for target in enables:
                edges.append(
                    Edge(
                        source_id=source_id,
                        target_id=str(target),
                        edge_type=EdgeType.ENABLES,
                    )
                )

    # Extract conflict links
    links = data.get("links", {})
    if isinstance(links, dict):
        conflicts_with = links.get("conflicts_with", [])
        if isinstance(conflicts_with, list):
            for target in conflicts_with:
                edges.append(
                    Edge(
                        source_id=source_id,
                        target_id=str(target),
                        edge_type=EdgeType.CONFLICTS_WITH,
                    )
                )

    return edges


def validate_spec_structure(data: dict[str, Any]) -> list[str]:
    """
    Validate spec structure and return list of warnings/errors.

    Args:
        data: Parsed YAML data

    Returns:
        List of validation messages (empty if valid)
    """
    issues: list[str] = []

    # Check required fields
    required = ["id", "name", "intent"]
    for field in required:
        if field not in data:
            issues.append(f"Missing required field: {field}")

    # Check structure section
    if "structure" in data:
        structure = data["structure"]
        if not isinstance(structure, dict):
            issues.append("structure must be a dictionary")
        else:
            if "files" not in structure and "modules" not in structure:
                issues.append("structure should contain 'files' or 'modules'")

    # Check acceptance section
    if "acceptance" in data:
        acceptance = data["acceptance"]
        if not isinstance(acceptance, dict):
            issues.append("acceptance must be a dictionary")
        else:
            if "tests" not in acceptance:
                issues.append("acceptance should contain 'tests'")

    return issues
