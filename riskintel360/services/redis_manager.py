"""
Redis Connection Manager for RiskIntel360 Platform
Handles connections to both local Redis (development) and AWS ElastiCache (production)
"""

import asyncio
import logging
import os
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager
import json

import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError, RedisError

from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class RedisConnectionManager:
    """
    Manages Redis connections for both local development and AWS ElastiCache production.
    Provides automatic failover, connection pooling, and environment-specific configuration.
    """
    
    def __init__(self):
        """Initialize Redis connection manager"""
        self.settings = get_settings()
        self.client: Optional[redis.Redis] = None
        self.connection_pool: Optional[redis.ConnectionPool] = None
        self.is_connected = False
        self.connection_retries = 0
        self.max_retries = 3
        
    async def initialize(self) -> bool:
        """
        Initialize Redis connection based on environment.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.settings.environment.value == "development":
                success = await self._connect_local_redis()
            else:
                success = await self._connect_elasticache()
            
            if success:
                self.is_connected = True
                logger.info("??Redis connection manager initialized successfully")
                return True
            else:
                logger.error("??Failed to initialize Redis connection")
                return False
                
        except Exception as e:
            logger.error(f"??Redis initialization error: {e}")
            return False
    
    async def _connect_local_redis(self) -> bool:
        """Connect to local Redis instance"""
        try:
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            db = int(os.getenv("REDIS_DB", "0"))
            password = os.getenv("REDIS_PASSWORD")
            
            # Create connection pool
            self.connection_pool = redis.ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Create Redis client
            self.client = redis.Redis(connection_pool=self.connection_pool)
            
            # Test connection
            await self.client.ping()
            logger.info(f"??Connected to local Redis at {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"??Failed to connect to local Redis: {e}")
            return False
    
    async def _connect_elasticache(self) -> bool:
        """Connect to AWS ElastiCache"""
        try:
            cluster_endpoint = os.getenv("ELASTICACHE_ENDPOINT")
            if not cluster_endpoint:
                logger.error("??ELASTICACHE_ENDPOINT not configured")
                return False
            
            port = int(os.getenv("ELASTICACHE_PORT", "6379"))
            
            # Create connection pool for ElastiCache
            self.connection_pool = redis.ConnectionPool(
                host=cluster_endpoint,
                port=port,
                decode_responses=True,
                max_connections=50,  # Higher for production
                retry_on_timeout=True,
                socket_timeout=10,
                socket_connect_timeout=10,
                ssl=True,  # ElastiCache typically uses SSL
                ssl_cert_reqs=None
            )
            
            # Create Redis client
            self.client = redis.Redis(connection_pool=self.connection_pool)
            
            # Test connection
            await self.client.ping()
            logger.info(f"??Connected to ElastiCache at {cluster_endpoint}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"??Failed to connect to ElastiCache: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        try:
            if self.client:
                await self.client.close()
            if self.connection_pool:
                await self.connection_pool.disconnect()
            
            self.is_connected = False
            logger.info("??Disconnected from Redis")
            
        except Exception as e:
            logger.error(f"??Error disconnecting from Redis: {e}")
    
    async def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            if not self.client:
                return False
            
            await self.client.ping()
            return True
            
        except Exception as e:
            logger.warning(f" Redis health check failed: {e}")
            return False
    
    async def reconnect(self) -> bool:
        """Attempt to reconnect to Redis"""
        if self.connection_retries >= self.max_retries:
            logger.error(f"??Max reconnection attempts ({self.max_retries}) exceeded")
            return False
        
        self.connection_retries += 1
        logger.info(f"?? Attempting Redis reconnection ({self.connection_retries}/{self.max_retries})")
        
        await self.disconnect()
        success = await self.initialize()
        
        if success:
            self.connection_retries = 0
            logger.info("??Redis reconnection successful")
        
        return success
    
    @asynccontextmanager
    async def get_client(self):
        """
        Get Redis client with automatic reconnection.
        
        Usage:
            async with redis_manager.get_client() as client:
                await client.set("key", "value")
        """
        if not self.is_connected or not await self.health_check():
            if not await self.reconnect():
                raise ConnectionError("Unable to establish Redis connection")
        
        try:
            yield self.client
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f" Redis operation failed, attempting reconnection: {e}")
            if await self.reconnect():
                yield self.client
            else:
                raise
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a key-value pair in Redis.
        
        Args:
            key: Redis key
            value: Value to store (will be JSON serialized)
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            async with self.get_client() as client:
                serialized_value = json.dumps(value, default=str)
                
                if ttl:
                    await client.setex(key, ttl, serialized_value)
                else:
                    await client.set(key, serialized_value)
                
                return True
                
        except Exception as e:
            logger.error(f"??Failed to set Redis key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from Redis.
        
        Args:
            key: Redis key
            
        Returns:
            Any: Deserialized value or None if not found
        """
        try:
            async with self.get_client() as client:
                value = await client.get(key)
                if value is None:
                    return None
                
                return json.loads(value)
                
        except Exception as e:
            logger.error(f"??Failed to get Redis key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Args:
            key: Redis key
            
        Returns:
            bool: True if key was deleted, False otherwise
        """
        try:
            async with self.get_client() as client:
                result = await client.delete(key)
                return result > 0
                
        except Exception as e:
            logger.error(f"??Failed to delete Redis key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        
        Args:
            key: Redis key
            
        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            async with self.get_client() as client:
                return await client.exists(key) > 0
                
        except Exception as e:
            logger.error(f"??Failed to check Redis key existence {key}: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching a pattern.
        
        Args:
            pattern: Redis key pattern
            
        Returns:
            List[str]: List of matching keys
        """
        try:
            async with self.get_client() as client:
                return await client.keys(pattern)
                
        except Exception as e:
            logger.error(f"??Failed to get Redis keys with pattern {pattern}: {e}")
            return []
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration for a key.
        
        Args:
            key: Redis key
            ttl: Time to live in seconds
            
        Returns:
            bool: True if expiration was set, False otherwise
        """
        try:
            async with self.get_client() as client:
                return await client.expire(key, ttl)
                
        except Exception as e:
            logger.error(f"??Failed to set Redis key expiration {key}: {e}")
            return False
    
    async def hset(self, name: str, mapping: Dict[str, Any]) -> bool:
        """
        Set hash fields.
        
        Args:
            name: Hash name
            mapping: Field-value mapping
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            async with self.get_client() as client:
                # Serialize values in mapping
                serialized_mapping = {
                    k: json.dumps(v, default=str) for k, v in mapping.items()
                }
                await client.hset(name, mapping=serialized_mapping)
                return True
                
        except Exception as e:
            logger.error(f"??Failed to set Redis hash {name}: {e}")
            return False
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """
        Get hash field value.
        
        Args:
            name: Hash name
            key: Field key
            
        Returns:
            Any: Deserialized field value or None if not found
        """
        try:
            async with self.get_client() as client:
                value = await client.hget(name, key)
                if value is None:
                    return None
                
                return json.loads(value)
                
        except Exception as e:
            logger.error(f"??Failed to get Redis hash field {name}.{key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """
        Get all hash fields.
        
        Args:
            name: Hash name
            
        Returns:
            Dict[str, Any]: Dictionary of field-value pairs
        """
        try:
            async with self.get_client() as client:
                hash_data = await client.hgetall(name)
                
                # Deserialize values
                return {
                    k: json.loads(v) for k, v in hash_data.items()
                }
                
        except Exception as e:
            logger.error(f"??Failed to get Redis hash {name}: {e}")
            return {}
    
    async def lpush(self, name: str, *values: Any) -> bool:
        """
        Push values to the left of a list.
        
        Args:
            name: List name
            values: Values to push
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            async with self.get_client() as client:
                serialized_values = [json.dumps(v, default=str) for v in values]
                await client.lpush(name, *serialized_values)
                return True
                
        except Exception as e:
            logger.error(f"??Failed to push to Redis list {name}: {e}")
            return False
    
    async def rpop(self, name: str) -> Optional[Any]:
        """
        Pop value from the right of a list.
        
        Args:
            name: List name
            
        Returns:
            Any: Deserialized value or None if list is empty
        """
        try:
            async with self.get_client() as client:
                value = await client.rpop(name)
                if value is None:
                    return None
                
                return json.loads(value)
                
        except Exception as e:
            logger.error(f"??Failed to pop from Redis list {name}: {e}")
            return None
    
    async def llen(self, name: str) -> int:
        """
        Get list length.
        
        Args:
            name: List name
            
        Returns:
            int: List length
        """
        try:
            async with self.get_client() as client:
                return await client.llen(name)
                
        except Exception as e:
            logger.error(f"??Failed to get Redis list length {name}: {e}")
            return 0


# Global Redis manager instance
_redis_manager: Optional[RedisConnectionManager] = None


async def get_redis_manager() -> RedisConnectionManager:
    """
    Get or create the global Redis manager instance.
    
    Returns:
        RedisConnectionManager: The global Redis manager instance
    """
    global _redis_manager
    
    if _redis_manager is None:
        _redis_manager = RedisConnectionManager()
        success = await _redis_manager.initialize()
        if not success:
            raise RuntimeError("Failed to initialize Redis connection manager")
    
    return _redis_manager


async def shutdown_redis_manager() -> None:
    """Shutdown the global Redis manager"""
    global _redis_manager
    
    if _redis_manager is not None:
        await _redis_manager.disconnect()
        _redis_manager = None
