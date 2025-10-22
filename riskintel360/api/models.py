"""
Centralized API Models for RiskIntel360 Platform
Standardized request/response models and schemas for all API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class APIVersion(str, Enum):
    """API version enumeration"""
    V1 = "v1"
    V2 = "v2"


class ResponseStatus(str, Enum):
    """Standard response status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL = "partial"


class ErrorCode(str, Enum):
    """Standard error codes"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INVALID_REQUEST = "INVALID_REQUEST"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"


class APIMetadata(BaseModel):
    """Standard API response metadata"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: str = Field(..., description="Unique request identifier")
    version: APIVersion = Field(default=APIVersion.V1, description="API version")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    rate_limit_remaining: Optional[int] = Field(None, description="Remaining rate limit requests")
    rate_limit_reset: Optional[datetime] = Field(None, description="Rate limit reset time")


class APIError(BaseModel):
    """Standard API error model"""
    code: ErrorCode = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    field: Optional[str] = Field(None, description="Field that caused the error (for validation errors)")
    trace_id: Optional[str] = Field(None, description="Error trace identifier")


class StandardResponse(BaseModel):
    """Standard API response wrapper"""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    status: ResponseStatus = Field(..., description="Response status")
    data: Optional[Any] = Field(None, description="Response data")
    errors: Optional[List[APIError]] = Field(None, description="List of errors")
    warnings: Optional[List[str]] = Field(None, description="List of warnings")
    metadata: APIMetadata = Field(..., description="Response metadata")


class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")


class PaginationMetadata(BaseModel):
    """Standard pagination metadata"""
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(StandardResponse):
    """Standard paginated response"""
    pagination: Optional[PaginationMetadata] = Field(None, description="Pagination metadata")


class HealthCheckResponse(BaseModel):
    """Standard health check response"""
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    services: Dict[str, Dict[str, Any]] = Field(..., description="Service health status")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information"""
    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Validation error message")
    invalid_value: Any = Field(..., description="The invalid value that was provided")
    constraint: Optional[str] = Field(None, description="Validation constraint that was violated")


class RateLimitInfo(BaseModel):
    """Rate limiting information"""
    limit: int = Field(..., description="Rate limit per window")
    remaining: int = Field(..., description="Remaining requests in current window")
    reset_time: datetime = Field(..., description="When the rate limit window resets")
    window_seconds: int = Field(..., description="Rate limit window duration in seconds")


class APIConfiguration(BaseModel):
    """API configuration information"""
    version: APIVersion = Field(..., description="API version")
    environment: str = Field(..., description="Environment name")
    features: List[str] = Field(..., description="Enabled features")
    rate_limits: Dict[str, RateLimitInfo] = Field(..., description="Rate limit information")
    maintenance_mode: bool = Field(default=False, description="Whether maintenance mode is active")
    deprecation_warnings: List[str] = Field(default_factory=list, description="API deprecation warnings")


# Request/Response models for common operations
class BulkOperationRequest(BaseModel):
    """Standard bulk operation request"""
    items: List[Dict[str, Any]] = Field(..., description="Items to process")
    options: Optional[Dict[str, Any]] = Field(None, description="Operation options")
    batch_size: Optional[int] = Field(default=100, ge=1, le=1000, description="Batch processing size")


class BulkOperationResponse(BaseModel):
    """Standard bulk operation response"""
    total_items: int = Field(..., description="Total number of items processed")
    successful_items: int = Field(..., description="Number of successfully processed items")
    failed_items: int = Field(..., description="Number of failed items")
    results: List[Dict[str, Any]] = Field(..., description="Individual item results")
    errors: List[APIError] = Field(default_factory=list, description="Processing errors")


class AsyncOperationResponse(BaseModel):
    """Standard asynchronous operation response"""
    operation_id: str = Field(..., description="Unique operation identifier")
    status: str = Field(..., description="Operation status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Operation creation time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    progress_percentage: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage")
    result_url: Optional[str] = Field(None, description="URL to retrieve results when complete")


class FileUploadResponse(BaseModel):
    """Standard file upload response"""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    size_bytes: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="File content type")
    upload_url: Optional[str] = Field(None, description="URL for direct file upload")
    expires_at: Optional[datetime] = Field(None, description="Upload URL expiration time")


# Export commonly used types
__all__ = [
    "APIVersion",
    "ResponseStatus", 
    "ErrorCode",
    "APIMetadata",
    "APIError",
    "StandardResponse",
    "PaginationParams",
    "PaginationMetadata", 
    "PaginatedResponse",
    "HealthCheckResponse",
    "ValidationErrorDetail",
    "RateLimitInfo",
    "APIConfiguration",
    "BulkOperationRequest",
    "BulkOperationResponse",
    "AsyncOperationResponse",
    "FileUploadResponse"
]