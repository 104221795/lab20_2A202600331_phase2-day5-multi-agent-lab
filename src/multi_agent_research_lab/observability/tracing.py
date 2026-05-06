"""Tracing helpers with OpenTelemetry when available."""

from collections.abc import Iterator
from contextlib import contextmanager, suppress
from os import getenv
from time import perf_counter
from typing import Any

_tracer: Any | None = None


def configure_tracing(service_name: str = "multi-agent-research-system") -> None:
    """Configure a console OpenTelemetry exporter if the optional package exists."""

    global _tracer
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

        provider = TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))
        if getenv("OTEL_CONSOLE_EXPORTER", "").lower() in {"1", "true", "yes"}:
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        with suppress(Exception):
            trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(service_name)
    except Exception:
        _tracer = None


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Trace a span and always yield a serializable local span dict."""

    started = perf_counter()
    local_span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "duration_seconds": None,
    }
    if _tracer is None:
        try:
            yield local_span
        finally:
            local_span["duration_seconds"] = perf_counter() - started
        return

    with _tracer.start_as_current_span(name) as span:
        for key, value in (attributes or {}).items():
            span.set_attribute(key, value)
        try:
            yield local_span
        finally:
            duration = perf_counter() - started
            local_span["duration_seconds"] = duration
            span.set_attribute("duration_seconds", duration)
