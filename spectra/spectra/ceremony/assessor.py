"""Risk and complexity assessment for ceremony level recommendation."""

from typing import Any, Optional

from spectra.ceremony.levels import get_minimum_level_for_category
from spectra.ceremony.models import ChangeCategory, CeremonyLevel


class CeremonyAssessor:
    """Assesses appropriate ceremony level based on spec characteristics."""

    def assess_change_category(
        self, spec_data: dict[str, Any], graph_context: Optional[dict[str, Any]] = None
    ) -> ChangeCategory:
        """
        Analyze spec to determine change category.

        Factors considered:
        - Number of files/modules touched
        - Number of dependencies
        - Number of dependents (impact)
        - Explicit risk markers
        - Lifecycle state

        Args:
            spec_data: Spec metadata
            graph_context: Optional graph context (dependencies, dependents, etc.)

        Returns:
            Assessed change category
        """
        score = 0

        # Factor 1: Structure size
        structure = spec_data.get("structure", {})
        if isinstance(structure, dict):
            files = structure.get("files", [])
            modules = structure.get("modules", [])
            components = structure.get("components", [])

            total_items = len(files) + len(modules) + len(components)

            if total_items == 0:
                score += 0
            elif total_items <= 2:
                score += 1
            elif total_items <= 5:
                score += 2
            elif total_items <= 10:
                score += 3
            else:
                score += 4

        # Factor 2: Dependencies
        dependencies = spec_data.get("dependencies", {})
        if isinstance(dependencies, dict):
            depends_on = dependencies.get("depends_on", [])
            if isinstance(depends_on, list):
                dep_count = len(depends_on)
                if dep_count > 5:
                    score += 2
                elif dep_count > 2:
                    score += 1

        # Factor 3: Impact (from graph context)
        if graph_context:
            dependents = graph_context.get("dependents", [])
            if isinstance(dependents, list):
                if len(dependents) > 10:
                    score += 3
                elif len(dependents) > 5:
                    score += 2
                elif len(dependents) > 2:
                    score += 1

        # Factor 4: Explicit risk markers
        notes = spec_data.get("notes", {})
        if isinstance(notes, dict):
            risks = notes.get("risks", [])
            if isinstance(risks, list):
                risk_count = len(risks)
                if risk_count > 3:
                    score += 3
                elif risk_count > 1:
                    score += 2
                elif risk_count > 0:
                    score += 1

        # Factor 5: Check for critical keywords
        intent = spec_data.get("intent", "").lower()
        critical_keywords = ["breaking", "migration", "security", "critical", "major refactor"]
        if any(keyword in intent for keyword in critical_keywords):
            score += 3

        # Map score to category
        if score == 0:
            return ChangeCategory.PATCH
        elif score <= 3:
            return ChangeCategory.MINOR
        elif score <= 6:
            return ChangeCategory.STANDARD
        elif score <= 10:
            return ChangeCategory.MAJOR
        else:
            return ChangeCategory.CRITICAL

    def suggest_ceremony_level(
        self, spec_data: dict[str, Any], graph_context: Optional[dict[str, Any]] = None
    ) -> CeremonyLevel:
        """
        Suggest appropriate ceremony level for a spec.

        Args:
            spec_data: Spec metadata
            graph_context: Optional graph context

        Returns:
            Suggested ceremony level
        """
        category = self.assess_change_category(spec_data, graph_context)
        return get_minimum_level_for_category(category)

    def get_assessment_details(
        self, spec_data: dict[str, Any], graph_context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Get detailed assessment information.

        Args:
            spec_data: Spec metadata
            graph_context: Optional graph context

        Returns:
            Dictionary with assessment details
        """
        category = self.assess_change_category(spec_data, graph_context)
        suggested_level = self.suggest_ceremony_level(spec_data, graph_context)

        # Count various factors
        structure = spec_data.get("structure", {})
        files = structure.get("files", []) if isinstance(structure, dict) else []
        modules = structure.get("modules", []) if isinstance(structure, dict) else []

        dependencies = spec_data.get("dependencies", {})
        depends_on = dependencies.get("depends_on", []) if isinstance(dependencies, dict) else []

        notes = spec_data.get("notes", {})
        risks = notes.get("risks", []) if isinstance(notes, dict) else []

        dependents_count = 0
        if graph_context:
            dependents = graph_context.get("dependents", [])
            dependents_count = len(dependents) if isinstance(dependents, list) else 0

        return {
            "category": category.value,
            "suggested_level": suggested_level,
            "factors": {
                "files_count": len(files),
                "modules_count": len(modules),
                "dependencies_count": len(depends_on),
                "dependents_count": dependents_count,
                "risks_count": len(risks),
            },
        }
