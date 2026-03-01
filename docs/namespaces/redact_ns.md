# llm.redact — Redaction Audit Record

> **Note:** This namespace payload records *metadata about a redaction operation* —
> for example, which PII types were detected and which policy was applied.
> It is distinct from the runtime `llm_toolkit_schema.redact` module that
> performs the actual field-level redaction.

> **Auto-documented module:** `llm_toolkit_schema.namespaces.redact`

## Field reference

| Field | Type | Description |
|-------|------|-------------|
| `policy_id` | `str` | Identifier of the `RedactionPolicy` applied. |
| `pii_types_detected` | `list[str]` | PII type strings that were detected (e.g. `["email", "phone"]`). |
| `fields_redacted` | `list[str]` | Payload field paths that were redacted. |
| `redaction_count` | `int` | Total number of individual redaction substitutions made. |
| `sensitivity_level` | `str` | Highest `SensitivityLevel` encountered. |

## Example

```python
from llm_toolkit_schema.namespaces.redact import RedactPayload

payload = RedactPayload(
    policy_id="default-v1",
    pii_types_detected=["email", "phone"],
    fields_redacted=["prompt", "completion"],
    redaction_count=3,
    sensitivity_level="HIGH",
)
```
