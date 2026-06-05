"""Optional OpenTelemetry instrumentation."""

import logging
import os

logger = logging.getLogger("travelsouls.telemetry")
_initialized = False


def setup_telemetry(service_name: str = "travelsouls-api") -> None:
    global _initialized
    if _initialized:
        return
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set; telemetry disabled")
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(provider)
        HTTPXClientInstrumentor().instrument()
        _initialized = True
        logger.info("OpenTelemetry initialized for %s", service_name)
    except ImportError:
        logger.warning("OpenTelemetry packages not installed; skipping instrumentation")
    except Exception as exc:
        logger.warning("OpenTelemetry setup failed: %s", exc)


def instrument_fastapi(app) -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("FastAPI instrumentation failed: %s", exc)
