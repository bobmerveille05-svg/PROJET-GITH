"""Tests for lifecycle promotion and demotion with gates."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from spectra.ceremony.enforcer import CeremonyEnforcer
from spectra.ceremony.models import CeremonyLevel
from spectra.constitution.engine import ConstitutionEngine
from spectra.constitution.profiles.balanced import get_balanced_constitution
from spectra.constitution.profiles.strict import get_strict_constitution
from spectra.core.database import get_connection, run_migrations
from spectra.core.events import EventBus, EventType
from spectra.core.exceptions import CeremonyError, ConstitutionViolation, LifecycleError
from spectra.lifecycle.models import SpecState, STATE_CEREMONY_GATES
from spectra.lifecycle.promotion import LifecyclePromoter


@pytest.fixture
def db_conn():
    """Create temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = get_connection(db_path)
        run_migrations(conn)
        yield conn
        conn.close()


@pytest.fixture
def event_bus(db_conn):
    """Create event bus."""
    return EventBus(db_conn)


@pytest.fixture
def promoter(db_conn, event_bus):
    """Create lifecycle promoter."""
    return LifecyclePromoter(
        db_conn,
        event_bus,
        CeremonyEnforcer(),
        ConstitutionEngine(),
    )


@pytest.fixture
def minimal_spec_data():
    """Minimal valid spec data."""
    return {
        "id": "test-spec",
        "name": "Test Spec",
        "intent": "Test intent statement",
        "lifecycle_state": "DRAFT",
        "ceremony_level": 0,
    }


@pytest.fixture
def complete_spec_data():
    """Complete spec data that passes all gates."""
    return {
        "id": "test-spec",
        "name": "Test Spec",
        "intent": "Test intent statement",
        "lifecycle_state": "DRAFT",
        "ceremony_level": 4,
        "structure": {
            "files": ["test.py"],
        },
        "acceptance": {
            "tests": ["Test passes"],
        },
        "review": {
            "checklist": ["Code reviewed"],
        },
        "notes": {
            "context": "Documentation",
        },
    }


class TestPromotion:
    """Test spec promotion."""

    def test_promote_from_draft_to_specified(self, promoter, complete_spec_data):
        """Can promote from DRAFT to SPECIFIED with proper ceremony level."""
        complete_spec_data["ceremony_level"] = 2  # DRAFT level
        transition = promoter.promote(
            spec_id="test-spec",
            spec_data=complete_spec_data,
            actor="test-user",
        )

        assert transition.from_state == SpecState.DRAFT
        assert transition.to_state == SpecState.SPECIFIED
        assert transition.actor == "test-user"

    def test_promote_blocked_by_ceremony_gate(self, promoter, minimal_spec_data):
        """Promotion blocked if ceremony requirements not met."""
        # DRAFT state with ceremony level 0 trying to promote to SPECIFIED
        # SPECIFIED requires ceremony level 2
        with pytest.raises(CeremonyError, match="ceremony requirements not met"):
            promoter.promote(
                spec_id="test-spec",
                spec_data=minimal_spec_data,
                actor="test-user",
            )

    def test_promote_blocked_by_constitution(self, promoter, complete_spec_data):
        """Promotion blocked if constitution rules violated."""
        strict_constitution = get_strict_constitution()

        # Missing reviewers in spec data
        spec_data = complete_spec_data.copy()
        spec_data.pop("review", None)

        with pytest.raises(ConstitutionViolation, match="constitution violations"):
            promoter.promote(
                spec_id="test-spec",
                spec_data=spec_data,
                actor="test-user",
                constitution=strict_constitution,
            )

    def test_promote_emits_event(self, promoter, complete_spec_data, event_bus):
        """Promotion emits SPEC_PROMOTED event."""
        events_before = len(event_bus.history(EventType.SPEC_PROMOTED))

        complete_spec_data["ceremony_level"] = 2
        promoter.promote(
            spec_id="test-spec",
            spec_data=complete_spec_data,
            actor="test-user",
        )

        events_after = len(event_bus.history(EventType.SPEC_PROMOTED))
        assert events_after == events_before + 1

    def test_promote_records_transition(self, promoter, complete_spec_data, db_conn):
        """Promotion records transition in database."""
        complete_spec_data["ceremony_level"] = 2

        promoter.promote(
            spec_id="test-spec",
            spec_data=complete_spec_data,
            actor="test-user",
            reason="Ready for implementation",
        )

        # Check transition was recorded
        cursor = db_conn.execute(
            "SELECT * FROM lifecycle_transitions WHERE spec_id = ?",
            ("test-spec",),
        )
        transitions = cursor.fetchall()
        assert len(transitions) == 1
        assert transitions[0]["from_state"] == "DRAFT"
        assert transitions[0]["to_state"] == "SPECIFIED"
        assert transitions[0]["actor"] == "test-user"

    def test_cannot_promote_from_terminal_state(self, promoter, complete_spec_data):
        """Cannot promote from COMPLETE state."""
        complete_spec_data["lifecycle_state"] = "COMPLETE"

        # COMPLETE can only go to ARCHIVED or demote to VALIDATING
        # Promoting would try to go to next forward state, but there isn't one except ARCHIVED
        with pytest.raises(LifecycleError, match="no forward state available"):
            promoter.promote(
                spec_id="test-spec",
                spec_data=complete_spec_data,
                actor="test-user",
            )

    def test_promote_with_balanced_constitution(self, promoter, complete_spec_data):
        """Promotion succeeds with balanced constitution."""
        balanced_constitution = get_balanced_constitution()

        # Balanced constitution is more lenient
        spec_data = {
            "id": "test-spec",
            "name": "Test Spec",
            "intent": "Test intent",
            "lifecycle_state": "DRAFT",
            "ceremony_level": 2,
            "structure": {"files": ["test.py"]},
            "acceptance": {"tests": ["Test 1"]},
        }

        transition = promoter.promote(
            spec_id="test-spec",
            spec_data=spec_data,
            actor="test-user",
            constitution=balanced_constitution,
        )

        assert transition.to_state == SpecState.SPECIFIED


class TestDemotion:
    """Test spec demotion."""

    def test_demote_from_specified_to_draft(self, promoter, complete_spec_data):
        """Can demote from SPECIFIED to DRAFT."""
        complete_spec_data["lifecycle_state"] = "SPECIFIED"

        transition = promoter.demote(
            spec_id="test-spec",
            spec_data=complete_spec_data,
            actor="test-user",
            reason="Requirements changed",
        )

        assert transition.from_state == SpecState.SPECIFIED
        assert transition.to_state == SpecState.DRAFT
        assert transition.reason == "Requirements changed"

    def test_demote_requires_reason(self, promoter, complete_spec_data):
        """Demotion requires a reason."""
        complete_spec_data["lifecycle_state"] = "SPECIFIED"

        with pytest.raises(LifecycleError, match="Reason required"):
            promoter.demote(
                spec_id="test-spec",
                spec_data=complete_spec_data,
                actor="test-user",
                reason="",  # Empty reason
            )

    def test_demote_emits_event(self, promoter, complete_spec_data, event_bus):
        """Demotion emits SPEC_DEMOTED event."""
        complete_spec_data["lifecycle_state"] = "SPECIFIED"
        events_before = len(event_bus.history(EventType.SPEC_DEMOTED))

        promoter.demote(
            spec_id="test-spec",
            spec_data=complete_spec_data,
            actor="test-user",
            reason="Need rework",
        )

        events_after = len(event_bus.history(EventType.SPEC_DEMOTED))
        assert events_after == events_before + 1

    def test_demote_records_transition(self, promoter, complete_spec_data, db_conn):
        """Demotion records transition with reason."""
        complete_spec_data["lifecycle_state"] = "IMPLEMENTING"

        promoter.demote(
            spec_id="test-spec",
            spec_data=complete_spec_data,
            actor="test-user",
            reason="Tests failing",
        )

        cursor = db_conn.execute(
            "SELECT * FROM lifecycle_transitions WHERE spec_id = ?",
            ("test-spec",),
        )
        transitions = cursor.fetchall()
        assert len(transitions) == 1
        assert transitions[0]["reason"] == "Tests failing"

    def test_cannot_demote_from_draft(self, promoter, complete_spec_data):
        """Cannot demote from DRAFT state (no previous state)."""
        complete_spec_data["lifecycle_state"] = "DRAFT"

        with pytest.raises(LifecycleError, match="no previous state"):
            promoter.demote(
                spec_id="test-spec",
                spec_data=complete_spec_data,
                actor="test-user",
                reason="Mistake",
            )


class TestCeremonyGates:
    """Test ceremony gate enforcement."""

    def test_state_ceremony_gates_defined(self):
        """All states have ceremony gates defined."""
        for state in SpecState:
            assert state in STATE_CEREMONY_GATES

    def test_ceremony_gate_increases_with_state(self):
        """Ceremony gates generally increase as states advance."""
        assert STATE_CEREMONY_GATES[SpecState.DRAFT] == 0
        assert STATE_CEREMONY_GATES[SpecState.SPECIFIED] == 2
        assert STATE_CEREMONY_GATES[SpecState.VALIDATING] == 3
        assert STATE_CEREMONY_GATES[SpecState.COMPLETE] == 4

    def test_archived_has_no_gate(self):
        """ARCHIVED state has no ceremony gate."""
        assert STATE_CEREMONY_GATES[SpecState.ARCHIVED] == 0
