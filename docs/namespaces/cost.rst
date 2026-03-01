.. _ns_cost:

llm.cost — Cost Tracking
==========================

.. automodule:: llm_toolkit_schema.namespaces.cost
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
   * - ``input_cost``
     - ``float``
     - Cost of prompt tokens in USD.
   * - ``output_cost``
     - ``float``
     - Cost of completion tokens in USD.
   * - ``total_cost``
     - ``float``
     - Sum of input and output cost.
   * - ``currency``
     - ``str``
     - ISO 4217 currency code (default ``"USD"``).
   * - ``pricing_tier``
     - ``str | None``
     - Provider pricing tier name (e.g. ``"batch"``, ``"realtime"``).

Example
-------

.. code-block:: python

   from llm_toolkit_schema.namespaces.cost import CostPayload

   payload = CostPayload(
       input_cost=0.0015,
       output_cost=0.0006,
       total_cost=0.0021,
       currency="USD",
   )
