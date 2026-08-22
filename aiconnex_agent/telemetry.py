"""
OpenTelemetry (OTel) & Observability Helper Module.
Provides tracer initialization, span tracing context manager, and metrics utilities.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import Span, Tracer

# Global tracer initialization
_provider = TracerProvider()
_processor = SimpleSpanProcessor(ConsoleSpanExporter())
_provider.add_span_processor(_processor)
trace.set_tracer_provider(_provider)

tracer: Tracer = trace.get_tracer("aiconnex_agent", "2.0.0")


def get_tracer() -> Tracer:
    """Return configured OpenTelemetry tracer."""
    return tracer


@contextmanager
def trace_span(span_name: str, attributes: dict[str, Any] | None = None) -> Generator[Span, None, None]:
    """
    Context manager to trace an execution block with OpenTelemetry.
    """
    with tracer.start_as_current_span(span_name) as span:
        if attributes:
            for key, val in attributes.items():
                span.set_attribute(key, str(val))
        yield span
