"""
Caching Service for RiskIntel360 Platform
Implements caching strategies using AWS ElastiCache and Python decorators.
"""

import asyncio
import json
import logging
import hashlib
import pickle
from typing import Any, Optional, Dict, List, Callable, Union
from functools import wraps
from datetime import datetime, timezone, timedelta
import time

from riskintel360.services.connection_pool import get_connection_pool_manager
from riskintel360.config.settings import get_settings

logger = logging.getLogger(__name__)


class CacheStats:
    """Cache statistics tracking"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0
        self.total_time = 0.0
        self.start_time = time.time()
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time"""
        total_ops = self.hits + self.misses + self.sets + self.deletes
        return (self.total_time / total_ops) if total_ops > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'sets': self.sets,
            'deletes': self.deletes,
            'errors': self.errors,
            'hit_rate': self.hit_rate,
            'avg_response_time': self.avg_response_time,
            'uptime_seconds': time.time() - self.start_time
        }


class CacheKey:
    """Cache key generator and manager"""
    
    @staticmethod
    def generate(prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments"""
        # Create a deterministic string from args and kwargs
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        
        # Create hash of the data
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{prefix}:{key_hash}"
    
    @staticmethod
    def pattern(prefix: str) -> str:
        """Generate pattern for key matching"""
        return f"{prefix}:*"


class CachingService:
    """Main caching service with ElastiCache integration"""
    
    def __init__(self):
        self.settings = get_settings()
        self.pool_manager = get_connection_pool_manager()
        self.stats = CacheStats()
        
        # Default TTL values (in seconds)
        self.default_ttl = self.settings.database.redis_ttl_seconds
        self.ttl_config = {
            'market_data': 300,      # 5 minutes
            'agent_results': 1800,   # 30 minutes
            'user_sessions': 3600,   # 1 hour
            'api_responses': 600,    # 10 minutes
            'external_data': 900,    # 15 minutes
            'validation_cache': 7200, # 2 hours
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        start_time = time.time()
        
        try:
            async with self.pool_manager.redis_pool.get_connection() as redis:
                cached_data = await redis.get(key)
                
                if cached_data:
                    self.stats.hits += 1
                    # Try to deserialize as JSON first, then pickle
                    try:
                        return json.loads(cached_data)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            return pickle.loads(cached_data)
                        except (pickle.PickleError, TypeError):
                            return cached_data.decode('utf-8') if isinstance(cached_data, bytes) else cached_data
                else:
                    self.stats.misses += 1
                    return None
                    
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache get error for key {key}: {e}")
            return None
        finally:
            self.stats.total_time += time.time() - start_time
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        start_time = time.time()
        
        try:
            # Determine TTL
            if ttl is None:
                ttl = self.default_ttl
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            elif isinstance(value, (str, int, float, bool)):
                serialized_value = json.dumps(value)
            else:
                # Use pickle for complex objects
                serialized_value = pickle.dumps(value)
            
            async with self.pool_manager.redis_pool.get_connection() as redis:
                result = await redis.set(key, serialized_value, ex=ttl)
                self.stats.sets += 1
                return bool(result)
                
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache set error for key {key}: {e}")
            return False
        finally:
            self.stats.total_time += time.time() - start_time
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        start_time = time.time()
        
        try:
            async with self.pool_manager.redis_pool.get_connection() as redis:
                result = await redis.delete(key)
                self.stats.deletes += 1
                return bool(result)
                
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
        finally:
            self.stats.total_time += time.time() - start_time
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            async with self.pool_manager.redis_pool.get_connection() as redis:
                return await redis.exists(key)
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            async with self.pool_manager.redis_pool.get_connection() as redis:
                keys = await redis.keys(pattern)
                if keys:
                    deleted = await redis.delete(*keys)
                    self.stats.deletes += deleted
                    return deleted
                return 0
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    async def get_ttl(self, key: str) -> int:
        """Get TTL for key"""
        try:
            async with self.pool_manager.redis_pool.get_connection() as redis:
                return await redis.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1
    
    async def extend_ttl(self, key: str, ttl: int) -> bool:
        """Extend TTL for existing key"""
        try:
            async with self.pool_manager.redis_pool.get_connection() as redis:
                return await redis.expire(key, ttl)
        except Exception as e:
            logger.error(f"Cache extend TTL error for key {key}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.stats.to_dict()
    
    def reset_stats(self) -> None:
        """Reset cache statistics"""
        self.stats = CacheStats()


# Caching decorators
def cached(
    prefix: str,
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_func: Custom function to generate cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_service = get_caching_service()
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = CacheKey.generate(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function
            logger.debug(f"Cache miss for key: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache_ttl = ttl or cache_service.ttl_config.get(prefix, cache_service.default_ttl)
            await cache_service.set(cache_key, result, cache_ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate(prefix: str, key_func: Optional[Callable] = None):
    """
    Decorator for invalidating cache entries
    
    Args:
        prefix: Cache key prefix to invalidate
        key_func: Custom function to generate cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute function first
            result = await func(*args, **kwargs)
            
            # Invalidate cache
            cache_service = get_caching_service()
            
            if key_func:
                cache_key = key_func(*args, **kwargs)
                await cache_service.delete(cache_key)
            else:
                # Clear all keys with this prefix
                pattern = CacheKey.pattern(prefix)
                await cache_service.clear_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator


class MarketDataCache:
    """Specialized cache for market data"""
    
    def __init__(self, cache_service: CachingService):
        self.cache = cache_service
        self.prefix = "market_data"
    
    async def get_market_analysis(self, business_concept: str, target_market: str) -> Optional[Dict[str, Any]]:
        """Get cached market analysis"""
        key = CacheKey.generate(self.prefix, "analysis", business_concept, target_market)
        return await self.cache.get(key)
    
    async def set_market_analysis(self, business_concept: str, target_market: str, analysis: Dict[str, Any]) -> bool:
        """Cache market analysis"""
        key = CacheKey.generate(self.prefix, "analysis", business_concept, target_market)
        return await self.cache.set(key, analysis, self.cache.ttl_config['market_data'])
    
    async def get_competitor_data(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Get cached competitor data"""
        key = CacheKey.generate(self.prefix, "competitor", company_name)
        return await self.cache.get(key)
    
    async def set_competitor_data(self, company_name: str, data: Dict[str, Any]) -> bool:
        """Cache competitor data"""
        key = CacheKey.generate(self.prefix, "competitor", company_name)
        return await self.cache.set(key, data, self.cache.ttl_config['market_data'])


class AgentResultCache:
    """Specialized cache for agent results"""
    
    def __init__(self, cache_service: CachingService):
        self.cache = cache_service
        self.prefix = "agent_results"
    
    async def get_agent_result(self, agent_type: str, request_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached agent result"""
        key = CacheKey.generate(self.prefix, agent_type, request_hash)
        return await self.cache.get(key)
    
    async def set_agent_result(self, agent_type: str, request_hash: str, result: Dict[str, Any]) -> bool:
        """Cache agent result"""
        key = CacheKey.generate(self.prefix, agent_type, request_hash)
        return await self.cache.set(key, result, self.cache.ttl_config['agent_results'])
    
    async def invalidate_agent_results(self, agent_type: str) -> int:
        """Invalidate all results for an agent type"""
        pattern = CacheKey.pattern(f"{self.prefix}:{agent_type}")
        return await self.cache.clear_pattern(pattern)


class SessionCache:
    """Specialized cache for user sessions"""
    
    def __init__(self, cache_service: CachingService):
        self.cache = cache_service
        self.prefix = "user_sessions"
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session data"""
        key = CacheKey.generate(self.prefix, session_id)
        return await self.cache.get(key)
    
    async def set_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Cache session data"""
        key = CacheKey.generate(self.prefix, session_id)
        return await self.cache.set(key, session_data, self.cache.ttl_config['user_sessions'])
    
    async def extend_session(self, session_id: str) -> bool:
        """Extend session TTL"""
        key = CacheKey.generate(self.prefix, session_id)
        return await self.cache.extend_ttl(key, self.cache.ttl_config['user_sessions'])
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from cache"""
        key = CacheKey.generate(self.prefix, session_id)
        return await self.cache.delete(key)


class CacheManager:
    """High-level cache manager with specialized caches"""
    
    def __init__(self):
        self.cache_service = CachingService()
        self.market_data = MarketDataCache(self.cache_service)
        self.agent_results = AgentResultCache(self.cache_service)
        self.sessions = SessionCache(self.cache_service)
    
    async def initialize(self) -> None:
        """Initialize cache manager"""
        await self.cache_service.pool_manager.initialize_all()
        logger.info("Cache manager initialized")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        try:
            # Test basic operations
            test_key = "health_check_test"
            test_value = {"timestamp": datetime.now(timezone.utc).isoformat()}
            
            # Test set
            set_result = await self.cache_service.set(test_key, test_value, 60)
            
            # Test get
            get_result = await self.cache_service.get(test_key)
            
            # Test delete
            delete_result = await self.cache_service.delete(test_key)
            
            return {
                'status': 'healthy' if all([set_result, get_result, delete_result]) else 'unhealthy',
                'operations': {
                    'set': set_result,
                    'get': get_result is not None,
                    'delete': delete_result
                },
                'stats': self.cache_service.get_stats()
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'stats': self.cache_service.get_stats()
            }
    
    async def clear_all(self) -> Dict[str, int]:
        """Clear all cached data"""
        results = {}
        
        for cache_type in ['market_data', 'agent_results', 'user_sessions', 'api_responses', 'external_data', 'validation_cache']:
            pattern = CacheKey.pattern(cache_type)
            deleted = await self.cache_service.clear_pattern(pattern)
            results[cache_type] = deleted
        
        return results
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return {
            'service_stats': self.cache_service.get_stats(),
            'pool_stats': self.cache_service.pool_manager.redis_pool.get_stats().to_dict() if hasattr(self.cache_service.pool_manager.redis_pool.get_stats(), 'to_dict') else str(self.cache_service.pool_manager.redis_pool.get_stats())
        }


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_caching_service() -> CachingService:
    """Get the global caching service"""
    return get_cache_manager().cache_service


def get_cache_manager() -> CacheManager:
    """Get the global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
