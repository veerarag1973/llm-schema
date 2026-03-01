# llm_toolkit_schema.export

This module provides the export backends for llm-toolkit-schema events.

> **Auto-documented module:** `llm_toolkit_schema.export`

See the [Export User Guide](../user_guide/export.md) for usage examples.

## OTLP Backend

> **Auto-documented module:** `llm_toolkit_schema.export.otlp`

`OTLPExporter` — sends events to an OpenTelemetry collector via OTLP/HTTP JSON.

## Webhook Backend

> **Auto-documented module:** `llm_toolkit_schema.export.webhook`

`WebhookExporter` — POSTs events as JSON to an arbitrary HTTP endpoint.

## JSONL Backend

> **Auto-documented module:** `llm_toolkit_schema.export.jsonl`

`JSONLExporter` — writes events as newline-delimited JSON to a local file.
