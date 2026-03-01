# llm.diff — Prompt/Response Delta

> **Auto-documented module:** `llm_toolkit_schema.namespaces.diff`

## Field reference

| Field | Type | Description |
|-------|------|-------------|
| `base_event_id` | `str` | ULID of the event being compared against. |
| `diff_type` | `str` | What changed: `"prompt"`, `"completion"`, or `"both"`. |
| `prompt_diff` | `str \| None` | Unified-diff string for the prompt change. |
| `completion_diff` | `str \| None` | Unified-diff string for the completion change. |
| `similarity_score` | `float \| None` | Semantic similarity (0–1) between base and new output. |

## Example

```python
from llm_toolkit_schema.namespaces.diff import DiffPayload

payload = DiffPayload(
    base_event_id="01HX...",
    diff_type="prompt",
    prompt_diff="--- a\n+++ b\n@@ -1 +1 @@\n-Hello\n+Hi",
    similarity_score=0.92,
)
```
