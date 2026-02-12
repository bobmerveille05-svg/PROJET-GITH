"""Completeness validator for specs."""

from typing import Any


def validate_spec_completeness(spec_data: dict[str, Any], min_completeness: float = 0.7) -> list[str]:
    """
    Validate that spec has sufficient information.

    Args:
        spec_data: Spec metadata
        min_completeness: Minimum completeness ratio (0.0 to 1.0)

    Returns:
        List of validation issues (empty if valid)
    """
    issues: list[str] = []

    # Required fields
    required_fields = ["id", "name", "intent"]
    for field in required_fields:
        if field not in spec_data or not spec_data[field]:
            issues.append(f"Required field missing: {field}")

    # Recommended fields for completeness
    recommended_fields = [
        "structure",
        "acceptance",
        "dependencies",
        "review",
    ]

    present_count = sum(
        1 for field in recommended_fields if field in spec_data and spec_data[field]
    )
    completeness_ratio = present_count / len(recommended_fields)

    if completeness_ratio < min_completeness:
        issues.append(
            f"Spec completeness is {completeness_ratio:.0%}, "
            f"should be at least {min_completeness:.0%}"
        )
        missing = [
            field for field in recommended_fields
            if field not in spec_data or not spec_data[field]
        ]
        issues.append(f"Missing recommended sections: {', '.join(missing)}")

    return issues
