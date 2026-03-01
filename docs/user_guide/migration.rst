.. _user_guide_migration:

Migration Guide
===============

:mod:`llm_toolkit_schema.migrate` provides helpers for upgrading stored event payloads
to use new namespace payload schemas.

MigrationResult
---------------

Every migration function returns a :class:`~llm_toolkit_schema.migrate.MigrationResult`
dataclass:

.. code-block:: python

   @dataclass
   class MigrationResult:
       migrated: list[LLMEvent]   # successfully transformed events
       skipped:  list[LLMEvent]   # events that needed no change
       errors:   list[dict]       # {"event_id": str, "error": str}

   @property
   def success(self) -> bool:
       return len(self.errors) == 0

Migrating v1 → v2 (scaffold)
------------------------------

The v1_to_v2 scaffold converts events recorded with the ``llm.trace.*``
payload from the frozen v1.0 schema to any updated v2 layout that ships in
Phase 9:

.. code-block:: python

   from llm_toolkit_schema.migrate import v1_to_v2

   result = v1_to_v2(events)

   if result.success:
       save(result.migrated)
   else:
       for err in result.errors:
           print(f"{err['event_id']}: {err['error']}")

The function is idempotent — events whose ``schema_version`` is already
``"2.0"`` are placed in ``result.skipped`` unchanged.

Batch migration from JSONL
---------------------------

Read a JSONL archive, migrate, and write the output:

.. code-block:: python

   import json
   from llm_toolkit_schema.event import LLMEvent
   from llm_toolkit_schema.migrate import v1_to_v2

   events = [LLMEvent(**json.loads(line)) for line in open("archive.jsonl")]
   result = v1_to_v2(events)

   with open("archive_v2.jsonl", "w") as f:
       for event in result.migrated + result.skipped:
           f.write(json.dumps(event.to_dict()) + "\n")

   print(f"Migrated: {len(result.migrated)}")
   print(f"Skipped:  {len(result.skipped)}")
   print(f"Errors:   {len(result.errors)}")

Phase 9 roadmap
---------------

Phase 9 will ship breaking-change namespace payload schemas alongside a
``migrate`` sub-command for the CLI:

.. code-block:: bash

   llm-toolkit-schema migrate --from v1 --to v2 archive.jsonl --out archive_v2.jsonl

Until Phase 9 ships, the :func:`~llm_toolkit_schema.migrate.v1_to_v2` Python API is
the primary migration path.  The function signature and
:class:`~llm_toolkit_schema.migrate.MigrationResult` dataclass fields are considered
**stable** and will not change in Phase 9.
