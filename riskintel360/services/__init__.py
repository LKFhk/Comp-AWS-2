"""
Services module for RiskIntel360 Platform
Contains business logic services, external integrations, and orchestration services.
"""

# Import all services for easy access
from .connection_pool import (
    ConnectionPoolManager,
    PostgreSQLConnectionPool,
    DynamoDBConnectionPool,
    RedisConnectionPool,
    get_connection_pool_manager
)

from .caching_service import (
    CacheManager,
    CachingService,
    get_caching_service,
    get_cache_manager,
    cached,
    cache_invalidate
)

from .performance_optimizer import (
    PerformanceOptimizer,
    PerformanceMonitor,
    get_performance_optimizer,
    performance_monitor
)

from .auto_scaling import (
    AutoScalingService,
    ScalingMetrics
)

__all__ = [
    # Connection Pool
    'ConnectionPoolManager',
    'PostgreSQLConnectionPool', 
    'DynamoDBConnectionPool',
    'RedisConnectionPool',
    'get_connection_pool_manager',
    
    # Caching
    'CacheManager',
    'CachingService',
    'get_caching_service',
    'get_cache_manager',
    'cached',
    'cache_invalidate',
    
    # Performance
    'PerformanceOptimizer',
    'PerformanceMonitor',
    'get_performance_optimizer',
    'performance_monitor',
    
    # Auto Scaling
    'AutoScalingService',
    'ScalingMetrics',
]
