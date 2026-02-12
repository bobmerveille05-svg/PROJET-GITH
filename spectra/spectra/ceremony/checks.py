"""Individual ceremony check implementations."""

from typing import Any


def has_intent(spec_data: dict[str, Any]) -> bool:
    """
    Check if spec has a non-empty intent statement.

    Args:
        spec_data: Spec metadata dictionary

    Returns:
        True if intent exists and is non-empty
    """
    intent = spec_data.get("intent", "")
    return isinstance(intent, str) and len(intent.strip()) > 0


def has_structure(spec_data: dict[str, Any]) -> bool:
    """
    Check if spec has structure definition.

    Args:
        spec_data: Spec metadata dictionary

    Returns:
        True if structure section exists with files or modules
    """
    structure = spec_data.get("structure", {})
    if not isinstance(structure, dict):
        return False

    files = structure.get("files", [])
    modules = structure.get("modules", [])
    components = structure.get("components", [])

    return len(files) > 0 or len(modules) > 0 or len(components) > 0


def has_tests(spec_data: dict[str, Any]) -> bool:
    """
    Check if spec has acceptance tests defined.

    Args:
        spec_data: Spec metadata dictionary

    Returns:
        True if acceptance.tests is non-empty
    """
    acceptance = spec_data.get("acceptance", {})
    if not isinstance(acceptance, dict):
        return False

    tests = acceptance.get("tests", [])
    return isinstance(tests, list) and len(tests) > 0


def has_review_checklist(spec_data: dict[str, Any]) -> bool:
    """
    Check if spec has review criteria.

    Args:
        spec_data: Spec metadata dictionary

    Returns:
        True if review.checklist exists
    """
    review = spec_data.get("review", {})
    if not isinstance(review, dict):
        return False

    checklist = review.get("checklist", [])
    return isinstance(checklist, list) and len(checklist) > 0


def has_documentation(spec_data: dict[str, Any]) -> bool:
    """
    Check if spec has documentation links or embedded docs.

    Args:
        spec_data: Spec metadata dictionary

    Returns:
        True if documentation is present
    """
    # Check for notes section with context
    notes = spec_data.get("notes", {})
    if isinstance(notes, dict) and notes.get("context"):
        return True

    # Check for links to related documentation
    links = spec_data.get("links", {})
    if isinstance(links, dict) and links.get("related"):
        return True

    # Check for explicit docs field in structure
    structure = spec_data.get("structure", {})
    if isinstance(structure, dict):
        docs = structure.get("documentation", [])
        if isinstance(docs, list) and len(docs) > 0:
            return True

    return False


def has_formal_approval(spec_data: dict[str, Any]) -> bool:
    """
    Check if spec has formal approval record.

    Args:
        spec_data: Spec metadata dictionary

    Returns:
        True if approval record exists
    """
    review = spec_data.get("review", {})
    if not isinstance(review, dict):
        return False

    # Check for approvals field
    approvals = review.get("approvals", [])
    if isinstance(approvals, list) and len(approvals) > 0:
        return True

    # Check for approved flag
    approved = review.get("approved", False)
    if approved:
        return True

    return False


# Map check names to functions
CHECK_FUNCTIONS: dict[str, Any] = {
    "has_intent": has_intent,
    "has_structure": has_structure,
    "has_tests": has_tests,
    "has_review_checklist": has_review_checklist,
    "has_documentation": has_documentation,
    "has_formal_approval": has_formal_approval,
}


def get_check_function(check_name: str) -> Any:
    """
    Get check function by name.

    Args:
        check_name: Name of check

    Returns:
        Check function or None
    """
    return CHECK_FUNCTIONS.get(check_name)
