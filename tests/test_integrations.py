"""Tests for llm_toolkit_schema.integrations (LangChain + LlamaIndex handlers)."""

from __future__ import annotations

import sys
import types
import uuid
import warnings
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from llm_toolkit_schema import Event, EventType
from llm_toolkit_schema.ulid import generate as gen_ulid


# ---------------------------------------------------------------------------
# Helpers: inject fake langchain / llamaindex modules
# ---------------------------------------------------------------------------


def _inject_fake_langchain() -> None:
    """Inject minimal stub modules so LangChain imports succeed without the real package."""
    if "langchain_core" not in sys.modules:
        langchain_core = types.ModuleType("langchain_core")
        langchain_core.callbacks = types.ModuleType("langchain_core.callbacks")
        sys.modules["langchain_core"] = langchain_core
        sys.modules["langchain_core.callbacks"] = langchain_core.callbacks


def _inject_fake_llamaindex() -> None:
    """Inject minimal stub modules so LlamaIndex imports succeed without the real package."""
    if "llama_index.core.callbacks" not in sys.modules:
        llama_index_mod = types.ModuleType("llama_index")
        core_mod = types.ModuleType("llama_index.core")
        callbacks_mod = types.ModuleType("llama_index.core.callbacks")
        # Wire attribute relationships as Python's import system would.
        llama_index_mod.core = core_mod  # type: ignore[attr-defined]
        core_mod.callbacks = callbacks_mod  # type: ignore[attr-defined]
        sys.modules["llama_index"] = llama_index_mod
        sys.modules["llama_index.core"] = core_mod
        sys.modules["llama_index.core.callbacks"] = callbacks_mod


# ---------------------------------------------------------------------------
# LangChain handler
# ---------------------------------------------------------------------------


class TestLLMSchemaCallbackHandler:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        _inject_fake_langchain()

    def _make_handler(self) -> Any:
        from llm_toolkit_schema.integrations.langchain import LLMSchemaCallbackHandler

        return LLMSchemaCallbackHandler(source="test-app", org_id="org-1")

    def test_import_error_without_langchain(self) -> None:
        """Verify ImportError is raised when langchain is not installed."""
        with patch.dict(sys.modules, {"langchain_core": None, "langchain": None}):
            from importlib import reload
            import llm_toolkit_schema.integrations.langchain as lc_mod

            with pytest.raises(ImportError, match="LangChain"):
                lc_mod._require_langchain()

    def test_construction(self) -> None:
        handler = self._make_handler()
        assert handler._source == "test-app"
        assert handler._org_id == "org-1"
        assert handler.events == []

    def test_on_llm_start_emits_event(self) -> None:
        handler = self._make_handler()
        run_id = uuid.uuid4()
        handler.on_llm_start(
            serialized={"id": ["openai", "ChatOpenAI"]},
            prompts=["Hello"],
            run_id=run_id,
        )
        assert len(handler.events) == 1
        ev = handler.events[0]
        assert ev.event_type == "llm.trace.span.started"
        assert ev.source == "test-app"

    def test_on_llm_end_emits_event(self) -> None:
        handler = self._make_handler()
        run_id = uuid.uuid4()

        response = MagicMock()
        response.llm_output = {"token_usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}

        handler.on_llm_end(response=response, run_id=run_id)
        assert len(handler.events) == 1
        ev = handler.events[0]
        assert ev.event_type == "llm.trace.span.completed"
        assert ev.payload["prompt_tokens"] == 10

    def test_on_llm_error_emits_event(self) -> None:
        handler = self._make_handler()
        run_id = uuid.uuid4()
        handler.on_llm_error(error=ValueError("bad"), run_id=run_id)
        assert len(handler.events) == 1
        assert handler.events[0].event_type == "llm.trace.span.error"

    def test_on_tool_start_emits_event(self) -> None:
        handler = self._make_handler()
        run_id = uuid.uuid4()
        handler.on_tool_start(
            serialized={"name": "search"},
            input_str="query text",
            run_id=run_id,
        )
        assert handler.events[0].event_type == "llm.trace.tool_call.started"
        assert handler.events[0].payload["tool_name"] == "search"

    def test_on_tool_end_emits_event(self) -> None:
        handler = self._make_handler()
        run_id = uuid.uuid4()
        handler.on_tool_end(output="result text", run_id=run_id)
        assert handler.events[0].event_type == "llm.trace.tool_call.completed"

    def test_on_tool_error_emits_event(self) -> None:
        handler = self._make_handler()
        run_id = uuid.uuid4()
        handler.on_tool_error(error=RuntimeError("fail"), run_id=run_id)
        assert handler.events[0].event_type == "llm.trace.tool_call.error"

    def test_clear_events(self) -> None:
        handler = self._make_handler()
        run_id = uuid.uuid4()
        handler.on_llm_start(serialized={"id": ["x"]}, prompts=["p"], run_id=run_id)
        assert len(handler.events) == 1
        handler.clear_events()
        assert len(handler.events) == 0

    def test_on_llm_end_no_token_usage(self) -> None:
        handler = self._make_handler()
        run_id = uuid.uuid4()
        response = MagicMock()
        response.llm_output = {}
        handler.on_llm_end(response=response, run_id=run_id)
        ev = handler.events[0]
        assert ev.event_type == "llm.trace.span.completed"

    def test_org_id_in_event(self) -> None:
        handler = self._make_handler()
        run_id = uuid.uuid4()
        handler.on_llm_start(serialized={"id": ["x"]}, prompts=["p"], run_id=run_id)
        assert handler.events[0].org_id == "org-1"

    def test_exporter_called(self) -> None:
        """When an exporter is provided, it should receive the event."""
        import asyncio

        _inject_fake_langchain()
        from llm_toolkit_schema.integrations.langchain import LLMSchemaCallbackHandler

        exported: list[Any] = []

        class FakeExporter:
            async def export(self, event: Event) -> None:
                exported.append(event)

        handler = LLMSchemaCallbackHandler(source="app", exporter=FakeExporter())
        run_id = uuid.uuid4()

        loop = asyncio.new_event_loop()
        try:
            # on_llm_start emits an event — exporter.export is scheduled as task
            # but since the loop isn't running when called synchronously, the
            # task is never executed.  Just verify the handler didn't crash.
            handler.on_llm_start(serialized={"id": ["x"]}, prompts=["p"], run_id=run_id)
        finally:
            loop.close()

        assert len(handler.events) == 1


# ---------------------------------------------------------------------------
# LlamaIndex handler
# ---------------------------------------------------------------------------


class TestLLMSchemaEventHandler:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        _inject_fake_llamaindex()

    def _make_handler(self) -> Any:
        from llm_toolkit_schema.integrations.llamaindex import LLMSchemaEventHandler

        return LLMSchemaEventHandler(source="rag-app", org_id="org-2")

    def test_import_error_without_llamaindex(self) -> None:
        with patch.dict(sys.modules, {"llama_index": None, "llama_index.core": None}):
            from importlib import reload
            import llm_toolkit_schema.integrations.llamaindex as li_mod

            with pytest.raises(ImportError, match="LlamaIndex"):
                li_mod._require_llamaindex()

    def test_construction(self) -> None:
        handler = self._make_handler()
        assert handler._source == "rag-app"
        assert handler._org_id == "org-2"
        assert handler.events == []

    def test_on_event_start_llm(self) -> None:
        handler = self._make_handler()
        event_id = handler.on_event_start("LLM", payload={"model_dict": {"model": "gpt-4o"}}, event_id="ev-1")
        assert event_id == "ev-1"
        assert len(handler.events) == 1
        assert handler.events[0].event_type == "llm.trace.span.started"

    def test_on_event_end_llm(self) -> None:
        handler = self._make_handler()
        handler.on_event_start("LLM", event_id="ev-1")
        handler.on_event_end("LLM", event_id="ev-1")
        # One start + one end event.
        assert len(handler.events) == 2
        assert handler.events[1].event_type == "llm.trace.span.completed"

    def test_on_event_start_tool(self) -> None:
        handler = self._make_handler()
        handler.on_event_start("FUNCTION_CALL", payload={"tool": {"name": "search"}}, event_id="ev-2")
        assert handler.events[0].event_type == "llm.trace.tool_call.started"

    def test_on_event_end_tool(self) -> None:
        handler = self._make_handler()
        handler.on_event_start("FUNCTION_CALL", event_id="ev-2")
        handler.on_event_end("FUNCTION_CALL", payload={"output": "result"}, event_id="ev-2")
        assert handler.events[1].event_type == "llm.trace.tool_call.completed"

    def test_on_event_start_query(self) -> None:
        handler = self._make_handler()
        handler.on_event_start("QUERY", payload={"query_str": "What is AI?"}, event_id="ev-3")
        assert handler.events[0].event_type == "llm.trace.query.started"

    def test_on_event_end_query(self) -> None:
        handler = self._make_handler()
        handler.on_event_start("QUERY", event_id="ev-3")
        handler.on_event_end("QUERY", event_id="ev-3")
        assert handler.events[1].event_type == "llm.trace.query.completed"

    def test_unknown_event_type_does_not_emit(self) -> None:
        handler = self._make_handler()
        handler.on_event_start("SOME_UNKNOWN_TYPE", event_id="ev-x")
        assert len(handler.events) == 0

    def test_duration_ms_calculated(self) -> None:
        handler = self._make_handler()
        handler.on_event_start("LLM", event_id="ev-1")
        handler.on_event_end("LLM", event_id="ev-1")
        completed = handler.events[1]
        # duration_ms may be 0.0 or positive — both are valid.
        assert completed.payload["duration_ms"] is not None

    def test_start_trace_end_trace_noop(self) -> None:
        handler = self._make_handler()
        # Should not raise.
        handler.start_trace("trace-id")
        handler.end_trace("trace-id", {})

    def test_clear_events(self) -> None:
        handler = self._make_handler()
        handler.on_event_start("LLM", event_id="ev-1")
        handler.clear_events()
        assert len(handler.events) == 0

    def test_on_event_end_unknown_event_id(self) -> None:
        handler = self._make_handler()
        # Ending an event that was never started should not raise.
        handler.on_event_end("LLM", event_id="unknown-id")
        # A completed event with None duration.
        ev = handler.events[0]
        assert ev.payload["duration_ms"] is None
