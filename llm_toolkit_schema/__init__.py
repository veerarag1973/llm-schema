"""llm-toolkit-schema — Shared Event Schema for the LLM Developer Toolkit.

This package provides the foundational event contract used by every tool in
the LLM Developer Toolkit.  It is OpenTelemetry-compatible, versioned, and
designed for enterprise-grade observability.

Quick start
-----------
::

    from llm_toolkit_schema import Event, EventType, Tags

    event = Event(
        event_type=EventType.TRACE_SPAN_COMPLETED,
        source="llm-trace@0.3.1",
        payload={"span_name": "run_agent", "status": "ok"},
        tags=Tags(env="production", model="gpt-4o"),
    )
    event.validate()
    print(event.to_json())

PII redaction (v0.2+)
---------------------
::

    from llm_toolkit_schema import Event, EventType
    from llm_toolkit_schema.redact import Redactable, RedactionPolicy, Sensitivity

    policy = RedactionPolicy(min_sensitivity=Sensitivity.PII, redacted_by="policy:corp")
    event = Event(
        event_type=EventType.PROMPT_SAVED,
        source="promptlock@1.0.0",
        payload={"author": Redactable("alice@example.com", Sensitivity.PII, {"email"})},
    )
    result = policy.apply(event)

Pydantic models (optional, requires pydantic>=2.7)
--------------------------------------------------
::

    from llm_toolkit_schema.models import EventModel
    model = EventModel.from_event(event)
    print(model.model_json_schema())

HMAC signing & audit chain (v0.3+)
-----------------------------------
::

    from llm_toolkit_schema.signing import sign, verify, verify_chain, AuditStream

    # Sign individual events
    signed = sign(event, org_secret="my-secret")
    assert verify(signed, org_secret="my-secret")

    # Build a tamper-evident chain
    stream = AuditStream(org_secret="my-secret", source="signing-daemon@1.0.0")
    for evt in events:
        stream.append(evt)
    result = stream.verify()
    assert result.valid

Public API
----------
The following names are the stable, supported public interface.

* :class:`~llm_toolkit_schema.event.Event`
* :class:`~llm_toolkit_schema.event.Tags`
* :class:`~llm_toolkit_schema.types.EventType`
* :data:`~llm_toolkit_schema.event.SCHEMA_VERSION`
* :func:`~llm_toolkit_schema.ulid.generate`
* :func:`~llm_toolkit_schema.ulid.validate`
* :func:`~llm_toolkit_schema.ulid.extract_timestamp_ms`
* :func:`~llm_toolkit_schema.types.is_registered`
* :func:`~llm_toolkit_schema.types.namespace_of`
* :func:`~llm_toolkit_schema.types.validate_custom`
* :func:`~llm_toolkit_schema.types.get_by_value`
* :class:`~llm_toolkit_schema.exceptions.LLMSchemaError`
* :class:`~llm_toolkit_schema.exceptions.SchemaValidationError`
* :class:`~llm_toolkit_schema.exceptions.ULIDError`
* :class:`~llm_toolkit_schema.exceptions.SerializationError`
* :class:`~llm_toolkit_schema.exceptions.DeserializationError`
* :class:`~llm_toolkit_schema.exceptions.EventTypeError`
* :class:`~llm_toolkit_schema.exceptions.SigningError`
* :class:`~llm_toolkit_schema.exceptions.VerificationError`
* :class:`~llm_toolkit_schema.redact.Sensitivity`
* :class:`~llm_toolkit_schema.redact.Redactable`
* :class:`~llm_toolkit_schema.redact.RedactionPolicy`
* :class:`~llm_toolkit_schema.redact.RedactionResult`
* :class:`~llm_toolkit_schema.redact.PIINotRedactedError`
* :func:`~llm_toolkit_schema.redact.contains_pii`
* :func:`~llm_toolkit_schema.redact.assert_redacted`
* :func:`~llm_toolkit_schema.signing.sign`
* :func:`~llm_toolkit_schema.signing.verify`
* :func:`~llm_toolkit_schema.signing.verify_chain`
* :func:`~llm_toolkit_schema.signing.assert_verified`
* :class:`~llm_toolkit_schema.signing.ChainVerificationResult`
* :class:`~llm_toolkit_schema.signing.AuditStream`
* :class:`~llm_toolkit_schema.export.otlp.OTLPExporter`
* :class:`~llm_toolkit_schema.export.otlp.ResourceAttributes`
* :class:`~llm_toolkit_schema.export.webhook.WebhookExporter`
* :class:`~llm_toolkit_schema.export.jsonl.JSONLExporter`
* :class:`~llm_toolkit_schema.stream.EventStream`
* :class:`~llm_toolkit_schema.stream.Exporter`
* :class:`~llm_toolkit_schema.exceptions.ExportError`
* :func:`~llm_toolkit_schema.validate.validate_event`
* Namespace payloads (v0.5): :mod:`llm_toolkit_schema.namespaces` — see sub-module
  docs for :class:`~llm_toolkit_schema.namespaces.trace.SpanCompletedPayload`
  (**FROZEN v1**), :class:`~llm_toolkit_schema.namespaces.cost.CostRecordedPayload`,
  :class:`~llm_toolkit_schema.namespaces.eval_.EvalScenarioPayload`, and all others.

Version history
---------------
v0.1 — Core ``Event``, ``EventType``, ULID, JSON serialisation, validation.
        Zero external dependencies.
v0.2 — PII redaction framework (``Redactable``, ``RedactionPolicy``,
        ``Sensitivity``).  Pydantic v2 model layer (``llm_toolkit_schema.models``).
v0.3 — HMAC-SHA256 signing (``sign``, ``verify``), tamper-evident audit chain
        (``verify_chain``, ``AuditStream``), key rotation, gap detection.
v0.4 — OTLP/JSON export (``OTLPExporter``), HTTP webhook export
        (``WebhookExporter``), JSONL file export (``JSONLExporter``),
        ``EventStream`` with filtering and routing.
v0.5 — Namespace payload dataclasses for all 10 reserved namespaces
        (``llm_toolkit_schema.namespaces``).  Published JSON Schema
        (``schemas/v1.0/schema.json``).  ``validate_event()`` for schema
        validation with optional ``jsonschema`` backend.
v1.0 — Production-ready GA release.  Compliance toolkit
        (``llm_toolkit_schema.compliance``) with multi-tenant isolation checks,
        audit chain integrity verification, and third-party compatibility
        checker.  Migration scaffold ``llm_toolkit_schema.migrate.v1_to_v2``.
        ``llm-toolkit-schema check-compat`` CLI command.
"""

from llm_toolkit_schema.event import SCHEMA_VERSION, Event, Tags
from llm_toolkit_schema.exceptions import (
    DeserializationError,
    EventTypeError,
    ExportError,
    LLMSchemaError,
    SchemaValidationError,
    SerializationError,
    SigningError,
    ULIDError,
    VerificationError,
)
from llm_toolkit_schema.redact import (
    PIINotRedactedError,
    PII_TYPES,
    Redactable,
    RedactionPolicy,
    RedactionResult,
    Sensitivity,
    assert_redacted,
    contains_pii,
)
from llm_toolkit_schema.signing import (
    AuditStream,
    ChainVerificationResult,
    assert_verified,
    sign,
    verify,
    verify_chain,
)
from llm_toolkit_schema.types import (
    EventType,
    get_by_value,
    is_registered,
    namespace_of,
    validate_custom,
)
from llm_toolkit_schema.ulid import extract_timestamp_ms
from llm_toolkit_schema.ulid import generate as generate_ulid
from llm_toolkit_schema.ulid import validate as validate_ulid

from llm_toolkit_schema.export import JSONLExporter, OTLPExporter, ResourceAttributes, WebhookExporter
from llm_toolkit_schema.stream import EventStream, Exporter
from llm_toolkit_schema.validate import validate_event
from llm_toolkit_schema.compliance import (
    CompatibilityResult,
    CompatibilityViolation,
    ChainIntegrityResult,
    ChainIntegrityViolation,
    IsolationResult,
    IsolationViolation,
    test_compatibility,
    verify_chain_integrity,
    verify_events_scoped,
    verify_tenant_isolation,
)
from llm_toolkit_schema.migrate import MigrationResult, v1_to_v2
from llm_toolkit_schema.namespaces import (
    # cache
    CacheEvictedPayload,
    CacheHitPayload,
    CacheMissPayload,
    # cost
    BudgetThresholdPayload,
    CostRecordedPayload,
    # diff
    DiffComparisonPayload,
    DiffReportPayload,
    # eval
    EvalRegressionPayload,
    EvalScenarioPayload,
    # fence
    FenceValidationFailedPayload,
    RetryTriggeredPayload,
    ValidationPassedPayload,
    # guard
    GuardBlockedPayload,
    GuardFlaggedPayload,
    # prompt
    PromptApprovedPayload,
    PromptPromotedPayload,
    PromptRolledBackPayload,
    PromptSavedPayload,
    # redact (namespace)
    PIIDetectedPayload,
    PIIRedactedPayload,
    ScanCompletedPayload,
    # template
    TemplateRenderedPayload,
    TemplateValidationFailedPayload,
    VariableMissingPayload,
    # trace (FROZEN v1)
    ModelInfo,
    SpanCompletedPayload,
    TokenUsage,
    ToolCall,
)

__version__: str = "1.0.1"
__all__: list[str] = [
    # Core
    "Event",
    "Tags",
    "EventType",
    "SCHEMA_VERSION",
    # ULID
    "generate_ulid",
    "validate_ulid",
    "extract_timestamp_ms",
    # EventType helpers
    "is_registered",
    "namespace_of",
    "validate_custom",
    "get_by_value",
    # PII Redaction (v0.2)
    "Sensitivity",
    "Redactable",
    "RedactionPolicy",
    "RedactionResult",
    "PIINotRedactedError",
    "contains_pii",
    "assert_redacted",
    "PII_TYPES",
    # HMAC Signing & Audit Chain (v0.3)
    "sign",
    "verify",
    "verify_chain",
    "assert_verified",
    "ChainVerificationResult",
    "AuditStream",
    # Export backends (v0.4)
    "OTLPExporter",
    "ResourceAttributes",
    "WebhookExporter",
    "JSONLExporter",
    # Event routing (v0.4)
    "EventStream",
    "Exporter",
    # Exceptions
    "LLMSchemaError",
    "SchemaValidationError",
    "ULIDError",
    "SerializationError",
    "DeserializationError",
    "EventTypeError",
    "SigningError",
    "VerificationError",
    "ExportError",
    # Validation (v0.5)
    "validate_event",
    # Namespace payloads (v0.5) — cache
    "CacheHitPayload",
    "CacheMissPayload",
    "CacheEvictedPayload",
    # Namespace payloads (v0.5) — cost
    "CostRecordedPayload",
    "BudgetThresholdPayload",
    # Namespace payloads (v0.5) — diff
    "DiffComparisonPayload",
    "DiffReportPayload",
    # Namespace payloads (v0.5) — eval
    "EvalScenarioPayload",
    "EvalRegressionPayload",
    # Namespace payloads (v0.5) — fence
    "ValidationPassedPayload",
    "FenceValidationFailedPayload",
    "RetryTriggeredPayload",
    # Namespace payloads (v0.5) — guard
    "GuardBlockedPayload",
    "GuardFlaggedPayload",
    # Namespace payloads (v0.5) — prompt
    "PromptSavedPayload",
    "PromptPromotedPayload",
    "PromptApprovedPayload",
    "PromptRolledBackPayload",
    # Namespace payloads (v0.5) — redact namespace
    "PIIDetectedPayload",
    "PIIRedactedPayload",
    "ScanCompletedPayload",
    # Namespace payloads (v0.5) — template
    "TemplateRenderedPayload",
    "VariableMissingPayload",
    "TemplateValidationFailedPayload",
    # Namespace payloads (v0.5) — trace (FROZEN v1)
    "TokenUsage",
    "ModelInfo",
    "ToolCall",
    "SpanCompletedPayload",
    # Compliance toolkit (v1.0)
    "test_compatibility",
    "CompatibilityResult",
    "CompatibilityViolation",
    "verify_chain_integrity",
    "ChainIntegrityResult",
    "ChainIntegrityViolation",
    "verify_tenant_isolation",
    "verify_events_scoped",
    "IsolationResult",
    "IsolationViolation",
    # Migration scaffold (v1.0)
    "MigrationResult",
    "v1_to_v2",
    # Metadata
    "__version__",
]
