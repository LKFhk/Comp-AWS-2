"""
Data source specific error handling and recovery mechanisms.

This module provides specialized error handling for external data sources
including APIs, databases, and third-party services.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

from .error_handling import (
    ErrorHandlingManager, CircuitBreakerConfig, RetryConfig,
    GracefulDegradationManager, ErrorContext, ErrorSeverity
)

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Types of data sources."""
    API = "api"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    CACHE = "cache"
    EXTERNAL_SERVICE = "external_service"


class DataSourceError(Exception):
    """Base exception for data source errors."""
    
    def __init__(self, message: str, source_type: DataSourceType, source_name: str):
        super().__init__(message)
        self.source_type = source_type
        self.source_name = source_name
        self.timestamp = datetime.now()


class APIError(DataSourceError):
    """API-specific error."""
    
    def __init__(self, message: str, source_name: str, status_code: Optional[int] = None):
        super().__init__(message, DataSourceType.API, source_name)
        self.status_code = status_code


class DatabaseError(DataSourceError):
    """Database-specific error."""
    
    def __init__(self, message: str, source_name: str, query: Optional[str] = None):
        super().__init__(message, DataSourceType.DATABASE, source_name)
        self.query = query


class CacheError(DataSourceError):
    """Cache-specific error."""
    
    def __init__(self, message: str, source_name: str, key: Optional[str] = None):
        super().__init__(message, DataSourceType.CACHE, source_name)
        self.key = key


class DataSourceManager:
    """
    Manages data source connections and error handling.
    
    Provides unified interface for accessing various data sources with
    built-in error handling, retry logic, and fallback mechanisms.
    """
    
    def __init__(self):
        self.error_manager = ErrorHandlingManager()
        self.data_sources: Dict[str, Any] = {}
        self.fallback_sources: Dict[str, List[str]] = {}
        self.cache_manager: Optional[Any] = None
        self._setup_error_handling()
    
    def _setup_error_handling(self):
        """Setup error handling configurations for different data sources."""
        
        # API circuit breakers
        api_circuit_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=APIError
        )
        
        # Database circuit breakers
        db_circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=DatabaseError
        )
        
        # Cache circuit breakers
        cache_circuit_config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=15,
            expected_exception=CacheError
        )
        
        # Retry configurations
        api_retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=30.0,
            backoff_multiplier=2.0
        )
        
        db_retry_config = RetryConfig(
            max_attempts=2,
            base_delay=0.5,
            max_delay=10.0,
            backoff_multiplier=2.0
        )
        
        # Register configurations
        self.error_manager.register_circuit_breaker("api", api_circuit_config)
        self.error_manager.register_circuit_breaker("database", db_circuit_config)
        self.error_manager.register_circuit_breaker("cache", cache_circuit_config)
        
        self.error_manager.register_retry_handler("api", api_retry_config)
        self.error_manager.register_retry_handler("database", db_retry_config)
    
    def register_data_source(self, name: str, source: Any, source_type: DataSourceType):
        """Register a data source."""
        self.data_sources[name] = {
            'source': source,
            'type': source_type,
            'last_success': datetime.now(),
            'failure_count': 0
        }
        logger.info(f"Registered data source: {name} ({source_type.value})")
    
    def register_fallback_chain(self, primary_source: str, fallback_sources: List[str]):
        """Register fallback sources for a primary source."""
        self.fallback_sources[primary_source] = fallback_sources
        logger.info(f"Registered fallback chain for {primary_source}: {fallback_sources}")
    
    async def fetch_data(
        self,
        source_name: str,
        operation: str,
        *args,
        use_cache: bool = True,
        **kwargs
    ) -> Any:
        """
        Fetch data from a source with error handling and fallbacks.
        
        Args:
            source_name: Name of the data source
            operation: Operation to perform (method name or function)
            use_cache: Whether to use cache for this operation
            *args, **kwargs: Arguments for the operation
        
        Returns:
            Data from the source or fallback
        """
        cache_key = f"{source_name}:{operation}:{hash(str(args) + str(kwargs))}"
        
        # Try cache first if enabled
        if use_cache and self.cache_manager:
            try:
                cached_data = await self._get_from_cache(cache_key)
                if cached_data is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_data
            except CacheError as e:
                logger.warning(f"Cache error for {cache_key}: {e}")
        
        # Try primary source
        try:
            data = await self._fetch_from_source(source_name, operation, *args, **kwargs)
            
            # Cache successful result
            if use_cache and self.cache_manager:
                try:
                    await self._store_in_cache(cache_key, data)
                except CacheError as e:
                    logger.warning(f"Failed to cache data for {cache_key}: {e}")
            
            return data
        
        except DataSourceError as e:
            logger.warning(f"Primary source {source_name} failed: {e}")
            
            # Try fallback sources
            if source_name in self.fallback_sources:
                for fallback_name in self.fallback_sources[source_name]:
                    try:
                        logger.info(f"Trying fallback source: {fallback_name}")
                        data = await self._fetch_from_source(fallback_name, operation, *args, **kwargs)
                        
                        # Cache fallback result with shorter TTL
                        if use_cache and self.cache_manager:
                            try:
                                await self._store_in_cache(cache_key, data, ttl=300)  # 5 minutes
                            except CacheError:
                                pass
                        
                        return data
                    except DataSourceError as fallback_error:
                        logger.warning(f"Fallback source {fallback_name} failed: {fallback_error}")
                        continue
            
            # All sources failed, try degraded response
            degraded_data = await self._get_degraded_response(source_name, operation, *args, **kwargs)
            if degraded_data is not None:
                return degraded_data
            
            # No fallback available, re-raise original error
            raise e
    
    async def _fetch_from_source(self, source_name: str, operation: str, *args, **kwargs) -> Any:
        """Fetch data from a specific source with error handling."""
        if source_name not in self.data_sources:
            raise DataSourceError(f"Unknown data source: {source_name}", DataSourceType.EXTERNAL_SERVICE, source_name)
        
        source_info = self.data_sources[source_name]
        source = source_info['source']
        source_type = source_info['type']
        
        try:
            # Execute with error protection
            if hasattr(source, operation):
                func = getattr(source, operation)
                result = await self.error_manager.execute_with_protection(
                    source_name, func, *args, **kwargs
                )
            else:
                raise DataSourceError(f"Operation {operation} not available on {source_name}", source_type, source_name)
            
            # Update success metrics
            source_info['last_success'] = datetime.now()
            source_info['failure_count'] = 0
            
            return result
        
        except Exception as e:
            # Update failure metrics
            source_info['failure_count'] += 1
            
            # Convert to appropriate data source error
            if source_type == DataSourceType.API:
                status_code = getattr(e, 'status_code', None)
                raise APIError(str(e), source_name, status_code)
            elif source_type == DataSourceType.DATABASE:
                query = getattr(e, 'query', None)
                raise DatabaseError(str(e), source_name, query)
            elif source_type == DataSourceType.CACHE:
                key = kwargs.get('key', None)
                raise CacheError(str(e), source_name, key)
            else:
                raise DataSourceError(str(e), source_type, source_name)
    
    async def _get_from_cache(self, key: str) -> Any:
        """Get data from cache."""
        if not self.cache_manager:
            return None
        
        try:
            return await self.cache_manager.get(key)
        except Exception as e:
            raise CacheError(f"Failed to get cache key {key}: {e}", "cache", key)
    
    async def _store_in_cache(self, key: str, data: Any, ttl: int = 3600):
        """Store data in cache."""
        if not self.cache_manager:
            return
        
        try:
            await self.cache_manager.set(key, data, ttl=ttl)
        except Exception as e:
            raise CacheError(f"Failed to store cache key {key}: {e}", "cache", key)
    
    async def _get_degraded_response(self, source_name: str, operation: str, *args, **kwargs) -> Optional[Any]:
        """Get degraded response when all sources fail."""
        # This could return cached data, default values, or simplified responses
        logger.info(f"Generating degraded response for {source_name}:{operation}")
        
        # Example degraded responses based on operation type
        if operation in ['get_market_data', 'fetch_market_info']:
            return {
                'status': 'degraded',
                'message': 'Market data temporarily unavailable',
                'data': {},
                'confidence': 0.1
            }
        elif operation in ['get_competitor_info', 'fetch_competitive_data']:
            return {
                'status': 'degraded',
                'message': 'Competitive intelligence temporarily unavailable',
                'competitors': [],
                'confidence': 0.1
            }
        elif operation in ['get_financial_data', 'fetch_financial_metrics']:
            return {
                'status': 'degraded',
                'message': 'Financial data temporarily unavailable',
                'metrics': {},
                'confidence': 0.1
            }
        
        return None
    
    def get_source_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all data sources."""
        health_status = {}
        
        for name, info in self.data_sources.items():
            circuit_breaker = self.error_manager.circuit_breakers.get(info['type'].value)
            
            health_status[name] = {
                'type': info['type'].value,
                'last_success': info['last_success'].isoformat(),
                'failure_count': info['failure_count'],
                'circuit_breaker_state': circuit_breaker.state.value if circuit_breaker else 'unknown',
                'is_healthy': info['failure_count'] < 3 and (
                    datetime.now() - info['last_success']
                ).total_seconds() < 3600
            }
        
        return health_status


# Global data source manager instance
data_source_manager = DataSourceManager()
