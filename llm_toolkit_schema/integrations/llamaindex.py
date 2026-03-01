"""LlamaIndex event handler for llm-toolkit-schema.

Bridges LlamaIndex's ``CallbackManager`` into the llm-toolkit-schema event
model.  Each ``CBEventType.LLM`` start/end pair emits a
``llm.trace.span.started`` / ``llm.trace.span.completed`` event.  Each
``CBEventType.FUNCTION_CALL`` start/end pair emits a
``llm.trace.tool_call.started`` / ``llm.trace.tool_call.completed`` event.

Requires LlamaIndex to be installed::

    pip install "llm-toolkit-schema[llamaindex]"

Example::

    from llm_toolkit_schema.integrations.llamaindex import LLMSchemaEventHandler
    from llama_index.core import Settings

    handler = LLMSchemaEventHandler(source="my-app", org_id="acme")
    Settings.callback_manager.add_handler(handler)
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

__all__ = ["LLMSchemaEventHandler"]

# ---------------------------------------------------------------------------
# Lazy import guard
# ---------------------------------------------------------------------------


def _require_llamaindex() -> Any:
    try:
        import llama_index.core.callbacks  # type: ignore[import-untyped]
        return llama_index.core.callbacks
    except ImportError:
        pass
    try:
        import llama_index.callbacks  # type: ignore[import-untyped]
        return llama_index.callbacks
    except ImportError as exc:
        raise ImportError(
            "LlamaIndex is required for LLMSchemaEventHandler. "
            'Install it with: pip install "llm-toolkit-schema[llamaindex]"'
        ) from exc


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


class LLMSchemaEventHandler:
    """LlamaIndex callback handler that emits llm-toolkit-schema events.

    Compatible with both ``llama_index.core`` (≥ 0.10) and older ``llama_index``
    (≥ 0.9) package layouts.

    Extends ``BaseCallbackHandler`` from LlamaIndex dynamically at
    instantiation so that LlamaIndex remains a soft dependency.

    Args:
        source:    Logical source name (appears in ``event.source``).
        org_id:    Optional organisation / tenant identifier.
        exporter:  Optional exporter for async event delivery.

    Example::

        handler = LLMSchemaEventHandler(source="rag-pipeline", org_id="acme")
        Settings.callback_manager.add_handler(handler)
    """

    # LlamaIndex event-type strings (from CBEventType enum)
    _LLM_TYPES = frozenset({"llm", "LLM"})
    _TOOL_TYPES = frozenset({"function_call", "FUNCTION_CALL"})
    _EMBED_TYPES = frozenset({"embedding", "EMBEDDING"})
    _RETRIEVE_TYPES = frozenset({"retrieve", "RETRIEVE"})
    _QUERY_TYPES = frozenset({"query", "QUERY"})

    def __new__(cls, *args: Any, **kwargs: Any) -> "LLMSchemaEventHandler":
        _require_llamaindex()
        return super().__new__(cls)

    def __init__(
        self,
        source: str = "llamaindex",
        *,
        org_id: Optional[str] = None,
        exporter: Optional[Any] = None,
    ) -> None:
        self._source = source
        self._org_id = org_id
        self._exporter = exporter
        self._events: List[Any] = []
        # Track in-progress event start times keyed by cb_id.
        self._starts: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_event(self, event_type: str, payload: Dict[str, Any]) -> Any:
        from llm_toolkit_schema.event import Event

        event = Event(
            event_type=event_type,
            source=self._source,
            org_id=self._org_id,
            payload=payload,
        )
        self._events.append(event)
        if self._exporter is not None:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._exporter.export(event))
            except RuntimeError:  # pragma: no cover
                pass
        return event

    @staticmethod
    def _cb_event_type_str(event_type: Any) -> str:
        """Normalise a CBEventType enum or string to a plain string."""
        if hasattr(event_type, "value"):
            return str(event_type.value)
        return str(event_type)

    # ------------------------------------------------------------------
    # LlamaIndex BaseCallbackHandler interface
    # ------------------------------------------------------------------

    def on_event_start(
        self,
        event_type: Any,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        parent_id: str = "",
        **kwargs: Any,
    ) -> str:
        """Handle the start of a LlamaIndex event.

        Args:
            event_type: The ``CBEventType`` enum value or string.
            payload:    Optional payload dict from LlamaIndex.
            event_id:   LlamaIndex-assigned event id.
            parent_id:  Parent event id for nested calls.

        Returns:
            *event_id* (pass-through as per LlamaIndex contract).
        """
        et = self._cb_event_type_str(event_type)
        self._starts[event_id] = time.time()

        if et.lower() in self._LLM_TYPES:
            self._make_event(
                "llm.trace.span.started",
                {
                    "event_id": event_id,
                    "parent_id": parent_id,
                    "model": (payload or {}).get("model_dict", {}).get("model", "unknown"),
                    "start_time": self._starts[event_id],
                },
            )
        elif et.lower() in {e.lower() for e in self._TOOL_TYPES}:
            self._make_event(
                "llm.trace.tool_call.started",
                {
                    "event_id": event_id,
                    "parent_id": parent_id,
                    "tool_name": (payload or {}).get("tool", {}).get("name", "unknown"),
                    "start_time": self._starts[event_id],
                },
            )
        elif et.lower() in {e.lower() for e in self._QUERY_TYPES}:
            self._make_event(
                "llm.trace.query.started",
                {
                    "event_id": event_id,
                    "query": (payload or {}).get("query_str", ""),
                    "start_time": self._starts[event_id],
                },
            )
        return event_id

    def on_event_end(
        self,
        event_type: Any,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        """Handle the end of a LlamaIndex event.

        Args:
            event_type: The ``CBEventType`` enum value or string.
            payload:    Optional response payload dict from LlamaIndex.
            event_id:   LlamaIndex-assigned event id matching the start call.
        """
        et = self._cb_event_type_str(event_type)
        start_time = self._starts.pop(event_id, None)
        duration_ms: Optional[float] = None
        if start_time is not None:
            duration_ms = (time.time() - start_time) * 1000.0

        if et.lower() in self._LLM_TYPES:
            response = (payload or {}).get("response", {})
            token_info: Dict[str, Any] = {}
            if hasattr(response, "raw") and isinstance(response.raw, dict):
                usage = response.raw.get("usage", {})
                token_info = {
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                }
            self._make_event(
                "llm.trace.span.completed",
                {
                    "event_id": event_id,
                    "duration_ms": duration_ms,
                    **token_info,
                },
            )
        elif et.lower() in {e.lower() for e in self._TOOL_TYPES}:
            self._make_event(
                "llm.trace.tool_call.completed",
                {
                    "event_id": event_id,
                    "duration_ms": duration_ms,
                    "output_preview": str((payload or {}).get("output", ""))[:200],
                },
            )
        elif et.lower() in {e.lower() for e in self._QUERY_TYPES}:
            self._make_event(
                "llm.trace.query.completed",
                {"event_id": event_id, "duration_ms": duration_ms},
            )

    def start_trace(self, trace_id: Optional[str] = None) -> None:
        """No-op required by LlamaIndex BaseCallbackHandler contract."""

    def end_trace(
        self,
        trace_id: Optional[str] = None,
        trace_map: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """No-op required by LlamaIndex BaseCallbackHandler contract."""

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def events(self) -> List[Any]:
        """Return a snapshot of all emitted events.

        Returns:
            List of :class:`~llm_toolkit_schema.event.Event` objects.
        """
        return list(self._events)

    def clear_events(self) -> None:
        """Clear the in-memory event buffer and start-time tracking dict."""
        self._events.clear()
        self._starts.clear()

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"LLMSchemaEventHandler(source={self._source!r}, "
            f"events={len(self._events)})"
        )
