"""
Unit tests for Agent Memory System
Tests memory storage, retrieval, learning functionality, and cross-agent knowledge sharing.
"""

import pytest
import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from riskintel360.services.agent_memory import (
    AgentMemoryManager,
    MemoryType,
    MemoryScope,
    MemoryEntry,
    ValidationPattern,
    RedisMemoryBackend,
    ElastiCacheMemoryBackend,
    InMemoryMessageQueue,
    SQSMessageQueue,
    create_memory_manager
)
from riskintel360.models.core import (
    ValidationRequest,
    ValidationResult,
    Priority,
    MarketAnalysisResult,
    FinancialAnalysisResult
)


class TestMemoryEntry:
    """Test MemoryEntry data model"""
    
    def test_memory_entry_creation(self):
        """Test memory entry creation and serialization"""
        now = datetime.now(timezone.utc)
        entry = MemoryEntry(
            id="test-id",
            agent_id="test-agent",
            memory_type=MemoryType.SHORT_TERM,
            scope=MemoryScope.AGENT_PRIVATE,
            key="test-key",
            value={"data": "test"},
            metadata={"source": "test"},
            created_at=now,
            updated_at=now,
            confidence_score=0.8
        )
        
        assert entry.id == "test-id"
        assert entry.agent_id == "test-agent"
        assert entry.memory_type == MemoryType.SHORT_TERM
        assert entry.scope == MemoryScope.AGENT_PRIVATE
        assert entry.confidence_score == 0.8
    
    def test_memory_entry_serialization(self):
        """Test memory entry to_dict and from_dict"""
        now = datetime.now(timezone.utc)
        entry = MemoryEntry(
            id="test-id",
            agent_id="test-agent",
            memory_type=MemoryType.LONG_TERM,
            scope=MemoryScope.GLOBAL_SHARED,
            key="test-key",
            value={"data": "test"},
            metadata={"source": "test"},
            created_at=now,
            updated_at=now
        )
        
        # Test serialization
        data = entry.to_dict()
        assert data["id"] == "test-id"
        assert data["memory_type"] == "long_term"
        assert data["scope"] == "global_shared"
        
        # Test deserialization
        restored_entry = MemoryEntry.from_dict(data)
        assert restored_entry.id == entry.id
        assert restored_entry.memory_type == entry.memory_type
        assert restored_entry.scope == entry.scope


class TestValidationPattern:
    """Test ValidationPattern data model"""
    
    def test_validation_pattern_creation(self):
        """Test validation pattern creation"""
        now = datetime.now(timezone.utc)
        pattern = ValidationPattern(
            pattern_id="pattern-1",
            business_concept_hash="abc123",
            target_market="fintech",
            analysis_results={"score": 85},
            success_indicators=["high_market_demand"],
            failure_indicators=["regulatory_barriers"],
            confidence_score=0.9,
            usage_count=5,
            created_at=now,
            last_used=now
        )
        
        assert pattern.pattern_id == "pattern-1"
        assert pattern.confidence_score == 0.9
        assert pattern.usage_count == 5
    
    def test_validation_pattern_serialization(self):
        """Test validation pattern serialization"""
        now = datetime.now(timezone.utc)
        pattern = ValidationPattern(
            pattern_id="pattern-1",
            business_concept_hash="abc123",
            target_market="fintech",
            analysis_results={"score": 85},
            success_indicators=["high_market_demand"],
            failure_indicators=["regulatory_barriers"],
            confidence_score=0.9,
            usage_count=5,
            created_at=now,
            last_used=now
        )
        
        # Test serialization
        data = pattern.to_dict()
        assert data["pattern_id"] == "pattern-1"
        assert data["confidence_score"] == 0.9
        
        # Test deserialization
        restored_pattern = ValidationPattern.from_dict(data)
        assert restored_pattern.pattern_id == pattern.pattern_id
        assert restored_pattern.confidence_score == pattern.confidence_score


class TestRedisMemoryBackend:
    """Test Redis memory backend"""
    
    @pytest.fixture
    def redis_backend(self):
        """Create Redis backend for testing"""
        return RedisMemoryBackend(host="localhost", port=6379, db=1)
    
    @pytest.mark.asyncio
    async def test_redis_connection_success(self, redis_backend):
        """Test successful Redis connection"""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.ping.return_value = True
            
            success = await redis_backend.connect()
            assert success is True
            mock_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure(self, redis_backend):
        """Test Redis connection failure"""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.ping.side_effect = Exception("Connection failed")
            
            success = await redis_backend.connect()
            assert success is False
    
    @pytest.mark.asyncio
    async def test_redis_store_retrieve(self, redis_backend):
        """Test Redis store and retrieve operations"""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            redis_backend.client = mock_client
            
            test_data = {"key": "value", "number": 42}
            
            # Test store
            mock_client.set.return_value = True
            success = await redis_backend.store("test-key", test_data)
            assert success is True
            mock_client.set.assert_called_once()
            
            # Test retrieve
            mock_client.get.return_value = json.dumps(test_data)
            result = await redis_backend.retrieve("test-key")
            assert result == test_data
    
    @pytest.mark.asyncio
    async def test_redis_store_with_ttl(self, redis_backend):
        """Test Redis store with TTL"""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            redis_backend.client = mock_client
            
            test_data = {"key": "value"}
            
            # Test store with TTL
            mock_client.setex.return_value = True
            success = await redis_backend.store("test-key", test_data, ttl=3600)
            assert success is True
            mock_client.setex.assert_called_once_with("test-key", 3600, json.dumps(test_data, default=str))
    
    @pytest.mark.asyncio
    async def test_redis_delete_exists(self, redis_backend):
        """Test Redis delete and exists operations"""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            redis_backend.client = mock_client
            
            # Test delete
            mock_client.delete.return_value = 1
            success = await redis_backend.delete("test-key")
            assert success is True
            
            # Test exists
            mock_client.exists.return_value = 1
            exists = await redis_backend.exists("test-key")
            assert exists is True
    
    @pytest.mark.asyncio
    async def test_redis_keys_pattern(self, redis_backend):
        """Test Redis keys pattern matching"""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            redis_backend.client = mock_client
            
            mock_client.keys.return_value = ["key1", "key2", "key3"]
            keys = await redis_backend.keys("test-*")
            assert keys == ["key1", "key2", "key3"]


class TestInMemoryMessageQueue:
    """Test in-memory message queue"""
    
    @pytest.fixture
    def message_queue(self):
        """Create in-memory message queue for testing"""
        return InMemoryMessageQueue()
    
    @pytest.mark.asyncio
    async def test_message_queue_connect(self, message_queue):
        """Test message queue connection"""
        success = await message_queue.connect()
        assert success is True
    
    @pytest.mark.asyncio
    async def test_send_receive_message(self, message_queue):
        """Test sending and receiving messages"""
        await message_queue.connect()
        
        test_message = {"type": "test", "data": "hello"}
        
        # Send message
        success = await message_queue.send_message(test_message)
        assert success is True
        
        # Receive message
        messages = await message_queue.receive_messages(max_messages=1, wait_time=1)
        assert len(messages) == 1
        assert messages[0]["body"] == test_message
    
    @pytest.mark.asyncio
    async def test_delayed_message(self, message_queue):
        """Test delayed message sending"""
        await message_queue.connect()
        
        test_message = {"type": "delayed", "data": "delayed_hello"}
        
        # Send delayed message (short delay for testing)
        success = await message_queue.send_message(test_message, delay_seconds=0.1)
        assert success is True
        
        # Should not receive immediately
        messages = await message_queue.receive_messages(max_messages=1, wait_time=0.05)
        assert len(messages) == 0
        
        # Should receive after delay
        await asyncio.sleep(0.2)
        messages = await message_queue.receive_messages(max_messages=1, wait_time=0.1)
        assert len(messages) == 1


class TestAgentMemoryManager:
    """Test Agent Memory Manager"""
    
    @pytest.fixture
    def memory_manager(self):
        """Create memory manager for testing"""
        return AgentMemoryManager()
    
    @pytest.fixture
    def mock_backend(self):
        """Create mock memory backend"""
        backend = AsyncMock()
        backend.connect.return_value = True
        backend.store.return_value = True
        backend.retrieve.return_value = None
        backend.delete.return_value = True
        backend.exists.return_value = False
        backend.keys.return_value = []
        return backend
    
    @pytest.fixture
    def mock_message_queue(self):
        """Create mock message queue"""
        queue = AsyncMock()
        queue.connect.return_value = True
        queue.send_message.return_value = True
        queue.receive_messages.return_value = []
        return queue
    
    @pytest.mark.asyncio
    async def test_memory_manager_initialization_development(self, memory_manager):
        """Test memory manager initialization in development environment"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            with patch('riskintel360.services.agent_memory.RedisMemoryBackend') as mock_redis:
                with patch('riskintel360.services.agent_memory.InMemoryMessageQueue') as mock_queue:
                    with patch.object(memory_manager, 'settings') as mock_settings:
                        mock_settings.environment.value = "development"
                        
                        mock_backend = AsyncMock()
                        mock_backend.connect.return_value = True
                        mock_redis.return_value = mock_backend
                        
                        mock_msg_queue = AsyncMock()
                        mock_msg_queue.connect.return_value = True
                        mock_queue.return_value = mock_msg_queue
                        
                        # Mock background tasks
                        memory_manager._load_validation_patterns = AsyncMock()
                        memory_manager._start_background_tasks = AsyncMock()
                        
                        success = await memory_manager.initialize()
                        assert success is True
                        assert isinstance(memory_manager.backend, type(mock_backend))
    
    @pytest.mark.asyncio
    async def test_memory_manager_initialization_production(self, memory_manager):
        """Test memory manager initialization in production environment"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "ELASTICACHE_ENDPOINT": "test-cluster.cache.amazonaws.com"
        }):
            with patch('riskintel360.services.agent_memory.ElastiCacheMemoryBackend') as mock_elasticache:
                with patch('riskintel360.services.agent_memory.SQSMessageQueue') as mock_sqs:
                    with patch.object(memory_manager, 'settings') as mock_settings:
                        mock_settings.environment.value = "production"
                        
                        mock_backend = AsyncMock()
                        mock_backend.connect.return_value = True
                        mock_elasticache.return_value = mock_backend
                        
                        mock_msg_queue = AsyncMock()
                        mock_msg_queue.connect.return_value = True
                        mock_sqs.return_value = mock_msg_queue
                        
                        # Mock background tasks
                        memory_manager._load_validation_patterns = AsyncMock()
                        memory_manager._start_background_tasks = AsyncMock()
                        
                        success = await memory_manager.initialize()
                        assert success is True
    
    @pytest.mark.asyncio
    async def test_store_memory(self, memory_manager, mock_backend, mock_message_queue):
        """Test storing memory entries"""
        memory_manager.backend = mock_backend
        memory_manager.message_queue = mock_message_queue
        
        entry_id = await memory_manager.store_memory(
            agent_id="test-agent",
            memory_type=MemoryType.SHORT_TERM,
            scope=MemoryScope.AGENT_PRIVATE,
            key="test-key",
            value={"data": "test"},
            metadata={"source": "test"},
            confidence_score=0.8
        )
        
        assert entry_id != ""
        mock_backend.store.assert_called_once()
        assert memory_manager.stats["entries_stored"] == 1
    
    @pytest.mark.asyncio
    async def test_retrieve_memory_cache_hit(self, memory_manager, mock_backend):
        """Test retrieving memory from cache"""
        memory_manager.backend = mock_backend
        
        # Add entry to cache
        now = datetime.now(timezone.utc)
        entry = MemoryEntry(
            id="test-id",
            agent_id="test-agent",
            memory_type=MemoryType.SHORT_TERM,
            scope=MemoryScope.AGENT_PRIVATE,
            key="test-key",
            value={"data": "test"},
            metadata={},
            created_at=now,
            updated_at=now
        )
        
        storage_key = memory_manager._generate_storage_key(
            "test-agent", MemoryType.SHORT_TERM, MemoryScope.AGENT_PRIVATE, "test-key"
        )
        memory_manager.memory_cache[storage_key] = entry
        
        # Retrieve from cache
        retrieved_entry = await memory_manager.retrieve_memory(
            agent_id="test-agent",
            memory_type=MemoryType.SHORT_TERM,
            scope=MemoryScope.AGENT_PRIVATE,
            key="test-key"
        )
        
        assert retrieved_entry is not None
        assert retrieved_entry.id == "test-id"
        assert retrieved_entry.access_count == 1
        assert memory_manager.stats["cache_hits"] == 1
    
    @pytest.mark.asyncio
    async def test_retrieve_memory_cache_miss(self, memory_manager, mock_backend):
        """Test retrieving memory from backend (cache miss)"""
        memory_manager.backend = mock_backend
        
        # Mock backend return
        now = datetime.now(timezone.utc)
        entry_data = {
            "id": "test-id",
            "agent_id": "test-agent",
            "memory_type": "short_term",
            "scope": "agent_private",
            "key": "test-key",
            "value": {"data": "test"},
            "metadata": {},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "expires_at": None,
            "access_count": 0,
            "confidence_score": 1.0
        }
        mock_backend.retrieve.return_value = entry_data
        
        # Retrieve from backend
        retrieved_entry = await memory_manager.retrieve_memory(
            agent_id="test-agent",
            memory_type=MemoryType.SHORT_TERM,
            scope=MemoryScope.AGENT_PRIVATE,
            key="test-key"
        )
        
        assert retrieved_entry is not None
        assert retrieved_entry.id == "test-id"
        assert retrieved_entry.access_count == 1
        assert memory_manager.stats["cache_misses"] == 1
    
    @pytest.mark.asyncio
    async def test_search_memories(self, memory_manager, mock_backend):
        """Test searching for memory entries"""
        memory_manager.backend = mock_backend
        
        # Mock backend keys and retrieve
        mock_backend.keys.return_value = ["memory:test-agent:short_term:agent_private:key1"]
        
        now = datetime.now(timezone.utc)
        entry_data = {
            "id": "test-id",
            "agent_id": "test-agent",
            "memory_type": "short_term",
            "scope": "agent_private",
            "key": "key1",
            "value": {"data": "test"},
            "metadata": {},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "expires_at": None,
            "access_count": 0,
            "confidence_score": 1.0
        }
        mock_backend.retrieve.return_value = entry_data
        
        # Search memories
        entries = await memory_manager.search_memories(
            agent_id="test-agent",
            memory_type=MemoryType.SHORT_TERM,
            scope=MemoryScope.AGENT_PRIVATE,
            pattern="key*"
        )
        
        assert len(entries) == 1
        assert entries[0].id == "test-id"
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_manager, mock_backend):
        """Test deleting memory entries"""
        memory_manager.backend = mock_backend
        
        # Add entry to cache
        storage_key = memory_manager._generate_storage_key(
            "test-agent", MemoryType.SHORT_TERM, MemoryScope.AGENT_PRIVATE, "test-key"
        )
        memory_manager.memory_cache[storage_key] = Mock()
        
        # Delete memory
        success = await memory_manager.delete_memory(
            agent_id="test-agent",
            memory_type=MemoryType.SHORT_TERM,
            scope=MemoryScope.AGENT_PRIVATE,
            key="test-key"
        )
        
        assert success is True
        mock_backend.delete.assert_called_once()
        assert storage_key not in memory_manager.memory_cache
    
    @pytest.mark.asyncio
    async def test_learn_validation_pattern(self, memory_manager, mock_backend, mock_message_queue):
        """Test learning validation patterns"""
        memory_manager.backend = mock_backend
        memory_manager.message_queue = mock_message_queue
        
        # Create test validation request and result
        validation_request = ValidationRequest(
            user_id="test-user",
            business_concept="AI-powered fintech solution",
            target_market="financial services"
        )
        
        market_analysis = MarketAnalysisResult(confidence_score=0.8)
        financial_analysis = FinancialAnalysisResult(viability_score=0.9, confidence_score=0.85)
        
        validation_result = ValidationResult(
            request_id=validation_request.id,
            overall_score=85.0,
            confidence_level=0.8,
            market_analysis=market_analysis,
            financial_analysis=financial_analysis,
            data_quality_score=0.9,
            analysis_completeness=0.95
        )
        
        # Learn pattern
        pattern_id = await memory_manager.learn_validation_pattern(
            validation_request, validation_result
        )
        
        assert pattern_id != ""
        assert len(memory_manager.validation_patterns) == 1
        assert memory_manager.stats["patterns_learned"] == 1
        mock_backend.store.assert_called()
    
    @pytest.mark.asyncio
    async def test_find_similar_patterns(self, memory_manager):
        """Test finding similar validation patterns"""
        # Add test patterns
        now = datetime.now(timezone.utc)
        pattern1 = ValidationPattern(
            pattern_id="pattern-1",
            business_concept_hash="abc123",
            target_market="fintech",
            analysis_results={"score": 85},
            success_indicators=["high_demand"],
            failure_indicators=[],
            confidence_score=0.9,
            usage_count=5,
            created_at=now,
            last_used=now
        )
        
        pattern2 = ValidationPattern(
            pattern_id="pattern-2",
            business_concept_hash="def456",
            target_market="fintech",
            analysis_results={"score": 75},
            success_indicators=["market_ready"],
            failure_indicators=[],
            confidence_score=0.8,
            usage_count=3,
            created_at=now,
            last_used=now
        )
        
        memory_manager.validation_patterns = {
            "pattern-1": pattern1,
            "pattern-2": pattern2
        }
        
        # Find similar patterns
        similar_patterns = await memory_manager.find_similar_patterns(
            business_concept="AI fintech solution",
            target_market="fintech"
        )
        
        assert len(similar_patterns) == 2
        # Should be sorted by confidence and usage
        assert similar_patterns[0].pattern_id == "pattern-1"
    
    @pytest.mark.asyncio
    async def test_apply_pattern_insights(self, memory_manager):
        """Test applying pattern insights"""
        # Create test pattern
        now = datetime.now(timezone.utc)
        pattern = ValidationPattern(
            pattern_id="pattern-1",
            business_concept_hash="abc123",
            target_market="fintech",
            analysis_results={"overall_score": 85, "confidence_level": 0.8},
            success_indicators=["high_demand", "low_competition"],
            failure_indicators=["regulatory_risk"],
            confidence_score=0.9,
            usage_count=5,
            created_at=now,
            last_used=now
        )
        
        validation_request = ValidationRequest(
            user_id="test-user",
            business_concept="Similar fintech solution",
            target_market="fintech"
        )
        
        # Apply insights
        insights = await memory_manager.apply_pattern_insights(pattern, validation_request)
        
        assert insights["pattern_id"] == "pattern-1"
        assert insights["confidence_score"] == 0.9
        assert len(insights["recommendations"]) >= 1
        assert pattern.usage_count == 6  # Should increment
        assert memory_manager.stats["patterns_applied"] == 1
    
    @pytest.mark.asyncio
    async def test_share_knowledge(self, memory_manager, mock_message_queue):
        """Test sharing knowledge between agents"""
        memory_manager.message_queue = mock_message_queue
        
        knowledge_data = {
            "insight": "Market shows strong demand",
            "confidence": 0.8
        }
        
        success = await memory_manager.share_knowledge(
            sender_agent_id="market-research-agent",
            knowledge_type="market_insight",
            knowledge_data=knowledge_data,
            target_agents=["financial-validation-agent"]
        )
        
        assert success is True
        mock_message_queue.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_receive_shared_knowledge(self, memory_manager, mock_message_queue):
        """Test receiving shared knowledge"""
        memory_manager.message_queue = mock_message_queue
        
        # Mock received messages
        mock_messages = [
            {
                "id": "msg-1",
                "receipt_handle": "handle-1",
                "body": {
                    "type": "knowledge_sharing",
                    "sender_agent_id": "market-research-agent",
                    "knowledge_type": "market_insight",
                    "knowledge_data": {"insight": "Strong demand"},
                    "target_agents": ["financial-validation-agent"]
                }
            }
        ]
        mock_message_queue.receive_messages.return_value = mock_messages
        
        # Receive knowledge
        knowledge_messages = await memory_manager.receive_shared_knowledge("financial-validation-agent")
        
        assert len(knowledge_messages) == 1
        assert knowledge_messages[0]["knowledge_type"] == "market_insight"
        mock_message_queue.delete_message.assert_called_once_with("handle-1")
    
    def test_get_memory_stats(self, memory_manager):
        """Test getting memory statistics"""
        # Set some test stats
        memory_manager.stats["entries_stored"] = 10
        memory_manager.stats["cache_hits"] = 8
        memory_manager.stats["cache_misses"] = 2
        memory_manager.validation_patterns = {"p1": Mock(), "p2": Mock()}
        
        stats = memory_manager.get_memory_stats()
        
        assert stats["entries_stored"] == 10
        assert stats["validation_patterns"] == 2
        assert stats["cache_hit_rate"] == 80.0
    
    def test_generate_storage_key(self, memory_manager):
        """Test storage key generation"""
        key = memory_manager._generate_storage_key(
            agent_id="test-agent",
            memory_type=MemoryType.SHORT_TERM,
            scope=MemoryScope.AGENT_PRIVATE,
            key="test-key"
        )
        
        expected = "memory:test-agent:short_term:agent_private:test-key"
        assert key == expected


class TestMemorySystemIntegration:
    """Integration tests for memory system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_memory_workflow(self):
        """Test complete memory workflow"""
        # Create memory manager
        memory_manager = AgentMemoryManager()
        
        # Mock dependencies
        mock_backend = AsyncMock()
        mock_backend.connect.return_value = True
        mock_backend.store.return_value = True
        mock_backend.retrieve.return_value = None
        
        mock_queue = AsyncMock()
        mock_queue.connect.return_value = True
        mock_queue.send_message.return_value = True
        
        memory_manager.backend = mock_backend
        memory_manager.message_queue = mock_queue
        memory_manager._load_validation_patterns = AsyncMock()
        memory_manager._start_background_tasks = AsyncMock()
        
        # Mock the initialize method to avoid actual backend connections
        with patch.object(memory_manager, 'initialize', return_value=True):
            success = await memory_manager.initialize()
            assert success is True
        
        # Store memory
        entry_id = await memory_manager.store_memory(
            agent_id="test-agent",
            memory_type=MemoryType.LONG_TERM,
            scope=MemoryScope.GLOBAL_SHARED,
            key="market-insight",
            value={"trend": "growing", "confidence": 0.8},
            metadata={"source": "market-research"}
        )
        
        assert entry_id != ""
        
        # Share knowledge
        success = await memory_manager.share_knowledge(
            sender_agent_id="test-agent",
            knowledge_type="market_trend",
            knowledge_data={"trend": "growing"}
        )
        
        assert success is True
        
        # Shutdown
        await memory_manager.shutdown()


def test_create_memory_manager():
    """Test memory manager factory function"""
    manager = create_memory_manager()
    assert isinstance(manager, AgentMemoryManager)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
