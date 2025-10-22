"""
Centralized API Documentation for RiskIntel360 Platform
OpenAPI/Swagger specifications and documentation generation.
"""

from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from .models import (
    StandardResponse, APIError, APIMetadata, PaginatedResponse,
    HealthCheckResponse, ValidationErrorDetail, RateLimitInfo
)
from .config import get_api_config, FeatureFlag
from riskintel360.config.settings import get_settings


def customize_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """Customize OpenAPI schema with RiskIntel360 specific information"""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    settings = get_settings()
    api_config = get_api_config()
    
    openapi_schema = get_openapi(
        title="RiskIntel360 Platform API",
        version=settings.app_version,
        description="""
# RiskIntel360 Platform API

## Overview
Centralized Multi-Agent Financial Intelligence Platform for AWS AI Agent Competition.
Transform manual financial risk analysis into intelligent, automated insights.

## Key Features
- **Multi-Agent AI Architecture**: Five specialized fintech AI agents
- **Public-Data First Approach**: 90% functionality using free public sources
- **Advanced Fraud Detection**: Unsupervised ML with 90% false positive reduction
- **Regulatory Compliance Automation**: Real-time SEC, FINRA, CFPB monitoring
- **Market Intelligence**: AI-powered financial market analysis
- **Measurable Impact**: $20M+ annual value generation

## Authentication
Most endpoints require authentication via JWT tokens in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Rate Limiting
API requests are rate limited based on your service tier:
- **Free Tier**: 10 requests/minute, 1,000 requests/day
- **Basic Tier**: 60 requests/minute, 10,000 requests/day  
- **Professional Tier**: 300 requests/minute, 50,000 requests/day
- **Enterprise Tier**: 1,000 requests/minute, 200,000 requests/day

Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Requests allowed per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: When the rate limit window resets

## Response Format
All API responses follow a standardized format:

```json
{
  "status": "success|error|warning|partial",
  "data": { ... },
  "errors": [ ... ],
  "warnings": [ ... ],
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "uuid",
    "version": "v1",
    "processing_time_ms": 123.45,
    "rate_limit_remaining": 59,
    "rate_limit_reset": "2024-01-01T00:01:00Z"
  }
}
```

## Error Handling
Errors are returned with appropriate HTTP status codes and detailed error information:

```json
{
  "status": "error",
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Invalid input data",
      "details": { ... },
      "field": "entity_id",
      "trace_id": "uuid"
    }
  ],
  "metadata": { ... }
}
```

## Pagination
List endpoints support pagination with standard parameters:
- `page`: Page number (1-based, default: 1)
- `page_size`: Items per page (1-100, default: 20)
- `sort_by`: Field to sort by
- `sort_order`: Sort order (asc/desc, default: asc)

## Versioning
The API uses URL-based versioning:
- **V1**: `/api/v1/` - Current stable version
- **V2**: `/api/v2/` - Future version (planned)

## Support
For API support and documentation:
- **Documentation**: `/docs` (Swagger UI)
- **ReDoc**: `/redoc` (Alternative documentation)
- **OpenAPI Spec**: `/openapi.json`
- **Health Check**: `/health`
- **Configuration**: `/config`
- **Metrics**: `/metrics`
        """,
        routes=app.routes,
        contact={
            "name": "RiskIntel360 API Support",
            "email": "api-support@riskintel360.com",
            "url": "https://riskintel360.com/support"
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        servers=[
            {
                "url": "https://api.riskintel360.com",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.riskintel360.com", 
                "description": "Staging server"
            },
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            }
        ]
    )
    
    # Add custom components
    openapi_schema["components"]["schemas"].update({
        "StandardResponse": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["success", "error", "warning", "partial"],
                    "description": "Response status"
                },
                "data": {
                    "type": "object",
                    "description": "Response data"
                },
                "errors": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/APIError"},
                    "description": "List of errors"
                },
                "warnings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of warnings"
                },
                "metadata": {
                    "$ref": "#/components/schemas/APIMetadata",
                    "description": "Response metadata"
                }
            },
            "required": ["status", "metadata"]
        },
        "APIError": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": [
                        "VALIDATION_ERROR", "AUTHENTICATION_ERROR", "AUTHORIZATION_ERROR",
                        "NOT_FOUND", "INTERNAL_ERROR", "RATE_LIMIT_EXCEEDED",
                        "SERVICE_UNAVAILABLE", "INVALID_REQUEST", "RESOURCE_CONFLICT",
                        "EXTERNAL_SERVICE_ERROR"
                    ],
                    "description": "Error code"
                },
                "message": {
                    "type": "string",
                    "description": "Human-readable error message"
                },
                "details": {
                    "type": "object",
                    "description": "Additional error details"
                },
                "field": {
                    "type": "string",
                    "description": "Field that caused the error"
                },
                "trace_id": {
                    "type": "string",
                    "description": "Error trace identifier"
                }
            },
            "required": ["code", "message"]
        },
        "APIMetadata": {
            "type": "object",
            "properties": {
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Response timestamp"
                },
                "request_id": {
                    "type": "string",
                    "description": "Unique request identifier"
                },
                "version": {
                    "type": "string",
                    "enum": ["v1", "v2"],
                    "description": "API version"
                },
                "processing_time_ms": {
                    "type": "number",
                    "description": "Processing time in milliseconds"
                },
                "rate_limit_remaining": {
                    "type": "integer",
                    "description": "Remaining rate limit requests"
                },
                "rate_limit_reset": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Rate limit reset time"
                }
            },
            "required": ["timestamp", "request_id", "version"]
        },
        "PaginationMetadata": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Current page number"
                },
                "page_size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Items per page"
                },
                "total_items": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Total number of items"
                },
                "total_pages": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Total number of pages"
                },
                "has_next": {
                    "type": "boolean",
                    "description": "Whether there is a next page"
                },
                "has_previous": {
                    "type": "boolean",
                    "description": "Whether there is a previous page"
                }
            },
            "required": ["page", "page_size", "total_items", "total_pages", "has_next", "has_previous"]
        }
    })
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token authentication"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key authentication"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"ApiKeyAuth": []}
    ]
    
    # Add tags for better organization
    openapi_schema["tags"] = [
        {
            "name": "System",
            "description": "System health, configuration, and monitoring endpoints"
        },
        {
            "name": "Authentication", 
            "description": "User authentication and authorization"
        },
        {
            "name": "Fintech Intelligence",
            "description": "Core fintech analysis and intelligence endpoints"
        },
        {
            "name": "Risk Assessment",
            "description": "Financial risk analysis and assessment"
        },
        {
            "name": "Fraud Detection",
            "description": "Advanced fraud detection and prevention"
        },
        {
            "name": "Regulatory Compliance",
            "description": "Regulatory compliance monitoring and analysis"
        },
        {
            "name": "Market Analysis",
            "description": "Financial market intelligence and analysis"
        },
        {
            "name": "KYC Verification",
            "description": "Know Your Customer verification and screening"
        },
        {
            "name": "Cost Optimization",
            "description": "AWS cost monitoring and optimization"
        },
        {
            "name": "Performance Monitoring",
            "description": "System performance and metrics monitoring"
        },
        {
            "name": "Business Value",
            "description": "Business value calculation and ROI tracking"
        },
        {
            "name": "Competition Demo",
            "description": "AWS AI Agent Competition demonstration endpoints"
        }
    ]
    
    # Add custom extensions
    openapi_schema["x-api-features"] = {
        "enabled_features": [flag.value for flag, enabled in api_config.get_all_features().items() if enabled],
        "rate_limiting": True,
        "authentication": True,
        "monitoring": True,
        "caching": True,
        "versioning": True
    }
    
    openapi_schema["x-service-tiers"] = {
        "free": {
            "rate_limit": "10 req/min, 1K req/day",
            "features": ["basic_analysis", "health_checks"],
            "support": "community"
        },
        "basic": {
            "rate_limit": "60 req/min, 10K req/day", 
            "features": ["fintech_intelligence", "compliance_monitoring"],
            "support": "email"
        },
        "professional": {
            "rate_limit": "300 req/min, 50K req/day",
            "features": ["fraud_detection", "advanced_analytics", "kyc_verification"],
            "support": "priority_email"
        },
        "enterprise": {
            "rate_limit": "1K req/min, 200K req/day",
            "features": ["all_features", "custom_integrations", "dedicated_support"],
            "support": "dedicated_account_manager"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def get_api_documentation_info() -> Dict[str, Any]:
    """Get API documentation information"""
    settings = get_settings()
    api_config = get_api_config()
    
    return {
        "title": "RiskIntel360 Platform API",
        "version": settings.app_version,
        "description": "Centralized Multi-Agent Financial Intelligence Platform",
        "documentation_urls": {
            "swagger_ui": "/docs",
            "redoc": "/redoc", 
            "openapi_json": "/openapi.json",
            "postman_collection": "/docs/postman",
            "api_changelog": "/docs/changelog"
        },
        "authentication": {
            "methods": ["JWT Bearer Token", "API Key"],
            "jwt_header": "Authorization: Bearer <token>",
            "api_key_header": "X-API-Key: <key>"
        },
        "rate_limits": {
            "free": "10 req/min",
            "basic": "60 req/min",
            "professional": "300 req/min", 
            "enterprise": "1000 req/min"
        },
        "features": {
            "enabled": [flag.value for flag, enabled in api_config.get_all_features().items() if enabled],
            "total_endpoints": len(api_config.get_all_endpoint_configs()),
            "api_versions": ["v1", "v2"]
        },
        "support": {
            "documentation": "/docs",
            "health_check": "/health",
            "status_page": "/health",
            "metrics": "/metrics"
        }
    }


def generate_postman_collection() -> Dict[str, Any]:
    """Generate Postman collection for API testing"""
    settings = get_settings()
    
    return {
        "info": {
            "name": "RiskIntel360 Platform API",
            "description": "Postman collection for RiskIntel360 Platform API testing",
            "version": settings.app_version,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{jwt_token}}",
                    "type": "string"
                }
            ]
        },
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:8000",
                "type": "string"
            },
            {
                "key": "jwt_token",
                "value": "",
                "type": "string"
            }
        ],
        "item": [
            {
                "name": "System",
                "item": [
                    {
                        "name": "Health Check",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/health",
                                "host": ["{{base_url}}"],
                                "path": ["health"]
                            }
                        }
                    },
                    {
                        "name": "API Configuration",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/config",
                                "host": ["{{base_url}}"],
                                "path": ["config"]
                            }
                        }
                    },
                    {
                        "name": "API Metrics",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/metrics",
                                "host": ["{{base_url}}"],
                                "path": ["metrics"]
                            }
                        }
                    }
                ]
            },
            {
                "name": "Fintech Intelligence",
                "item": [
                    {
                        "name": "Risk Analysis",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": "{\n  \"entity_id\": \"fintech_startup_123\",\n  \"entity_type\": \"fintech_startup\",\n  \"analysis_scope\": [\"credit\", \"market\", \"operational\", \"regulatory\", \"fraud\"]\n}"
                            },
                            "url": {
                                "raw": "{{base_url}}/api/v1/fintech/risk-analysis",
                                "host": ["{{base_url}}"],
                                "path": ["api", "v1", "fintech", "risk-analysis"]
                            }
                        }
                    },
                    {
                        "name": "Fraud Detection",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": "{\n  \"transaction_data\": [],\n  \"analysis_type\": \"real_time\",\n  \"confidence_threshold\": 0.8\n}"
                            },
                            "url": {
                                "raw": "{{base_url}}/api/v1/fintech/fraud-detection",
                                "host": ["{{base_url}}"],
                                "path": ["api", "v1", "fintech", "fraud-detection"]
                            }
                        }
                    }
                ]
            }
        ]
    }


# Export documentation functions
__all__ = [
    "customize_openapi_schema",
    "get_api_documentation_info",
    "generate_postman_collection"
]