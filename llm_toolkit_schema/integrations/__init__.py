"""Framework integration callbacks for llm-toolkit-schema.

Provides thin adapter layers that bridge popular LLM orchestration frameworks
into the llm-toolkit-schema event model.  All integrations use **soft
dependencies** — the underlying framework must be installed separately.

Available integrations
-----------------------
* :mod:`~llm_toolkit_schema.integrations.langchain` — LangChain callback handler.
* :mod:`~llm_toolkit_schema.integrations.llamaindex` — LlamaIndex event handler.

Example — LangChain::

    from llm_toolkit_schema.integrations import LLMSchemaCallbackHandler

    handler = LLMSchemaCallbackHandler(source="my-app", org_id="acme")
    llm = ChatOpenAI(callbacks=[handler])

Example — LlamaIndex::

    from llm_toolkit_schema.integrations import LLMSchemaEventHandler

    handler = LLMSchemaEventHandler(source="my-app")
    from llama_index.core import Settings
    Settings.callback_manager.add_handler(handler)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

__all__ = [
    "LLMSchemaCallbackHandler",
    "LLMSchemaEventHandler",
]


def __getattr__(name: str) -> object:  # pragma: no cover
    if name == "LLMSchemaCallbackHandler":
        from llm_toolkit_schema.integrations.langchain import LLMSchemaCallbackHandler
        return LLMSchemaCallbackHandler
    if name == "LLMSchemaEventHandler":
        from llm_toolkit_schema.integrations.llamaindex import LLMSchemaEventHandler
        return LLMSchemaEventHandler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
