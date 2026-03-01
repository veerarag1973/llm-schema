"""llm-schema compliance test suite — v1.0 GA.

This package provides programmatic compliance tests that third-party tools
and enterprise consumers can use to verify their events conform to the
llm-schema contract.

Third-Party Adoption Checklist
------------------------------
To pass ``test_compatibility``, every event must satisfy all five rules:

=========  ==================================================================
Check ID   Rule
=========  ==================================================================
CHK-1      All REQUIRED envelope fields are present and non-empty.
CHK-2      ``event_type`` uses a registered namespace or ``x.*`` prefix.
CHK-3      ``source`` follows the ``<service>@<semver>`` pattern.
CHK-4      ``schema_version`` is present in every event (never omitted).
CHK-5      ``event_id`` is a valid ULID.
=========  ==================================================================

Quick start
-----------
::

    from llm_schema import Event, EventType
    from llm_schema.compliance import test_compatibility

    events = [
        Event(
            event_type=EventType.TRACE_SPAN_COMPLETED,
            source="my-tool@1.0.0",
            payload={"span_name": "run"},
        )
    ]
    result = test_compatibility(events)
    assert result.passed
"""

from llm_schema.compliance._compat import (
    CompatibilityResult,
    CompatibilityViolation,
    test_compatibility,
)
from llm_schema.compliance.test_chain import (
    ChainIntegrityResult,
    ChainIntegrityViolation,
    verify_chain_integrity,
)
from llm_schema.compliance.test_isolation import (
    IsolationResult,
    IsolationViolation,
    verify_events_scoped,
    verify_tenant_isolation,
)

__all__: list[str] = [
    # Compatibility checker (Third-Party Adoption Checklist)
    "test_compatibility",
    "CompatibilityResult",
    "CompatibilityViolation",
    # Audit chain integrity
    "verify_chain_integrity",
    "ChainIntegrityResult",
    "ChainIntegrityViolation",
    # Multi-tenant isolation
    "verify_tenant_isolation",
    "verify_events_scoped",
    "IsolationResult",
    "IsolationViolation",
]
