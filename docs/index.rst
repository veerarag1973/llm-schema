.. llm-toolkit-schema documentation master file

llm-toolkit-schema
==================

**The foundational shared event schema for the LLM Developer Toolkit.**

.. note::

   Current release: |release| — `Changelog <https://github.com/llm-toolkit/llm-toolkit-schema/releases>`_

llm-toolkit-schema transforms 17 independent LLM developer tools into a composable ecosystem
by providing an OpenTelemetry-compatible, versioned, enterprise-grade event contract.
Every tool in the toolkit emits structured :class:`~llm_toolkit_schema.event.Event` objects
that share a common envelope, enabling unified observability, audit trails,
cost attribution, and PII redaction across your entire LLM stack.

**Key features**

- **Zero required dependencies** — core event creation uses only the Python stdlib
- **OpenTelemetry-compatible** — OTLP export, trace/span identifiers, attribute mapping
- **Tamper-evident audit chain** — HMAC-SHA256 signing with gap detection
- **PII redaction framework** — field-level sensitivity tagging, policy-based scrubbing
- **10 namespace payload dataclasses** — typed payloads for trace, cost, eval, guard, and more
- **Compliance tooling** — :func:`~llm_toolkit_schema.compliance.test_compatibility` for third-party adoption
- **100% test coverage** — 1 084 tests, branch coverage, full CI

.. code-block:: python

   from llm_toolkit_schema import Event, EventType, Tags

   event = Event(
       event_type=EventType.TRACE_SPAN_COMPLETED,
       source="my-tool@1.0.0",
       payload={"span_name": "run_agent", "status": "ok"},
       tags=Tags(env="production", model="gpt-4o"),
   )
   print(event.to_json())


.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   quickstart
   installation

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index

.. toctree::
   :maxdepth: 2
   :caption: Namespace Payloads

   namespaces/index

.. toctree::
   :maxdepth: 1
   :caption: Command-Line Interface

   cli

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   changelog


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
