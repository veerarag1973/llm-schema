# llm.cost — Cost Tracking

> **Auto-documented module:** `llm_toolkit_schema.namespaces.cost`

## Field reference

| Field | Type | Description |
|-------|------|-------------|
| `input_cost` | `float` | Cost of prompt tokens in USD. |
| `output_cost` | `float` | Cost of completion tokens in USD. |
| `total_cost` | `float` | Sum of input and output cost. |
| `currency` | `str` | ISO 4217 currency code (default `"USD"`). |
| `pricing_tier` | `str \| None` | Provider pricing tier name (e.g. `"batch"`, `"realtime"`). |

## Example

```python
from llm_toolkit_schema.namespaces.cost import CostPayload

payload = CostPayload(
    input_cost=0.0015,
    output_cost=0.0006,
    total_cost=0.0021,
    currency="USD",
)
```
