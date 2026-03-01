.. _changelog:

Changelog
=========

All notable changes to llm-toolkit-schema are documented here.
The format follows `Keep a Changelog <https://keepachangelog.com/>`_ and
this project adheres to `Semantic Versioning <https://semver.org/>`_.

----

Unreleased
----------

*(No unreleased changes.)*

----

1.1.1 — 2026-03-15
--------------------

Fixed
^^^^^

- **``Event.payload``** now returns a read-only ``MappingProxyType``; mutating
  the returned object no longer silently corrupts event state.
- **``EventGovernancePolicy(strict_unknown=True)``** now correctly raises
  ``GovernanceViolationError`` for unregistered event types (was a no-op).
- **``_cli.py``** — broad ``except Exception`` replaced with typed
  ``(DeserializationError, SchemaValidationError, KeyError, TypeError)``.
- **``stream.py``** — broad ``except Exception`` in ``EventStream.from_file``
  and ``EventStream.from_kafka`` replaced with ``(LLMSchemaError, ValueError)``.
- **``validate.py``** — checksum regex tightened to ``^sha256:[0-9a-f]{64}$``
  and signature regex to ``^hmac-sha256:[0-9a-f]{64}$``, aligning with the
  prefixes produced by ``signing.py``.
- **``export/datadog.py``** — fallback IDs use deterministic SHA-256
  derivation; span start uses ``event.timestamp``; ``dd_site`` and
  ``agent_url`` validated on construction.
- **``export/otlp.py``** — ``export_batch`` now chunks by ``batch_size``;
  URL scheme validated on construction.
- **``export/webhook.py``** — URL scheme validated on construction.
- **``export/grafana.py``** — URL scheme validated on construction.
- **``redact.py``** — ``_has_redactable`` / ``_count_redactable`` use
  ``collections.abc.Mapping`` ABC instead of ``dict``.

Added
^^^^^

- **``GuardPolicy``** (``llm_toolkit_schema.namespaces.guard``) — runtime
  input/output guardrail enforcement (fail-open / fail-closed, callable
  checkers).
- **``FencePolicy``** (``llm_toolkit_schema.namespaces.fence``) —
  structured-output validation driver with retry-sequence loop.
- **``TemplatePolicy``** (``llm_toolkit_schema.namespaces.template``) —
  variable presence checking and output validation.
- **``iter_file()``** / **``aiter_file()``** (``llm_toolkit_schema.stream``)
  — synchronous and async generators for memory-efficient NDJSON streaming.

----

1.1.0 — 2026-03-01
--------------------

Added
^^^^^

- **Datadog APM exporter** (``DatadogExporter``, ``DatadogResourceAttributes``)
  — sends events to the Datadog Agent HTTP API as APM trace spans.
- **Grafana Loki exporter** (``GrafanaLokiExporter``) — pushes events to a
  Grafana Loki endpoint as structured log streams.
- **Kafka consumer support** — ``EventStream.from_kafka()`` reads events from
  a Kafka topic using the ``confluent_kafka`` optional extra.
- **Consumer registration API** (``llm_toolkit_schema.consumer``) —
  ``ConsumerRecord``, ``ConsumerRegistry``, ``register_consumer()``,
  ``assert_compatible()``, ``IncompatibleSchemaError``.
- **Schema governance engine** (``llm_toolkit_schema.governance``) —
  ``EventGovernancePolicy``, ``GovernanceViolationError``,
  ``GovernanceWarning``, ``set_global_policy()``, ``get_global_policy()``.
- **Deprecation registry** (``llm_toolkit_schema.deprecations``) —
  ``DeprecationNotice``, ``DeprecationRegistry``, ``mark_deprecated()``,
  ``warn_if_deprecated()``, ``list_deprecated()``.
- **LangChain & LlamaIndex adapters** (``llm_toolkit_schema.integrations``)
  — callback/handler shims for ecosystem observability.
- **v2 migration roadmap** — ``v2_migration_roadmap`` constant and
  ``llm-toolkit-schema migrate`` CLI sub-command.

Changed
^^^^^^^

- Version: ``1.0.1`` → ``1.1.0``

----

1.0.1 — 2026-03-01
--------------------

Changed
^^^^^^^

- **Python package renamed** from ``llm_schema`` to ``llm_toolkit_schema``.
  The import path is now ``import llm_toolkit_schema`` (or
  ``from llm_toolkit_schema import ...``).
  The distribution name ``llm-toolkit-schema`` and all runtime behaviour are
  unchanged.  This is the canonical, permanently stable import name.
- Version: ``1.0.0`` → ``1.0.1``

----

1.0.0 — 2026-03-01
--------------------

**General Availability release.**  The public API is now stable and covered
by semantic versioning guarantees.

Added
^^^^^

- **Compliance package** (``llm_toolkit_schema.compliance``) — programmatic v1.0
  compatibility checklist (CHK-1 through CHK-5), multi-tenant isolation
  verification, and audit chain integrity suite.  All checks are callable
  without a pytest dependency.
- **``test_compatibility()``** — applies the five-point adoption checklist to
  any sequence of events.  Powers the new ``llm-toolkit-schema check-compat`` CLI command.
- **``verify_tenant_isolation()`` / ``verify_events_scoped()``** — detect
  cross-tenant data leakage in multi-org deployments.
- **``verify_chain_integrity()``** — wraps ``verify_chain()`` with gap,
  tamper, and timestamp-monotonicity diagnostics.
- **``llm-toolkit-schema check-compat``** CLI sub-command — reads a JSON file of
  serialised events and prints compatibility violations.
- **``llm_toolkit_schema.migrate``** — ``MigrationResult`` dataclass and
  ``v1_to_v2()`` scaffold (raises ``NotImplementedError``; full implementation
  ships in Phase 9).
- Performance benchmark test suite (``tests/test_benchmarks.py``,
  ``@pytest.mark.perf``) validating all NFR targets.

Changed
^^^^^^^

- Version: ``0.5.0`` → ``1.0.0``
- PyPI classifier: ``Development Status :: 3 - Alpha`` →
  ``Development Status :: 5 - Production/Stable``

----

0.5.0 — 2026-02-22
--------------------

Added
^^^^^

- **Namespace payload dataclasses** for all 10 reserved namespaces
  (``llm.trace.*``, ``llm.cost.*``, ``llm.cache.*``, ``llm.diff.*``,
  ``llm.eval.*``, ``llm.fence.*``, ``llm.guard.*``, ``llm.prompt.*``,
  ``llm.redact.*``, ``llm.template.*``).  The ``llm.trace`` payload is
  **FROZEN** at v1 — no breaking changes permitted.
- **``schemas/v1.0/schema.json``** — published JSON Schema for the event envelope.
- **``validate_event()``** — validates an event against the JSON Schema with an
  optional ``jsonschema`` backend; falls back to structural stdlib checks.

----

0.4.0 — 2026-02-15
--------------------

Added
^^^^^

- **``OTLPExporter``** — async OTLP/HTTP JSON exporter with retry, gzip
  compression, and configurable resource attributes.
- **``WebhookExporter``** — async HTTP webhook exporter with configurable
  headers, retry backoff, and timeout.
- **``JSONLExporter``** — synchronous JSONL file exporter with optional
  per-event gzip compression.
- **``EventStream``** — in-process event router with type filters, org/team
  scoping, sampling, and fan-out to multiple exporters.

----

0.3.0 — 2026-02-08
--------------------

Added
^^^^^

- **``sign()`` / ``verify()``** — HMAC-SHA256 event signing and verification
  (``sha256:`` payload checksum + ``hmac-sha256:`` chain signature).
- **``verify_chain()``** — batch chain verification with gap detection and
  tampered-event identification.
- **``AuditStream``** — sequential event stream that signs and links every
  appended event via ``prev_id``.
- **Key rotation** — ``AuditStream.rotate_key()`` emits a signed rotation
  event and switches the active HMAC key.
- **``assert_verified()``** — strict raising variant of ``verify()``.

----

0.2.0 — 2026-02-01
--------------------

Added
^^^^^

- **PII redaction framework** — ``Redactable``, ``Sensitivity``,
  ``RedactionPolicy``, ``RedactionResult``, ``contains_pii()``,
  ``assert_redacted()``.
- **Pydantic v2 model layer** — ``llm_toolkit_schema.models.EventModel`` with
  ``from_event()`` / ``to_event()`` round-trip and ``model_json_schema()``.

----

0.1.0 — 2026-01-25
--------------------

Added
^^^^^

- **Core ``Event`` dataclass** — frozen, validated, zero external dependencies.
- **``EventType`` enum** — exhaustive registry of all 50+ first-party event types
  across 10 namespaces plus audit types.
- **ULID utilities** — ``generate()``, ``validate()``, ``extract_timestamp_ms()``.
- **``Tags``** dataclass — arbitrary ``str → str`` metadata.
- **JSON serialisation** — ``Event.to_dict()``, ``Event.to_json()``,
  ``Event.from_dict()``, ``Event.from_json()``.
- **``Event.validate()``** — full structural validation of all fields.
- **``is_registered()``**, **``validate_custom()``**, **``namespace_of()``** —
  event-type introspection helpers.
- **Domain exceptions hierarchy** — ``LLMSchemaError`` base with
  ``SchemaValidationError``, ``ULIDError``, ``SerializationError``,
  ``DeserializationError``, ``EventTypeError``.
