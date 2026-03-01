.. _api_reference:

API Reference
=============

The llm-toolkit-schema API surface is organised by module.  All public symbols are
exported at the top-level package under :mod:`llm_toolkit_schema`.

.. toctree::
   :maxdepth: 1

   event
   types
   signing
   redact
   compliance
   export
   stream
   validate
   migrate
   ulid
   exceptions
   models

Module summary
--------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Module
     - Responsibility
   * - :mod:`llm_toolkit_schema.event`
     - :class:`~llm_toolkit_schema.event.LLMEvent` envelope and serialisation
   * - :mod:`llm_toolkit_schema.types`
     - :class:`~llm_toolkit_schema.types.EventType` enum, custom type validation
   * - :mod:`llm_toolkit_schema.signing`
     - HMAC signing, :class:`~llm_toolkit_schema.signing.AuditStream`, chain verification
   * - :mod:`llm_toolkit_schema.redact`
     - :class:`~llm_toolkit_schema.redact.Redactable`, :class:`~llm_toolkit_schema.redact.RedactionPolicy`, PII helpers
   * - :mod:`llm_toolkit_schema.compliance`
     - Compatibility checks, isolation, chain integrity, scope verification
   * - :mod:`llm_toolkit_schema.export`
     - OTLP, Webhook, and JSONL export backends
   * - :mod:`llm_toolkit_schema.stream`
     - :class:`~llm_toolkit_schema.stream.EventStream` multiplexer
   * - :mod:`llm_toolkit_schema.validate`
     - JSON Schema validation helpers
   * - :mod:`llm_toolkit_schema.migrate`
     - :func:`~llm_toolkit_schema.migrate.v1_to_v2` migration scaffold
   * - :mod:`llm_toolkit_schema.ulid`
     - ULID generation and helpers
   * - :mod:`llm_toolkit_schema.exceptions`
     - Package-level exception hierarchy
   * - :mod:`llm_toolkit_schema.models`
     - Shared Pydantic base models
