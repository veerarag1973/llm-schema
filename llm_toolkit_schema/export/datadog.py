"""Datadog-specific exporter for llm-toolkit-schema events.

Sends events to Datadog via two channels:

* **Traces / APM** — events with a ``trace_id`` are forwarded to the Datadog
  APM agent using the Datadog trace format (JSON over HTTP to the agent on
  port 8126).
* **Metrics** — events with numeric payload fields (e.g. ``cost_usd``,
  ``token_count``) are forwarded to the Datadog Metrics intake as custom
  metrics via the **Datadog API v2 series endpoint**.

Both channels are opt-in.  Omit the ``api_key`` to use only the local agent
(trace + log forwarding via the agent), or pass ``api_key`` to enable the
direct metrics intake.

No ``ddtrace`` or ``datadog`` package required — this module builds the wire
format from stdlib only.  If you have the Datadog SDK installed you can use
the returned dicts directly.

Example::

    from llm_toolkit_schema.export.datadog import DatadogExporter

    exporter = DatadogExporter(
        service="llm-trace",
        env="production",
        api_key="dd-api-key",          # optional: enables direct metrics intake
        agent_url="http://localhost:8126",  # optional: default
    )
    await exporter.export(event)
"""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from llm_toolkit_schema.event import Event
from llm_toolkit_schema.exceptions import ExportError

__all__ = ["DatadogExporter", "DatadogResourceAttributes"]

# Default Datadog agent trace intake address.
_DEFAULT_AGENT_URL = "http://localhost:8126"
_TRACE_ENDPOINT = "/v0.3/traces"
_DD_METRICS_URL = "https://api.datadoghq.com/api/v2/series"

# Payload fields extracted as Datadog custom metrics (numeric values only).
_METRIC_FIELDS = frozenset(
    [
        "cost_usd",
        "token_count",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "latency_ms",
        "duration_ms",
        "score",
    ]
)


# ---------------------------------------------------------------------------
# Resource attributes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DatadogResourceAttributes:
    """Datadog resource attributes attached to every exported trace/metric.

    Attributes:
        service:  Datadog service name (``service`` tag on all spans).
        env:      Deployment environment (``env`` standard tag).
        version:  Application version (``version`` standard tag).
        extra:    Additional arbitrary Datadog tags in ``key:value`` format.

    Example::

        attrs = DatadogResourceAttributes(
            service="llm-trace",
            env="production",
            version="1.0.0",
            extra={"team": "ai-platform"},
        )
    """

    service: str
    env: str = "production"
    version: str = "1.0.0"
    extra: Dict[str, str] = field(default_factory=dict)

    def to_tags(self) -> List[str]:
        """Return a flat list of ``key:value`` Datadog tag strings."""
        tags = [
            f"service:{self.service}",
            f"env:{self.env}",
            f"version:{self.version}",
        ]
        for k, v in self.extra.items():
            tags.append(f"{k}:{v}")
        return tags


# ---------------------------------------------------------------------------
# DatadogExporter
# ---------------------------------------------------------------------------


class DatadogExporter:
    """Async exporter that sends llm-toolkit-schema events to Datadog.

    **Trace channel**: Events with a ``trace_id`` are sent to the local Datadog
    agent as spans (APM).  This requires the Datadog agent to be running on
    ``agent_url`` (default ``http://localhost:8126``).

    **Metrics channel**: Numeric payload fields listed in ``metric_fields`` are
    forwarded to the Datadog Metrics API.  Requires ``api_key``.

    Args:
        service:          Datadog service name.
        env:              Deployment environment (default ``"production"``).
        agent_url:        Datadog agent URL (default ``"http://localhost:8126"``).
        api_key:          Datadog API key for the metrics intake.  ``None``
                          disables direct metric forwarding.
        dd_site:          Datadog site (e.g. ``"datadoghq.eu"``).  Defaults to
                          ``"datadoghq.com"``.
        resource_attrs:   :class:`DatadogResourceAttributes` (constructed from
                          *service* / *env* / *version* when ``None``).
        timeout:          HTTP request timeout in seconds (default 5.0).
        metric_fields:    Set of payload field names to extract as metrics.
                          Defaults to :data:`_METRIC_FIELDS`.

    Example::

        exporter = DatadogExporter(service="llm-trace", api_key="dd-api-key")
        await exporter.export(event)
    """

    def __init__(
        self,
        service: str,
        *,
        env: str = "production",
        agent_url: str = _DEFAULT_AGENT_URL,
        api_key: Optional[str] = None,
        dd_site: str = "datadoghq.com",
        resource_attrs: Optional[DatadogResourceAttributes] = None,
        timeout: float = 5.0,
        metric_fields: Optional[frozenset[str]] = None,
    ) -> None:
        if not service:
            raise ValueError("service must be a non-empty string")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self._service = service
        self._env = env
        self._agent_url = agent_url.rstrip("/")
        self._api_key: Optional[str] = api_key
        self._dd_site = dd_site
        self._resource_attrs: DatadogResourceAttributes = resource_attrs or DatadogResourceAttributes(
            service=service, env=env
        )
        self._timeout = timeout
        self._metric_fields: frozenset[str] = metric_fields if metric_fields is not None else _METRIC_FIELDS

    # ------------------------------------------------------------------
    # Public mapping API (pure, no I/O)
    # ------------------------------------------------------------------

    def to_dd_span(self, event: Event) -> Dict[str, Any]:
        """Map a single event to a Datadog APM span dict.

        Args:
            event: The event to map.

        Returns:
            A Datadog APM span dict ready to POST to ``/v0.3/traces``.
        """
        import time as _time

        trace_id_int = (
            int(event.trace_id, 16) & 0xFFFFFFFFFFFFFFFF
            if event.trace_id
            else abs(hash(event.event_id)) & 0xFFFFFFFFFFFFFFFF
        )
        span_id_int = (
            int(event.span_id, 16) & 0xFFFFFFFFFFFFFFFF
            if event.span_id
            else abs(hash(event.event_id + "_span")) & 0xFFFFFFFFFFFFFFFF
        )
        parent_id_int = (
            int(event.parent_span_id, 16) & 0xFFFFFFFFFFFFFFFF
            if event.parent_span_id
            else 0
        )

        # Convert ISO-8601 timestamp to nanoseconds (approximate — uses current time
        # for start; real spans carry latency_ms in payload when available).
        start_ns = int(_time.time() * 1e9)
        duration_ns = int(event.payload.get("duration_ms", 0) * 1_000_000)

        meta: Dict[str, str] = {
            "llm.event_id": event.event_id,
            "llm.event_type": str(event.event_type),
            "llm.source": event.source,
            "llm.schema_version": event.schema_version,
        }
        if event.org_id:
            meta["llm.org_id"] = event.org_id
        if event.team_id:
            meta["llm.team_id"] = event.team_id
        if event.actor_id:
            meta["llm.actor_id"] = event.actor_id
        if event.session_id:
            meta["llm.session_id"] = event.session_id
        if event.tags:
            for k, v in event.tags.items():
                meta[f"llm.tag.{k}"] = v

        # Flatten string payload fields into meta.
        for k, v in event.payload.items():
            if isinstance(v, str):
                meta[f"llm.payload.{k}"] = v

        metrics: Dict[str, float] = {}
        for k, v in event.payload.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                metrics[f"llm.payload.{k}"] = float(v)

        return {
            "trace_id": trace_id_int,
            "span_id": span_id_int,
            "parent_id": parent_id_int,
            "name": str(event.event_type),
            "resource": str(event.event_type),
            "service": self._service,
            "type": "custom",
            "start": start_ns,
            "duration": max(duration_ns, 1),
            "error": 0,
            "meta": meta,
            "metrics": metrics,
        }

    def to_dd_metric_series(
        self,
        event: Event,
    ) -> List[Dict[str, Any]]:
        """Extract numeric payload fields as Datadog metric series points.

        Only fields whose names appear in :attr:`metric_fields` are extracted.

        Args:
            event: The event to extract metrics from.

        Returns:
            A list of Datadog v2 metric series dicts (may be empty if no
            matching numeric fields are found).
        """
        import time as _time

        ts = int(_time.time())
        tags = self._resource_attrs.to_tags() + [
            f"llm.event_type:{event.event_type}",
        ]
        if event.org_id:
            tags.append(f"llm.org_id:{event.org_id}")
        if event.tags:
            for k, v in event.tags.items():
                tags.append(f"llm.tag.{k}:{v}")

        series = []
        for field_name, value in event.payload.items():
            if field_name not in self._metric_fields:
                continue
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            series.append(
                {
                    "metric": f"llm.{field_name}",
                    "type": 1,  # gauge
                    "points": [{"timestamp": ts, "value": float(value)}],
                    "resources": [
                        {"name": self._service, "type": "service"}
                    ],
                    "tags": tags,
                }
            )
        return series

    # ------------------------------------------------------------------
    # Async export API
    # ------------------------------------------------------------------

    async def export(self, event: Event) -> None:
        """Export a single event to Datadog.

        Sends to the APM agent if ``trace_id`` is present.  Sends any
        numeric payload fields to the Datadog metrics intake if ``api_key``
        is configured.

        Args:
            event: The event to export.

        Raises:
            ExportError: If any Datadog HTTP request fails.
        """
        await self.export_batch([event])

    async def export_batch(self, events: Sequence[Event]) -> None:
        """Export a batch of events to Datadog.

        Args:
            events: Sequence of events to export.

        Raises:
            ExportError: If any Datadog HTTP request fails.
        """
        if not events:
            return

        # Split into trace events and all events for metrics.
        trace_spans = [self.to_dd_span(e) for e in events if e.trace_id]
        all_series: List[Dict[str, Any]] = []
        for e in events:
            all_series.extend(self.to_dd_metric_series(e))

        tasks = []
        if trace_spans:
            tasks.append(self._send_traces(trace_spans))
        if all_series and self._api_key:
            tasks.append(self._send_metrics(all_series))

        if tasks:
            await asyncio.gather(*tasks)

    # ------------------------------------------------------------------
    # HTTP transport helpers
    # ------------------------------------------------------------------

    async def _send_traces(self, spans: List[Dict[str, Any]]) -> None:
        """POST trace spans to the Datadog agent."""
        payload = json.dumps([spans], separators=(",", ":")).encode("utf-8")
        url = f"{self._agent_url}{_TRACE_ENDPOINT}"
        timeout = self._timeout

        def _do() -> None:
            req = urllib.request.Request(
                url=url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Datadog-Trace-Count": str(len(spans)),
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    resp.read()
            except urllib.error.HTTPError as exc:
                raise ExportError("datadog-traces", f"HTTP {exc.code}: {exc.reason}") from exc
            except OSError as exc:
                raise ExportError("datadog-traces", str(exc)) from exc

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _do)

    async def _send_metrics(self, series: List[Dict[str, Any]]) -> None:
        """POST metric series to the Datadog Metrics API v2."""
        payload = json.dumps({"series": series}, separators=(",", ":")).encode("utf-8")
        url = f"https://api.{self._dd_site}/api/v2/series"
        api_key = self._api_key
        timeout = self._timeout

        def _do() -> None:
            req = urllib.request.Request(
                url=url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "DD-API-KEY": api_key or "",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    resp.read()
            except urllib.error.HTTPError as exc:
                raise ExportError("datadog-metrics", f"HTTP {exc.code}: {exc.reason}") from exc
            except OSError as exc:
                raise ExportError("datadog-metrics", str(exc)) from exc

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _do)

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"DatadogExporter(service={self._service!r}, "
            f"env={self._env!r}, "
            f"agent_url={self._agent_url!r})"
        )
