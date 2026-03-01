.. _ns_trace:

llm.trace — Completion Trace (FROZEN v1)
==========================================

.. note::

   The ``llm.trace.*`` payload schema is **frozen at v1.0**.  No breaking
   changes will be made.  New fields may be added in a strictly additive
   manner in future minor releases.

.. automodule:: llm_toolkit_schema.namespaces.trace
   :members:
   :undoc-members:
   :show-inheritance:

Field reference
---------------

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Field
     - Type
     - Description
   * - ``model``
     - ``str``
     - Model identifier (e.g. ``"gpt-4o"``, ``"claude-3-5-sonnet"``).
   * - ``prompt_tokens``
     - ``int``
     - Number of tokens in the prompt.
   * - ``completion_tokens``
     - ``int``
     - Number of tokens in the completion.
   * - ``total_tokens``
     - ``int | None``
     - Sum of prompt and completion tokens (may be omitted).
   * - ``latency_ms``
     - ``float``
     - End-to-end request latency in milliseconds.
   * - ``finish_reason``
     - ``str | None``
     - Provider finish reason (``"stop"``, ``"length"``, ``"tool_calls"``…).
   * - ``stream``
     - ``bool``
     - Whether the response was streamed.

Example
-------

.. code-block:: python

   from llm_toolkit_schema.namespaces.trace import TracePayload

   payload = TracePayload(
       model="gpt-4o",
       prompt_tokens=512,
       completion_tokens=128,
       latency_ms=340.5,
       finish_reason="stop",
       stream=False,
   )
