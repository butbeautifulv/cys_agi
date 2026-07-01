from __future__ import annotations

import logging
from typing import Any

from bootstrap.settings import settings
from cys_core.application.ports.observability.trace_backend import TraceBackendPort
from cys_core.domain.observability.models import TraceContext

logger = logging.getLogger(__name__)


class OtelTraceBackend:
    """OpenTelemetry trace export (parallel sink)."""

    def __init__(self) -> None:
        self._tracer = None
        if settings.otel_enabled:
            try:
                from opentelemetry import trace
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                from opentelemetry.sdk.resources import Resource
                from opentelemetry.sdk.trace import TracerProvider
                from opentelemetry.sdk.trace.export import BatchSpanProcessor

                provider = TracerProvider(resource=Resource.create({"service.name": "egregore"}))
                exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint, insecure=True)
                provider.add_span_processor(BatchSpanProcessor(exporter))
                trace.set_tracer_provider(provider)
                self._tracer = trace.get_tracer("egregore")
            except Exception:
                logger.warning("OTel trace backend unavailable", exc_info=True)

    def get_callback_handler(self) -> Any | None:
        return None

    def start_span(self, ctx: TraceContext) -> str:
        if self._tracer is None:
            return ""
        span = self._tracer.start_span(ctx.span_name or "run")
        return format(span.get_span_context().span_id)

    def end_span(self, span_id: str) -> None:
        _ = span_id

    def flush(self) -> None:
        return None

    def shutdown(self) -> None:
        return None
