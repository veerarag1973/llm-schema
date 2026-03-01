"""Multi-tenant data isolation verification for llm-toolkit-schema events.

This module provides programmatic compliance tests that verify events from
different tenants are properly scoped and that no data from one tenant can
leak into another tenant's event stream.

Third-party tools and enterprise compliance frameworks can call these functions
directly — no pytest dependency is required.

Usage
-----
::

    from llm_toolkit_schema.compliance.test_isolation import (
        IsolationResult,
        verify_tenant_isolation,
    )

    events_org_a = build_events(org_id="org-alpha")
    events_org_b = build_events(org_id="org-beta")

    result = verify_tenant_isolation(events_org_a, events_org_b)
    assert result.passed, result.violations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from llm_toolkit_schema.event import Event

__all__: list[str] = [
    "IsolationViolation",
    "IsolationResult",
    "verify_tenant_isolation",
    "verify_events_scoped",
]


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IsolationViolation:
    """A single tenant-isolation non-conformance found during a check.

    Attributes:
        event_id: The ``event_id`` of the offending event.
        violation_type: Short code: ``"missing_org_id"``, ``"mixed_org_ids"``,
            ``"shared_org_id"``, ``"wrong_org_id"``, or ``"wrong_team_id"``.
        detail: Human-readable description of the problem.
    """

    event_id: str
    violation_type: str
    detail: str


@dataclass
class IsolationResult:
    """Result of a multi-tenant isolation compliance check.

    Attributes:
        passed: ``True`` only when zero violations are found.
        violations: Full list of :class:`IsolationViolation` instances.
    """

    passed: bool
    violations: List[IsolationViolation] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.passed


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def verify_tenant_isolation(
    tenant_a_events: Sequence[Event],
    tenant_b_events: Sequence[Event],
    *,
    strict: bool = True,
) -> IsolationResult:
    """Verify that two event sequences belong to separate, non-overlapping tenants.

    Checks performed:

    1. All events in each group share a consistent ``org_id`` value.
    2. Events without ``org_id`` in a multi-tenant context are flagged when
       *strict* is ``True``.
    3. The two tenant groups do not share any ``org_id`` value.

    Args:
        tenant_a_events: Events belonging to the first tenant.
        tenant_b_events: Events belonging to the second tenant.
        strict: When ``True`` (default), events missing ``org_id`` are treated
            as violations.  Set to ``False`` to allow unscoped events.

    Returns:
        An :class:`IsolationResult` with zero violations on success.
    """
    violations: list[IsolationViolation] = []
    violations.extend(_check_org_consistency(tenant_a_events, "tenant_a", strict=strict))
    violations.extend(_check_org_consistency(tenant_b_events, "tenant_b", strict=strict))
    violations.extend(_check_org_disjoint(tenant_a_events, tenant_b_events))
    return IsolationResult(passed=len(violations) == 0, violations=violations)


def verify_events_scoped(
    events: Sequence[Event],
    *,
    expected_org_id: Optional[str] = None,
    expected_team_id: Optional[str] = None,
) -> IsolationResult:
    """Verify that every event belongs to an expected tenant scope.

    Args:
        events: One or more events to inspect.
        expected_org_id: When provided, every event must carry exactly this
            ``org_id``.
        expected_team_id: When provided, every event must carry exactly this
            ``team_id``.

    Returns:
        An :class:`IsolationResult` with zero violations on success.
    """
    violations: list[IsolationViolation] = []
    for evt in events:
        if expected_org_id is not None and evt.org_id != expected_org_id:
            violations.append(
                IsolationViolation(
                    event_id=evt.event_id,
                    violation_type="wrong_org_id",
                    detail=(
                        f"expected org_id={expected_org_id!r}, got {evt.org_id!r}"
                    ),
                )
            )
        if expected_team_id is not None and evt.team_id != expected_team_id:
            violations.append(
                IsolationViolation(
                    event_id=evt.event_id,
                    violation_type="wrong_team_id",
                    detail=(
                        f"expected team_id={expected_team_id!r}, got {evt.team_id!r}"
                    ),
                )
            )
    return IsolationResult(passed=len(violations) == 0, violations=violations)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _check_org_consistency(
    events: Sequence[Event],
    label: str,
    *,
    strict: bool,
) -> list[IsolationViolation]:
    """Verify all events in a single tenant group carry a consistent ``org_id``.

    Two conditions are checked:

    * If *strict* is ``True``, every event must have a non-``None`` ``org_id``.
    * If more than one distinct ``org_id`` value is present, all events that
      deviate from the alphabetically-first value are flagged.
    """
    violations: list[IsolationViolation] = []

    if strict:
        for evt in events:
            if evt.org_id is None:
                violations.append(
                    IsolationViolation(
                        event_id=evt.event_id,
                        violation_type="missing_org_id",
                        detail=f"{label}: event has no org_id in a multi-tenant context",
                    )
                )

    real_org_ids = {evt.org_id for evt in events if evt.org_id is not None}
    if len(real_org_ids) > 1:
        reference = sorted(real_org_ids)[0]  # deterministic: alphabetically first
        for evt in events:
            if evt.org_id is not None and evt.org_id != reference:
                violations.append(
                    IsolationViolation(
                        event_id=evt.event_id,
                        violation_type="mixed_org_ids",
                        detail=(
                            f"{label}: org_id={evt.org_id!r} is inconsistent "
                            f"with expected {reference!r}"
                        ),
                    )
                )

    return violations


def _check_org_disjoint(
    tenant_a_events: Sequence[Event],
    tenant_b_events: Sequence[Event],
) -> list[IsolationViolation]:
    """Return violations if any ``org_id`` appears in both tenant groups."""
    violations: list[IsolationViolation] = []
    org_ids_a = {evt.org_id for evt in tenant_a_events if evt.org_id is not None}
    org_ids_b = {evt.org_id for evt in tenant_b_events if evt.org_id is not None}
    shared = org_ids_a & org_ids_b
    if shared:
        for evt in list(tenant_a_events) + list(tenant_b_events):
            if evt.org_id in shared:
                violations.append(
                    IsolationViolation(
                        event_id=evt.event_id,
                        violation_type="shared_org_id",
                        detail=f"org_id={evt.org_id!r} appears in both tenant groups",
                    )
                )
    return violations
