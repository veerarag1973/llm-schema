.. _namespaces:

Namespace Payload Catalogue
============================

llm-toolkit-schema ships typed payload objects for ten standard namespaces.  Every
namespace payload is a Python dataclass (and optionally a Pydantic model) that
can be serialised to/from a plain :class:`dict` for storage in
:attr:`~llm_toolkit_schema.event.LLMEvent.payload`.

.. toctree::
   :maxdepth: 1

   trace
   cost
   cache
   diff
   eval
   fence
   guard
   prompt
   redact_ns
   template

Namespace quick-reference
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 15 25 60

   * - Namespace prefix
     - Module
     - Purpose
   * - ``llm.trace.*``
     - :mod:`llm_toolkit_schema.namespaces.trace`
     - Model inputs, outputs, latency, token counts — **FROZEN v1**
   * - ``llm.cost.*``
     - :mod:`llm_toolkit_schema.namespaces.cost`
     - Per-event cost estimates and budget tracking
   * - ``llm.cache.*``
     - :mod:`llm_toolkit_schema.namespaces.cache`
     - Cache hit/miss, key, TTL, backend metadata
   * - ``llm.diff.*``
     - :mod:`llm_toolkit_schema.namespaces.diff`
     - Prompt/response delta between two events
   * - ``llm.eval.*``
     - :mod:`llm_toolkit_schema.namespaces.eval_`
     - Scoring, grading, and human-feedback payloads
   * - ``llm.fence.*``
     - :mod:`llm_toolkit_schema.namespaces.fence`
     - Perimeter checks, topic constraints, allow/block lists
   * - ``llm.guard.*``
     - :mod:`llm_toolkit_schema.namespaces.guard`
     - Safety classifier outputs and block decisions
   * - ``llm.prompt.*``
     - :mod:`llm_toolkit_schema.namespaces.prompt`
     - Prompt versioning, template rendering, variable sets
   * - ``llm.redact.*``
     - :mod:`llm_toolkit_schema.namespaces.redact`
     - PII detection and redaction audit records
   * - ``llm.template.*``
     - :mod:`llm_toolkit_schema.namespaces.template`
     - Template registry metadata and render snapshots

Using a namespace payload
--------------------------

.. code-block:: python

   from llm_toolkit_schema.event import LLMEvent
   from llm_toolkit_schema.namespaces.trace import TracePayload

   payload = TracePayload(
       model="gpt-4o",
       prompt_tokens=512,
       completion_tokens=128,
       latency_ms=340.5,
   )

   event = LLMEvent(
       event_type="llm.trace.completion",
       source="my-app@1.0.0",
       org_id="org_01HX",
       payload=payload.to_dict(),
   )
