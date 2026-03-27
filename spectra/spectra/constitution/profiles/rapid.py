"""Rapid constitution profile - minimal ceremony, fast iteration."""

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


def get_rapid_constitution() -> ConstitutionConfig:
    """Get rapid constitution configuration."""
    return ConstitutionConfig(
        profile="rapid",
        description="Rapid iteration - minimal ceremony, fast iteration",
        settings=ConstitutionSettings(
            strict_mode=False,
            auto_fix=True,
            ignore_archived=True,
        ),
        rules=[
            ConstitutionRule(
                name="require_intent",
                type=RuleType.REQUIRE,
                severity=RuleSeverity.WARNING,
                scope=RuleScope.SPEC,
                condition=RuleCondition(
                    field="intent",
                    operator=RuleOperator.EXISTS,
                ),
                message="Intent statement is recommended",
            ),
            ConstitutionRule(
                name="suggest_tests",
                type=RuleType.SUGGEST,
                severity=RuleSeverity.INFO,
                scope=RuleScope.ACCEPTANCE,
                condition=RuleCondition(
                    field="acceptance.tests",
                    operator=RuleOperator.EXISTS,
                ),
                message="Consider adding acceptance tests",
            ),
            ConstitutionRule(
                name="forbid_empty_intent",
                type=RuleType.FORBID,
                severity=RuleSeverity.WARNING,
                scope=RuleScope.SPEC,
                condition=RuleCondition(
                    field="intent",
                    operator=RuleOperator.EQUALS,
                    value="",
                ),
                message="Intent should not be empty",
            ),
        ],
    )
