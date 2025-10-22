"""
Tests for data storage infrastructure including memory management and Redis connections.
"""

import pytest
import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from riskintel360.services.agent_memory import (
    get_memory_manager, 
    shutdown_memory_manager,
    MemoryType,
    MemoryScope,
    AgentMemoryManager
)
from riskintel360.services.redis_manager import (
    get_redis_manager,
    shutdown_redis_manager,
    RedisConnectionManager
)


class TestAgentMemoryManager:
    """Test agent memory management functionality"""
    
    @pytest.mark.asyncio
    async def test_memory_manager_initialization(self):
        """Test memory manager can be initialized"""
        # Mock the Redis connection to avoid requiring actual Redis
        with patch('riskintel360.services.agent_memory.RedisMemoryBackend') as mock_redis:
            mock_backend = AsyncMock()
            mock_backend.connect.return_value = True
            mock_redis.return_value = mock_backend
            
            with patch('riskintel360.services.agent_memory.InMemoryMessageQueue') as mock_queue:
                mock_queue_instance = AsyncMock()
                mock_queue_instance.connect.return_value = True
                mock_queue.return_value = mock_queue_instance
                
                # Test memory manager creation
                memory_manager = await get_memory_manager()
                assert memory_manager is not None
                assert isinstance(memory_manager, AgentMemoryManager)
                
                # Test shutdown
                await shutdown_memory_manager()
    
    @pytest.mark.asyncio
    async def test_memory_storage_and_retrieval(self):
        """Test storing and retrieving memory entries"""
        with patch('riskintel360.services.agent_memory.RedisMemoryBackend') as mock_redis:
            mock_backend = AsyncMock()
            mock_backend.connect.return_value = True
            mock_backend.store.return_value = True
            mock_backend.retrieve.return_value = {
                'id': 'test_id',
                'agent_id': 'test_agent',
                'memory_type': 'short_term',
                'scope': 'agent_private',
                'key': 'test_key',
                'value': 'test_value',
                'metadata': {},
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'expires_at': None,
                'access_count': 0,
                'confidence_score': 1.0
            }
            mock_redis.return_value = mock_backend
            
            with patch('riskintel360.services.agent_memory.InMemoryMessageQueue') as mock_queue:
                mock_queue_instance = AsyncMock()
                mock_queue_instance.connect.return_value = True
                mock_queue.return_value = mock_queue_instance
                
                memory_manager = await get_memory_manager()
                
                # Test storing memory
                entry_id = await memory_manager.store_memory(
                    agent_id="test_agent",
                    memory_type=MemoryType.SHORT_TERM,
                    scope=MemoryScope.AGENT_PRIVATE,
                    key="test_key",
                    value="test_value"
                )
                
                assert entry_id != ""
                
                # Test retrieving memory
                entry = await memory_manager.retrieve_memory(
                    agent_id="test_agent",
                    memory_type=MemoryType.SHORT_TERM,
                    scope=MemoryScope.AGENT_PRIVATE,
                    key="test_key"
                )
                
                assert entry is not None
                assert entry.value == "test_value"
                
                await shutdown_memory_manager()


class TestRedisConnectionManager:
    """Test Redis connection management functionality"""
    
    @pytest.mark.asyncio
    async def test_redis_manager_initialization(self):
        """Test Redis manager can be initialized"""
        # Mock Redis connection to avoid requiring actual Redis
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client
            
            with patch('redis.asyncio.ConnectionPool') as mock_pool:
                mock_pool_instance = Mock()
                mock_pool.return_value = mock_pool_instance
                
                # Test Redis manager creation
                redis_manager = await get_redis_manager()
                assert redis_manager is not None
                assert isinstance(redis_manager, RedisConnectionManager)
                assert redis_manager.is_connected
                
                # Test shutdown
                await shutdown_redis_manager()
    
    @pytest.mark.asyncio
    async def test_redis_operations(self):
        """Test basic Redis operations"""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_client.set.return_value = True
            mock_client.get.return_value = '{"test": "value"}'
            mock_client.delete.return_value = 1
            mock_client.exists.return_value = 1
            mock_redis.return_value = mock_client
            
            with patch('redis.asyncio.ConnectionPool') as mock_pool:
                mock_pool_instance = Mock()
                mock_pool.return_value = mock_pool_instance
                
                redis_manager = await get_redis_manager()
                
                # Test set operation
                success = await redis_manager.set("test_key", {"test": "value"})
                assert success
                
                # Test get operation
                value = await redis_manager.get("test_key")
                assert value == {"test": "value"}
                
                # Test delete operation
                success = await redis_manager.delete("test_key")
                assert success
                
                # Test exists operation
                exists = await redis_manager.exists("test_key")
                assert exists
                
                await shutdown_redis_manager()
    
    @pytest.mark.asyncio
    async def test_redis_health_check(self):
        """Test Redis health check functionality"""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client
            
            with patch('redis.asyncio.ConnectionPool') as mock_pool:
                mock_pool_instance = Mock()
                mock_pool.return_value = mock_pool_instance
                
                redis_manager = await get_redis_manager()
                
                # Test health check
                is_healthy = await redis_manager.health_check()
                assert is_healthy
                
                await shutdown_redis_manager()


class TestDataPersistence:
    """Test data persistence across environments"""
    
    @pytest.mark.asyncio
    async def test_environment_specific_configuration(self):
        """Test that configuration switches correctly between environments"""
        # Test development environment
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
            with patch('riskintel360.services.agent_memory.RedisMemoryBackend') as mock_redis:
                mock_backend = AsyncMock()
                mock_backend.connect.return_value = True
                mock_redis.return_value = mock_backend
                
                with patch('riskintel360.services.agent_memory.InMemoryMessageQueue') as mock_queue:
                    mock_queue_instance = AsyncMock()
                    mock_queue_instance.connect.return_value = True
                    mock_queue.return_value = mock_queue_instance
                    
                    memory_manager = await get_memory_manager()
                    assert memory_manager is not None
                    
                    # Verify Redis backend was used
                    mock_redis.assert_called_once()
                    
                    await shutdown_memory_manager()
    
    @pytest.mark.asyncio
    async def test_production_configuration(self):
        """Test production environment configuration"""
        # Test production environment
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'ELASTICACHE_ENDPOINT': 'test-cluster.cache.amazonaws.com'
        }):
            with patch('riskintel360.services.agent_memory.ElastiCacheMemoryBackend') as mock_elasticache:
                mock_backend = AsyncMock()
                mock_backend.connect.return_value = True
                mock_elasticache.return_value = mock_backend
                
                with patch('riskintel360.services.agent_memory.SQSMessageQueue') as mock_sqs:
                    mock_queue_instance = AsyncMock()
                    mock_queue_instance.connect.return_value = True
                    mock_sqs.return_value = mock_queue_instance
                    
                    memory_manager = await get_memory_manager()
                    assert memory_manager is not None
                    
                    # Verify ElastiCache backend was used
                    mock_elasticache.assert_called_once()
                    
                    await shutdown_memory_manager()


class TestIntegrationScenarios:
    """Test integration scenarios between components"""
    
    @pytest.mark.asyncio
    async def test_agent_memory_with_redis(self):
        """Test agent memory system working with Redis"""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_client.set.return_value = True
            mock_client.get.return_value = None
            mock_redis.return_value = mock_client
            
            with patch('redis.asyncio.ConnectionPool') as mock_pool:
                mock_pool_instance = Mock()
                mock_pool.return_value = mock_pool_instance
                
                with patch('riskintel360.services.agent_memory.RedisMemoryBackend') as mock_memory_backend:
                    mock_backend = AsyncMock()
                    mock_backend.connect.return_value = True
                    mock_backend.store.return_value = True
                    mock_memory_backend.return_value = mock_backend
                    
                    with patch('riskintel360.services.agent_memory.InMemoryMessageQueue') as mock_queue:
                        mock_queue_instance = AsyncMock()
                        mock_queue_instance.connect.return_value = True
                        mock_queue.return_value = mock_queue_instance
                        
                        # Initialize both systems
                        redis_manager = await get_redis_manager()
                        memory_manager = await get_memory_manager()
                        
                        assert redis_manager.is_connected
                        assert memory_manager is not None
                        
                        # Test storing data through memory manager
                        entry_id = await memory_manager.store_memory(
                            agent_id="integration_test",
                            memory_type=MemoryType.SHARED,
                            scope=MemoryScope.GLOBAL_SHARED,
                            key="integration_key",
                            value={"test": "integration"}
                        )
                        
                        assert entry_id != ""
                        
                        # Cleanup
                        await shutdown_redis_manager()
                        await shutdown_memory_manager()


@pytest.mark.asyncio
async def test_get_memory_manager_import():
    """Test that get_memory_manager can be imported and called"""
    # This is the specific test mentioned in the task requirements
    try:
        from riskintel360.services.agent_memory import get_memory_manager
        
        # Mock the dependencies to avoid requiring actual Redis/SQS
        with patch('riskintel360.services.agent_memory.RedisMemoryBackend') as mock_redis:
            mock_backend = AsyncMock()
            mock_backend.connect.return_value = True
            mock_redis.return_value = mock_backend
            
            with patch('riskintel360.services.agent_memory.InMemoryMessageQueue') as mock_queue:
                mock_queue_instance = AsyncMock()
                mock_queue_instance.connect.return_value = True
                mock_queue.return_value = mock_queue_instance
                
                # This should work without errors
                memory_manager = await get_memory_manager()
                assert memory_manager is not None
                print('??Memory manager works')
                
                await shutdown_memory_manager()
        
    except ImportError as e:
        pytest.fail(f"Failed to import get_memory_manager: {e}")
    except Exception as e:
        pytest.fail(f"get_memory_manager failed: {e}")


if __name__ == "__main__":
    # Run the specific test that was mentioned in the task requirements
    asyncio.run(test_get_memory_manager_import())
