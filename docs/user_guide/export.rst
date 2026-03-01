.. _user_guide_export:

Export Backends & EventStream
==============================

llm-toolkit-schema ships three export backends and an :class:`~llm_toolkit_schema.stream.EventStream`
routing layer that ties them together.

Quick overview
--------------

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Class
     - Protocol
     - Typical use
   * - :class:`~llm_toolkit_schema.export.otlp.OTLPExporter`
     - OTLP / gRPC
     - OpenTelemetry collector, Grafana, Loki
   * - :class:`~llm_toolkit_schema.export.webhook.WebhookExporter`
     - HTTPS POST
     - Slack, PagerDuty, or any custom HTTP endpoint
   * - :class:`~llm_toolkit_schema.export.jsonl.JSONLExporter`
     - Local file
     - Data-lake ingestion, offline analysis, tests

JSONLExporter
-------------

The simplest backend — useful for local replay and testing:

.. code-block:: python

   from llm_toolkit_schema.export.jsonl import JSONLExporter

   exporter = JSONLExporter("events.jsonl", gzip=False)
   exporter.export(event)
   exporter.flush()

Pass ``gzip=True`` to compress inline:

.. code-block:: python

   exporter = JSONLExporter("events.jsonl.gz", gzip=True)

Each line is a compact JSON object identical to :meth:`~llm_toolkit_schema.event.LLMEvent.to_dict`.

WebhookExporter
---------------

POSTs each event as JSON to an arbitrary HTTP endpoint:

.. code-block:: python

   from llm_toolkit_schema.export.webhook import WebhookExporter

   exporter = WebhookExporter(
       url="https://hooks.example.com/llm-events",
       headers={"Authorization": "Bearer <token>"},
       timeout=5.0,
       max_retries=3,
       backoff_factor=0.5,
   )
   exporter.export(event)

Retry behaviour uses truncated-exponential back-off.  After ``max_retries``
failed attempts the event is dropped and a warning is logged.

OTLPExporter
------------

Sends events to an OpenTelemetry collector via gRPC:

.. code-block:: python

   from llm_toolkit_schema.export.otlp import OTLPExporter

   exporter = OTLPExporter(
       endpoint="http://otel-collector:4317",
       service_name="my-llm-service",
       resource_attrs={"deployment.environment": "production"},
       insecure=True,
       compression="gzip",
   )
   exporter.export(event)

Each :class:`~llm_toolkit_schema.event.LLMEvent` becomes an OTLP ``LogRecord``.  The
``event_type`` field is mapped to ``log.record.type`` and all payload keys
appear as OTLP attributes.

EventStream
-----------

:class:`~llm_toolkit_schema.stream.EventStream` multiplexes events across one or more
backends and supports filterable routing:

.. code-block:: python

   from llm_toolkit_schema.stream import EventStream
   from llm_toolkit_schema.export.jsonl import JSONLExporter
   from llm_toolkit_schema.export.webhook import WebhookExporter

   stream = EventStream()
   stream.add_exporter(JSONLExporter("all.jsonl"))
   stream.add_exporter(
       WebhookExporter("https://pagerduty.example/events"),
       filter=lambda e: e.event_type == "llm.guard.blocked",
   )

   stream.emit(event)     # emits to all matching exporters

Scope filtering
---------------

Restrict an exporter to a specific org or team:

.. code-block:: python

   from llm_toolkit_schema.stream import EventStream

   stream = EventStream()
   stream.add_exporter(
       JSONLExporter("team-alpha.jsonl"),
       filter=lambda e: e.team_id == "team_alpha",
   )

Fan-out pattern
---------------

Emit one event to many backends:

.. code-block:: python

   stream = EventStream()
   stream.add_exporter(JSONLExporter("archive.jsonl"))
   stream.add_exporter(OTLPExporter("http://otel:4317", service_name="llm"))
   stream.add_exporter(WebhookExporter("https://slack.example/webhook"))

   for event in events:
       stream.emit(event)

Flush and close
---------------

Exporters that buffer output implement a ``flush()`` method.  Use as a context
manager to ensure resources are released:

.. code-block:: python

   with JSONLExporter("events.jsonl") as exporter:
       for event in events:
           exporter.export(event)
   # flush + close called automatically
