"""LangChain callback handler for llm-toolkit-schema.

Bridges LangChain's callback system into the llm-toolkit-schema event model.
Each ``on_llm_start`` / ``on_llm_end`` / ``on_tool_start`` / ``on_tool_end``
pair emits a started + completed event pair.

Requires LangChain to be installed::

    pip install "llm-toolkit-schema[langchain]"

Example::

    from llm_toolkit_schema.integrations.langchain import LLMSchemaCallbackHandler

    handler = LLMSchemaCallbackHandler(
        source="my-app",
        org_id="acme",
        exporter=exporter,          # optional: any Exporter
    )
    llm = ChatOpenAI(callbacks=[handler])
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional, Sequence, Union

__all__ = ["LLMSchemaCallbackHandler"]

# ---------------------------------------------------------------------------
# Lazy import guard
# ---------------------------------------------------------------------------


def _require_langchain() -> Any:
    try:
        import langchain_core.callbacks  # noqa: F401
        return langchain_core.callbacks
    except ImportError:
        pass
    try:
        import langchain.callbacks  # noqa: F401
        return langchain.callbacks
    except ImportError as exc:
        raise ImportError(
            "LangChain is required for LLMSchemaCallbackHandler. "
            'Install it with: pip install "llm-toolkit-schema[langchain]"'
        ) from exc


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


class LLMSchemaCallbackHandler:
    """LangChain callback handler that emits llm-toolkit-schema events.

    Every LLM invocation is wrapped in a ``TRACE_SPAN_STARTED`` /
    ``TRACE_SPAN_COMPLETED`` pair.  Every tool call is wrapped in a
    ``TRACE_TOOL_CALL_STARTED`` / ``TRACE_TOOL_CALL_COMPLETED`` pair.

    Events are written to an optional :class:`~llm_toolkit_schema.stream.Exporter`
    provided at construction time.  When no exporter is provided, events are
    collected in memory and accessible via :attr:`events`.

    This class does **not** extend ``BaseCallbackHandler`` at import time so
    that LangChain is a soft dependency.  The real base class is mixed in
    dynamically on first instantiation.

    Args:
        source:    Logical source name (appears in ``event.source``).
        org_id:    Optional organisation / tenant identifier.
        exporter:  Optional exporter for async event delivery.

    Example::

        handler = LLMSchemaCallbackHandler(source="chatbot", org_id="acme")
        llm = ChatOpenAI(callbacks=[handler])
    """

    def __new__(cls, *args: Any, **kwargs: Any) -> "LLMSchemaCallbackHandler":
        """Dynamically mix in the LangChain BaseCallbackHandler at instantiation."""
        _require_langchain()
        return super().__new__(cls)

    def __init__(
        self,
        source: str = "langchain",
        *,
        org_id: Optional[str] = None,
        exporter: Optional[Any] = None,
    ) -> None:
        self._source = source
        self._org_id = org_id
        self._exporter = exporter
        self._events: List[Any] = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        run_id: Optional[uuid.UUID] = None,
    ) -> Any:
        """Create an Event and register it."""
        from llm_toolkit_schema.event import Event

        event = Event(
            event_type=event_type,
            source=self._source,
            org_id=self._org_id,
            payload={
                "run_id": str(run_id) if run_id else None,
                **payload,
            },
        )
        self._events.append(event)
        if self._exporter is not None:
            # Fire-and-forget export in any running event loop; otherwise skip.
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._exporter.export(event))
            except RuntimeError:  # pragma: no cover — no running event loop
                pass
        return event

    # ------------------------------------------------------------------
    # LangChain callback methods
    # ------------------------------------------------------------------

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Emit ``llm.trace.span.started`` when an LLM call begins.

        Args:
            serialized: Serialised LLM config.
            prompts:    List of prompt strings.
            run_id:     LangChain run identifier.
        """
        self._make_event(
            "llm.trace.span.started",
            {
                "model": serialized.get("id", ["unknown"])[-1],
                "prompt_count": len(prompts),
                "tags": tags or [],
                "start_time": time.time(),
            },
            run_id=run_id,
        )

    def on_llm_end(
        self,
        response: Any,
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Emit ``llm.trace.span.completed`` when an LLM call succeeds.

        Args:
            response: LangChain ``LLMResult`` object.
            run_id:   LangChain run identifier.
        """
        token_usage: Dict[str, Any] = {}
        if hasattr(response, "llm_output") and isinstance(response.llm_output, dict):
            token_usage = response.llm_output.get("token_usage", {})

        self._make_event(
            "llm.trace.span.completed",
            {
                "prompt_tokens": token_usage.get("prompt_tokens"),
                "completion_tokens": token_usage.get("completion_tokens"),
                "total_tokens": token_usage.get("total_tokens"),
                "end_time": time.time(),
            },
            run_id=run_id,
        )

    def on_llm_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Emit ``llm.trace.span.error`` on LLM failure.

        Args:
            error:  The exception that occurred.
            run_id: LangChain run identifier.
        """
        self._make_event(
            "llm.trace.span.error",
            {"error": str(error), "error_type": type(error).__name__},
            run_id=run_id,
        )

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Emit ``llm.trace.tool_call.started`` when a tool is invoked.

        Args:
            serialized: Serialised tool config.
            input_str:  Stringified tool input.
            run_id:     LangChain run identifier.
        """
        self._make_event(
            "llm.trace.tool_call.started",
            {
                "tool_name": serialized.get("name", "unknown"),
                "input_preview": input_str[:200],
                "tags": tags or [],
                "start_time": time.time(),
            },
            run_id=run_id,
        )

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Emit ``llm.trace.tool_call.completed`` when a tool finishes.

        Args:
            output: Stringified tool output.
            run_id: LangChain run identifier.
        """
        self._make_event(
            "llm.trace.tool_call.completed",
            {"output_preview": str(output)[:200], "end_time": time.time()},
            run_id=run_id,
        )

    def on_tool_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Emit ``llm.trace.tool_call.error`` when a tool call fails.

        Args:
            error:  The exception that occurred.
            run_id: LangChain run identifier.
        """
        self._make_event(
            "llm.trace.tool_call.error",
            {"error": str(error), "error_type": type(error).__name__},
            run_id=run_id,
        )

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def events(self) -> List[Any]:
        """Return the list of events emitted so far (snapshot).

        Returns:
            List of :class:`~llm_toolkit_schema.event.Event` objects.
        """
        return list(self._events)

    def clear_events(self) -> None:
        """Clear the in-memory event buffer."""
        self._events.clear()

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"LLMSchemaCallbackHandler(source={self._source!r}, "
            f"events={len(self._events)})"
        )
