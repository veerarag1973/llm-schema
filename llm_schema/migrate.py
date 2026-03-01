"""Migration helpers for llm-schema events.

This module provides forward-migration utilities for transforming events from
one schema version to the next.  Implementations are added incrementally in
subsequent minor releases; until then, calling these functions raises
:exc:`NotImplementedError` so that integrators can write the call-site today
and receive a working implementation when it ships.

Usage
-----
::

    from llm_schema.migrate import v1_to_v2, MigrationResult

    # Raises NotImplementedError in v1.0 — wires up the call-site now.
    event_v2, result = v1_to_v2(event_v1)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from llm_schema.event import Event

__all__: list[str] = [
    "MigrationResult",
    "v1_to_v2",
]


@dataclass(frozen=True)
class MigrationResult:
    """Metadata about a completed migration operation.

    Attributes:
        source_version: The schema version the event was migrated *from*.
        target_version: The schema version the event was migrated *to*.
        event_id: The ``event_id`` of the event that was transformed.
        success: ``True`` when the migration completed without errors.
        transformed_fields: Names of the event fields that were modified.
        warnings: Any non-fatal issues encountered during migration.
    """

    source_version: str
    target_version: str
    event_id: str
    success: bool
    transformed_fields: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()


def v1_to_v2(event: "Event") -> "Tuple[Event, MigrationResult]":
    """Migrate a v1.0 event to the v2.0 schema.

    .. note::
        This function is a **scaffold** for the upcoming Phase 9 migration
        work.  It raises :exc:`NotImplementedError` in the v1.0 release.
        Write the call-site now and upgrade to the full implementation when
        v2.0 is released.

    Args:
        event: A v1.0 :class:`~llm_schema.event.Event` to migrate.

    Returns:
        A ``(event_v2, MigrationResult)`` tuple.

    Raises:
        NotImplementedError: Always — v2 schema is not yet defined.
    """
    raise NotImplementedError(
        "v1_to_v2 is a scaffold for Phase 9; the v2.0 schema is not yet defined. "
        "This function will be implemented in a future release."
    )
