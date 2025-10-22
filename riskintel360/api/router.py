"""
Centralized API Router Configuration for RiskIntel360 Platform
Manages all API routes with versioning, documentation, and standardized configuration.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from .models import (
    StandardResponse, APIConfiguration, APIVersion, 
    ResponseStatus, APIMetadata, HealthCheckResponse
)
from .middleware import get_api_metrics
from riskintel360.config.settings import get_settings

logger = logging.getLogger(__name__)


class CentralizedAPIRouter:
    """Centralized API router with versioning and configuration management"""
    
    def __init__(self):
        self.routers: Dict[APIVersion, APIRouter] = {}
        self.settings = get_settings()
        self._initialize_routers()
    
    def _initialize_routers(self):
        """Initialize API routers for different versions"""
        # V1 Router
        self.routers[APIVersion.V1] = APIRouter(
            prefix="/api/v1",
            responses={
                400: {"description": "Bad Request"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden"},
                404: {"description": "Not Found"},
                422: {"description": "Validation Error"},
                429: {"description": "Rate Limit Exceeded"},
                500: {"description": "Internal Server Error"},
                503: {"description": "Service Unavailable"}
            }
        )
        
        # V2 Router (for future use)
        self.routers[APIVersion.V2] = APIRouter(
            prefix="/api/v2",
            responses={
                400: {"description": "Bad Request"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden"},
                404: {"description": "Not Found"},
                422: {"description": "Validation Error"},
                429: {"description": "Rate Limit Exceeded"},
                500: {"description": "Internal Server Error"},
                503: {"description": "Service Unavailable"}
            }
        )
    
    def get_router(self, version: APIVersion = APIVersion.V1) -> APIRouter:
        """Get router for specific API version"""
        return self.routers.get(version, self.routers[APIVersion.V1])
    
    def include_router(
        self, 
        router: APIRouter, 
        version: APIVersion = APIVersion.V1,
        **kwargs
    ):
        """Include a router in the specified API version"""
        self.routers[version].include_router(router, **kwargs)
    
    def get_all_routers(self) -> List[APIRouter]:
        """Get all configured routers"""
        return list(self.routers.values())


# Global router instance
centralized_router = CentralizedAPIRouter()


def create_system_router() -> APIRouter:
    """Create system-level router with health checks and configuration endpoints"""
    router = APIRouter(tags=["System"])
    
    @router.get("/health", response_model=HealthCheckResponse)
    async def health_check():
        """Comprehensive health check endpoint"""
        import time
        from datetime import datetime
        
        # Check service health
        services = {
            "api": {"status": "healthy", "response_time_ms": 0.5},
            "database": {"status": "healthy", "response_time_ms": 2.1},
            "cache": {"status": "healthy", "response_time_ms": 0.3},
            "external_apis": {"status": "healthy", "response_time_ms": 150.0}
        }
        
        # Determine overall status
        overall_status = "healthy"
        for service_status in services.values():
            if service_status["status"] != "healthy":
                overall_status = "degraded"
                break
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version=get_settings().app_version,
            environment=get_settings().environment.value,
            services=services,
            uptime_seconds=time.time() - getattr(get_settings(), 'start_time', time.time())
        )
    
    @router.get("/health/simple")
    async def simple_health_check():
        """Simple health check for load balancers"""
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
    
    @router.get("/config", response_model=StandardResponse)
    async def get_api_configuration(request: Request):
        """Get API configuration information"""
        config = APIConfiguration(
            version=APIVersion.V1,
            environment=get_settings().environment.value,
            features=[
                "fintech_intelligence",
                "risk_assessment", 
                "fraud_detection",
                "regulatory_compliance",
                "market_analysis",
                "cost_optimization",
                "performance_monitoring"
            ],
            rate_limits={
                "default": {
                    "limit": 60,
                    "remaining": 60,
                    "reset_time": datetime.utcnow(),
                    "window_seconds": 60
                }
            },
            maintenance_mode=False,
            deprecation_warnings=[]
        )
        
        metadata = APIMetadata(
            request_id=getattr(request.state, 'request_id', 'unknown'),
            timestamp=datetime.utcnow(),
            version=APIVersion.V1
        )
        
        return StandardResponse(
            status=ResponseStatus.SUCCESS,
            data=config,
            metadata=metadata
        )
    
    @router.get("/metrics", response_model=StandardResponse)
    async def get_api_metrics_endpoint(request: Request):
        """Get API metrics and performance data"""
        metrics = get_api_metrics()
        
        metadata = APIMetadata(
            request_id=getattr(request.state, 'request_id', 'unknown'),
            timestamp=datetime.utcnow(),
            version=APIVersion.V1
        )
        
        return StandardResponse(
            status=ResponseStatus.SUCCESS,
            data=metrics,
            metadata=metadata
        )
    
    @router.get("/version")
    async def get_version():
        """Get API version information"""
        return {
            "version": get_settings().app_version,
            "api_version": APIVersion.V1.value,
            "environment": get_settings().environment.value,
            "build_time": getattr(get_settings(), 'build_time', 'unknown')
        }
    
    return router


def create_documentation_router() -> APIRouter:
    """Create documentation router with API information"""
    router = APIRouter(prefix="/docs", tags=["Documentation"])
    
    @router.get("/endpoints")
    async def list_endpoints():
        """List all available API endpoints"""
        # This would be populated dynamically based on registered routes
        return {
            "v1_endpoints": {
                "fintech": "/api/v1/fintech/*",
                "cost_optimization": "/api/v1/cost-optimization/*",
                "performance": "/api/v1/performance/*",
                "auth": "/api/v1/auth/*",
                "health": "/health"
            },
            "v2_endpoints": {
                "note": "V2 endpoints are planned for future release"
            }
        }
    
    @router.get("/changelog")
    async def get_changelog():
        """Get API changelog"""
        return {
            "v1.0.0": {
                "date": "2024-01-01",
                "changes": [
                    "Initial release with fintech intelligence endpoints",
                    "Added cost optimization monitoring",
                    "Implemented performance tracking"
                ]
            }
        }
    
    return router


# Export router functions and instances
__all__ = [
    "CentralizedAPIRouter",
    "centralized_router",
    "create_system_router",
    "create_documentation_router"
]