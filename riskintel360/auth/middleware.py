"""
Authentication Middleware for RiskIntel360 Platform
Provides JWT token validation and security middleware for FastAPI.
"""

import logging
import time
from typing import Dict, List
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt
from datetime import datetime, timezone

from riskintel360.config.settings import get_settings
from riskintel360.auth.auth_decorators import get_current_user_from_token

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https: wss: ws:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        # HSTS for HTTPS
        settings = get_settings()
        if settings.security.ssl_enabled:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_requests: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Clean old requests
        if client_ip in self.client_requests:
            self.client_requests[client_ip] = [
                req_time
                for req_time in self.client_requests[client_ip]
                if current_time - req_time < 60  # Keep requests from last minute
            ]
        else:
            self.client_requests[client_ip] = []

        # Check rate limit
        if len(self.client_requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        # Add current request
        self.client_requests[client_ip].append(current_time)

        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        if request.client:
            return request.client.host

        return "unknown"


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle JWT authentication for protected endpoints"""

    def __init__(self, app):
        super().__init__(app)
        self.protected_paths = [
            "/api/v1/validations",
            "/auth/me",
            "/auth/validate",
            "/auth/permissions",
            "/api/v1/progress",
            "/api/v1/visualizations",
            "/api/v1/cost-management",
            "/api/v1/performance",
        ]
        self.public_paths = [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/auth/login",
            "/auth/refresh",
            "/auth/health",
            "/auth/test-token",
        ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        logger.debug(f"AuthenticationMiddleware: Processing path: {path}")

        # Skip authentication for public paths (exact match or starts with)
        is_public = any(
            path == public_path or path.startswith(public_path + "/")
            for public_path in self.public_paths
        )
        if is_public:
            logger.debug(
                f"AuthenticationMiddleware: Path {path} is public, skipping auth"
            )
            return await call_next(request)

        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            logger.debug("AuthenticationMiddleware: OPTIONS request, skipping auth")
            return await call_next(request)

        # Check if path requires authentication (exact match or starts with)
        requires_auth = any(
            path == protected_path or path.startswith(protected_path + "/")
            for protected_path in self.protected_paths
        )
        logger.debug(
            f"AuthenticationMiddleware: Path {path} requires auth: {requires_auth}"
        )

        if requires_auth:
            # Extract and validate token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "Authentication required",
                        "error": "missing_token",
                        "message": (
                            "Please provide a valid Bearer token in the "
                            "Authorization header"
                        ),
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )

            token = auth_header.split(" ", 1)[1]

            try:
                # Try JWT validation first for development
                try:
                    user_data = validate_jwt_token(token)
                    logger.info(
                        "JWT authentication successful for user: %s",
                        user_data.get("user_id"),
                    )
                except Exception as jwt_error:
                    logger.debug(f"JWT validation failed, trying Cognito: {jwt_error}")
                    # Fall back to Cognito validation
                    user_data = await get_current_user_from_token(token)

                # Add user data to request state for use in endpoints
                request.state.current_user = user_data
                logger.debug(
                    "User authenticated: %s for path %s",
                    user_data.get("user_id"),
                    path,
                )

            except Exception as e:
                logger.warning("Authentication failed for path %s: %s", path, e)
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "Invalid authentication credentials",
                        "error": "invalid_token",
                        "message": str(e),
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )

        response = await call_next(request)
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate and sanitize requests"""

    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_request_size = max_request_size

    async def dispatch(self, request: Request, call_next):
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": "Request entity too large",
                    "max_size": self.max_request_size,
                    "received_size": int(content_length),
                },
            )

        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")

            # For API endpoints, expect JSON
            if request.url.path.startswith("/api/") and not content_type.startswith(
                "application/json"
            ):
                return JSONResponse(
                    status_code=415,
                    content={
                        "detail": "Unsupported media type",
                        "expected": "application/json",
                        "received": content_type,
                    },
                )

        response = await call_next(request)
        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor API performance and response times"""

    def __init__(self, app):
        super().__init__(app)
        self.cache = {}  # Simple in-memory cache for performance
        self.cache_ttl = 60  # 60 seconds TTL

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Check cache for GET requests to public endpoints
        cache_key = None
        if request.method == "GET" and request.url.path in ["/health", "/", "/docs"]:
            cache_key = f"{request.method}:{request.url.path}"
            if cache_key in self.cache:
                cached_response, cached_time = self.cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    # Return cached response
                    cached_response.headers["X-Cache"] = "HIT"
                    cached_response.headers["X-Process-Time"] = "0.001"
                    return cached_response

        response = await call_next(request)

        process_time = time.time() - start_time

        # Add performance headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Cache"] = "MISS"

        # Cache successful GET responses for public endpoints
        if cache_key and response.status_code == 200:
            self.cache[cache_key] = (response, time.time())

        # Log slow requests (reduced threshold for better performance)
        if process_time > 0.5:  # Log requests taking more than 0.5 seconds
            logger.warning(
                "Slow request: %s %s took %.3fs",
                request.method,
                request.url.path,
                process_time,
            )

        # Only log performance metrics for slow requests to reduce overhead
        if process_time > 0.1 or response.status_code >= 400:
            logger.info(
                "Request: %s %s - Status: %s - Time: %.3fs",
                request.method,
                request.url.path,
                response.status_code,
                process_time,
            )

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle errors and prevent information disclosure"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response

        except HTTPException as e:
            # Re-raise HTTP exceptions to be handled by FastAPI
            raise e

        except ValueError as e:
            # Handle validation errors with proper 400 response
            logger.warning(
                f"Validation error in {request.method} {request.url.path}: {e}"
            )
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Bad request",
                    "error": "validation_error",
                    "message": str(e),
                },
            )

        except FileNotFoundError as e:
            # Handle file not found errors with proper 404 response
            logger.warning(
                f"Resource not found in {request.method} {request.url.path}: {e}"
            )
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "Resource not found",
                    "error": "not_found",
                    "message": "The requested resource was not found",
                },
            )

        except PermissionError as e:
            # Handle permission errors with proper 403 response
            logger.warning(
                f"Permission denied in {request.method} {request.url.path}: {e}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Forbidden",
                    "error": "permission_denied",
                    "message": "You don't have permission to access this resource",
                },
            )

        except Exception as e:
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}: {e}",
                exc_info=True,
            )

            # Return detailed error response for better debugging
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error": "server_error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "error_type": type(e).__name__,
                },
            )


def create_mock_jwt_token(
    user_id: str = "test-user", email: str = "test@example.com"
) -> str:
    """Create a mock JWT token for testing purposes"""
    settings = get_settings()

    payload = {
        "sub": user_id,
        "email": email,
        "tenant_id": "test-tenant",
        "roles": ["user"],
        "iat": datetime.now(timezone.utc).timestamp(),
        "exp": datetime.now(timezone.utc).timestamp() + 3600,  # 1 hour
    }

    return jwt.encode(
        payload,
        settings.security.jwt_secret_key,
        algorithm=settings.security.jwt_algorithm,
    )


def validate_jwt_token(token: str) -> Dict[str, str]:
    """Validate JWT token and return user data"""
    settings = get_settings()

    try:
        # Decode and validate token
        payload = jwt.decode(
            token,
            settings.security.jwt_secret_key,
            algorithms=[settings.security.jwt_algorithm],
        )

        # Check token expiration
        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            raise jwt.ExpiredSignatureError("Token has expired")

        # Validate required fields
        user_id = payload.get("sub")
        if not user_id:
            raise jwt.InvalidTokenError("Token missing user ID")

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "tenant_id": payload.get("tenant_id", "default"),
            "roles": payload.get("roles", ["user"]),
        }

    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise ValueError(f"Token validation failed: {str(e)}")


# Input sanitization functions
def sanitize_html_input(text: str) -> str:
    """Sanitize HTML input to prevent XSS attacks"""
    if not isinstance(text, str):
        return text

    # Remove script tags and javascript: protocol
    dangerous_patterns = [
        "<script",
        "</script>",
        "javascript:",
        "onload=",
        "onerror=",
        "onclick=",
        "onmouseover=",
        "<iframe",
        "</iframe>",
        "eval(",
        "alert(",
        "document.cookie",
        "document.write",
    ]

    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern, "")
        sanitized = sanitized.replace(pattern.upper(), "")

    return sanitized


def validate_sql_input(text: str) -> bool:
    """Validate input for potential SQL injection"""
    if not isinstance(text, str):
        return True

    # Check for common SQL injection patterns
    sql_patterns = [
        "'; DROP",
        "' OR '1'='1",
        "'; DELETE",
        "'; UPDATE",
        "'; INSERT",
        "UNION SELECT",
        "' OR 1=1",
        "--",
        "/*",
        "*/",
    ]

    text_upper = text.upper()
    for pattern in sql_patterns:
        if pattern.upper() in text_upper:
            return False

    return True


def validate_path_traversal(path: str) -> bool:
    """Validate path for traversal attempts"""
    if not isinstance(path, str):
        return True

    # Check for path traversal patterns
    traversal_patterns = ["../", "..\\", "..%2f", "..%5c", "%2e%2e%2f", "%2e%2e%5c"]

    path_lower = path.lower()
    for pattern in traversal_patterns:
        if pattern in path_lower:
            return False

    return True
