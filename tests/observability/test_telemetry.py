"""
Unit tests for OpenTelemetry & Prometheus observability engine.
"""

import importlib.util
from pathlib import Path

from aiconnex_agent.telemetry import get_tracer, trace_span

_app_path = Path(__file__).resolve().parent.parent.parent / "data-studio" / "intake" / "app.py"
_app_spec = importlib.util.spec_from_file_location("app_mod", _app_path)
assert _app_spec is not None and _app_spec.loader is not None
_app_mod = importlib.util.module_from_spec(_app_spec)
_app_spec.loader.exec_module(_app_mod)


def test_opentelemetry_tracer_and_span():
    tracer = get_tracer()
    assert tracer is not None

    with trace_span("test.unit_span", {"test_key": "test_value"}) as span:
        assert span is not None


def test_prometheus_metrics_endpoint():
    response = _app_mod.metrics_endpoint()
    assert response.status_code == 200
    assert "text/plain" in response.media_type
    assert len(response.body) > 0
