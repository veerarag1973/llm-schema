"""Audit chain integrity test suite for llm-schema events.

This module verifies that a sequence of signed events forms a valid,
tamper-free cryptographic chain.  It wraps the lower-level
:func:`llm_schema.signing.verify_chain` primitive with higher-level
diagnostics including timestamp monotonicity checks.

Third-party tools and enterprise audit frameworks can call these functions
directly — no pytest dependency is required.

Usage
-----
::

    from llm_schema.compliance.test_chain import (
        ChainIntegrityResult,
        verify_chain_integrity,
    )

    result = verify_chain_integrity(events, org_secret="my-org-secret")
    if not result:
        for v in result.violations:
            print(v.violation_type, v.detail)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from llm_schema.event import Event
from llm_schema.signing import ChainVerificationResult, verify_chain

__all__: list[str] = [
    "ChainIntegrityViolation",
    "ChainIntegrityResult",
    "verify_chain_integrity",
]


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChainIntegrityViolation:
    """A single chain-integrity non-conformance found during a check.

    Attributes:
        violation_type: Short code: ``"tampered"``, ``"gap"``, or
            ``"non_monotonic_timestamp"``.
        event_id: The ``event_id`` of the offending event, when applicable.
        detail: Human-readable description of the problem.
    """

    violation_type: str
    event_id: Optional[str]
    detail: str


@dataclass
class ChainIntegrityResult:
    """Result of an audit chain integrity compliance check.

    Attributes:
        passed: ``True`` only when zero violations are found.
        chain_result: The underlying :class:`~llm_schema.signing.ChainVerificationResult`,
            or ``None`` when the event list was empty.
        violations: Full list of :class:`ChainIntegrityViolation` instances.
        events_verified: How many events were inspected.
        gaps_detected: Number of detected chain gaps (missing events).
    """

    passed: bool
    chain_result: Optional[ChainVerificationResult]
    violations: List[ChainIntegrityViolation] = field(default_factory=list)
    events_verified: int = 0
    gaps_detected: int = 0

    def __bool__(self) -> bool:
        return self.passed


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def verify_chain_integrity(
    events: Sequence[Event],
    org_secret: str,
    *,
    check_monotonic_timestamps: bool = True,
) -> ChainIntegrityResult:
    """Verify that *events* form an intact, tamper-free audit chain.

    Checks performed:

    1. **Cryptographic integrity** — each event's HMAC matches its predecessor
       via :func:`llm_schema.signing.verify_chain`.
    2. **Gap detection** — any missing events in the chain are flagged.
    3. **Timestamp monotonicity** (optional) — events must not travel backward
       in time.

    Args:
        events: Ordered sequence of events to verify.
        org_secret: Shared secret used when the events were signed.
        check_monotonic_timestamps: When ``True`` (default), flag any event
            whose timestamp is earlier than the preceding event.

    Returns:
        A :class:`ChainIntegrityResult`.  Check :attr:`~ChainIntegrityResult.passed`
        or use it in a boolean context to determine compliance.
    """
    # Fast path — empty input is trivially valid
    if not events:
        return ChainIntegrityResult(
            passed=True,
            chain_result=None,
            violations=[],
            events_verified=0,
            gaps_detected=0,
        )

    event_list = list(events)
    violations: list[ChainIntegrityViolation] = []

    chain_result = verify_chain(event_list, org_secret=org_secret)

    # Tamper detection
    if not chain_result.valid and chain_result.first_tampered is not None:
        violations.append(
            ChainIntegrityViolation(
                violation_type="tampered",
                event_id=chain_result.first_tampered,
                detail=(
                    f"event {chain_result.first_tampered!r} failed HMAC verification; "
                    f"{chain_result.tampered_count} tampered event(s) total"
                ),
            )
        )

    # Gap detection
    for gap_event_id in chain_result.gaps:
        violations.append(
            ChainIntegrityViolation(
                violation_type="gap",
                event_id=gap_event_id,
                detail=f"chain gap detected before event {gap_event_id!r}",
            )
        )

    # Optional timestamp monotonicity check
    if check_monotonic_timestamps:
        violations.extend(_check_monotonic_timestamps(event_list))

    return ChainIntegrityResult(
        passed=len(violations) == 0,
        chain_result=chain_result,
        violations=violations,
        events_verified=len(event_list),
        gaps_detected=len(chain_result.gaps),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _check_monotonic_timestamps(events: list[Event]) -> list[ChainIntegrityViolation]:
    """Return violations for consecutive events where time moves backward."""
    violations: list[ChainIntegrityViolation] = []
    for prev, curr in zip(events, events[1:]):
        if curr.timestamp < prev.timestamp:
            violations.append(
                ChainIntegrityViolation(
                    violation_type="non_monotonic_timestamp",
                    event_id=curr.event_id,
                    detail=(
                        f"timestamp {curr.timestamp!r} is earlier than "
                        f"preceding event timestamp {prev.timestamp!r}"
                    ),
                )
            )
    return violations
