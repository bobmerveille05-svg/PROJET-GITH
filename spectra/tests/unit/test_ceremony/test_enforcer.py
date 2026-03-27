"""Tests for ceremony enforcement."""

import pytest

from spectra.ceremony.enforcer import CeremonyEnforcer
from spectra.ceremony.models import CeremonyLevel


class TestCeremonyEnforcer:
    """Test ceremony gate enforcement."""

    def test_enforce_explore_level_no_requirements(self):
        """EXPLORE level has no requirements."""
        enforcer = CeremonyEnforcer()
        spec_data = {"id": "test", "name": "Test", "intent": ""}

        results = enforcer.enforce_ceremony(spec_data, CeremonyLevel.EXPLORE)

        assert len(results) == 0
        assert enforcer.can_proceed(spec_data, CeremonyLevel.EXPLORE) is True

    def test_enforce_sketch_requires_intent(self):
        """SKETCH level requires intent."""
        enforcer = CeremonyEnforcer()

        # Without intent
        spec_data = {"id": "test", "name": "Test", "intent": ""}
        results = enforcer.enforce_ceremony(spec_data, CeremonyLevel.SKETCH)

        assert len(results) == 1
        assert results[0].check_name == "has_intent"
        assert results[0].passed is False
        assert enforcer.can_proceed(spec_data, CeremonyLevel.SKETCH) is False

        # With intent
        spec_data["intent"] = "Some intent"
        results = enforcer.enforce_ceremony(spec_data, CeremonyLevel.SKETCH)

        assert all(r.passed for r in results)
        assert enforcer.can_proceed(spec_data, CeremonyLevel.SKETCH) is True

    def test_enforce_draft_requires_structure_and_tests(self):
        """DRAFT level requires intent, structure, and tests."""
        enforcer = CeremonyEnforcer()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Test intent",
        }

        results = enforcer.enforce_ceremony(spec_data, CeremonyLevel.DRAFT)

        # Should have 3 checks: has_intent, has_structure, has_tests
        assert len(results) == 3

        failing_checks = [r.check_name for r in results if not r.passed]
        assert "has_structure" in failing_checks
        assert "has_tests" in failing_checks
        assert enforcer.can_proceed(spec_data, CeremonyLevel.DRAFT) is False

    def test_enforce_draft_passes_with_complete_data(self):
        """DRAFT level passes with complete data."""
        enforcer = CeremonyEnforcer()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Test intent",
            "structure": {"files": ["test.py"]},
            "acceptance": {"tests": ["Test 1"]},
        }

        results = enforcer.enforce_ceremony(spec_data, CeremonyLevel.DRAFT)

        assert all(r.passed for r in results)
        assert enforcer.can_proceed(spec_data, CeremonyLevel.DRAFT) is True

    def test_enforce_specified_requires_review_checklist(self):
        """SPECIFIED level requires review checklist."""
        enforcer = CeremonyEnforcer()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Test intent",
            "structure": {"files": ["test.py"]},
            "acceptance": {"tests": ["Test 1"]},
        }

        results = enforcer.enforce_ceremony(spec_data, CeremonyLevel.SPECIFIED)

        failing_checks = [r.check_name for r in results if not r.passed]
        assert "has_review_checklist" in failing_checks

    def test_enforce_validated_requires_documentation(self):
        """VALIDATED level requires documentation."""
        enforcer = CeremonyEnforcer()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Test intent",
            "structure": {"files": ["test.py"]},
            "acceptance": {"tests": ["Test 1"]},
            "review": {"checklist": ["Check 1"]},
        }

        results = enforcer.enforce_ceremony(spec_data, CeremonyLevel.VALIDATED)

        failing_checks = [r.check_name for r in results if not r.passed]
        assert "has_documentation" in failing_checks

    def test_enforce_locked_requires_formal_approval(self):
        """LOCKED level requires formal approval."""
        enforcer = CeremonyEnforcer()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Test intent",
            "structure": {"files": ["test.py"]},
            "acceptance": {"tests": ["Test 1"]},
            "review": {"checklist": ["Check 1"]},
            "notes": {"context": "Documentation"},
        }

        results = enforcer.enforce_ceremony(spec_data, CeremonyLevel.LOCKED)

        failing_checks = [r.check_name for r in results if not r.passed]
        assert "has_formal_approval" in failing_checks

    def test_get_blockers_returns_only_failures(self):
        """get_blockers returns only failed checks."""
        enforcer = CeremonyEnforcer()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Test intent",
            # Missing structure and tests
        }

        blockers = enforcer.get_blockers(spec_data, CeremonyLevel.DRAFT)

        assert len(blockers) >= 2
        assert all(not b.passed for b in blockers)

    def test_get_progress_calculates_percentage(self):
        """get_progress returns progress statistics."""
        enforcer = CeremonyEnforcer()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Test intent",
            "structure": {"files": ["test.py"]},
            # Has 2 out of 3 required for DRAFT
        }

        progress = enforcer.get_progress(spec_data, CeremonyLevel.DRAFT)

        assert progress["target_level"] == "DRAFT"
        assert progress["total"] == 3  # has_intent, has_structure, has_tests
        assert progress["passed"] == 2  # intent and structure
        assert progress["percentage"] == pytest.approx(66.67, rel=0.1)
        assert progress["can_proceed"] is False

    def test_progressive_ceremony_levels(self):
        """Each level adds more requirements."""
        enforcer = CeremonyEnforcer()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Test intent",
            "structure": {"files": ["test.py"]},
            "acceptance": {"tests": ["Test 1"]},
            "review": {"checklist": ["Check 1"]},
            "notes": {"context": "Documentation"},
        }

        # Track requirement counts
        level_requirements = {}
        for level in [
            CeremonyLevel.EXPLORE,
            CeremonyLevel.SKETCH,
            CeremonyLevel.DRAFT,
            CeremonyLevel.SPECIFIED,
            CeremonyLevel.VALIDATED,
        ]:
            results = enforcer.enforce_ceremony(spec_data, level)
            level_requirements[level.name] = len(results)

        # Requirements should generally increase
        assert level_requirements["EXPLORE"] == 0
        assert level_requirements["SKETCH"] < level_requirements["DRAFT"]
        assert level_requirements["DRAFT"] < level_requirements["SPECIFIED"]
        assert level_requirements["SPECIFIED"] < level_requirements["VALIDATED"]


class TestCeremonyResultFormatting:
    """Test ceremony result display."""

    def test_ceremony_result_string_representation(self):
        """CeremonyResult has readable string format."""
        from spectra.ceremony.models import CeremonyLevel, CeremonyResult

        result = CeremonyResult(
            check_name="has_intent",
            passed=True,
            current_level=CeremonyLevel.DRAFT,
            details="Intent exists",
        )

        str_repr = str(result)
        assert "has_intent" in str_repr
        assert "Intent exists" in str_repr
        assert "✓" in str_repr  # Success symbol

    def test_ceremony_result_failure_format(self):
        """Failed results show failure indicator."""
        from spectra.ceremony.models import CeremonyLevel, CeremonyResult

        result = CeremonyResult(
            check_name="has_tests",
            passed=False,
            current_level=CeremonyLevel.DRAFT,
            details="No tests defined",
        )

        str_repr = str(result)
        assert "✗" in str_repr  # Failure symbol
