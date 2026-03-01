# llm_toolkit_schema.models

This module provides the Pydantic v2 model layer for llm-toolkit-schema.

> **Auto-documented module:** `llm_toolkit_schema.models`

Requires the `pydantic` extra:

```bash
pip install "llm-toolkit-schema[pydantic]"
```

`EventModel` supports `from_event()` / `to_event()` round-trip conversion and
`model_json_schema()` for schema export.
