"""Third-party adoption compatibility checker for llm-toolkit-schema events.

This module provides the :func:`test_compatibility` function that applies the
llm-toolkit-schema v1.0 compatibility checklist to a sequence of events.  The checks
are numbered **CHK-1** through **CHK-5** so that compliance reports can
reference them unambiguously.

Third-party tools and enterprise compliance frameworks can call these functions
directly — no pytest dependency is required.

Usage
-----
::

    from llm_toolkit_schema.compliance import test_compatibility

    result = test_compatibility(my_events)
    if not result:
        for v in result.violations:
            print(f"[{v.check_id}] {v.rule}: {v.detail}")

Checks
------
CHK-1 — Required fields present
    ``schema_version``, ``source``, and ``payload`` must all be non-empty.

CHK-2 — Event type is registered or valid custom
    If the event type matches a registered llm-toolkit-schema namespace it passes.
    Otherwise it must conform to the custom event-type format
    (``x.`` prefix, ``name@major.minor`` pattern).

CHK-3 — Source identifier format
    ``source`` must match ``^[a-z][a-z0-9-]*@\\d+\\.\\d+(.\\d+)?([.-][a-z0-9]+)*$``.

CHK-5 — Event ID is a valid ULID
    ``event_id`` must be a well-formed 26-character ULID string.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from llm_toolkit_schema.event import Event
from llm_toolkit_schema.exceptions import EventTypeError
from llm_toolkit_schema.types import is_registered, validate_custom
from llm_toolkit_schema.ulid import validate as validate_ulid

__all__: list[str] = [
    "CompatibilityViolation",
    "CompatibilityResult",
    "test_compatibility",
]

# CHK-3 — source identifier pattern
# Pattern: identifier@semver — e.g. "my-service@1.2.3" or "sdk@2.0.0-beta.1"
_SOURCE_RE = re.compile(
    r"^[a-z][a-z0-9-]*@\d+\.\d+(\.\d+)?([.-][a-z0-9]+)*$"
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompatibilityViolation:
    """A single compatibility non-conformance found during a check.

    Attributes:
        check_id: Numeric code, e.g. ``"CHK-1"``.
        rule: Short description of the rule that was violated.
        detail: Human-readable description of the specific problem.
        event_id: The ``event_id`` of the offending event.
    """

    check_id: str
    rule: str
    detail: str
    event_id: str


@dataclass
class CompatibilityResult:
    """Result of a compatibility compliance check across a batch of events.

    Attributes:
        passed: ``True`` only when zero violations are found.
        events_checked: Number of events that were inspected.
        violations: Full list of :class:`CompatibilityViolation` instances.
    """

    passed: bool
    events_checked: int
    violations: List[CompatibilityViolation] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.passed


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def test_compatibility(events: Sequence[Event]) -> CompatibilityResult:
    """Apply the llm-toolkit-schema v1.0 compatibility checklist to *events*.

    Args:
        events: One or more :class:`~llm_toolkit_schema.event.Event` instances to
            inspect.

    Returns:
        A :class:`CompatibilityResult`.  Use it in a boolean context or
        inspect :attr:`~CompatibilityResult.violations` for details.
    """
    violations: list[CompatibilityViolation] = []
    for evt in events:
        violations.extend(_check_event(evt))
    return CompatibilityResult(
        passed=len(violations) == 0,
        events_checked=len(events),
        violations=violations,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _check_event(event: Event) -> list[CompatibilityViolation]:
    """Run all compatibility checks against a single *event*."""
    violations: list[CompatibilityViolation] = []

    # ------------------------------------------------------------------
    # CHK-1: Required fields must be non-empty
    # ------------------------------------------------------------------
    if not event.schema_version:
        violations.append(
            CompatibilityViolation(
                check_id="CHK-1",
                rule="Required fields present",
                detail="schema_version is empty",
                event_id=event.event_id,
            )
        )
    if not event.source:
        violations.append(
            CompatibilityViolation(
                check_id="CHK-1",
                rule="Required fields present",
                detail="source is empty",
                event_id=event.event_id,
            )
        )
    if not event.payload:
        violations.append(
            CompatibilityViolation(
                check_id="CHK-1",
                rule="Required fields present",
                detail="payload is empty",
                event_id=event.event_id,
            )
        )

    # ------------------------------------------------------------------
    # CHK-2: Event type is registered or valid custom
    # ------------------------------------------------------------------
    event_type_str = event.event_type  # always a str via @property
    if not is_registered(event_type_str):
        try:
            validate_custom(event_type_str)
        except EventTypeError as exc:
            violations.append(
                CompatibilityViolation(
                    check_id="CHK-2",
                    rule="Event type is registered or valid custom",
                    detail=str(exc),
                    event_id=event.event_id,
                )
            )

    # ------------------------------------------------------------------
    # CHK-3: Source identifier format
    # ------------------------------------------------------------------
    if event.source and not _SOURCE_RE.match(event.source):
        violations.append(
            CompatibilityViolation(
                check_id="CHK-3",
                rule="Source identifier format",
                detail=(
                    f"source {event.source!r} does not match "
                    r"^[a-z][a-z0-9-]*@\d+\.\d+(\.\d+)?([.-][a-z0-9]+)*$"
                ),
                event_id=event.event_id,
            )
        )

    # ------------------------------------------------------------------
    # CHK-5: Event ID must be a valid ULID
    # ------------------------------------------------------------------
    if not validate_ulid(event.event_id):
        violations.append(
            CompatibilityViolation(
                check_id="CHK-5",
                rule="Event ID is a valid ULID",
                detail=f"event_id {event.event_id!r} is not a valid ULID",
                event_id=event.event_id,
            )
        )

    return violations
