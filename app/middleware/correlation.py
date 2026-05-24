import uuid
import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
from app.logging_config import (
    correlation_id_var, trace_id_var, span_id_var, user_id_var, request_id_var
)

logger = logging.getLogger(__name__)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Adds correlation IDs to all requests and logs
    Enables request tracking across services
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or get correlation IDs from headers
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        span_id = request.headers.get("X-Span-ID", str(uuid.uuid4()))
        user_id = request.headers.get("X-User-ID", "anonymous")
        request_id = str(uuid.uuid4())[:8]
        
        # Store in context variables
        correlation_id_var.set(correlation_id)
        trace_id_var.set(trace_id)
        span_id_var.set(span_id)
        user_id_var.set(user_id)
        request_id_var.set(request_id)
        
        # Track request start
        start_time = time.time()
        
        # Log request start
        logger.info(
            "request_started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_string": str(request.query_params),
                "correlation_id": correlation_id,
                "trace_id": trace_id,
                "user_id": user_id
            }
        )
        
        try:
            # Call next middleware
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log request completion
            logger.info(
                "request_completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": int(duration * 1000),
                    "correlation_id": correlation_id,
                    "trace_id": trace_id,
                    "user_id": user_id
                }
            )
            
            # Add correlation IDs to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Span-ID"] = span_id
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "request_failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": int(duration * 1000),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "correlation_id": correlation_id,
                    "trace_id": trace_id,
                    "user_id": user_id
                },
                exc_info=True
            )
            raise


def get_correlation_context() -> dict:
    """Get current correlation context"""
    return {
        'correlation_id': correlation_id_var.get(),
        'trace_id': trace_id_var.get(),
        'span_id': span_id_var.get(),
        'user_id': user_id_var.get(),
        'request_id': request_id_var.get(),
    }