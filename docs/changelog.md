# Changelog

All notable changes to llm-toolkit-schema are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/) and
this project adheres to [Semantic Versioning](https://semver.org/).

---

## Unreleased

*(No unreleased changes.)*

---

## 1.1.1 — 2026-03-15

### Fixed

- **`Event.payload`** now returns a read-only `MappingProxyType` — mutating
  the returned object no longer silently corrupts event state.
- **`EventGovernancePolicy(strict_unknown=True)`** now correctly raises
  `GovernanceViolationError` for unregistered event types (was a no-op
  previously); docstring corrected to match actual behaviour.
- **`_cli.py`** — broad `except Exception` replaced with typed
  `(DeserializationError, SchemaValidationError, KeyError, TypeError)`,
  preventing silent swallowing of unexpected errors.
- **`stream.py`** — broad `except Exception` in `EventStream.from_file` and
  `EventStream.from_kafka` replaced with `(LLMSchemaError, ValueError)`.
- **`validate.py`** — checksum regex tightened to `^sha256:[0-9a-f]{64}$`
  and signature regex to `^hmac-sha256:[0-9a-f]{64}$`, aligning with the
  prefixes actually produced by `signing.py` (bare 64-hex patterns accepted
  invalid values).
- **`export/datadog.py`**:
  - Fallback span/trace IDs are now deterministic SHA-256 derivations of the
    event ID instead of Python `hash()` (non-reproducible across processes).
  - Span start timestamp uses `event.timestamp` rather than wall-clock time.
  - `dd_site` is validated as a hostname (no scheme/path).
  - `agent_url` is validated as an `http://` or `https://` URL.
- **`export/otlp.py`** — `export_batch` now chunks the event list by
  `batch_size` and issues one request per chunk; previously the parameter
  was accepted but never applied.  URL scheme validated on construction.
- **`export/webhook.py`** — URL scheme validated on construction (`http://`
  or `https://` only).
- **`export/grafana.py`** — URL scheme validated on construction.
- **`redact.py`** — `_has_redactable` / `_count_redactable` use the
  `collections.abc.Mapping` ABC instead of `dict`, so payloads built from
  `MappingProxyType` or other mapping types are handled correctly.

### Added

- **`GuardPolicy`** (`llm_toolkit_schema.namespaces.guard`) — runtime
  input/output guardrail enforcement with configurable fail-open / fail-closed
  mode and callable checker injection.
- **`FencePolicy`** (`llm_toolkit_schema.namespaces.fence`) — structured-output
  validation driver with retry-sequence loop and `max_retries` limit.
- **`TemplatePolicy`** (`llm_toolkit_schema.namespaces.template`) — variable
  presence checking and output validation for prompt-template workflows.
- **`iter_file(path)`** (`llm_toolkit_schema.stream`) — synchronous generator
  that streams events from an NDJSON file without buffering the entire file.
- **`aiter_file(path)`** (`llm_toolkit_schema.stream`) — async-generator
  equivalent of `iter_file`.

---

## 1.1.0 — 2026-03-01

### Added

**Phase 7 — Enterprise Export Backends**

- **`DatadogExporter`** (`llm_toolkit_schema.export.datadog`) — async exporter
  that sends events as Datadog APM trace spans (via the local Agent) and as
  Datadog metrics series (via the public API). No `ddtrace` dependency.
- **`DatadogResourceAttributes`** — frozen dataclass with `service`, `env`,
  `version`, and `extra` fields; `.to_tags()` for tag-string serialisation.
- **`GrafanaLokiExporter`** (`llm_toolkit_schema.export.grafana`) — async
  exporter that pushes events to Grafana Loki via the `/loki/api/v1/push`
  HTTP endpoint. Supports multi-tenant deployments via `X-Scope-OrgID`.
- **`ConsumerRegistry`** / **`ConsumerRecord`** (`llm_toolkit_schema.consumer`)
  — thread-safe registry for declaring schema-namespace dependencies at startup.
  `assert_compatible()` raises `IncompatibleSchemaError` on version mismatches.
- **`EventGovernancePolicy`** (`llm_toolkit_schema.governance`) — data-class
  policy with blocked types, deprecated-type warnings, and arbitrary custom
  rule callbacks. Module-level `set_global_policy()` / `check_event()`.
- **`GovernanceViolationError`**, **`GovernanceWarning`** — governance
  exception and warning types.

**Phase 8 — Ecosystem Integrations & Kafka**

- **`EventStream.from_kafka()`** — classmethod constructor that drains a Kafka
  topic into an `EventStream`. Requires optional extra `kafka`.
- **`DeprecationRegistry`** / **`DeprecationNotice`**
  (`llm_toolkit_schema.deprecations`) — structured per-event-type deprecation
  tracking with `warn_if_deprecated()` and `list_deprecated()`.
- **`LLMSchemaCallbackHandler`** (`llm_toolkit_schema.integrations.langchain`)
  — LangChain `BaseCallbackHandler` that emits `llm.trace.*` events for all LLM
  and tool invocations. Requires optional extra `langchain`.
- **`LLMSchemaEventHandler`** (`llm_toolkit_schema.integrations.llamaindex`)
  — LlamaIndex callback event handler. Requires optional extra `llamaindex`.

**Phase 9 — v2 Migration Framework**

- **`SunsetPolicy`** (`llm_toolkit_schema.migrate`) — `Enum` classifying
  removal urgency: `NEXT_MAJOR`, `NEXT_MINOR`, `LONG_TERM`, `UNSCHEDULED`.
- **`DeprecationRecord`** (`llm_toolkit_schema.migrate`) — frozen dataclass
  capturing `event_type`, `since`, `sunset`, `sunset_policy`, `replacement`,
  `migration_notes`, and `field_renames` for structured migration guidance.
- **`v2_migration_roadmap()`** — returns all 9 deprecation records for event
  types that will change in v2.0, sorted by `event_type`.
- **CLI: `list-deprecated`** — prints all deprecation notices from the global
  registry.
- **CLI: `migration-roadmap [--json]`** — prints the v2 migration roadmap in
  human-readable or JSON form.
- **CLI: `check-consumers`** — lists all registered consumers and their
  compatibility status against the installed schema version.

### Changed

- Version: `1.0.1` → `1.1.0`
- `export/__init__.py` now re-exports `DatadogExporter`,
  `DatadogResourceAttributes`, and `GrafanaLokiExporter`.
- Top-level `llm_toolkit_schema` package re-exports all Phase 7/8/9 public
  symbols.

### Optional extras added

| Extra | Enables |
|-------|---------|
| `kafka` | `EventStream.from_kafka()` via `kafka-python>=2.0` |
| `langchain` | `LLMSchemaCallbackHandler` via `langchain-core>=0.2` |
| `llamaindex` | `LLMSchemaEventHandler` via `llama-index-core>=0.10` |
| `datadog` | `DatadogExporter` (stdlib-only transport; extra reserved for future `ddtrace` integration) |
| `all` | All optional extras in one install target |

---

## 1.0.1 — 2026-03-01

### Changed

- **Python package renamed** from `llm_schema` to `llm_toolkit_schema`.
  The import path is now `import llm_toolkit_schema` (or
  `from llm_toolkit_schema import ...`).
  The distribution name `llm-toolkit-schema` and all runtime behaviour are
  unchanged. This is the canonical, permanently stable import name.
- Version: `1.0.0` → `1.0.1`

---

## 1.0.0 — 2026-03-01

**General Availability release.** The public API is now stable and covered
by semantic versioning guarantees.

### Added

- **Compliance package** (`llm_toolkit_schema.compliance`) — programmatic v1.0
  compatibility checklist (CHK-1 through CHK-5), multi-tenant isolation
  verification, and audit chain integrity suite. All checks are callable
  without a pytest dependency.
- **`test_compatibility()`** — applies the five-point adoption checklist to
  any sequence of events. Powers the new `llm-toolkit-schema check-compat` CLI command.
- **`verify_tenant_isolation()` / `verify_events_scoped()`** — detect
  cross-tenant data leakage in multi-org deployments.
- **`verify_chain_integrity()`** — wraps `verify_chain()` with gap,
  tamper, and timestamp-monotonicity diagnostics.
- **`llm-toolkit-schema check-compat`** CLI sub-command — reads a JSON file of
  serialised events and prints compatibility violations.
- **`llm_toolkit_schema.migrate`** — `MigrationResult` dataclass and
  `v1_to_v2()` scaffold (raises `NotImplementedError`; full implementation
  ships in Phase 9).
- Performance benchmark test suite (`tests/test_benchmarks.py`,
  `@pytest.mark.perf`) validating all NFR targets.

### Changed

- Version: `0.5.0` → `1.0.0`
- PyPI classifier: `Development Status :: 3 - Alpha` →
  `Development Status :: 5 - Production/Stable`

---

## 0.5.0 — 2026-02-22

### Added

- **Namespace payload dataclasses** for all 10 reserved namespaces
  (`llm.trace.*`, `llm.cost.*`, `llm.cache.*`, `llm.diff.*`,
  `llm.eval.*`, `llm.fence.*`, `llm.guard.*`, `llm.prompt.*`,
  `llm.redact.*`, `llm.template.*`). The `llm.trace` payload is
  **FROZEN** at v1 — no breaking changes permitted.
- **`schemas/v1.0/schema.json`** — published JSON Schema for the event envelope.
- **`validate_event()`** — validates an event against the JSON Schema with an
  optional `jsonschema` backend; falls back to structural stdlib checks.

---

## 0.4.0 — 2026-02-15

### Added

- **`OTLPExporter`** — async OTLP/HTTP JSON exporter with retry, gzip
  compression, and configurable resource attributes.
- **`WebhookExporter`** — async HTTP webhook exporter with configurable
  headers, retry backoff, and timeout.
- **`JSONLExporter`** — synchronous JSONL file exporter with optional
  per-event gzip compression.
- **`EventStream`** — in-process event router with type filters, org/team
  scoping, sampling, and fan-out to multiple exporters.

---

## 0.3.0 — 2026-02-08

### Added

- **`sign()` / `verify()`** — HMAC-SHA256 event signing and verification
  (`sha256:` payload checksum + `hmac-sha256:` chain signature).
- **`verify_chain()`** — batch chain verification with gap detection and
  tampered-event identification.
- **`AuditStream`** — sequential event stream that signs and links every
  appended event via `prev_id`.
- **Key rotation** — `AuditStream.rotate_key()` emits a signed rotation
  event and switches the active HMAC key.
- **`assert_verified()`** — strict raising variant of `verify()`.

---

## 0.2.0 — 2026-02-01

### Added

- **PII redaction framework** — `Redactable`, `Sensitivity`,
  `RedactionPolicy`, `RedactionResult`, `contains_pii()`,
  `assert_redacted()`.
- **Pydantic v2 model layer** — `llm_toolkit_schema.models.EventModel` with
  `from_event()` / `to_event()` round-trip and `model_json_schema()`.

---

## 0.1.0 — 2026-01-25

### Added

- **Core `Event` dataclass** — frozen, validated, zero external dependencies.
- **`EventType` enum** — exhaustive registry of all 50+ first-party event types
  across 10 namespaces plus audit types.
- **ULID utilities** — `generate()`, `validate()`, `extract_timestamp_ms()`.
- **`Tags`** dataclass — arbitrary `str → str` metadata.
- **JSON serialisation** — `Event.to_dict()`, `Event.to_json()`,
  `Event.from_dict()`, `Event.from_json()`.
- **`Event.validate()`** — full structural validation of all fields.
- **`is_registered()`**, **`validate_custom()`**, **`namespace_of()`** —
  event-type introspection helpers.
- **Domain exceptions hierarchy** — `LLMSchemaError` base with
  `SchemaValidationError`, `ULIDError`, `SerializationError`,
  `DeserializationError`, `EventTypeError`.
