"""
Database Connection Pooling Service for RiskIntel360 Platform
Optimizes Aurora and DynamoDB connections for performance.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, AsyncContextManager
from contextlib import asynccontextmanager
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

import boto3
import aioboto3
from botocore.exceptions import ClientError
import asyncpg
from asyncpg import Pool as AsyncPGPool
import redis.asyncio as aioredis
from redis.asyncio import Redis

from riskintel360.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ConnectionStats:
    """Connection pool statistics"""
    total_connections: int
    active_connections: int
    idle_connections: int
    created_at: datetime
    last_activity: datetime
    total_queries: int
    avg_query_time: float


@dataclass
class PoolConfig:
    """Connection pool configuration"""
    min_size: int
    max_size: int
    max_queries: int
    max_inactive_connection_lifetime: float
    timeout: float
    command_timeout: float


class PostgreSQLConnectionPool:
    """Optimized PostgreSQL connection pool for Aurora"""
    
    def __init__(self):
        self.settings = get_settings()
        self.pool: Optional[AsyncPGPool] = None
        self.stats = ConnectionStats(
            total_connections=0,
            active_connections=0,
            idle_connections=0,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            total_queries=0,
            avg_query_time=0.0
        )
        self.query_times: List[float] = []
        self.max_query_history = 1000
        
        # Pool configuration based on environment
        if self.settings.environment.value == "production":
            self.config = PoolConfig(
                min_size=5,
                max_size=20,
                max_queries=50000,
                max_inactive_connection_lifetime=300.0,  # 5 minutes
                timeout=10.0,
                command_timeout=60.0
            )
        else:
            self.config = PoolConfig(
                min_size=2,
                max_size=10,
                max_queries=10000,
                max_inactive_connection_lifetime=600.0,  # 10 minutes
                timeout=5.0,
                command_timeout=30.0
            )
    
    async def initialize(self) -> None:
        """Initialize the connection pool"""
        try:
            # Build connection string
            if self.settings.environment.value == "development":
                # Local PostgreSQL
                dsn = f"postgresql://{self.settings.database.aurora_username}:password@localhost:{self.settings.database.aurora_port}/{self.settings.database.aurora_database_name}"
            else:
                # Aurora Serverless
                dsn = f"postgresql://{self.settings.database.aurora_username}:{self.settings.database.aurora_password}@{self.settings.database.aurora_cluster_name}.cluster-xyz.{boto3.Session().region_name}.rds.amazonaws.com:{self.settings.database.aurora_port}/{self.settings.database.aurora_database_name}"
            
            self.pool = await asyncpg.create_pool(
                dsn,
                min_size=self.config.min_size,
                max_size=self.config.max_size,
                max_queries=self.config.max_queries,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
                timeout=self.config.timeout,
                command_timeout=self.config.command_timeout,
                server_settings={
                    'application_name': 'riskintel360',
                    'tcp_keepalives_idle': '600',
                    'tcp_keepalives_interval': '30',
                    'tcp_keepalives_count': '3',
                }
            )
            
            # Update stats
            self.stats.total_connections = self.config.max_size
            self.stats.created_at = datetime.now(timezone.utc)
            
            logger.info(f"PostgreSQL connection pool initialized with {self.config.min_size}-{self.config.max_size} connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncContextManager:
        """Get a connection from the pool"""
        if not self.pool:
            await self.initialize()
        
        start_time = time.time()
        connection = None
        
        try:
            connection = await self.pool.acquire(timeout=self.config.timeout)
            self.stats.active_connections += 1
            self.stats.last_activity = datetime.now(timezone.utc)
            
            yield connection
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                await self.pool.release(connection)
                self.stats.active_connections -= 1
                
                # Track query time
                query_time = time.time() - start_time
                self.query_times.append(query_time)
                if len(self.query_times) > self.max_query_history:
                    self.query_times.pop(0)
                
                self.stats.total_queries += 1
                self.stats.avg_query_time = sum(self.query_times) / len(self.query_times)
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        async with self.get_connection() as conn:
            result = await conn.fetch(query, *args)
            return [dict(row) for row in result]
    
    async def execute_command(self, command: str, *args) -> str:
        """Execute a command and return status"""
        async with self.get_connection() as conn:
            return await conn.execute(command, *args)
    
    async def close(self) -> None:
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    def get_stats(self) -> ConnectionStats:
        """Get connection pool statistics"""
        if self.pool:
            self.stats.idle_connections = self.pool.get_idle_size()
            self.stats.active_connections = self.pool.get_size() - self.stats.idle_connections
        
        return self.stats


class DynamoDBConnectionPool:
    """Optimized DynamoDB connection pool"""
    
    def __init__(self):
        self.settings = get_settings()
        self.session = None
        self.clients: Dict[str, Any] = {}
        self.resources: Dict[str, Any] = {}
        self.stats = ConnectionStats(
            total_connections=0,
            active_connections=0,
            idle_connections=0,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            total_queries=0,
            avg_query_time=0.0
        )
        self.query_times: List[float] = []
        self.max_query_history = 1000
        
        # Connection configuration
        self.max_pool_connections = 50 if self.settings.environment.value == "production" else 20
    
    async def initialize(self) -> None:
        """Initialize DynamoDB connections"""
        try:
            # Create aioboto3 session
            self.session = aioboto3.Session()
            
            # Configure connection pooling
            config = boto3.session.Config(
                max_pool_connections=self.max_pool_connections,
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                },
                read_timeout=60,
                connect_timeout=10
            )
            
            # Create async client and resource
            self.clients['dynamodb'] = self.session.client('dynamodb', config=config)
            self.resources['dynamodb'] = self.session.resource('dynamodb', config=config)
            
            self.stats.total_connections = self.max_pool_connections
            self.stats.created_at = datetime.now(timezone.utc)
            
            logger.info(f"DynamoDB connection pool initialized with {self.max_pool_connections} max connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB connection pool: {e}")
            raise
    
    @asynccontextmanager
    async def get_client(self) -> AsyncContextManager:
        """Get DynamoDB client"""
        if not self.session:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            async with self.clients['dynamodb'] as client:
                self.stats.active_connections += 1
                self.stats.last_activity = datetime.now(timezone.utc)
                yield client
        finally:
            self.stats.active_connections -= 1
            
            # Track query time
            query_time = time.time() - start_time
            self.query_times.append(query_time)
            if len(self.query_times) > self.max_query_history:
                self.query_times.pop(0)
            
            self.stats.total_queries += 1
            self.stats.avg_query_time = sum(self.query_times) / len(self.query_times)
    
    @asynccontextmanager
    async def get_resource(self) -> AsyncContextManager:
        """Get DynamoDB resource"""
        if not self.session:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            async with self.resources['dynamodb'] as resource:
                self.stats.active_connections += 1
                self.stats.last_activity = datetime.now(timezone.utc)
                yield resource
        finally:
            self.stats.active_connections -= 1
            
            # Track query time
            query_time = time.time() - start_time
            self.query_times.append(query_time)
            if len(self.query_times) > self.max_query_history:
                self.query_times.pop(0)
            
            self.stats.total_queries += 1
            self.stats.avg_query_time = sum(self.query_times) / len(self.query_times)
    
    async def get_table(self, table_name: str):
        """Get DynamoDB table resource"""
        async with self.get_resource() as dynamodb:
            return await dynamodb.Table(table_name)
    
    async def close(self) -> None:
        """Close DynamoDB connections"""
        if self.clients:
            for client in self.clients.values():
                if hasattr(client, 'close'):
                    await client.close()
        
        if self.resources:
            for resource in self.resources.values():
                if hasattr(resource, 'close'):
                    await resource.close()
        
        logger.info("DynamoDB connection pool closed")
    
    def get_stats(self) -> ConnectionStats:
        """Get connection pool statistics"""
        return self.stats


class RedisConnectionPool:
    """Optimized Redis connection pool for ElastiCache"""
    
    def __init__(self):
        self.settings = get_settings()
        self.pool: Optional[Redis] = None
        self.redis: Optional[Redis] = None
        self.stats = ConnectionStats(
            total_connections=0,
            active_connections=0,
            idle_connections=0,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            total_queries=0,
            avg_query_time=0.0
        )
        self.query_times: List[float] = []
        self.max_query_history = 1000
        
        # Pool configuration
        if self.settings.environment.value == "production":
            self.max_connections = 50
            self.retry_on_timeout = True
            self.health_check_interval = 30
        else:
            self.max_connections = 20
            self.retry_on_timeout = False
            self.health_check_interval = 60
    
    async def initialize(self) -> None:
        """Initialize Redis connection pool"""
        try:
            # Build Redis URL
            if self.settings.environment.value == "development":
                # Local Redis
                redis_url = f"redis://localhost:{self.settings.database.redis_port}/0"
            else:
                # ElastiCache Redis
                redis_url = f"redis://{self.settings.database.redis_cluster_name}.xyz.cache.amazonaws.com:{self.settings.database.redis_port}/0"
            
            # Create Redis client with connection pool
            self.redis = aioredis.from_url(
                redis_url,
                max_connections=self.max_connections,
                retry_on_timeout=self.retry_on_timeout,
                health_check_interval=self.health_check_interval,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 3,  # TCP_KEEPINTVL
                    3: 5,  # TCP_KEEPCNT
                }
            )
            
            # Store reference for pool management
            self.pool = self.redis
            
            # Test connection
            await self.redis.ping()
            
            self.stats.total_connections = self.max_connections
            self.stats.created_at = datetime.now(timezone.utc)
            
            logger.info(f"Redis connection pool initialized with {self.max_connections} max connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection pool: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncContextManager:
        """Get Redis connection"""
        if not self.redis:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            self.stats.active_connections += 1
            self.stats.last_activity = datetime.now(timezone.utc)
            yield self.redis
        finally:
            self.stats.active_connections -= 1
            
            # Track query time
            query_time = time.time() - start_time
            self.query_times.append(query_time)
            if len(self.query_times) > self.max_query_history:
                self.query_times.pop(0)
            
            self.stats.total_queries += 1
            self.stats.avg_query_time = sum(self.query_times) / len(self.query_times)
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        async with self.get_connection() as redis:
            return await redis.get(key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis"""
        async with self.get_connection() as redis:
            return await redis.set(key, value, ex=ex)
    
    async def delete(self, key: str) -> int:
        """Delete key from Redis"""
        async with self.get_connection() as redis:
            return await redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        async with self.get_connection() as redis:
            return await redis.exists(key)
    
    async def close(self) -> None:
        """Close Redis connection pool"""
        if self.redis:
            await self.redis.close()
        if self.redis:
            await self.redis.aclose()
        logger.info("Redis connection pool closed")
    
    def get_stats(self) -> ConnectionStats:
        """Get connection pool statistics"""
        return self.stats


class ConnectionPoolManager:
    """Manages all database connection pools"""
    
    def __init__(self):
        self.postgresql_pool = PostgreSQLConnectionPool()
        self.dynamodb_pool = DynamoDBConnectionPool()
        self.redis_pool = RedisConnectionPool()
        self._initialized = False
    
    async def initialize_all(self) -> None:
        """Initialize all connection pools"""
        if self._initialized:
            return
        
        try:
            await asyncio.gather(
                self.postgresql_pool.initialize(),
                self.dynamodb_pool.initialize(),
                self.redis_pool.initialize()
            )
            self._initialized = True
            logger.info("All connection pools initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pools: {e}")
            raise
    
    async def close_all(self) -> None:
        """Close all connection pools"""
        if not self._initialized:
            return
        
        await asyncio.gather(
            self.postgresql_pool.close(),
            self.dynamodb_pool.close(),
            self.redis_pool.close(),
            return_exceptions=True
        )
        self._initialized = False
        logger.info("All connection pools closed")
    
    def get_all_stats(self) -> Dict[str, ConnectionStats]:
        """Get statistics for all connection pools"""
        return {
            'postgresql': self.postgresql_pool.get_stats(),
            'dynamodb': self.dynamodb_pool.get_stats(),
            'redis': self.redis_pool.get_stats()
        }
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all connection pools"""
        results = {}
        
        # PostgreSQL health check
        try:
            async with self.postgresql_pool.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            results['postgresql'] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            results['postgresql'] = False
        
        # DynamoDB health check
        try:
            async with self.dynamodb_pool.get_client() as client:
                await client.list_tables()
            results['dynamodb'] = True
        except Exception as e:
            logger.error(f"DynamoDB health check failed: {e}")
            results['dynamodb'] = False
        
        # Redis health check
        try:
            async with self.redis_pool.get_connection() as redis:
                await redis.ping()
            results['redis'] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            results['redis'] = False
        
        return results


# Global connection pool manager
_connection_pool_manager: Optional[ConnectionPoolManager] = None


def get_connection_pool_manager() -> ConnectionPoolManager:
    """Get the global connection pool manager"""
    global _connection_pool_manager
    if _connection_pool_manager is None:
        _connection_pool_manager = ConnectionPoolManager()
    return _connection_pool_manager
