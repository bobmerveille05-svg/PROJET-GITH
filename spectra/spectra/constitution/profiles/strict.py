"""Strict constitution profile - everything required, no shortcuts."""

from spectra.constitution.schema import (
    ConstitutionConfig,
    ConstitutionRule,
    ConstitutionSettings,
    RuleCondition,
    RuleOperator,
    RuleSeverity,
    RuleScope,
    RuleType,
)


def get_strict_constitution() -> ConstitutionConfig:
    """Get strict constitution configuration."""
    return ConstitutionConfig(
        profile="strict",
        description="Strict governance - everything required, no shortcuts",
        settings=ConstitutionSettings(
            strict_mode=True,
            auto_fix=False,
            ignore_archived=True,
        ),
        rules=[
            ConstitutionRule(
                name="require_intent",
                type=RuleType.REQUIRE,
                severity=RuleSeverity.ERROR,
                scope=RuleScope.SPEC,
                condition=RuleCondition(
                    field="intent",
                    operator=RuleOperator.EXISTS,
                ),
                message="Intent statement is required",
            ),
            ConstitutionRule(
                name="require_structure",
                type=RuleType.REQUIRE,
                severity=RuleSeverity.ERROR,
                scope=RuleScope.STRUCTURE,
                condition=RuleCondition(
                    field="structure.files",
                    operator=RuleOperator.EXISTS,
                ),
                message="Structure definition is required",
            ),
            ConstitutionRule(
                name="require_acceptance_tests",
                type=RuleType.REQUIRE,
                severity=RuleSeverity.ERROR,
                scope=RuleScope.ACCEPTANCE,
                condition=RuleCondition(
                    field="acceptance.tests",
                    operator=RuleOperator.EXISTS,
                ),
                message="Acceptance tests are required",
            ),
            ConstitutionRule(
                name="require_review_checklist",
                type=RuleType.REQUIRE,
                severity=RuleSeverity.ERROR,
                scope=RuleScope.REVIEW,
                condition=RuleCondition(
                    field="review.checklist",
                    operator=RuleOperator.EXISTS,
                ),
                message="Review checklist is required",
            ),
            ConstitutionRule(
                name="require_reviewers",
                type=RuleType.REQUIRE,
                severity=RuleSeverity.ERROR,
                scope=RuleScope.REVIEW,
                condition=RuleCondition(
                    field="review.reviewers",
                    operator=RuleOperator.EXISTS,
                ),
                message="At least one reviewer must be specified",
            ),
            ConstitutionRule(
                name="forbid_empty_intent",
                type=RuleType.FORBID,
                severity=RuleSeverity.ERROR,
                scope=RuleScope.SPEC,
                condition=RuleCondition(
                    field="intent",
                    operator=RuleOperator.EQUALS,
                    value="",
                ),
                message="Intent cannot be empty",
            ),
            ConstitutionRule(
                name="require_risk_assessment",
                type=RuleType.REQUIRE,
                severity=RuleSeverity.WARNING,
                scope=RuleScope.SPEC,
                condition=RuleCondition(
                    field="notes.risks",
                    operator=RuleOperator.EXISTS,
                ),
                message="Risk assessment is recommended",
            ),
        ],
    )
