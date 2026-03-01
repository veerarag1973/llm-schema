.. _ns_redact_ns:

llm.redact — Redaction Audit Record
=====================================

.. note::

   This namespace payload records *metadata about a redaction operation* —
   for example, which PII types were detected and which policy was applied.
   It is distinct from the runtime :mod:`llm_toolkit_schema.redact` module that
   performs the actual field-level redaction.

.. automodule:: llm_toolkit_schema.namespaces.redact
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
   * - ``policy_id``
     - ``str``
     - Identifier of the :class:`~llm_toolkit_schema.redact.RedactionPolicy` applied.
   * - ``pii_types_detected``
     - ``list[str]``
     - PII type strings that were detected (e.g. ``["email", "phone"]``).
   * - ``fields_redacted``
     - ``list[str]``
     - Payload field paths that were redacted.
   * - ``redaction_count``
     - ``int``
     - Total number of individual redaction substitutions made.
   * - ``sensitivity_level``
     - ``str``
     - Highest :class:`~llm_toolkit_schema.redact.SensitivityLevel` encountered.

Example
-------

.. code-block:: python

   from llm_toolkit_schema.namespaces.redact import RedactPayload

   payload = RedactPayload(
       policy_id="default-v1",
       pii_types_detected=["email", "phone"],
       fields_redacted=["prompt", "completion"],
       redaction_count=3,
       sensitivity_level="HIGH",
   )
