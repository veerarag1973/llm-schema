.. _ns_prompt:

llm.prompt — Prompt Versioning
================================

.. automodule:: llm_toolkit_schema.namespaces.prompt
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
   * - ``template_id``
     - ``str``
     - Identifier of the prompt template used.
   * - ``template_version``
     - ``str``
     - Semantic version of the template (e.g. ``"1.2.0"``).
   * - ``rendered_prompt``
     - ``str | None``
     - Final rendered prompt text after variable substitution.
   * - ``variables``
     - ``dict[str, str] | None``
     - Variables substituted into the template.
   * - ``system_prompt_hash``
     - ``str | None``
     - SHA-256 hash of the system prompt for integrity checking.

Example
-------

.. code-block:: python

   from llm_toolkit_schema.namespaces.prompt import PromptPayload

   payload = PromptPayload(
       template_id="support-reply-v3",
       template_version="3.1.0",
       variables={"customer_name": "Alice", "product": "widget"},
       system_prompt_hash="sha256:deadbeef...",
   )
