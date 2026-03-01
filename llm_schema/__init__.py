"""llm-schema — Shared Event Schema for the LLM Developer Toolkit.

This package provides the foundational event contract used by every tool in
the LLM Developer Toolkit.  It is OpenTelemetry-compatible, versioned, and
designed for enterprise-grade observability.

Quick start
-----------
::

    from llm_schema import Event, EventType, Tags

    event = Event(
        event_type=EventType.TRACE_SPAN_COMPLETED,
        source="llm-trace@0.3.1",
        payload={"span_name": "run_agent", "status": "ok"},
        tags=Tags(env="production", model="gpt-4o"),
    )
    event.validate()
    print(event.to_json())

Public API
----------
The following names are the stable, supported public interface.

* :class:`~llm_schema.event.Event`
* :class:`~llm_schema.event.Tags`
* :class:`~llm_schema.types.EventType`
* :data:`~llm_schema.event.SCHEMA_VERSION`
* :func:`~llm_schema.ulid.generate`
* :func:`~llm_schema.ulid.validate`
* :func:`~llm_schema.ulid.extract_timestamp_ms`
* :func:`~llm_schema.types.is_registered`
* :func:`~llm_schema.types.namespace_of`
* :func:`~llm_schema.types.validate_custom`
* :func:`~llm_schema.types.get_by_value`
* :class:`~llm_schema.exceptions.LLMSchemaError`
* :class:`~llm_schema.exceptions.SchemaValidationError`
* :class:`~llm_schema.exceptions.ULIDError`
* :class:`~llm_schema.exceptions.SerializationError`
* :class:`~llm_schema.exceptions.DeserializationError`
* :class:`~llm_schema.exceptions.EventTypeError`

Version history
---------------
v0.1 — Core ``Event``, ``EventType``, ULID, JSON serialisation, validation.
        Zero external dependencies.
"""

from llm_schema.event import SCHEMA_VERSION, Event, Tags
from llm_schema.exceptions import (
    DeserializationError,
    EventTypeError,
    LLMSchemaError,
    SchemaValidationError,
    SerializationError,
    ULIDError,
)
from llm_schema.types import (
    EventType,
    get_by_value,
    is_registered,
    namespace_of,
    validate_custom,
)
from llm_schema.ulid import extract_timestamp_ms
from llm_schema.ulid import generate as generate_ulid
from llm_schema.ulid import validate as validate_ulid

__version__: str = "0.1.0"
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
    # Exceptions
    "LLMSchemaError",
    "SchemaValidationError",
    "ULIDError",
    "SerializationError",
    "DeserializationError",
    "EventTypeError",
    # Metadata
    "__version__",
]
