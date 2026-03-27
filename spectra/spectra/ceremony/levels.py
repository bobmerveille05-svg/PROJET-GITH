"""Ceremony level definitions and requirements."""

from spectra.ceremony.models import ChangeCategory, CeremonyLevel

# Map change category to minimum required ceremony level
CATEGORY_TO_LEVEL: dict[ChangeCategory, CeremonyLevel] = {
    ChangeCategory.PATCH: CeremonyLevel.SKETCH,
    ChangeCategory.MINOR: CeremonyLevel.DRAFT,
    ChangeCategory.STANDARD: CeremonyLevel.SPECIFIED,
    ChangeCategory.MAJOR: CeremonyLevel.VALIDATED,
    ChangeCategory.CRITICAL: CeremonyLevel.LOCKED,
}

# Level descriptions
LEVEL_DESCRIPTIONS: dict[CeremonyLevel, str] = {
    CeremonyLevel.EXPLORE: "Free-form ideation - no requirements",
    CeremonyLevel.SKETCH: "Basic intent statement required",
    CeremonyLevel.DRAFT: "Intent + structure + at least 1 test criterion",
    CeremonyLevel.SPECIFIED: "Full spec + tests + review checklist",
    CeremonyLevel.VALIDATED: "Spec + tests + review + CI passing + docs",
    CeremonyLevel.LOCKED: "All of above + formal approval",
}

# Requirements per level
LEVEL_REQUIREMENTS: dict[CeremonyLevel, list[str]] = {
    CeremonyLevel.EXPLORE: [],
    CeremonyLevel.SKETCH: [
        "has_intent",
    ],
    CeremonyLevel.DRAFT: [
        "has_intent",
        "has_structure",
        "has_tests",
    ],
    CeremonyLevel.SPECIFIED: [
        "has_intent",
        "has_structure",
        "has_tests",
        "has_review_checklist",
    ],
    CeremonyLevel.VALIDATED: [
        "has_intent",
        "has_structure",
        "has_tests",
        "has_review_checklist",
        "has_documentation",
    ],
    CeremonyLevel.LOCKED: [
        "has_intent",
        "has_structure",
        "has_tests",
        "has_review_checklist",
        "has_documentation",
        "has_formal_approval",
    ],
}


def get_level_description(level: CeremonyLevel) -> str:
    """Get human-readable description of a ceremony level."""
    return LEVEL_DESCRIPTIONS.get(level, "Unknown level")


def get_level_requirements(level: CeremonyLevel) -> list[str]:
    """Get list of required checks for a ceremony level."""
    return LEVEL_REQUIREMENTS.get(level, [])


def get_minimum_level_for_category(category: ChangeCategory) -> CeremonyLevel:
    """Get minimum ceremony level for a change category."""
    return CATEGORY_TO_LEVEL.get(category, CeremonyLevel.SPECIFIED)
