# llm.template — Template Registry

> **Auto-documented module:** `llm_toolkit_schema.namespaces.template`

## Field reference

| Field | Type | Description |
|-------|------|-------------|
| `template_id` | `str` | Registry identifier for the template. |
| `version` | `str` | Semantic version of the template. |
| `author` | `str \| None` | Email or username of the template author. |
| `tags` | `list[str] \| None` | Freeform tags for categorisation (e.g. `["support", "v3"]`). |
| `render_hash` | `str \| None` | SHA-256 of the rendered output for integrity auditing. |
| `engine` | `str \| None` | Template engine used (e.g. `"jinja2"`, `"mustache"`). |

## Example

```python
from llm_toolkit_schema.namespaces.template import TemplatePayload

payload = TemplatePayload(
    template_id="onboarding-email-v2",
    version="2.0.1",
    author="eng@company.com",
    tags=["onboarding", "email"],
    engine="jinja2",
)
```
