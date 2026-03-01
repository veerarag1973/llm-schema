.. _installation:

Installation
============

Requirements
------------

- Python **3.9** or later
- No required third-party dependencies for core event creation

Install from PyPI
-----------------

.. code-block:: bash

   pip install llm-toolkit-schema

Optional extras
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Extra
     - Install command
     - What it enables
   * - ``jsonschema``
     - ``pip install "llm-toolkit-schema[jsonschema]"``
     - :func:`~llm_toolkit_schema.validate.validate_event` with full JSON Schema validation
   * - ``http``
     - ``pip install "llm-toolkit-schema[http]"``
     - :class:`~llm_toolkit_schema.export.otlp.OTLPExporter` and
       :class:`~llm_toolkit_schema.export.webhook.WebhookExporter` (requires ``httpx``)
   * - ``pydantic``
     - ``pip install "llm-toolkit-schema[pydantic]"``
     - :mod:`llm_toolkit_schema.models` — Pydantic v2 model layer, ``model_json_schema()``
   * - ``otel``
     - ``pip install "llm-toolkit-schema[otel]"``
     - OpenTelemetry SDK integration (``opentelemetry-sdk``)

Install all optional extras at once:

.. code-block:: bash

   pip install "llm-toolkit-schema[jsonschema,http,pydantic]"

Development installation
-------------------------

.. code-block:: bash

   git clone https://github.com/llm-toolkit/llm-toolkit-schema.git
   cd llm-toolkit-schema
   python -m venv .venv
   .venv/Scripts/activate          # Windows
   # source .venv/bin/activate     # macOS / Linux
   pip install -e ".[dev]"

This installs all development dependencies including pytest, ruff, mypy, and
all optional extras.

Verify the installation
------------------------

.. code-block:: python

   import llm_toolkit_schema
   print(llm_toolkit_schema.__version__)   # 1.0.0
   print(llm_toolkit_schema.SCHEMA_VERSION)  # 1.0

   from llm_toolkit_schema import Event, EventType
   evt = Event(
       event_type=EventType.TRACE_SPAN_COMPLETED,
       source="smoke-test@1.0.0",
       payload={"ok": True},
   )
   evt.validate()
   print("Installation OK")
