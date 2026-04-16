"""
Observability module — Sentry error tracking + OpenTelemetry tracing.

Gracefully degrades when optional packages (sentry-sdk, opentelemetry-*)
are not installed: logs a warning and continues without instrumentation.
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sentry
# ---------------------------------------------------------------------------

def init_sentry(dsn: str, environment: str, release: str) -> None:
    """Initialise the Sentry SDK.  Silently skips when *dsn* is empty/None."""
    if not dsn:
        logger.warning("SENTRY_DSN is empty — Sentry error tracking disabled.")
        return

    try:
        import sentry_sdk  # noqa: WPS433
    except ImportError:
        logger.warning(
            "sentry-sdk is not installed — Sentry error tracking disabled."
        )
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        traces_sample_rate=1.0 if environment == "development" else 0.2,
        send_default_pii=False,
    )
    logger.info(
        "Sentry initialised (env=%s, release=%s).", environment, release
    )


# ---------------------------------------------------------------------------
# OpenTelemetry
# ---------------------------------------------------------------------------

def init_otel(service_name: str, otlp_endpoint: str | None, app: "FastAPI") -> None:
    """Set up OpenTelemetry tracing with OTLP or console exporter."""
    try:
        from opentelemetry import trace  # noqa: WPS433
        from opentelemetry.sdk.trace import TracerProvider  # noqa: WPS433
        from opentelemetry.sdk.trace.export import (  # noqa: WPS433
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource  # noqa: WPS433
    except ImportError:
        logger.warning(
            "opentelemetry packages are not installed — OTEL tracing disabled."
        )
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # noqa: WPS433, E501
                OTLPSpanExporter,
            )
        except ImportError:
            logger.warning(
                "opentelemetry-exporter-otlp-proto-grpc is not installed — "
                "falling back to ConsoleSpanExporter."
            )
            provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )
        else:
            provider.add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
                )
            )
            logger.info(
                "OTEL OTLP exporter configured (endpoint=%s).", otlp_endpoint
            )
    else:
        provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )
        logger.info("OTEL ConsoleSpanExporter configured (dev mode).")

    trace.set_tracer_provider(provider)

    # Instrument FastAPI if the instrumentation package is available.
    try:
        from opentelemetry.instrumentation.fastapi import (  # noqa: WPS433
            FastAPIInstrumentor,
        )

        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI OTEL instrumentation enabled.")
    except ImportError:
        logger.warning(
            "opentelemetry-instrumentation-fastapi is not installed — "
            "automatic FastAPI instrumentation skipped."
        )


# ---------------------------------------------------------------------------
# Trace-ID response middleware
# ---------------------------------------------------------------------------

def _add_trace_id_middleware(app: "FastAPI") -> None:
    """Middleware that copies the current OTEL trace ID into a response header."""
    try:
        from opentelemetry import trace as otel_trace  # noqa: WPS433
    except ImportError:
        # Nothing to do without opentelemetry installed.
        return

    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response

    class TraceIdMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):  # noqa: ANN001
            response: Response = await call_next(request)
            span = otel_trace.get_current_span()
            ctx = span.get_span_context()
            if ctx and ctx.trace_id:
                response.headers["X-Trace-Id"] = format(ctx.trace_id, "032x")
            return response

    app.add_middleware(TraceIdMiddleware)


# ---------------------------------------------------------------------------
# Convenience entry-point
# ---------------------------------------------------------------------------

def setup_observability(app: "FastAPI") -> None:
    """Read config from environment / Settings and wire up Sentry + OTEL."""
    from app.config import get_settings

    settings = get_settings()

    sentry_dsn = settings.sentry_dsn or os.getenv("SENTRY_DSN", "")
    sentry_env = settings.sentry_environment or os.getenv(
        "SENTRY_ENVIRONMENT", "development"
    )
    app_version = os.getenv("APP_VERSION", "0.0.0")

    otlp_endpoint = (
        settings.otel_exporter_otlp_endpoint
        or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        or None
    )
    service_name = settings.otel_service_name or os.getenv(
        "OTEL_SERVICE_NAME", "bpo-nexus-api"
    )

    # --- Sentry ---
    init_sentry(dsn=sentry_dsn, environment=sentry_env, release=app_version)

    # --- OpenTelemetry ---
    init_otel(
        service_name=service_name,
        otlp_endpoint=otlp_endpoint if otlp_endpoint else None,
        app=app,
    )

    # --- Trace-ID header middleware ---
    _add_trace_id_middleware(app)
