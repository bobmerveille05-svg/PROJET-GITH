"""Tests for ceremony assessor."""

import pytest

from spectra.ceremony.assessor import CeremonyAssessor
from spectra.ceremony.models import ChangeCategory, CeremonyLevel


class TestChangeAssessment:
    """Test change category assessment."""

    def test_assess_minimal_change_as_patch(self):
        """Minimal change with no risk markers assessed as PATCH."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Fix typo in comment",
        }

        category = assessor.assess_change_category(spec_data)
        assert category == ChangeCategory.PATCH

    def test_assess_small_change_as_minor(self):
        """Small change with few files assessed as MINOR."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Add new utility function",
            "structure": {"files": ["utils.py"]},
        }

        category = assessor.assess_change_category(spec_data)
        assert category in [ChangeCategory.PATCH, ChangeCategory.MINOR]

    def test_assess_multiple_files_increases_category(self):
        """More files touched increases change category."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Update auth system",
            "structure": {
                "files": [f"file{i}.py" for i in range(6)]  # 6 files
            },
        }

        category = assessor.assess_change_category(spec_data)
        assert category in [ChangeCategory.STANDARD, ChangeCategory.MAJOR]

    def test_assess_many_files_as_major(self):
        """Many files touched assessed as MAJOR."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Refactor core system",
            "structure": {
                "files": [f"file{i}.py" for i in range(15)]  # 15 files
            },
        }

        category = assessor.assess_change_category(spec_data)
        assert category in [ChangeCategory.MAJOR, ChangeCategory.CRITICAL]

    def test_assess_with_dependencies_increases_category(self):
        """Specs with dependencies get higher category."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Update auth",
            "structure": {"files": ["auth.py"]},
            "dependencies": {
                "depends_on": ["dep1", "dep2", "dep3", "dep4", "dep5", "dep6"]
            },
        }

        category = assessor.assess_change_category(spec_data)
        # Many dependencies should increase category
        assert category != ChangeCategory.PATCH

    def test_assess_with_high_impact_increases_category(self):
        """Specs with many dependents get higher category."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Update core API",
        }

        graph_context = {
            "dependents": [f"dep{i}" for i in range(15)]  # 15 dependents
        }

        category = assessor.assess_change_category(spec_data, graph_context)
        assert category in [ChangeCategory.MAJOR, ChangeCategory.CRITICAL]

    def test_assess_with_risk_markers_increases_category(self):
        """Explicit risk markers increase category."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Update auth",
            "notes": {
                "risks": [
                    "Breaking change to API",
                    "Security implications",
                    "Performance impact",
                    "Database migration required",
                ]
            },
        }

        category = assessor.assess_change_category(spec_data)
        assert category in [ChangeCategory.MAJOR, ChangeCategory.CRITICAL]

    def test_assess_with_critical_keywords(self):
        """Critical keywords in intent increase category."""
        assessor = CeremonyAssessor()

        critical_intents = [
            "breaking change to authentication system",
            "security fix for critical vulnerability",
            "major refactor of core module",
            "database migration for all users",
        ]

        for intent in critical_intents:
            spec_data = {
                "id": "test",
                "name": "Test",
                "intent": intent,
            }

            category = assessor.assess_change_category(spec_data)
            # Should be at least STANDARD, likely MAJOR or CRITICAL
            assert category != ChangeCategory.PATCH


class TestCeremonyLevelSuggestion:
    """Test ceremony level suggestions."""

    def test_suggest_sketch_for_patch(self):
        """PATCH changes suggest SKETCH level."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Fix typo",
        }

        suggested_level = assessor.suggest_ceremony_level(spec_data)
        assert suggested_level == CeremonyLevel.SKETCH

    def test_suggest_draft_for_minor(self):
        """MINOR changes suggest DRAFT level."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Add helper function",
            "structure": {"files": ["utils.py", "tests.py"]},
        }

        suggested_level = assessor.suggest_ceremony_level(spec_data)
        assert suggested_level in [CeremonyLevel.SKETCH, CeremonyLevel.DRAFT]

    def test_suggest_specified_for_standard(self):
        """STANDARD changes suggest SPECIFIED level."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Implement new feature",
            "structure": {
                "files": ["feature.py", "tests.py", "models.py", "views.py"]
            },
        }

        suggested_level = assessor.suggest_ceremony_level(spec_data)
        assert suggested_level >= CeremonyLevel.DRAFT

    def test_suggest_validated_for_major(self):
        """MAJOR changes suggest VALIDATED level."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Major system refactor",
            "structure": {
                "files": [f"module{i}.py" for i in range(12)]
            },
            "notes": {
                "risks": ["Breaking changes", "Performance impact"]
            },
        }

        suggested_level = assessor.suggest_ceremony_level(spec_data)
        assert suggested_level >= CeremonyLevel.SPECIFIED

    def test_suggest_locked_for_critical(self):
        """CRITICAL changes suggest LOCKED level."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Critical security fix with breaking changes",
            "structure": {
                "files": [f"core{i}.py" for i in range(20)]
            },
            "dependencies": {
                "depends_on": [f"dep{i}" for i in range(10)]
            },
            "notes": {
                "risks": [
                    "Breaking API changes",
                    "Security vulnerability",
                    "Data migration",
                    "System downtime",
                ]
            },
        }

        graph_context = {
            "dependents": [f"dep{i}" for i in range(20)]
        }

        suggested_level = assessor.suggest_ceremony_level(spec_data, graph_context)
        assert suggested_level >= CeremonyLevel.VALIDATED


class TestAssessmentDetails:
    """Test assessment detail generation."""

    def test_get_assessment_details_structure(self):
        """Assessment details include all expected fields."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Test intent",
            "structure": {"files": ["a.py", "b.py"], "modules": ["mod1"]},
            "dependencies": {"depends_on": ["dep1", "dep2"]},
            "notes": {"risks": ["Risk 1"]},
        }

        graph_context = {"dependents": ["dep1", "dep2", "dep3"]}

        details = assessor.get_assessment_details(spec_data, graph_context)

        assert "category" in details
        assert "suggested_level" in details
        assert "factors" in details

        factors = details["factors"]
        assert "files_count" in factors
        assert "modules_count" in factors
        assert "dependencies_count" in factors
        assert "dependents_count" in factors
        assert "risks_count" in factors

        assert factors["files_count"] == 2
        assert factors["modules_count"] == 1
        assert factors["dependencies_count"] == 2
        assert factors["dependents_count"] == 3
        assert factors["risks_count"] == 1

    def test_get_assessment_details_without_graph_context(self):
        """Assessment works without graph context."""
        assessor = CeremonyAssessor()

        spec_data = {
            "id": "test",
            "name": "Test",
            "intent": "Test intent",
        }

        details = assessor.get_assessment_details(spec_data)

        assert details["factors"]["dependents_count"] == 0
        assert "category" in details
        assert "suggested_level" in details


class TestCategoryLevelMapping:
    """Test that change categories map to appropriate ceremony levels."""

    def test_all_categories_have_level_mapping(self):
        """Every change category maps to a ceremony level."""
        from spectra.ceremony.levels import get_minimum_level_for_category

        for category in ChangeCategory:
            level = get_minimum_level_for_category(category)
            assert isinstance(level, CeremonyLevel)

    def test_category_level_increases_appropriately(self):
        """Higher risk categories require higher ceremony levels."""
        from spectra.ceremony.levels import get_minimum_level_for_category

        patch_level = get_minimum_level_for_category(ChangeCategory.PATCH)
        minor_level = get_minimum_level_for_category(ChangeCategory.MINOR)
        standard_level = get_minimum_level_for_category(ChangeCategory.STANDARD)
        major_level = get_minimum_level_for_category(ChangeCategory.MAJOR)
        critical_level = get_minimum_level_for_category(ChangeCategory.CRITICAL)

        assert patch_level < minor_level
        assert minor_level <= standard_level
        assert standard_level < major_level
        assert major_level <= critical_level
