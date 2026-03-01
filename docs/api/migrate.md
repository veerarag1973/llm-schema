# llm_toolkit_schema.migrate

Migration helpers for upgrading events from one schema version to the next.

See the [Migration Guide](../user_guide/migration.md) for background and strategy.

> **Note:** The v1.0 release provides scaffolding only. `v1_to_v2()` raises
> `NotImplementedError` until the v2.0 schema is defined. Write the call-site
> now to receive the working implementation in a future release.

---

## `MigrationResult`

```python
@dataclass(frozen=True)
class MigrationResult:
    source_version: str
    target_version: str
    event_id: str
    success: bool
    transformed_fields: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
```

Metadata about a completed migration operation.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `source_version` | `str` | The schema version the event was migrated *from*. |
| `target_version` | `str` | The schema version the event was migrated *to*. |
| `event_id` | `str` | The `event_id` of the event that was transformed. |
| `success` | `bool` | `True` when migration completed without errors. |
| `transformed_fields` | `Tuple[str, ...]` | Names of event fields that were modified. |
| `warnings` | `Tuple[str, ...]` | Any non-fatal issues encountered during migration. |

---

## Module-level functions

### `v1_to_v2(event: Event) -> Tuple[Event, MigrationResult]`

Migrate a v1.0 event to the v2.0 schema.

> **Scaffold only** — raises `NotImplementedError` in v1.0. Write the call-site
> now and upgrade to the full implementation when v2.0 is released.

**Args:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `event` | `Event` | A v1.0 `Event` to migrate. |

**Returns:** `Tuple[Event, MigrationResult]` — `(migrated_event, result)` tuple.

**Raises:** `NotImplementedError` — always in v1.0 (v2 schema not yet defined).

**Example:**

```python
from llm_toolkit_schema.migrate import v1_to_v2

# Write the call-site now; will work when v2.0 ships.
event_v2, result = v1_to_v2(event_v1)  # raises NotImplementedError in v1.0
```
