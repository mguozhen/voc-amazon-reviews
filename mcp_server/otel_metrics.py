"""Optional OpenTelemetry metrics exporter.

This module is fail-open:
- If OTel dependencies are missing, calls become no-ops.
- If exporter setup fails, tool calls continue unaffected.
"""
from __future__ import annotations

import os
from typing import Any

_ENABLED = os.getenv("OTEL_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
_READY = False
_TOOL_CALLS = None
_TOOL_LATENCY = None


def _init() -> None:
    global _READY, _TOOL_CALLS, _TOOL_LATENCY
    if not _ENABLED:
        return

    try:
        from opentelemetry import metrics
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
    except Exception:
        return

    try:
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", "http://localhost:4318/v1/metrics")
        service_name = os.getenv("OTEL_SERVICE_NAME", "voc-amazon-reviews-mcp")
        reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint))
        resource = Resource.create({"service.name": service_name})
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(provider)
        meter = metrics.get_meter("voc.mcp")
        _TOOL_CALLS = meter.create_counter(
            name="mcp_tool_calls_total",
            description="Total MCP tool calls",
        )
        _TOOL_LATENCY = meter.create_histogram(
            name="mcp_tool_latency_ms",
            description="MCP tool call latency in milliseconds",
            unit="ms",
        )
        _READY = True
    except Exception:
        _READY = False


_init()


def record(tool: str, status: str, latency_ms: int, client: str, error_type: str | None) -> None:
    """Record OTel metrics for one tool call. Never raises."""
    if not _READY or _TOOL_CALLS is None or _TOOL_LATENCY is None:
        return

    attrs: dict[str, Any] = {
        "tool": tool,
        "status": status,
        "client": client,
        "error_type": error_type or "none",
    }
    try:
        _TOOL_CALLS.add(1, attrs)
        _TOOL_LATENCY.record(int(latency_ms), attrs)
    except Exception:
        pass
