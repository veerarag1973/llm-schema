# llm_toolkit_schema.export

Export backends for delivering llm-toolkit-schema events to external systems.

All exporters implement the `Exporter` protocol from `llm_toolkit_schema.stream`
(async `export_batch` method) and satisfy the `EventStream.drain()` / `route()` API.

See the [Export User Guide](../user_guide/export.md) for usage examples.

---

## `llm_toolkit_schema.export.jsonl` — JSONL File Exporter

### `JSONLExporter`

```python
class JSONLExporter(
    path: Union[str, Path],
    mode: str = "a",
    encoding: str = "utf-8",
)
```

Async exporter that appends events as newline-delimited JSON.

- `path="-"` writes to stdout (useful for log pipelines).
- Async-safe: an `asyncio.Lock` serialises concurrent appends.
- Acts as an async context manager: `async with JSONLExporter(...) as e:`.

**Args:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str \| Path` | — | File path or `"-"` for stdout. |
| `mode` | `str` | `"a"` | File open mode: `"a"` (append) or `"w"` (truncate). |
| `encoding` | `str` | `"utf-8"` | File encoding. |

**Raises:** `OSError` — if the file cannot be opened or written.

**Example:**

```python
from llm_toolkit_schema.export.jsonl import JSONLExporter

async with JSONLExporter("events.jsonl") as exporter:
    for event in events:
        await exporter.export(event)
```

#### Methods

##### `async export(event: Event) -> None`

Append a single event as one JSON line.

**Raises:** `RuntimeError` — if the exporter has been closed. `OSError` — if the write fails.

##### `async export_batch(events: Sequence[Event]) -> int`

Append multiple events, one JSON line each.

**Returns:** `int` — number of events written.

**Raises:** `RuntimeError` — if the exporter has been closed. `OSError` — if the write fails.

##### `flush() -> None`

Flush internal write buffers to the OS. Safe to call before the file is opened.

##### `close() -> None`

Flush and close the underlying file handle. Idempotent. Does not close stdout.

---

## `llm_toolkit_schema.export.otlp` — OTLP Exporter

### `ResourceAttributes`

```python
@dataclass(frozen=True)
class ResourceAttributes(
    service_name: str,
    deployment_environment: str = "production",
    extra: Dict[str, str] = field(default_factory=dict),
)
```

OTel resource attributes attached to every exported OTLP payload.

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `service_name` | `str` | — | Value for the `service.name` resource attribute. |
| `deployment_environment` | `str` | `"production"` | Value for `deployment.environment`. |
| `extra` | `Dict[str, str]` | `{}` | Additional arbitrary resource attributes. |

#### Methods

##### `to_otlp() -> List[Dict[str, Any]]`

Return a list of OTLP `KeyValue` dicts for the resource.

---

### `OTLPExporter`

```python
class OTLPExporter(
    endpoint: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    resource_attrs: Optional[ResourceAttributes] = None,
    timeout: float = 5.0,
    batch_size: int = 500,
)
```

Async exporter that serialises events to OTLP/JSON and HTTP-POSTs to a collector.

- Events **with** `trace_id` → OTLP spans (`resourceSpans`).
- Events **without** `trace_id` → OTLP log records (`resourceLogs`).
- No `opentelemetry-sdk` dependency — stdlib-only HTTP transport.

**Args:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `endpoint` | `str` | — | Full OTLP HTTP URL, e.g. `"http://otel-collector:4318/v1/traces"`. |
| `headers` | `Dict[str, str] \| None` | `None` | Optional extra HTTP request headers (e.g. API keys). |
| `resource_attrs` | `ResourceAttributes \| None` | `None` | OTel resource attributes. Defaults to `service_name="llm-toolkit-schema"`. |
| `timeout` | `float` | `5.0` | HTTP request timeout in seconds. |
| `batch_size` | `int` | `500` | Maximum events per `export_batch` call. |

**Example:**

```python
from llm_toolkit_schema.export.otlp import OTLPExporter, ResourceAttributes

exporter = OTLPExporter(
    endpoint="http://localhost:4318/v1/traces",
    resource_attrs=ResourceAttributes(service_name="llm-trace"),
)
await exporter.export(event)
```

#### Methods

##### `to_otlp_span(event: Event) -> Dict[str, Any]`

Map a single event to an OTLP span dict (pure, no I/O).

If the event has no `span_id`, a deterministic synthetic ID is derived.
If the event has no `trace_id`, a zero-filled placeholder is used.

**Returns:** `Dict[str, Any]` — OTLP-compatible span dict.

##### `to_otlp_log(event: Event) -> Dict[str, Any]`

Map a single event to an OTLP log record dict (pure, no I/O).

**Returns:** `Dict[str, Any]` — OTLP-compatible log record dict.

##### `async export(event: Event) -> Dict[str, Any]`

Export a single event as an OTLP payload and HTTP POST it.

Span vs log selection is automatic based on `event.trace_id`.

**Returns:** `Dict[str, Any]` — the OTLP record dict that was sent.

**Raises:** `ExportError` — if the HTTP request fails.

##### `async export_batch(events: Sequence[Event]) -> List[Dict[str, Any]]`

Export a sequence of events, batching spans and log records into separate HTTP requests.

**Returns:** `List[Dict[str, Any]]` — list of OTLP record dicts.

**Raises:** `ExportError` — if any HTTP request fails.

---

## `llm_toolkit_schema.export.webhook` — Webhook Exporter

### `WebhookExporter`

```python
class WebhookExporter(
    url: str,
    *,
    secret: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0,
    max_retries: int = 3,
)
```

Async exporter that sends events to an HTTP webhook endpoint.

- Single events are delivered as a JSON-encoded body.
- Batch events are delivered as a JSON array.
- Optional HMAC-SHA256 request signing via `X-llm-toolkit-schema-Signature` header.
- Retry logic uses truncated exponential back-off (1s, 2s, 4s … capped at 30s).
- The `secret` is **never** included in repr, logs, or exception messages.

**Args:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | — | Destination webhook URL. |
| `secret` | `str \| None` | `None` | Optional HMAC-SHA256 signing secret. |
| `headers` | `Dict[str, str] \| None` | `None` | Optional extra HTTP request headers. |
| `timeout` | `float` | `10.0` | Per-request timeout in seconds. |
| `max_retries` | `int` | `3` | Maximum retry attempts on transient failures. |

**Example:**

```python
from llm_toolkit_schema.export.webhook import WebhookExporter

exporter = WebhookExporter(
    url="https://hooks.example.com/events",
    secret="my-hmac-secret",
)
await exporter.export(event)
```

#### Methods

##### `async export(event: Event) -> None`

Export a single event as a JSON-encoded HTTP POST.

**Raises:** `ExportError` — if all retry attempts fail.

##### `async export_batch(events: Sequence[Event]) -> int`

Export multiple events as a JSON array in a single HTTP POST.

**Returns:** `int` — number of events sent.

**Raises:** `ExportError` — if all retry attempts fail.

> **Auto-documented module:** `llm_toolkit_schema.export.webhook`

`WebhookExporter` — POSTs events as JSON to an arbitrary HTTP endpoint.

## JSONL Backend

> **Auto-documented module:** `llm_toolkit_schema.export.jsonl`

`JSONLExporter` — writes events as newline-delimited JSON to a local file.
