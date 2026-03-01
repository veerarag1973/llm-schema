.. _cli:

Command-Line Interface
======================

llm-toolkit-schema ships a command-line tool, ``llm-toolkit-schema``, for operational tasks.
The entry-point is installed automatically when you ``pip install llm-toolkit-schema``.

.. code-block:: bash

   llm-toolkit-schema --help

.. code-block:: text

   usage: llm-toolkit-schema [-h] <command> ...

   llm-toolkit-schema command-line utilities

   positional arguments:
     <command>
       check-compat    Check a JSON file of events against the v1.0 compatibility checklist

   options:
     -h, --help        show this help message and exit


``check-compat``
-----------------

Validate a batch of serialised events against the llm-toolkit-schema v1.0 compatibility
checklist (CHK-1 through CHK-5).  Useful in CI pipelines, pre-commit hooks,
and onboarding audits for third-party tool authors.

**Usage**

.. code-block:: bash

   llm-toolkit-schema check-compat EVENTS_JSON

``EVENTS_JSON``
    Path to a JSON file containing a top-level array of serialised
    :class:`~llm_toolkit_schema.event.Event` objects (the output of
    ``[evt.to_dict() for evt in events]``).

**Exit codes**

.. list-table::
   :header-rows: 1
   :widths: 10 90

   * - Code
     - Meaning
   * - ``0``
     - All events passed every compatibility check.
   * - ``1``
     - One or more compatibility violations were found (details printed to stdout).
   * - ``2``
     - Usage error, file not found, or invalid JSON.

**Example — passing**

.. code-block:: bash

   $ llm-toolkit-schema check-compat events.json
   OK — 42 event(s) passed all compatibility checks.

**Example — violations found**

.. code-block:: bash

   $ llm-toolkit-schema check-compat events.json
   FAIL — 2 violation(s) found in 42 event(s):

     [01JPXXX...] CHK-3 (Source identifier format): source 'MyTool/1.0' does not match ...
     [01JPYYY...] CHK-5 (Event ID is a valid ULID): event_id 'not-a-ulid' is not a valid ULID

**Example — generating an events file**

.. code-block:: python

   import json
   from llm_toolkit_schema import Event, EventType

   events = [
       Event(
           event_type=EventType.TRACE_SPAN_COMPLETED,
           source="my-tool@1.0.0",
           payload={"span_name": "chat"},
       )
       for _ in range(5)
   ]

   with open("events.json", "w") as f:
       json.dump([evt.to_dict() for evt in events], f, indent=2)

**Using in CI (GitHub Actions)**

.. code-block:: yaml

   - name: Validate event compatibility
     run: |
       python -c "
       import json
       from llm_toolkit_schema import Event, EventType
       events = [Event(event_type=EventType.TRACE_SPAN_COMPLETED,
                       source='my-tool@1.0.0', payload={'ok': True})]
       with open('/tmp/events.json', 'w') as f:
           json.dump([e.to_dict() for e in events], f)
       "
       llm-toolkit-schema check-compat /tmp/events.json

Compatibility checks
---------------------

The ``check-compat`` command applies these checks to every event:

.. list-table::
   :header-rows: 1
   :widths: 10 35 55

   * - Check ID
     - Rule
     - Details
   * - CHK-1
     - Required fields present
     - ``schema_version``, ``source``, and ``payload`` must be non-empty.
   * - CHK-2
     - Event type is registered or valid custom
     - Must be a first-party :class:`~llm_toolkit_schema.types.EventType` value, or pass
       :func:`~llm_toolkit_schema.types.validate_custom` (``x.<company>.<…>`` format).
   * - CHK-3
     - Source identifier format
     - Must match ``^[a-z][a-z0-9-]*@\d+\.\d+(\.\d+)?([.-][a-z0-9]+)*$``
       (e.g. ``my-tool@1.2.3``).
   * - CHK-5
     - Event ID is a valid ULID
     - ``event_id`` must be a well-formed 26-character ULID string.

Programmatic usage (no CLI required)
--------------------------------------

The same checks are available directly in Python:

.. code-block:: python

   from llm_toolkit_schema.compliance import test_compatibility

   result = test_compatibility(events)
   if not result:
       for v in result.violations:
           print(f"[{v.check_id}] {v.rule}: {v.detail}")

See :mod:`llm_toolkit_schema.compliance` for the full compliance API.
