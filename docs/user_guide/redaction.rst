.. _user_guide_redaction:

PII Redaction
=============

llm-toolkit-schema provides a field-level PII redaction framework that lets you mark
sensitive values at the point of creation and apply policies before the event
is stored, exported, or logged.

Sensitivity levels
------------------

:class:`~llm_toolkit_schema.redact.Sensitivity` defines five ordered levels:

.. code-block:: python

   from llm_toolkit_schema.redact import Sensitivity

   Sensitivity.PUBLIC       # 1 — safe to log anywhere
   Sensitivity.INTERNAL     # 2 — internal-only
   Sensitivity.CONFIDENTIAL # 3 — restricted
   Sensitivity.PII          # 4 — personally identifiable information
   Sensitivity.SECRET       # 5 — credentials, tokens, keys

Marking fields as redactable
------------------------------

Wrap any payload value in :class:`~llm_toolkit_schema.redact.Redactable` to mark it:

.. code-block:: python

   from llm_toolkit_schema import Event, EventType
   from llm_toolkit_schema.redact import Redactable, Sensitivity

   event = Event(
       event_type=EventType.PROMPT_SAVED,
       source="promptlock@1.0.0",
       payload={
           "prompt_text": Redactable(
               value="User email: alice@example.com",
               sensitivity=Sensitivity.PII,
               pii_types={"email"},
           ),
           "model": "gpt-4o",           # plain value — not redactable
       },
   )

Applying a redaction policy
-----------------------------

:class:`~llm_toolkit_schema.redact.RedactionPolicy` scrubs every ``Redactable`` field
whose sensitivity is at or above the policy's ``min_sensitivity``:

.. code-block:: python

   from llm_toolkit_schema.redact import RedactionPolicy, Sensitivity

   policy = RedactionPolicy(
       min_sensitivity=Sensitivity.PII,
       redacted_by="policy:corp-v1",
   )

   result = policy.apply(event)
   # result.event.payload["prompt_text"] == "[REDACTED]"
   # result.event.payload["model"]       == "gpt-4o"  (unchanged)

   print(result.redacted_count)          # 1
   print(result.fields_redacted)         # ["prompt_text"]

Inspecting redaction results
-----------------------------

.. code-block:: python

   result = policy.apply(event)

   for field_name in result.fields_redacted:
       print(f"  {field_name} was redacted")

   # Check nothing was missed
   from llm_toolkit_schema.redact import assert_redacted
   assert_redacted(result, min_sensitivity=Sensitivity.PII)
   # raises PIINotRedactedError if any PII field was left unredacted

Detecting PII without redacting
---------------------------------

.. code-block:: python

   from llm_toolkit_schema.redact import contains_pii

   if contains_pii(event):
       print("Event contains PII — apply policy before exporting")

Built-in PII types
-------------------

:data:`~llm_toolkit_schema.redact.PII_TYPES` provides the built-in set of PII type
labels:

.. code-block:: python

   from llm_toolkit_schema.redact import PII_TYPES
   print(PII_TYPES)
   # frozenset({'email', 'phone', 'name', 'address', 'ip', 'ssn', 'dob', ...})

Policy-based workflow
----------------------

The recommended workflow is:

1. Tools emit events with ``Redactable`` wrappers on all sensitive fields.
2. The event collector/exporter applies the appropriate ``RedactionPolicy``
   before writing to storage or sending over the wire.
3. CI runs ``assert_redacted()`` or ``contains_pii()`` on sampled events to
   catch unannotated fields.

.. code-block:: python

   from llm_toolkit_schema.redact import RedactionPolicy, Sensitivity, assert_redacted

   # Strict policy — redact everything at PII or above
   CORP_POLICY = RedactionPolicy(
       min_sensitivity=Sensitivity.PII,
       redacted_by="policy:corp-v1",
   )

   def export_event(event):
       result = CORP_POLICY.apply(event)
       assert_redacted(result, min_sensitivity=Sensitivity.PII)
       write_to_storage(result.event)
