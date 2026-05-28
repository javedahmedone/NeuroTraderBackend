# from opentelemetry import trace, metrics
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor
# from opentelemetry.exporter.jaeger.thrift import JaegerExporter
# from opentelemetry.sdk.metrics import MeterProvider
# from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
# from opentelemetry.instrumentation.requests import RequestsInstrumentor
# from opentelemetry.instrumentation.redis import RedisInstrumentor
# from opentelemetry.sdk.resources import Resource, SERVICE_NAME
# import os
# import logging

# logger = logging.getLogger(__name__)


# def init_tracing():
#     """Initialize OpenTelemetry tracing with Jaeger"""
#     try:
#         # Create resource with service name
#         resource = Resource.create({
#             SERVICE_NAME: "neurotrader-backend",
#             "environment": os.getenv("ENV", "development"),
#             "version": "1.0.0"
#         })
        
#         # Jaeger exporter
#         jaeger_host = os.getenv("JAEGER_HOST", "localhost")
#         jaeger_port = int(os.getenv("JAEGER_PORT", 6831))
        
#         jaeger_exporter = JaegerExporter(
#             agent_host_name=jaeger_host,
#             agent_port=jaeger_port,
#         )
        
#         # Trace provider
#         trace_provider = TracerProvider(resource=resource)
#         trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
#         trace.set_tracer_provider(trace_provider)
        
#         logger.info(f"✓ Jaeger tracing initialized: {jaeger_host}:{jaeger_port}")
        
#         return trace.get_tracer(__name__)
        
#     except Exception as e:
#         logger.warning(f"⚠ Failed to initialize Jaeger tracing: {e}")
#         return trace.get_tracer(__name__)


# def init_metrics():
#     """Initialize OpenTelemetry metrics"""
#     try:
#         # Meter provider (no external exporter, we use Prometheus client directly)
#         resource = Resource.create({SERVICE_NAME: "neurotrader-backend"})
#         meter_provider = MeterProvider(resource=resource)
#         metrics.set_meter_provider(meter_provider)
        
#         logger.info("✓ Metrics initialized (using Prometheus client)")
#         return metrics.get_meter(__name__)
        
#     except Exception as e:
#         logger.warning(f"⚠ Failed to initialize metrics: {e}")
#         return metrics.get_meter(__name__)


# def init_instrumentation(app=None):
#     """Initialize auto-instrumentation for FastAPI"""
#     try:
#         # Instrument FastAPI (only if app is provided)
#         if app:
#             FastAPIInstrumentor.instrument_app(app)
        
#         # Instrument requests library
#         RequestsInstrumentor().instrument()
        
#         # Instrument Redis
#         RedisInstrumentor().instrument()
        
#         logger.info("✓ OpenTelemetry auto-instrumentation initialized")
        
#     except Exception as e:
#         logger.warning(f"⚠ Failed to initialize auto-instrumentation: {e}")


# def init_observability(app):
#     """Initialize all observability components"""
#     init_tracing()
#     init_metrics()
#     init_instrumentation(app)