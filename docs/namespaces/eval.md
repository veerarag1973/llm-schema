# llm.eval — Scoring & Evaluation

> **Auto-documented module:** `llm_toolkit_schema.namespaces.eval_`

## Field reference

| Field | Type | Description |
|-------|------|-------------|
| `evaluator` | `str` | Evaluator identifier (e.g. `"human"`, `"gpt-4o"`, `"rubric-v2"`). |
| `score` | `float` | Numeric score (range depends on `scale`). |
| `scale` | `str` | Score scale descriptor (e.g. `"0-1"`, `"1-5"`, `"pass/fail"`). |
| `label` | `str \| None` | Categorical label (e.g. `"correct"`, `"hallucinated"`). |
| `rationale` | `str \| None` | Free-text explanation of the score. |
| `criteria` | `list[str] \| None` | Evaluation criteria applied. |

## Example

```python
from llm_toolkit_schema.namespaces.eval import EvalPayload

payload = EvalPayload(
    evaluator="gpt-4o",
    score=0.85,
    scale="0-1",
    label="mostly_correct",
    rationale="Answer is accurate but verbose.",
)
```
