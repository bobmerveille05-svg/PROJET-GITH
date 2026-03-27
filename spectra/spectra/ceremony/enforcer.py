"""Ceremony gate enforcement logic."""

from typing import Any

from spectra.ceremony.checks import get_check_function
from spectra.ceremony.levels import get_level_requirements
from spectra.ceremony.models import CeremonyLevel, CeremonyResult


class CeremonyEnforcer:
    """Enforces ceremony gates and requirements."""

    def enforce_ceremony(
        self, spec_data: dict[str, Any], target_level: CeremonyLevel
    ) -> list[CeremonyResult]:
        """
        Run all checks for a target ceremony level.

        Args:
            spec_data: Spec metadata
            target_level: Target ceremony level to check against

        Returns:
            List of check results
        """
        results: list[CeremonyResult] = []

        # Get required checks for this level
        required_checks = get_level_requirements(target_level)

        for check_name in required_checks:
            check_fn = get_check_function(check_name)

            if check_fn is None:
                results.append(
                    CeremonyResult(
                        check_name=check_name,
                        passed=False,
                        current_level=target_level,
                        details="Check function not found",
                    )
                )
                continue

            try:
                passed = check_fn(spec_data)
                results.append(
                    CeremonyResult(
                        check_name=check_name,
                        passed=passed,
                        current_level=target_level,
                        details="Passed" if passed else "Failed",
                    )
                )
            except Exception as e:
                results.append(
                    CeremonyResult(
                        check_name=check_name,
                        passed=False,
                        current_level=target_level,
                        details=f"Error: {e}",
                    )
                )

        return results

    def can_proceed(self, spec_data: dict[str, Any], target_level: CeremonyLevel) -> bool:
        """
        Check if all required checks pass for a ceremony level.

        Args:
            spec_data: Spec metadata
            target_level: Target ceremony level

        Returns:
            True if all required checks pass
        """
        results = self.enforce_ceremony(spec_data, target_level)
        return all(result.passed for result in results)

    def get_blockers(
        self, spec_data: dict[str, Any], target_level: CeremonyLevel
    ) -> list[CeremonyResult]:
        """
        Get failing checks that block progression.

        Args:
            spec_data: Spec metadata
            target_level: Target ceremony level

        Returns:
            List of failed check results
        """
        results = self.enforce_ceremony(spec_data, target_level)
        return [result for result in results if not result.passed]

    def get_progress(self, spec_data: dict[str, Any], target_level: CeremonyLevel) -> dict[str, Any]:
        """
        Get ceremony progress statistics.

        Args:
            spec_data: Spec metadata
            target_level: Target ceremony level

        Returns:
            Dictionary with progress information
        """
        results = self.enforce_ceremony(spec_data, target_level)

        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)

        return {
            "target_level": target_level.name,
            "passed": passed_count,
            "total": total_count,
            "percentage": (passed_count / total_count * 100) if total_count > 0 else 100.0,
            "can_proceed": passed_count == total_count,
        }
