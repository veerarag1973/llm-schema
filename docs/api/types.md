# llm_toolkit_schema.types

This module contains the `EventType` enum and custom event type validation helpers.

> **Auto-documented module:** `llm_toolkit_schema.types`

## Key symbols

- `EventType` — exhaustive enum of all 50+ first-party event types across 10 namespaces plus audit types
- `is_registered()` — check whether an event type string is a registered first-party type
- `validate_custom()` — validate a custom `x.<company>.<…>` event type string
- `namespace_of()` — return the namespace prefix of a given event type string
