"""Tests for llm_schema.migrate.

Covers:
- MigrationResult dataclass (creation, field access, immutability)
- v1_to_v2() raises NotImplementedError (scaffold behaviour)
"""

from __future__ import annotations

import pytest

from llm_schema.migrate import MigrationResult, v1_to_v2
from llm_schema import Event, EventType


# ---------------------------------------------------------------------------
# MigrationResult
# ---------------------------------------------------------------------------


class TestMigrationResult:
    def test_required_fields(self) -> None:
        result = MigrationResult(
            source_version="1.0",
            target_version="2.0",
            event_id="evt-abc",
            success=True,
        )
        assert result.source_version == "1.0"
        assert result.target_version == "2.0"
        assert result.event_id == "evt-abc"
        assert result.success is True

    def test_default_optional_fields(self) -> None:
        result = MigrationResult(
            source_version="1.0",
            target_version="2.0",
            event_id="evt-abc",
            success=True,
        )
        assert result.transformed_fields == ()
        assert result.warnings == ()

    def test_optional_fields_explicit(self) -> None:
        result = MigrationResult(
            source_version="1.0",
            target_version="2.0",
            event_id="evt-abc",
            success=False,
            transformed_fields=("payload", "event_type"),
            warnings=("unknown field 'foo' ignored",),
        )
        assert result.transformed_fields == ("payload", "event_type")
        assert result.warnings == ("unknown field 'foo' ignored",)

    def test_frozen_immutability(self) -> None:
        result = MigrationResult(
            source_version="1.0",
            target_version="2.0",
            event_id="evt-abc",
            success=True,
        )
        with pytest.raises((TypeError, AttributeError)):
            result.success = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# v1_to_v2
# ---------------------------------------------------------------------------


class TestV1ToV2:
    def test_raises_not_implemented(self) -> None:
        """v1_to_v2 is a Phase 9 scaffold — must raise NotImplementedError."""
        evt = Event(
            event_type=EventType.TRACE_SPAN_COMPLETED,
            source="llm-trace@0.3.1",
            payload={"span_name": "test"},
        )
        with pytest.raises(NotImplementedError):
            v1_to_v2(evt)

    def test_error_message_informative(self) -> None:
        """The NotImplementedError message references the migration scaffold."""
        evt = Event(
            event_type=EventType.TRACE_SPAN_COMPLETED,
            source="llm-trace@0.3.1",
            payload={"span_name": "test"},
        )
        with pytest.raises(NotImplementedError, match="v1_to_v2"):
            v1_to_v2(evt)
