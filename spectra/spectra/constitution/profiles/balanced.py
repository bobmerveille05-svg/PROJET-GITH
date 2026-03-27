"""Balanced constitution profile - reasonable defaults for most teams."""

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


def get_balanced_constitution() -> ConstitutionConfig:
    """Get balanced constitution configuration."""
    return ConstitutionConfig(
        profile="balanced",
        description="Balanced governance - reasonable defaults for most teams",
        settings=ConstitutionSettings(
            strict_mode=False,
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
                name="suggest_structure",
                type=RuleType.SUGGEST,
                severity=RuleSeverity.INFO,
                scope=RuleScope.STRUCTURE,
                condition=RuleCondition(
                    field="structure",
                    operator=RuleOperator.EXISTS,
                ),
                message="Consider defining implementation structure",
            ),
            ConstitutionRule(
                name="require_acceptance_tests",
                type=RuleType.REQUIRE,
                severity=RuleSeverity.WARNING,
                scope=RuleScope.ACCEPTANCE,
                condition=RuleCondition(
                    field="acceptance.tests",
                    operator=RuleOperator.EXISTS,
                ),
                message="Acceptance tests should be defined",
            ),
            ConstitutionRule(
                name="suggest_review_checklist",
                type=RuleType.SUGGEST,
                severity=RuleSeverity.INFO,
                scope=RuleScope.REVIEW,
                condition=RuleCondition(
                    field="review.checklist",
                    operator=RuleOperator.EXISTS,
                ),
                message="Consider adding a review checklist",
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
        ],
    )
