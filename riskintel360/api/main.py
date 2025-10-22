"""
Centralized Main FastAPI Application for RiskIntel360 Platform
Entry point for the REST API with centralized routing, middleware, and configuration.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from riskintel360.config.settings import get_settings
from riskintel360.config.environment import get_environment_manager
from riskintel360.services.agent_runtime import get_session_manager, shutdown_session_manager
from riskintel360.models import data_manager
from riskintel360.utils.logging import setup_logging

# Centralized API components
from .middleware import (
    RequestContextMiddleware,
    APILoggingMiddleware,
    CentralizedErrorHandlingMiddleware,
    CentralizedRateLimitingMiddleware,
    APIMetricsMiddleware
)
from .router import centralized_router, create_system_router, create_documentation_router
from .config import get_api_config
from .models import APIVersion
from .documentation import customize_openapi_schema

# Import existing routers
from riskintel360.api.health import router as health_router
from riskintel360.api.auth import router as auth_router
from riskintel360.api.users import router as users_router
from riskintel360.api.validations import router as validations_router
from riskintel360.api.progress import router as progress_router
from riskintel360.api.websockets import router as websockets_router
from riskintel360.api.visualizations import router as visualizations_router
from riskintel360.api.competition_demo import router as competition_demo_router
from riskintel360.api.cost_management import router as cost_management_router
from riskintel360.api.cost_optimization_endpoints import router as cost_optimization_router
from riskintel360.api.performance import router as performance_router
from riskintel360.api.credentials import router as credentials_router
from riskintel360.api.fintech_endpoints import router as fintech_router

# Initialize logging with timestamped log files
setup_logging(log_level="INFO", log_dir="logs", app_name="riskintel360")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown"""
    
    # Startup
    logger.info("Starting RiskIntel360 Platform API")
    
    try:
        # Initialize environment manager
        env_manager = get_environment_manager()
        env_manager.log_configuration()
        
        # Validate configuration
        if not env_manager.validate_configuration():
            logger.error("Configuration validation failed")
            raise RuntimeError("Invalid configuration")
        
        # Initialize data manager (database)
        await data_manager.initialize()
        logger.info("Data manager initialized successfully")
        
        # Initialize session manager
        session_manager = await get_session_manager()
        logger.info("Session manager initialized successfully")
        
        logger.info("RiskIntel360 Platform API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down RiskIntel360 Platform API")
    
    try:
        # Shutdown session manager
        await shutdown_session_manager()
        logger.info("Session manager shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    
    logger.info("RiskIntel360 Platform API shutdown completed")


def create_app() -> FastAPI:
    """Create and configure the centralized FastAPI application"""
    
    settings = get_settings()
    api_config = get_api_config()
    
    # Validate configuration
    if not api_config.validate_configuration():
        logger.error("API configuration validation failed")
        raise RuntimeError("Invalid API configuration")
    
    app = FastAPI(
        title="RiskIntel360 Platform API",
        description="Centralized Multi-Agent Financial Intelligence Platform for AWS AI Agent Competition",
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Centralized middleware (order matters - add from innermost to outermost)
    app.add_middleware(CentralizedErrorHandlingMiddleware)
    app.add_middleware(APIMetricsMiddleware)
    app.add_middleware(APILoggingMiddleware, log_request_body=False, log_response_body=False)
    app.add_middleware(
        CentralizedRateLimitingMiddleware, 
        default_requests_per_minute=1000,  # Increased for development
        endpoint_limits={
            "GET:/api/v1/validations/": 1000,  # Allow frequent polling for dashboard
            "GET:/api/v1/users/preferences": 1000,  # Allow frequent user preference calls
            "PUT:/api/v1/users/preferences": 1000,  # Allow frequent user preference updates
            "GET:/api/v1/demo/status": 1000,  # Allow frequent demo status checks
            "GET:/api/v1/demo/scenarios": 1000,  # Allow frequent demo scenario requests
            "POST:/api/v1/demo/scenarios/": 1000,  # Allow frequent demo executions
            "POST:/api/v1/fintech/fraud-detection": 1000,  # Increased for testing
            "POST:/api/v1/fintech/risk-analysis": 1000,  # Increased for testing
            "GET:/api/v1/fintech/market-intelligence": 1000,
            "GET:/health": 2000,  # Health checks should be unlimited
            "GET:/": 2000  # Root endpoint should be unlimited
        }
    )
    app.add_middleware(RequestContextMiddleware)
    
    # CORS middleware (should be last/outermost)
    # Allow all origins in development for demo purposes
    cors_origins = ["*"] if settings.environment.value == "development" else settings.api.cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Include system routers
    app.include_router(create_system_router())
    app.include_router(create_documentation_router())
    
    # Include V1 API routers through centralized router
    v1_router = centralized_router.get_router(APIVersion.V1)
    
    # Register all existing routers with V1
    centralized_router.include_router(auth_router, version=APIVersion.V1, tags=["Authentication"])
    centralized_router.include_router(users_router, version=APIVersion.V1, tags=["Users"])
    centralized_router.include_router(validations_router, version=APIVersion.V1, tags=["Validations"])
    centralized_router.include_router(progress_router, version=APIVersion.V1, tags=["Progress"])
    centralized_router.include_router(websockets_router, version=APIVersion.V1, tags=["WebSockets"])
    centralized_router.include_router(visualizations_router, version=APIVersion.V1, tags=["Visualizations"])
    centralized_router.include_router(competition_demo_router, version=APIVersion.V1, tags=["Competition Demo"])
    centralized_router.include_router(cost_management_router, version=APIVersion.V1, tags=["Cost Management"])
    centralized_router.include_router(cost_optimization_router, version=APIVersion.V1, tags=["Cost Optimization"])
    centralized_router.include_router(performance_router, version=APIVersion.V1, tags=["Performance Monitoring"])
    centralized_router.include_router(credentials_router, version=APIVersion.V1, tags=["Credentials Management"])
    centralized_router.include_router(fintech_router, version=APIVersion.V1, tags=["Fintech Intelligence"])
    
    # Include all versioned routers
    for router in centralized_router.get_all_routers():
        app.include_router(router)
    
    # Legacy health router (for backward compatibility)
    app.include_router(health_router, tags=["Health - Legacy"])
    
    # Root endpoint with centralized information
    @app.get("/")
    async def root(request: Request):
        """Root endpoint with centralized API information"""
        from .models import StandardResponse, APIMetadata, ResponseStatus
        
        metadata = APIMetadata(
            request_id=getattr(request.state, 'request_id', 'unknown'),
            timestamp=datetime.utcnow(),
            version=APIVersion.V1
        )
        
        api_info = {
            "name": "RiskIntel360 Platform API",
            "description": "Centralized Multi-Agent Financial Intelligence Platform",
            "version": settings.app_version,
            "environment": settings.environment.value,
            "api_version": APIVersion.V1.value,
            "status": "running",
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json",
                "health": "/health",
                "config": "/config",
                "metrics": "/metrics",
                "v1_api": "/api/v1",
                "v2_api": "/api/v2"
            },
            "features": list(api_config.get_all_features().keys())
        }
        
        return StandardResponse(
            status=ResponseStatus.SUCCESS,
            data=api_info,
            metadata=metadata
        ).model_dump()
    
    # Customize OpenAPI schema
    app.openapi = lambda: customize_openapi_schema(app)
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "riskintel360.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload,
        log_level=settings.logging.level.lower(),
    )
