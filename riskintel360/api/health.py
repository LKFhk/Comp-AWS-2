"""
Health Check API for RiskIntel360 Platform
Provides health check endpoints for container and ECS deployment monitoring.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from riskintel360.config.settings import get_settings
from riskintel360.config.environment import get_environment_config
from riskintel360.services.agent_runtime import get_session_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthStatus(BaseModel):
    """Health status response model"""
    status: str
    timestamp: datetime
    version: str
    environment: str
    deployment_target: str
    uptime_seconds: float
    components: Dict[str, Any]


class ComponentHealth(BaseModel):
    """Individual component health status"""
    status: str
    response_time_ms: float
    details: Dict[str, Any]


# Track application start time for uptime calculation
_start_time = datetime.now(timezone.utc)


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Comprehensive health check endpoint for container monitoring.
    Used by Docker health checks and ECS health monitoring.
    """
    try:
        settings = get_settings()
        env_config = get_environment_config()
        
        # Calculate uptime
        uptime = (datetime.now(timezone.utc) - _start_time).total_seconds()
        
        # Check components
        components = {}
        
        # Check session manager
        try:
            start_time = datetime.now(timezone.utc)
            session_manager = await get_session_manager()
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            session_counts = await session_manager.get_session_count()
            
            components["session_manager"] = ComponentHealth(
                status="healthy",
                response_time_ms=response_time,
                details={
                    "running": session_manager._running,
                    "session_counts": session_counts,
                    "max_sessions": session_manager.max_sessions,
                }
            ).model_dump()
        except Exception as e:
            logger.error(f"Session manager health check failed: {e}")
            components["session_manager"] = ComponentHealth(
                status="unhealthy",
                response_time_ms=0.0,
                details={"error": str(e)}
            ).model_dump()
        
        # Check configuration
        try:
            components["configuration"] = ComponentHealth(
                status="healthy",
                response_time_ms=0.0,
                details={
                    "environment": env_config.environment.value,
                    "deployment_target": env_config.deployment_target.value,
                    "database_host": env_config.database_host,
                    "redis_host": env_config.redis_host,
                }
            ).model_dump()
        except Exception as e:
            logger.error(f"Configuration health check failed: {e}")
            components["configuration"] = ComponentHealth(
                status="unhealthy",
                response_time_ms=0.0,
                details={"error": str(e)}
            ).model_dump()
        
        # Determine overall status
        overall_status = "healthy"
        if any(comp["status"] == "unhealthy" for comp in components.values()):
            overall_status = "unhealthy"
        elif any(comp["status"] == "degraded" for comp in components.values()):
            overall_status = "degraded"
        
        return HealthStatus(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            version=settings.app_version,
            environment=env_config.environment.value,
            deployment_target=env_config.deployment_target.value,
            uptime_seconds=uptime,
            components=components,
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check endpoint for Kubernetes and ECS deployment.
    Returns 200 when the application is ready to serve traffic.
    """
    try:
        # Check if session manager is running
        session_manager = await get_session_manager()
        if not session_manager._running:
            raise HTTPException(status_code=503, detail="Session manager not ready")
        
        return {"status": "ready", "timestamp": datetime.now(timezone.utc)}
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check endpoint for Kubernetes and ECS deployment.
    Returns 200 when the application is alive and responsive.
    """
    try:
        # Simple liveness check - just verify the application is responding
        return {"status": "alive", "timestamp": datetime.now(timezone.utc)}
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Not alive: {str(e)}")


@router.get("/metrics")
async def metrics_endpoint():
    """
    Metrics endpoint for monitoring and observability.
    Provides Prometheus-compatible metrics.
    """
    try:
        session_manager = await get_session_manager()
        session_counts = await session_manager.get_session_count()
        
        # Generate Prometheus-style metrics
        metrics = []
        
        # Application info
        metrics.append(f'RiskIntel360_info{{version="{get_settings().app_version}"}} 1')
        
        # Uptime
        uptime = (datetime.now(timezone.utc) - _start_time).total_seconds()
        metrics.append(f'RiskIntel360_uptime_seconds {uptime}')
        
        # Session metrics
        for status, count in session_counts.items():
            metrics.append(f'RiskIntel360_sessions_total{{status="{status}"}} {count}')
        
        # Memory usage (placeholder - in production, use actual memory metrics)
        metrics.append(f'RiskIntel360_memory_usage_bytes 0')
        
        return "\n".join(metrics)
        
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        raise HTTPException(status_code=503, detail=f"Metrics unavailable: {str(e)}")


@router.get("/health/components")
async def component_health():
    """
    Detailed component health check for debugging and monitoring.
    """
    try:
        components = {}
        
        # Session manager detailed health
        session_manager = await get_session_manager()
        sessions = await session_manager.list_sessions()
        
        components["session_manager"] = {
            "status": "healthy" if session_manager._running else "unhealthy",
            "running": session_manager._running,
            "total_sessions": len(sessions),
            "session_counts": await session_manager.get_session_count(),
            "max_sessions": session_manager.max_sessions,
            "cleanup_task_running": session_manager._cleanup_task is not None and not session_manager._cleanup_task.done(),
        }
        
        # Environment configuration
        env_config = get_environment_config()
        components["environment"] = {
            "status": "healthy",
            "environment": env_config.environment.value,
            "deployment_target": env_config.deployment_target.value,
            "local_development": env_config.deployment_target.value == "local_docker",
            "cloud_deployment": env_config.deployment_target.value in ["aws_ecs", "kubernetes"],
        }
        
        # Application settings
        settings = get_settings()
        components["settings"] = {
            "status": "healthy",
            "debug": settings.debug,
            "app_name": settings.app_name,
            "app_version": settings.app_version,
        }
        
        return {
            "timestamp": datetime.now(timezone.utc),
            "components": components,
        }
        
    except Exception as e:
        logger.error(f"Component health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Component health check failed: {str(e)}")
