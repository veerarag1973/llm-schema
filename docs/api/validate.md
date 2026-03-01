# llm_toolkit_schema.validate

This module provides JSON Schema validation helpers for llm-toolkit-schema events.

> **Auto-documented module:** `llm_toolkit_schema.validate`

## Key functions

- `validate_event()` — validates an event against the published JSON Schema (`schemas/v1.0/schema.json`).
  Uses the `jsonschema` library when available (install with `pip install "llm-toolkit-schema[jsonschema]"`),
  otherwise falls back to structural stdlib checks.
