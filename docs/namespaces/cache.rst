.. _ns_cache:

llm.cache — Cache Metadata
============================

.. automodule:: llm_toolkit_schema.namespaces.cache
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
   * - ``hit``
     - ``bool``
     - ``True`` if the response was served from cache.
   * - ``cache_key``
     - ``str | None``
     - Opaque cache key used for lookup.
   * - ``ttl_seconds``
     - ``int | None``
     - Time-to-live of the cached entry in seconds.
   * - ``backend``
     - ``str | None``
     - Cache backend identifier (e.g. ``"redis"``, ``"memcached"``, ``"in-memory"``).
   * - ``latency_ms``
     - ``float | None``
     - Cache lookup latency in milliseconds.

Example
-------

.. code-block:: python

   from llm_toolkit_schema.namespaces.cache import CachePayload

   payload = CachePayload(
       hit=True,
       cache_key="sha256:abc123",
       ttl_seconds=3600,
       backend="redis",
       latency_ms=2.1,
   )
