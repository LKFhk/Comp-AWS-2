"""
Performance Monitoring API for RiskIntel360 Platform
Provides real-time performance metrics and monitoring endpoints.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from riskintel360.services.performance_optimizer import get_performance_optimizer
from riskintel360.services.caching_service import get_cache_manager
from riskintel360.services.connection_pool import get_connection_pool_manager
from riskintel360.services.auto_scaling import AutoScalingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance")


class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response model"""
    timestamp: datetime
    overall_stats: Dict[str, Any]
    agent_stats: Dict[str, Any]
    cache_stats: Dict[str, Any]
    connection_pool_stats: Dict[str, Any]
    auto_scaling_stats: Optional[Dict[str, Any]] = None


class PerformanceTargetsResponse(BaseModel):
    """Performance targets response model"""
    targets: Dict[str, float]
    current_performance: Dict[str, Any]
    target_compliance: Dict[str, bool]


class SystemHealthResponse(BaseModel):
    """System health response model"""
    status: str
    timestamp: datetime
    components: Dict[str, Any]
    performance_summary: Dict[str, Any]


@router.get("/metrics", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    hours: int = Query(default=1, ge=1, le=24, description="Hours of metrics to retrieve")
):
    """
    Get comprehensive performance metrics for the platform.
    
    Args:
        hours: Number of hours of historical data to include
    
    Returns:
        Comprehensive performance metrics including agents, cache, and connections
    """
    try:
        performance_optimizer = get_performance_optimizer()
        cache_manager = get_cache_manager()
        pool_manager = get_connection_pool_manager()
        
        # Get performance stats
        overall_stats = performance_optimizer.monitor.get_stats(hours=hours)
        
        # Get agent-specific stats
        agent_stats = {}
        agent_types = [
            'market_research', 'competitive_intel', 'financial_validation',
            'risk_assessment', 'customer_intel', 'synthesis'
        ]
        
        for agent_type in agent_types:
            agent_stats[agent_type] = performance_optimizer.monitor.get_stats(
                operation_name=agent_type, hours=hours
            )
        
        # Get cache stats
        cache_stats = cache_manager.get_comprehensive_stats()
        
        # Get connection pool stats
        connection_pool_stats = pool_manager.get_all_stats()
        
        # Convert ConnectionStats to dict for JSON serialization
        serialized_pool_stats = {}
        for pool_name, stats in connection_pool_stats.items():
            serialized_pool_stats[pool_name] = {
                'total_connections': stats.total_connections,
                'active_connections': stats.active_connections,
                'idle_connections': stats.idle_connections,
                'created_at': stats.created_at.isoformat(),
                'last_activity': stats.last_activity.isoformat(),
                'total_queries': stats.total_queries,
                'avg_query_time': stats.avg_query_time
            }
        
        # Try to get auto-scaling stats (may not be available in development)
        auto_scaling_stats = None
        try:
            auto_scaling_service = AutoScalingService()
            metrics = await auto_scaling_service.collect_metrics()
            auto_scaling_stats = {
                'cpu_utilization': metrics.cpu_utilization,
                'memory_utilization': metrics.memory_utilization,
                'active_sessions': metrics.active_sessions,
                'request_rate': metrics.request_rate,
                'response_time': metrics.response_time,
                'timestamp': metrics.timestamp.isoformat()
            }
        except Exception as e:
            logger.debug(f"Auto-scaling stats not available (development mode): {e}")
            # Provide mock stats for development
            auto_scaling_stats = {
                'cpu_utilization': 45.2,
                'memory_utilization': 62.8,
                'active_sessions': 12,
                'request_rate': 25.5,
                'response_time': 0.15,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'mode': 'development_mock'
            }
        
        return PerformanceMetricsResponse(
            timestamp=datetime.now(timezone.utc),
            overall_stats=overall_stats,
            agent_stats=agent_stats,
            cache_stats=cache_stats,
            connection_pool_stats=serialized_pool_stats,
            auto_scaling_stats=auto_scaling_stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        # Return graceful fallback response instead of error
        return PerformanceMetricsResponse(
            timestamp=datetime.now(timezone.utc),
            overall_stats={'message': 'Performance monitoring initializing'},
            agent_stats={},
            cache_stats={'status': 'initializing'},
            connection_pool_stats={},
            auto_scaling_stats={
                'cpu_utilization': 45.2,
                'memory_utilization': 62.8,
                'active_sessions': 12,
                'request_rate': 25.5,
                'response_time': 0.15,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'mode': 'development_mock'
            }
        )


@router.get("/targets", response_model=PerformanceTargetsResponse)
async def get_performance_targets():
    """
    Get performance targets and current compliance status.
    
    Returns:
        Performance targets and current compliance status
    """
    try:
        performance_optimizer = get_performance_optimizer()
        
        # Get targets
        targets = {
            name: target.target_time_seconds 
            for name, target in performance_optimizer.monitor.targets.items()
        }
        
        # Get current performance for each target
        current_performance = {}
        target_compliance = {}
        
        for target_name, target_time in targets.items():
            stats = performance_optimizer.monitor.get_stats(operation_name=target_name, hours=1)
            
            if stats:
                current_avg = stats.get('avg_duration', 0)
                current_performance[target_name] = {
                    'avg_duration': current_avg,
                    'target_duration': target_time,
                    'performance_ratio': current_avg / target_time if target_time > 0 else 0
                }
                target_compliance[target_name] = current_avg <= target_time
            else:
                current_performance[target_name] = {
                    'avg_duration': 0,
                    'target_duration': target_time,
                    'performance_ratio': 0
                }
                target_compliance[target_name] = True  # No data means compliant
        
        return PerformanceTargetsResponse(
            targets=targets,
            current_performance=current_performance,
            target_compliance=target_compliance
        )
        
    except Exception as e:
        logger.error(f"Failed to get performance targets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance targets: {str(e)}")


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health():
    """
    Get comprehensive system health including performance indicators.
    
    Returns:
        System health status with performance summary
    """
    try:
        performance_optimizer = get_performance_optimizer()
        cache_manager = get_cache_manager()
        pool_manager = get_connection_pool_manager()
        
        components = {}
        
        # Performance optimizer health
        try:
            perf_stats = performance_optimizer.monitor.get_stats(hours=1)
            components['performance_optimizer'] = {
                'status': 'healthy',
                'metrics_count': len(performance_optimizer.monitor.metrics),
                'recent_operations': perf_stats.get('total_operations', 0),
                'success_rate': perf_stats.get('success_rate', 100)
            }
        except Exception as e:
            components['performance_optimizer'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Cache health
        try:
            cache_health = await cache_manager.health_check()
            components['cache'] = cache_health
        except Exception as e:
            components['cache'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Connection pool health
        try:
            pool_health = await pool_manager.health_check()
            components['connection_pools'] = {
                'status': 'healthy' if all(pool_health.values()) else 'degraded',
                'pools': pool_health
            }
        except Exception as e:
            components['connection_pools'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Auto-scaling health (optional)
        try:
            auto_scaling_service = AutoScalingService()
            current_capacity = await auto_scaling_service.get_current_capacity()
            components['auto_scaling'] = {
                'status': 'healthy',
                'current_capacity': current_capacity,
                'cluster_name': auto_scaling_service.cluster_name
            }
        except Exception as e:
            components['auto_scaling'] = {
                'status': 'unavailable',
                'note': 'Auto-scaling not available in development environment'
            }
        
        # Determine overall status
        unhealthy_components = [name for name, comp in components.items() 
                             if comp.get('status') == 'unhealthy']
        degraded_components = [name for name, comp in components.items() 
                             if comp.get('status') == 'degraded']
        
        if unhealthy_components:
            overall_status = 'unhealthy'
        elif degraded_components:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        # Performance summary
        performance_summary = {
            'overall_health': overall_status,
            'components_healthy': len([c for c in components.values() if c.get('status') == 'healthy']),
            'components_total': len(components),
            'performance_targets_met': 'unknown'  # Would need more complex calculation
        }
        
        return SystemHealthResponse(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            components=components,
            performance_summary=performance_summary
        )
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.post("/optimize")
async def trigger_performance_optimization():
    """
    Trigger automatic performance optimization.
    
    Returns:
        Results of the optimization process
    """
    try:
        performance_optimizer = get_performance_optimizer()
        
        # Run auto-tuning
        tuning_results = await performance_optimizer.auto_tune_performance()
        
        return {
            'timestamp': datetime.now(timezone.utc),
            'optimization_triggered': True,
            'tuning_results': tuning_results,
            'message': 'Performance optimization completed'
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger performance optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger optimization: {str(e)}")


@router.get("/warmup")
async def warmup_services():
    """
    Warm up all performance-critical services.
    
    Returns:
        Results of the warmup process
    """
    try:
        performance_optimizer = get_performance_optimizer()
        
        # Warm up services
        warmup_results = await performance_optimizer.warm_up_services()
        
        return {
            'timestamp': datetime.now(timezone.utc),
            'warmup_completed': True,
            'results': warmup_results,
            'message': 'Service warmup completed'
        }
        
    except Exception as e:
        logger.error(f"Failed to warm up services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to warm up services: {str(e)}")


@router.get("/report")
async def get_performance_report():
    """
    Get comprehensive performance report.
    
    Returns:
        Detailed performance report with recommendations
    """
    try:
        performance_optimizer = get_performance_optimizer()
        
        # Get comprehensive report
        report = performance_optimizer.get_performance_report()
        
        # Add timestamp
        report['generated_at'] = datetime.now(timezone.utc).isoformat()
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate performance report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/agents/{agent_name}/metrics")
async def get_agent_performance_metrics(
    agent_name: str,
    hours: int = Query(default=1, ge=1, le=24, description="Hours of metrics to retrieve")
):
    """
    Get performance metrics for a specific agent.
    
    Args:
        agent_name: Name of the agent (e.g., 'market_research', 'competitive_intel')
        hours: Number of hours of historical data to include
    
    Returns:
        Performance metrics for the specified agent
    """
    try:
        performance_optimizer = get_performance_optimizer()
        
        # Validate agent name
        valid_agents = [
            'market_research', 'competitive_intel', 'financial_validation',
            'risk_assessment', 'customer_intel', 'synthesis'
        ]
        
        if agent_name not in valid_agents:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid agent name. Valid agents: {', '.join(valid_agents)}"
            )
        
        # Get agent-specific stats
        agent_stats = performance_optimizer.monitor.get_stats(
            operation_name=agent_name, hours=hours
        )
        
        if not agent_stats:
            return {
                'agent_name': agent_name,
                'timestamp': datetime.now(timezone.utc),
                'message': f'No metrics available for {agent_name} in the last {hours} hours',
                'stats': {}
            }
        
        return {
            'agent_name': agent_name,
            'timestamp': datetime.now(timezone.utc),
            'stats': agent_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent metrics for {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent metrics: {str(e)}")
