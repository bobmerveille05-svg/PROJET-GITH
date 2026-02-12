"""Pydantic models for constitution YAML."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class RuleType(str, Enum):
    """Types of constitution rules."""

    REQUIRE = "require"
    FORBID = "forbid"
    SUGGEST = "suggest"


class RuleSeverity(str, Enum):
    """Severity levels for rule violations."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleScope(str, Enum):
    """Scope where rule applies."""

    ALL = "all"
    SPEC = "spec"
    STRUCTURE = "structure"
    ACCEPTANCE = "acceptance"
    REVIEW = "review"


class RuleOperator(str, Enum):
    """Operators for rule conditions."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class RuleCondition(BaseModel):
    """Condition for rule evaluation."""

    field: str = Field(..., description="Field path to check (e.g., 'acceptance.tests')")
    operator: RuleOperator = Field(..., description="Comparison operator")
    value: Optional[Any] = Field(None, description="Value to compare against")

    class Config:
        use_enum_values = True


class ConstitutionRule(BaseModel):
    """A single constitution rule."""

    name: str = Field(..., description="Unique rule name")
    type: RuleType = Field(..., description="Rule type (require/forbid/suggest)")
    severity: RuleSeverity = Field(
        default=RuleSeverity.ERROR, description="Violation severity"
    )
    scope: RuleScope = Field(default=RuleScope.ALL, description="Where rule applies")
    condition: RuleCondition = Field(..., description="Condition to evaluate")
    message: str = Field(..., description="Message to display on violation")
    enabled: bool = Field(default=True, description="Whether rule is active")

    class Config:
        use_enum_values = True


class ConstitutionSettings(BaseModel):
    """Constitution configuration settings."""

    strict_mode: bool = Field(
        default=False, description="Fail on warnings in addition to errors"
    )
    auto_fix: bool = Field(default=False, description="Automatically fix violations")
    ignore_archived: bool = Field(
        default=True, description="Skip archived specs in enforcement"
    )


class ConstitutionConfig(BaseModel):
    """Complete constitution configuration."""

    profile: str = Field(..., description="Profile name")
    description: str = Field(default="", description="Profile description")
    rules: list[ConstitutionRule] = Field(
        default_factory=list, description="List of rules"
    )
    settings: ConstitutionSettings = Field(
        default_factory=ConstitutionSettings, description="Configuration settings"
    )

    class Config:
        use_enum_values = True
