"""
Observability setup for RetailXAI Dashboard
"""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from app.core.config import settings

logger = logging.getLogger(__name__)


def setup_observability() -> None:
    """Set up observability tools."""
    
    # Setup Sentry
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[
                FastApiIntegration(auto_enabling_instrumentations=False),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            traces_sample_rate=0.1,
            environment="production",
        )
        logger.info("Sentry initialized")
    
    # Setup OpenTelemetry
    if settings.otel_exporter_otlp_endpoint:
        resource = Resource.create({
            "service.name": "retailxai-dashboard",
            "service.version": "1.0.0",
        })
        
        trace.set_tracer_provider(TracerProvider(resource=resource))
        
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
        )
        
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        logger.info("OpenTelemetry initialized")
    
    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    
    # Instrument Redis
    RedisInstrumentor().instrument()
    
    logger.info("Observability setup complete")


def instrument_fastapi(app) -> None:
    """Instrument FastAPI app for tracing."""
    FastAPIInstrumentor.instrument_app(app)
    logger.info("FastAPI instrumented for tracing")
