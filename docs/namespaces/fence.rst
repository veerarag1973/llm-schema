.. _ns_fence:

llm.fence — Perimeter Checks
==============================

.. automodule:: llm_toolkit_schema.namespaces.fence
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
   * - ``allowed``
     - ``bool``
     - ``True`` if the content passed all perimeter checks.
   * - ``check_name``
     - ``str``
     - Name of the fence rule that evaluated the content.
   * - ``topic``
     - ``str | None``
     - Topic classification result.
   * - ``confidence``
     - ``float | None``
     - Model confidence (0–1) in the check result.
   * - ``triggered_rules``
     - ``list[str] | None``
     - Names of rules that were triggered.

Example
-------

.. code-block:: python

   from llm_toolkit_schema.namespaces.fence import FencePayload

   payload = FencePayload(
       allowed=False,
       check_name="topic-allowlist-v2",
       topic="competitor-discussion",
       confidence=0.97,
       triggered_rules=["no-competitor-mention"],
   )
