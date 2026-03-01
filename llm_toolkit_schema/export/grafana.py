"""Grafana Loki exporter for llm-toolkit-schema events.

Delivers events as structured log entries to a Grafana Loki instance via the
Loki HTTP push API (``/loki/api/v1/push``).

Each event is pushed as a single Loki log entry with:

* The **timestamp** taken from the event's ``timestamp`` field (nanoseconds).
* The **log line** set to the canonical JSON of the event (``event.to_json()``).
* **Labels** derived from the event's envelope fields (``env``, ``service``,
  ``event_type``, ``org_id``).

Loki streams are grouped by label set, so events with identical labels are
batched into a single stream when using :meth:`export_batch`.

No external Grafana SDK required — uses stdlib HTTP only.

Example::

    from llm_toolkit_schema.export.grafana import GrafanaLokiExporter

    exporter = GrafanaLokiExporter(
        url="http://localhost:3100",
        labels={"env": "production", "service": "llm-trace"},
    )
    await exporter.export(event)
"""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Sequence

from llm_toolkit_schema.event import Event
from llm_toolkit_schema.exceptions import ExportError

__all__ = ["GrafanaLokiExporter"]

_PUSH_PATH = "/loki/api/v1/push"


class GrafanaLokiExporter:
    """Async exporter that pushes llm-toolkit-schema events to Grafana Loki.

    Events are pushed as structured JSON log lines, grouped into Loki streams
    by label set.  Labels can be set globally at exporter construction and
    are supplemented with per-event envelope fields (``org_id``, ``event_type``).

    Args:
        url:              Base URL of the Loki push API, e.g.
                          ``"http://localhost:3100"``.
        labels:           Global label set applied to every push.  Typically
                          includes ``env`` and ``service``.
        include_envelope_labels:
                          When ``True`` (default), ``event_type`` and ``org_id``
                          (when present) are added to each stream's label set,
                          creating per-type Loki streams.
        tenant_id:        Optional Loki tenant ID header (``X-Scope-OrgID``).
                          Required for multi-tenant Loki deployments.
        extra_headers:    Optional extra HTTP request headers.
        timeout:          HTTP timeout in seconds (default 5.0).

    Example::

        exporter = GrafanaLokiExporter(
            url="http://loki:3100",
            labels={"env": "production", "service": "llm-trace"},
            tenant_id="acme",
        )
        await exporter.export(event)
    """

    def __init__(
        self,
        url: str,
        *,
        labels: Optional[Dict[str, str]] = None,
        include_envelope_labels: bool = True,
        tenant_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        timeout: float = 5.0,
    ) -> None:
        if not url:
            raise ValueError("url must be a non-empty string")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self._base_url = url.rstrip("/")
        self._global_labels: Dict[str, str] = dict(labels) if labels else {}
        self._include_envelope_labels = include_envelope_labels
        self._tenant_id = tenant_id
        self._extra_headers: Dict[str, str] = dict(extra_headers) if extra_headers else {}
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public mapping API (pure, no I/O)
    # ------------------------------------------------------------------

    def event_to_loki_entry(self, event: Event) -> Dict[str, Any]:
        """Convert a single event to a Loki stream + entry dict.

        Returns a dict with ``"stream"`` (label set) and ``"values"`` (list
        of ``[timestamp_ns_str, log_line]`` pairs).

        Args:
            event: The event to convert.

        Returns:
            A Loki stream dict with a single entry.
        """
        # Build label set for this event.
        stream_labels: Dict[str, str] = dict(self._global_labels)
        if self._include_envelope_labels:
            # Sanitise event_type for Loki labels (dots → underscores).
            stream_labels["event_type"] = str(event.event_type).replace(".", "_")
            if event.org_id:
                stream_labels["org_id"] = event.org_id

        # Convert ISO-8601 timestamp to nanoseconds.
        ts_ns = self._iso_to_ns(event.timestamp)

        return {
            "stream": stream_labels,
            "values": [[str(ts_ns), event.to_json()]],
        }

    # ------------------------------------------------------------------
    # Async export API
    # ------------------------------------------------------------------

    async def export(self, event: Event) -> None:
        """Push a single event to Loki.

        Args:
            event: The event to push.

        Raises:
            ExportError: If the HTTP push fails.
        """
        await self.export_batch([event])

    async def export_batch(self, events: Sequence[Event]) -> int:
        """Push multiple events to Loki, grouped by label set.

        Events that share an identical label set are batched into a single
        Loki stream, reducing the number of HTTP requests.

        Args:
            events: Sequence of events to push.

        Returns:
            Number of events pushed.

        Raises:
            ExportError: If the HTTP push fails.
        """
        if not events:
            return 0

        # Group entries by label-set key (serialise label dict as sorted JSON str).
        from collections import defaultdict

        stream_map: dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"stream": {}, "values": []}
        )

        for event in events:
            entry = self.event_to_loki_entry(event)
            key = json.dumps(entry["stream"], sort_keys=True)
            if not stream_map[key]["stream"]:
                stream_map[key]["stream"] = entry["stream"]
            stream_map[key]["values"].extend(entry["values"])

        payload = json.dumps(
            {"streams": list(stream_map.values())},
            separators=(",", ":"),
        ).encode("utf-8")

        await self._push(payload)
        return len(events)

    # ------------------------------------------------------------------
    # HTTP transport
    # ------------------------------------------------------------------

    async def _push(self, payload: bytes) -> None:
        """POST *payload* to the Loki push endpoint."""
        url = f"{self._base_url}{_PUSH_PATH}"
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            **self._extra_headers,
        }
        if self._tenant_id:
            headers["X-Scope-OrgID"] = self._tenant_id

        timeout = self._timeout

        def _do() -> None:
            req = urllib.request.Request(
                url=url,
                data=payload,
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    resp.read()
            except urllib.error.HTTPError as exc:
                raise ExportError("grafana-loki", f"HTTP {exc.code}: {exc.reason}") from exc
            except OSError as exc:
                raise ExportError("grafana-loki", str(exc)) from exc

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _do)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _iso_to_ns(timestamp: str) -> int:
        """Convert an ISO-8601 UTC timestamp to integer nanoseconds since epoch."""
        import sys
        from datetime import datetime, timezone

        normalised = timestamp.replace("Z", "+00:00")
        if sys.version_info >= (3, 11):  # pragma: no cover
            dt = datetime.fromisoformat(normalised)
        else:
            try:
                dt = datetime.strptime(normalised, "%Y-%m-%dT%H:%M:%S.%f+00:00")
            except ValueError:
                dt = datetime.strptime(normalised, "%Y-%m-%dT%H:%M:%S+00:00")
            dt = dt.replace(tzinfo=timezone.utc)

        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        delta = dt - epoch
        return int(delta.total_seconds() * 1_000_000_000)

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"GrafanaLokiExporter(url={self._base_url!r}, "
            f"labels={self._global_labels!r})"
        )
