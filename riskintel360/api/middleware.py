"""
Centralized API Middleware for RiskIntel360 Platform
Provides authentication, logging, error handling, rate limiting, and monitoring middleware.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .models import (
    StandardResponse, APIError, APIMetadata, ErrorCode, 
    ResponseStatus, APIVersion, RateLimitInfo
)
from riskintel360.config.settings import get_settings
from riskintel360.auth.auth_decorators import get_current_user_from_token

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context and generate request IDs"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.time()
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class APILoggingMiddleware(BaseHTTPMiddleware):
    """Centralized API request/response logging middleware"""
    
    def __init__(self, app: ASGIApp, log_request_body: bool = False, log_response_body: bool = False):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Log response
        await self._log_response(request, response, request_id, processing_time)
        
        return response
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details"""
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log request body if enabled (be careful with sensitive data)
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    log_data["body_size"] = len(body)
                    # Only log first 1000 characters to avoid huge logs
                    log_data["body_preview"] = body.decode()[:1000]
            except Exception as e:
                log_data["body_error"] = str(e)
        
        logger.info(f"API Request: {json.dumps(log_data)}")
    
    async def _log_response(self, request: Request, response: Response, request_id: str, processing_time: float):
        """Log response details"""
        log_data = {
            "request_id": request_id,
            "status_code": response.status_code,
            "processing_time_ms": processing_time,
            "response_headers": dict(response.headers),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Determine log level based on status code
        if response.status_code >= 500:
            logger.error(f"API Response: {json.dumps(log_data)}")
        elif response.status_code >= 400:
            logger.warning(f"API Response: {json.dumps(log_data)}")
        else:
            logger.info(f"API Response: {json.dumps(log_data)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


class CentralizedErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Centralized error handling with standardized response format"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            return await self._handle_http_exception(request, e)
        except Exception as e:
            return await self._handle_generic_exception(request, e)
    
    async def _handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions with standardized format"""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Map HTTP status codes to error codes
        error_code_map = {
            400: ErrorCode.VALIDATION_ERROR,
            401: ErrorCode.AUTHENTICATION_ERROR,
            403: ErrorCode.AUTHORIZATION_ERROR,
            404: ErrorCode.NOT_FOUND,
            409: ErrorCode.RESOURCE_CONFLICT,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
            503: ErrorCode.SERVICE_UNAVAILABLE,
        }
        
        error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        
        error = APIError(
            code=error_code,
            message=str(exc.detail),
            trace_id=request_id
        )
        
        metadata = APIMetadata(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            version=APIVersion.V1
        )
        
        response = StandardResponse(
            status=ResponseStatus.ERROR,
            errors=[error],
            metadata=metadata
        )
        
        logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail} (Request ID: {request_id})")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response.model_dump(mode='json')
        )
    
    async def _handle_generic_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle generic exceptions with standardized format"""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        error = APIError(
            code=ErrorCode.INTERNAL_ERROR,
            message="An internal server error occurred",
            details={"exception_type": type(exc).__name__},
            trace_id=request_id
        )
        
        metadata = APIMetadata(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            version=APIVersion.V1
        )
        
        response = StandardResponse(
            status=ResponseStatus.ERROR,
            errors=[error],
            metadata=metadata
        )
        
        logger.error(f"Unhandled Exception: {type(exc).__name__}: {str(exc)} (Request ID: {request_id})", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content=response.model_dump(mode='json')
        )


class CentralizedRateLimitingMiddleware(BaseHTTPMiddleware):
    """Centralized rate limiting with configurable limits per endpoint"""
    
    def __init__(
        self, 
        app: ASGIApp, 
        default_requests_per_minute: int = 60,
        endpoint_limits: Optional[Dict[str, int]] = None
    ):
        super().__init__(app)
        self.default_requests_per_minute = default_requests_per_minute
        self.endpoint_limits = endpoint_limits or {}
        self.client_requests: Dict[str, List[float]] = {}
    
    async def dispatch(self, request: Request, call_next):
        client_key = self._get_client_key(request)
        endpoint_key = self._get_endpoint_key(request)
        current_time = time.time()
        
        # Get rate limit for this endpoint
        rate_limit = self.endpoint_limits.get(endpoint_key, self.default_requests_per_minute)
        
        # Clean old requests
        if client_key in self.client_requests:
            self.client_requests[client_key] = [
                req_time for req_time in self.client_requests[client_key]
                if current_time - req_time < 60  # Keep requests from last minute
            ]
        else:
            self.client_requests[client_key] = []
        
        # Check rate limit
        if len(self.client_requests[client_key]) >= rate_limit:
            return await self._create_rate_limit_response(request, rate_limit)
        
        # Add current request
        self.client_requests[client_key].append(current_time)
        
        # Process request and add rate limit headers
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, rate_limit - len(self.client_requests[client_key]))
        reset_time = datetime.fromtimestamp(current_time + 60, tz=timezone.utc)
        
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = reset_time.isoformat()
        
        return response
    
    def _get_client_key(self, request: Request) -> str:
        """Generate client key for rate limiting"""
        # Use IP address for rate limiting (simpler and avoids async issues)
        # Authentication is handled separately by auth middleware
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"
    
    def _get_endpoint_key(self, request: Request) -> str:
        """Generate endpoint key for rate limiting"""
        path = request.url.path
        method = request.method
        return f"{method}:{path}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _create_rate_limit_response(self, request: Request, rate_limit: int) -> JSONResponse:
        """Create standardized rate limit exceeded response"""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        error = APIError(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"Rate limit exceeded. Maximum {rate_limit} requests per minute allowed.",
            details={"rate_limit": rate_limit, "window_seconds": 60},
            trace_id=request_id
        )
        
        metadata = APIMetadata(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            version=APIVersion.V1,
            rate_limit_remaining=0,
            rate_limit_reset=datetime.fromtimestamp(time.time() + 60, tz=timezone.utc)
        )
        
        response = StandardResponse(
            status=ResponseStatus.ERROR,
            errors=[error],
            metadata=metadata
        )
        
        return JSONResponse(
            status_code=429,
            content=response.model_dump(mode='json'),
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(rate_limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": metadata.rate_limit_reset.isoformat()
            }
        )


class APIMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect API metrics and performance data"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.metrics = {
            "requests_total": 0,
            "requests_by_method": {},
            "requests_by_status": {},
            "response_times": [],
            "errors_total": 0
        }
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        processing_time = (time.time() - start_time) * 1000
        
        # Update metrics
        self.metrics["requests_total"] += 1
        
        method = request.method
        self.metrics["requests_by_method"][method] = self.metrics["requests_by_method"].get(method, 0) + 1
        
        status_code = response.status_code
        self.metrics["requests_by_status"][status_code] = self.metrics["requests_by_status"].get(status_code, 0) + 1
        
        self.metrics["response_times"].append(processing_time)
        
        if status_code >= 400:
            self.metrics["errors_total"] += 1
        
        # Keep only last 1000 response times to prevent memory issues
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]
        
        # Add performance headers
        response.headers["X-Response-Time"] = f"{processing_time:.2f}ms"
        
        return response
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        response_times = self.metrics["response_times"]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "requests_total": self.metrics["requests_total"],
            "requests_by_method": self.metrics["requests_by_method"],
            "requests_by_status": self.metrics["requests_by_status"],
            "errors_total": self.metrics["errors_total"],
            "error_rate": self.metrics["errors_total"] / max(1, self.metrics["requests_total"]),
            "average_response_time_ms": avg_response_time,
            "metrics_collected_at": datetime.utcnow().isoformat()
        }


# Global metrics instance
api_metrics = APIMetricsMiddleware(None)


def get_api_metrics() -> Dict[str, Any]:
    """Get current API metrics"""
    return api_metrics.get_metrics()


# Export middleware classes
__all__ = [
    "RequestContextMiddleware",
    "APILoggingMiddleware", 
    "CentralizedErrorHandlingMiddleware",
    "CentralizedRateLimitingMiddleware",
    "APIMetricsMiddleware",
    "get_api_metrics"
]