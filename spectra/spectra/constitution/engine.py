"""Constitution rule evaluation engine."""

from dataclasses import dataclass
from typing import Any, Optional

from spectra.constitution.schema import (
    ConstitutionConfig,
    ConstitutionRule,
    RuleOperator,
    RuleSeverity,
    RuleType,
)


@dataclass
class RuleResult:
    """Result of evaluating a single rule."""

    rule_name: str
    passed: bool
    severity: RuleSeverity
    message: str
    details: str = ""

    def __str__(self) -> str:
        """Human-readable result."""
        status = "✓" if self.passed else "✗"
        severity_symbol = {
            RuleSeverity.ERROR: "❌",
            RuleSeverity.WARNING: "⚠️",
            RuleSeverity.INFO: "ℹ️",
        }.get(self.severity, "")
        return f"{status} {severity_symbol} {self.rule_name}: {self.message}"


class ConstitutionEngine:
    """Evaluates constitution rules against specs."""

    def evaluate_rule(
        self, rule: ConstitutionRule, spec_data: dict[str, Any], context: Optional[dict[str, Any]] = None
    ) -> RuleResult:
        """
        Evaluate a single rule against spec data.

        Args:
            rule: Rule to evaluate
            spec_data: Spec metadata dictionary
            context: Optional additional context

        Returns:
            Rule evaluation result
        """
        if not rule.enabled:
            return RuleResult(
                rule_name=rule.name,
                passed=True,
                severity=rule.severity,
                message="Rule disabled",
            )

        # Get field value
        field_value = self._get_field_value(spec_data, rule.condition.field)

        # Evaluate condition
        condition_met = self._evaluate_condition(
            field_value, rule.condition.operator, rule.condition.value
        )

        # Determine if rule passes based on type
        if rule.type == RuleType.REQUIRE:
            passed = condition_met
        elif rule.type == RuleType.FORBID:
            passed = not condition_met
        elif rule.type == RuleType.SUGGEST:
            # Suggestions always "pass" but provide info
            passed = True
        else:
            passed = False

        return RuleResult(
            rule_name=rule.name,
            passed=passed,
            severity=rule.severity,
            message=rule.message,
            details=f"Field: {rule.condition.field}, Value: {field_value}",
        )

    def enforce(
        self, spec_data: dict[str, Any], constitution: ConstitutionConfig
    ) -> list[RuleResult]:
        """
        Evaluate all rules in a constitution.

        Args:
            spec_data: Spec metadata
            constitution: Constitution config

        Returns:
            List of rule results
        """
        results: list[RuleResult] = []

        for rule in constitution.rules:
            result = self.evaluate_rule(rule, spec_data)
            results.append(result)

        return results

    def has_violations(self, results: list[RuleResult], strict_mode: bool = False) -> bool:
        """
        Check if there are any violations.

        Args:
            results: List of rule results
            strict_mode: If True, warnings count as violations

        Returns:
            True if violations exist
        """
        for result in results:
            if not result.passed:
                if result.severity == RuleSeverity.ERROR:
                    return True
                if strict_mode and result.severity == RuleSeverity.WARNING:
                    return True
        return False

    def get_violations(self, results: list[RuleResult]) -> list[RuleResult]:
        """
        Filter to only failed checks.

        Args:
            results: List of rule results

        Returns:
            List of failed results
        """
        return [r for r in results if not r.passed]

    def _get_field_value(self, data: dict[str, Any], field_path: str) -> Any:
        """
        Get value from nested dictionary using dot notation.

        Args:
            data: Data dictionary
            field_path: Dot-separated field path (e.g., "acceptance.tests")

        Returns:
            Field value or None if not found
        """
        parts = field_path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        return current

    def _evaluate_condition(
        self, field_value: Any, operator: RuleOperator, expected_value: Any
    ) -> bool:
        """
        Evaluate a condition.

        Args:
            field_value: Actual field value
            operator: Comparison operator
            expected_value: Expected value

        Returns:
            True if condition is met
        """
        if operator == RuleOperator.EQUALS:
            return field_value == expected_value

        elif operator == RuleOperator.NOT_EQUALS:
            return field_value != expected_value

        elif operator == RuleOperator.CONTAINS:
            if isinstance(field_value, (list, str)):
                return expected_value in field_value
            return False

        elif operator == RuleOperator.NOT_CONTAINS:
            if isinstance(field_value, (list, str)):
                return expected_value not in field_value
            return True

        elif operator == RuleOperator.GREATER_THAN:
            try:
                return field_value > expected_value
            except (TypeError, ValueError):
                return False

        elif operator == RuleOperator.LESS_THAN:
            try:
                return field_value < expected_value
            except (TypeError, ValueError):
                return False

        elif operator == RuleOperator.EXISTS:
            return field_value is not None

        elif operator == RuleOperator.NOT_EXISTS:
            return field_value is None

        return False
