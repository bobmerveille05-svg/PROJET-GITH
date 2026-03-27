"""Dynamic workflow generation based on ceremony level."""

from dataclasses import dataclass
from typing import Any, Callable

from spectra.ceremony.checks import get_check_function
from spectra.ceremony.levels import get_level_requirements
from spectra.ceremony.models import CeremonyLevel


@dataclass
class WorkflowStep:
    """Represents a step in the ceremony workflow."""

    name: str
    description: str
    required: bool
    check_fn: Callable[[dict[str, Any]], bool]


class WorkflowBuilder:
    """Builds dynamic workflows based on ceremony level."""

    def build_workflow(self, ceremony_level: CeremonyLevel) -> list[WorkflowStep]:
        """
        Generate workflow steps for a given ceremony level.

        Args:
            ceremony_level: Target ceremony level

        Returns:
            List of workflow steps
        """
        steps: list[WorkflowStep] = []

        # Get required checks for this level
        required_checks = get_level_requirements(ceremony_level)

        # Map checks to workflow steps
        check_descriptions = {
            "has_intent": "Define clear intent statement",
            "has_structure": "Define implementation structure (files/modules)",
            "has_tests": "Define acceptance tests",
            "has_review_checklist": "Create review checklist",
            "has_documentation": "Add documentation",
            "has_formal_approval": "Obtain formal approval",
        }

        for check_name in required_checks:
            check_fn = get_check_function(check_name)
            if check_fn:
                steps.append(
                    WorkflowStep(
                        name=check_name,
                        description=check_descriptions.get(check_name, check_name),
                        required=True,
                        check_fn=check_fn,
                    )
                )

        return steps

    def get_workflow_summary(self, ceremony_level: CeremonyLevel) -> str:
        """
        Get human-readable workflow summary.

        Args:
            ceremony_level: Ceremony level

        Returns:
            Summary string
        """
        steps = self.build_workflow(ceremony_level)

        if not steps:
            return f"Level {ceremony_level.name}: No requirements"

        lines = [f"Level {ceremony_level.name} Workflow:"]
        for i, step in enumerate(steps, 1):
            lines.append(f"  {i}. {step.description}")

        return "\n".join(lines)
