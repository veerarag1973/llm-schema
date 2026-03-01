# API Reference

The llm-toolkit-schema API surface is organised by module. All public symbols are
exported at the top-level package under `llm_toolkit_schema`.

## Modules

- [event](event.md)
- [types](types.md)
- [signing](signing.md)
- [redact](redact.md)
- [compliance](compliance.md)
- [export](export.md)
- [stream](stream.md)
- [validate](validate.md)
- [migrate](migrate.md)
- [ulid](ulid.md)
- [exceptions](exceptions.md)
- [models](models.md)

## Module summary

| Module | Responsibility |
|--------|---------------|
| `llm_toolkit_schema.event` | `LLMEvent` envelope and serialisation |
| `llm_toolkit_schema.types` | `EventType` enum, custom type validation |
| `llm_toolkit_schema.signing` | HMAC signing, `AuditStream`, chain verification |
| `llm_toolkit_schema.redact` | `Redactable`, `RedactionPolicy`, PII helpers |
| `llm_toolkit_schema.compliance` | Compatibility checks, isolation, chain integrity, scope verification |
| `llm_toolkit_schema.export` | OTLP, Webhook, and JSONL export backends |
| `llm_toolkit_schema.stream` | `EventStream` multiplexer |
| `llm_toolkit_schema.validate` | JSON Schema validation helpers |
| `llm_toolkit_schema.migrate` | `v1_to_v2` migration scaffold |
| `llm_toolkit_schema.ulid` | ULID generation and helpers |
| `llm_toolkit_schema.exceptions` | Package-level exception hierarchy |
| `llm_toolkit_schema.models` | Shared Pydantic base models |
