# llm_toolkit_schema.exceptions

This module contains the domain exception hierarchy for llm-toolkit-schema.

> **Auto-documented module:** `llm_toolkit_schema.exceptions`

## Exception hierarchy

- `LLMSchemaError` — base exception for all llm-toolkit-schema errors
  - `SchemaValidationError` — raised on field validation failures
  - `ULIDError` — raised on invalid ULID values
  - `SerializationError` — raised during serialisation failures
  - `DeserializationError` — raised during deserialisation failures
  - `EventTypeError` — raised on invalid or unrecognised event types
