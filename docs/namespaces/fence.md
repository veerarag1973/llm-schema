# llm.fence — Perimeter Checks

> **Auto-documented module:** `llm_toolkit_schema.namespaces.fence`

## Field reference

| Field | Type | Description |
|-------|------|-------------|
| `allowed` | `bool` | `True` if the content passed all perimeter checks. |
| `check_name` | `str` | Name of the fence rule that evaluated the content. |
| `topic` | `str \| None` | Topic classification result. |
| `confidence` | `float \| None` | Model confidence (0–1) in the check result. |
| `triggered_rules` | `list[str] \| None` | Names of rules that were triggered. |

## Example

```python
from llm_toolkit_schema.namespaces.fence import FencePayload

payload = FencePayload(
    allowed=False,
    check_name="topic-allowlist-v2",
    topic="competitor-discussion",
    confidence=0.97,
    triggered_rules=["no-competitor-mention"],
)
```
