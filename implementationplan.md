# llm-toolkit-schema — Implementation Plan
**Enterprise Product Specification v1.0 | February 2026**

> **The One Rule:** Do not start building `promptlock`, `llm-trace`, or any other tool until `llm-toolkit-schema v0.5` is complete and all namespace payload schemas are defined and reviewed.

---

## Overview

`llm-toolkit-schema` is the foundational shared event contract for the entire LLM Developer Toolkit. It transforms 17 independent utilities into a composable ecosystem by providing an OpenTelemetry-compatible, versioned, enterprise-grade event schema.

**Build Order:** #1 — Before Everything  
**Language:** Python 3.9+  
**Type:** Python Library  

---

## Phase 1 — Core Foundations (Week 1 → v0.1)

**Goal:** Establish the base event envelope with zero external dependencies.

### Deliverables

| Task | Details |
|------|---------|
| Repository setup | `pyproject.toml`, CI pipeline, linting, type-checking |
| `llm_toolkit_schema/event.py` | Base `Event` dataclass with all envelope fields |
| `llm_toolkit_schema/types.py` | `EventType` enum with all namespaced event type strings |
| `llm_toolkit_schema/ulid.py` | ULID generation — zero external dependencies |
| `llm_toolkit_schema/__init__.py` | Public API: `Event`, `EventType`, `Tags` |
| JSON serialisation | Canonical, deterministic `event.to_json()` — same event always produces same JSON |
| Basic validation | Field presence checks; typed `SchemaValidationError` exceptions — no bare raises |
| Unit tests | 100% coverage on `Event` creation, serialisation, and validation |

### Base Event Envelope Fields

```
REQUIRED: schema_version, event_id (ULID), event_type (namespaced), timestamp (UTC ISO-8601), source (tool@semver), payload
OPTIONAL: trace_id, span_id, parent_span_id, org_id, team_id, actor_id, session_id, tags, checksum, signature, prev_id
```

### Design Constraints to Enforce from Day 1

- Event IDs **must** be ULIDs (sortable, unique, no coordination required)
- `event_type` **must** follow `llm.<tool-namespace>.<entity>.<action>` pattern
- Every validation error **must** be a typed exception
- No OS-specific code; target Windows, macOS, Linux

### Exit Criteria

- `Event` can be created, validated, and serialised to JSON
- `EventType` enum covers all 10 tool namespaces
- Zero external package dependencies for core event creation
- All tests pass on Python 3.9, 3.10, 3.11, 3.12

---

## Phase 2 — Pydantic Models & PII Redaction (Week 2 → v0.2)

**Goal:** Strong typing via Pydantic and a complete PII redaction framework.

### Deliverables

| Task | Details |
|------|---------|
| `llm_toolkit_schema/redact.py` | `Redactable`, `RedactionPolicy`, `Sensitivity` levels |
| Pydantic model layer | Pydantic v2 models wrapping all envelope and payload fields |
| Redaction flow | `__redactable`, `__sensitivity`, `__pii_types` marker support |
| `policy.apply(event)` | Scrubs content; preserves structure; records `__redacted_at`, `__redacted_by` |
| `contains_pii()` | Post-redaction assertion — raises if PII detected after applying policy |
| Security constraints | Redactable content **never** appears in exception messages or stack traces |
| Unit tests | Redaction round-trips, sensitivity levels, policy configuration |

### Redaction Sensitivity Levels

`low` → `medium` → `high` → `pii` → `phi`

### Key Design Rules

- Redaction is opt-in **per field**, not per event
- Policies are configured per org / per event type / per sensitivity level — not hardcoded in tools
- Every redaction must emit an `llm.redact.pii.redacted` event (auditable, contains no PII itself)
- Static analysis tooling must flag unmarked string fields automatically (risk mitigation)

### Exit Criteria

- All payload fields that may contain PII are wrapped in `Redactable`
- `RedactionPolicy.apply()` preserves structure and marks redacted fields correctly
- `contains_pii()` assertion works reliably post-redaction
- Security review of all payload schemas is scheduled before v1.0 freeze

---

## Phase 3 — HMAC Signing & Tamper-Evident Audit Chain (Week 3 → v0.3)

**Goal:** Provide compliance-grade audit log integrity without a blockchain or external service.

### Deliverables

| Task | Details |
|------|---------|
| `llm_toolkit_schema/signing.py` | `sign()`, `verify()`, `verify_chain()` |
| Checksum computation | `checksum = SHA-256` of canonical JSON of `payload` |
| Chain signature | `signature = HMAC-SHA256(event_id + checksum + prev_id, org_secret)` |
| `AuditStream` class | Sequential event stream with chain linkage via `prev_id` |
| Gap detection | Missing `prev_id` links (deletions) are visible — not just modifications |
| Key rotation event | Key rotation is itself a schema-level audit event in the chain |
| `verify_chain()` API | Returns `valid`, `first_tampered` event_id, and list of `gaps` |
| Performance target | Event creation + HMAC signing: **< 5ms** |
| Security constraints | HMAC key **never** logged, **never** in stack traces; signing failure always raises |
| Unit tests | 100% coverage; tamper detection, gap detection, key rotation scenarios |

### Signing Algorithm

```python
from llm_toolkit_schema.audit import verify_chain
result = verify_chain(events, org_secret='...')
# result.valid          → True/False
# result.first_tampered → event_id of first modified event, or None
# result.gaps           → list of missing prev_id links (deletions visible)
```

### Exit Criteria

- Tampered events are reliably detected
- Deleted events leave detectable gaps in the chain
- Enterprise customers can verify chains independently with their own secret
- No dependency on hosted infrastructure for chain verification

---

## Phase 4 — OTLP Export & Event Routing (Week 4 → v0.4)

**Goal:** Enable zero-adapter routing to enterprise observability backends.

### Deliverables

| Task | Details |
|------|---------|
| `llm_toolkit_schema/export/otlp.py` | `OTLPExporter` — serialises events to OTLP spans or log records |
| `llm_toolkit_schema/export/webhook.py` | `WebhookExporter` with HMAC-SHA256 request signing |
| `llm_toolkit_schema/export/jsonl.py` | JSONL file exporter for local development |
| `llm_toolkit_schema/stream.py` | `EventStream`: `from_file()`, `from_queue()`, `filter()`, `route()` |
| OTLP mapping | Every event maps to a valid OTLP span or log record — no custom code needed |
| Resource attributes | `service.name`, `deployment.environment` support in exporter config |
| Async export | Exporters are async by default — no blocking on tool's critical path |
| Performance target | OTLP export batch of 500 events: **< 200ms** |

### Supported Backends (via OTLP)

| Backend | Protocol | Notes |
|---------|----------|-------|
| Datadog | OTLP gRPC | Spans → APM traces; `cost_usd` → custom metric |
| Grafana / Tempo | OTLP gRPC | Spans → distributed traces; Events → Loki logs |
| Honeycomb | OTLP HTTP | All payload fields exposed as trace fields |
| Splunk | HEC / OTLP | Events → Splunk events; audit chain in immutable index |
| Elastic | OTLP direct | ECS-mapped, searchable by envelope and payload fields |
| AWS CloudWatch | CloudWatch Logs | Via OTLP Collector → EMF format for cost metrics |
| Custom SIEM | Webhook / HTTP | JSON via configurable webhook with HMAC-SHA256 |

### Exit Criteria

- A llm-toolkit-schema event can be exported to Datadog and Grafana without custom adapter code
- `EventStream.route()` supports filtering by `event_type` and `tags`
- All exporters are opt-in (no network calls in core)

---

## Phase 5 — All Namespace Payloads & JSON Schema Publication (Week 5 → v0.5)

**Goal:** Define and review every tool namespace payload schema. Publish the official JSON Schema.

### Deliverables

| Task | Details |
|------|---------|
| `llm_toolkit_schema/namespaces/diff.py` | `DiffComparisonPayload`, `DiffReportPayload` |
| `llm_toolkit_schema/namespaces/prompt.py` | `PromptSavedPayload`, `PromptPromotedPayload`, `PromptApprovedPayload`, `PromptRolledBackPayload` |
| `llm_toolkit_schema/namespaces/trace.py` | `SpanCompletedPayload`, `ToolCall`, `ModelInfo`, `TokenUsage` |
| `llm_toolkit_schema/namespaces/cost.py` | `CostRecordedPayload`, `BudgetThresholdPayload` |
| `llm_toolkit_schema/namespaces/eval_.py` | `EvalScenarioPayload`, `EvalRegressionPayload` |
| `llm_toolkit_schema/namespaces/guard.py` | `GuardBlockedPayload`, `GuardFlaggedPayload` |
| `llm_toolkit_schema/namespaces/redact.py` | `PIIDetectedPayload`, `PIIRedactedPayload`, `ScanCompletedPayload` |
| `llm_toolkit_schema/namespaces/cache.py` | `CacheHitPayload`, `CacheMissPayload`, `CacheEvictedPayload` |
| `llm_toolkit_schema/namespaces/template.py` | `TemplateRenderedPayload`, `VariableMissingPayload`, `ValidationFailedPayload` |
| `llm_toolkit_schema/namespaces/fence.py` | `ValidationPassedPayload`, `ValidationFailedPayload`, `RetryTriggeredPayload` |
| `schemas/v1.0/schema.json` | Published JSON Schema — stable URL |
| `llm_toolkit_schema/validate.py` | JSON Schema validation against published spec |
| Design review | All 17 tool authors must review their namespace payload before freeze |

### Namespace Registry

| Namespace | Tool | Key Event Types |
|-----------|------|----------------|
| `llm.diff.*` | llm-diff | `comparison.started`, `comparison.completed`, `report.exported` |
| `llm.prompt.*` | promptlock | `saved`, `promoted`, `rolled_back`, `approved`, `rejected` |
| `llm.template.*` | promptblock | `rendered`, `variable.missing`, `validation.failed` |
| `llm.trace.*` | llm-trace | `span.started`, `span.completed`, `tool_call.started`, `tool_call.completed` |
| `llm.cost.*` | llm-cost | `recorded`, `budget.threshold_reached`, `budget.exceeded` |
| `llm.eval.*` | evalkit | `scenario.started`, `scenario.completed`, `regression.failed` |
| `llm.guard.*` | promptguard | `input.scanned`, `input.blocked`, `output.flagged` |
| `llm.redact.*` | llm-redact | `pii.detected`, `pii.redacted`, `scan.completed` |
| `llm.fence.*` | llm-fence | `validation.passed`, `validation.failed`, `retry.triggered` |
| `llm.cache.*` | llm-cache | `hit`, `miss`, `evicted` |

### Exit Criteria

- Every namespace payload reviewed by the owning tool author
- `llm.trace.span.completed` payload is frozen — it is consumed by llm-cost, llm-inspect, agentboard, and evalkit
- JSON Schema published at `schemas/v1.0/schema.json`
- `validate.py` passes all payloads against the published schema
- **This milestone gates all other tool development**

---

## Phase 6 — v1.0 General Availability (Week 6 → v1.0 GA)

**Goal:** Production-ready release with full compliance tooling, signed PyPI package, and live schema registry.

### Deliverables

| Task | Details |
|------|---------|
| `llm_toolkit_schema/compliance/test_isolation.py` | Multi-tenant data isolation verification test suite |
| `llm_toolkit_schema/compliance/test_chain.py` | Audit chain integrity test suite |
| `llm_toolkit_schema/migrate.py` | `v1_to_v2()` migration helper scaffold |
| Schema registry | Live at `https://schema.llm-toolkit.dev` — JSON Schema per version, deprecation notices |
| Compatibility checker | `llm-toolkit-schema check-compat --consumer promptlock --schema-version 1.2` |
| Signed PyPI release | Sigstore-signed package; SBOM published per release |
| Dependency audit | CI audit on every PR |
| Performance benchmarks | All NFR targets validated in CI (see below) |
| Documentation | Full API reference, adoption guide, integration examples |

### Non-Functional Requirements (must be validated in CI)

| Metric | Target |
|--------|--------|
| Event creation (no signing) | < 1ms |
| Event creation + HMAC signing | < 5ms |
| JSON serialisation of 1,000 events | < 50ms |
| OTLP export batch of 500 events | < 200ms |
| Chain verification of 1M events | < 30 seconds |
| Heap allocations on hot path | Zero — use `__slots__` |
| Test coverage (Event, signing, redaction) | 100% |

### Compatibility Matrix

- Python 3.9, 3.10, 3.11, 3.12 — all CI-tested
- Zero required dependencies for core Event creation
- Optional: `pydantic`, `opentelemetry-sdk`, `httpx`
- Windows, macOS, Linux

### Exit Criteria

- Compliance test suite passes at 100%
- Schema registry is live and serving JSON Schema
- PyPI package is signed via Sigstore
- SBOM published
- At least 1 design partner (enterprise customer) routing events to Datadog
- All open breaking-change proposals: **0**

---

## Phase 7 — Enterprise Integrations (Month 3 → v1.1)

**Goal:** Deepen enterprise backend support. No breaking changes.

### Deliverables

| Task | Details |
|------|---------|
| `llm_toolkit_schema/export/datadog.py` | Datadog-specific metric + trace exporter |
| Grafana / Loki exporter | Spans → distributed traces; Events → Loki logs |
| Kafka `EventStream` | `EventStream.from_kafka()` for high-throughput pipelines |
| Consumer registration API | Tools declare consumed versions/namespaces; registry alerts on breaking changes |
| Private registry mirror | Air-gapped enterprise deployment support |
| HSM-backed signing keys | Optional Hardware Security Module signing for regulated industries |
| Schema governance API | Block tools from emitting deprecated event types — enforced at collector layer |

### Success Metrics at Month 3

- PyPI downloads/month: **5,000+**
- GitHub stars: **500+**
- llm-toolkit tools emitting schema: **6**
- Enterprise customers routing to Datadog: **5+**

---

## Phase 8 — Ecosystem & Framework Integrations (Month 5 → v1.2)

**Goal:** Achieve broad adoption across the LLM framework ecosystem. No breaking changes.

### Deliverables

| Task | Details |
|------|---------|
| LangChain integration package | `llm-toolkit-schema-langchain` — emits `llm.trace.*` events from LangChain callbacks |
| LlamaIndex integration package | `llm-toolkit-schema-llamaindex` — emits events from LlamaIndex query/retrieval pipeline |
| Private registry | Enterprise private mirror with firewall deployment support |
| Deprecation tooling | CLI + CI tooling to detect usage of deprecated event types |
| Schema pinning | Enterprise orgs mandate a specific schema version across all tools |

### Ecosystem Goal

> Every major LLM framework (LangChain, LlamaIndex, AutoGen, DSPy) should emit llm-toolkit-schema events by v1.2. Budget **one sprint per framework** for integration support.

### Success Metrics at Month 5

- PyPI downloads/month: **25,000+**
- GitHub stars: **2,000+**
- All 17 llm-toolkit tools emitting schema
- Third-party tools registered: **10+**
- Framework integrations: **3+**
- Enterprise customers routing to Datadog: **20+**

---

## Phase 9 — v2.0 Breaking Change Window (12+ months)

**Goal:** Incorporate feedback from v1.x production usage. Full 6-month deprecation window.

### Process

1. Collect breaking-change proposals from v1.x feedback (tracked publicly)
2. Design review with all 17 tool authors and enterprise design partners
3. Publish deprecation notices 6 months before v2.0 release
4. Publish `llm_toolkit_schema.migrate.v1_to_v2(event)` migration helpers
5. Run 6-month parallel support window (v1.x and v2.x both supported)

### Versioning Rules (enforced across all phases)

| Change Type | Strategy |
|-------------|----------|
| Add optional field | Backward-compatible — consumers that don't know the field ignore it |
| Rename a field | **NEVER** — add new name, deprecate old with sunset date |
| Remove a field | Requires major version bump + 6-month sunset window |
| Change a field type | Always a breaking change — requires major version bump |
| Add new event type | Fully backward-compatible — consumers filter by `event_type` |

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Schema designed too narrowly | **Critical** | Review with all 17 tool authors before v1.0 freeze; require a concrete use case from each namespace owner |
| OTel spec evolves and schema becomes incompatible | Medium | Track OTel semantic conventions (semconv) from day one — not just the OTLP wire format |
| Namespace collisions between tools | Medium | Registry enforces uniqueness; tooling warns on unregistered namespaces; `x.*` prefix for unofficial tools |
| PII leaks via fields not marked `__redactable` | **High** | Security review of all payload schemas before v1.0; static analysis flags unmarked string fields |
| Signing key compromise exposes audit chain | **High** | Key rotation procedure documented and tested; HSM key storage option at v1.1 |
| Third-party adoption too slow | Medium | Invest in framework integration packages at v1.2; make `test_compatibility` trivial to run |
| Performance overhead makes tools feel sluggish | Low | Benchmark on hot path in CI; async export by default |

---

## Third-Party Adoption Checklist

For any external tool to be compatible with llm-toolkit-schema:

1. All REQUIRED envelope fields present and correctly typed
2. Uses a registered namespace or private `x.*` prefix (e.g. `x.mycompany.trace.*`)
3. Does not emit events in another tool's namespace without explicit permission
4. Passes: `llm_toolkit_schema.compliance.test_compatibility`
5. Includes `schema_version` in every event — never omitted
6. Adoption time for a simple tool: **< 2 hours**

---

## Implementation Timeline Summary

| Phase | Version | Timeline | Milestone |
|-------|---------|----------|-----------|
| 1 | v0.1 | Week 1 | Core Event, ULID, serialisation, basic validation |
| 2 | v0.2 | Week 2 | Pydantic models, Redaction framework |
| 3 | v0.3 | Week 3 | HMAC signing, audit chain, `verify_chain()` |
| 4 | v0.4 | Week 4 | OTLP exporter, WebhookExporter, EventStream routing |
| 5 | v0.5 | Week 5 | All namespace payloads, JSON Schema published |
| 6 | v1.0 GA | Week 6 | Compliance suite, schema registry live, signed PyPI |
| 7 | v1.1 | Month 3 | Datadog, Grafana/Loki, Kafka, consumer registration, HSM |
| 8 | v1.2 | Month 5 | LangChain + LlamaIndex integrations, private registry |
| 9 | v2.0 | 12+ months | Breaking changes, migration guide, 6-month sunset window |

---

*llm-toolkit-schema · Enterprise Product Specification · v1.0 · February 2026 · Confidential*
