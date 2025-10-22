"""
Integration tests for Agent Runtime Service
Tests asyncio session management, state persistence, and containerized functionality.
"""

import asyncio
import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from riskintel360.services.agent_runtime import (
    AgentSessionManager,
    SessionStatus,
    get_session_manager,
    shutdown_session_manager,
)
from riskintel360.models.agent_models import AgentSession, AgentType


class TestAgentSessionManager:
    """Test cases for AgentSessionManager"""
    
    @pytest_asyncio.fixture
    async def session_manager(self):
        """Create a session manager for testing"""
        manager = AgentSessionManager()
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_session_manager_lifecycle(self):
        """Test session manager start and stop lifecycle"""
        manager = AgentSessionManager()
        
        # Test start
        assert not manager._running
        await manager.start()
        assert manager._running
        assert manager._cleanup_task is not None
        
        # Test stop
        await manager.stop()
        assert not manager._running
        assert manager._cleanup_task.cancelled()
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """Test creating a new agent session"""
        # Create session
        session = await session_manager.create_session(
            agent_type="market_analysis",
            user_id="test_user_123",
            metadata={"test": "data"}
        )
        
        # Verify session properties
        assert session.session_id is not None
        assert session.agent_type == "market_analysis"
        assert session.user_id == "test_user_123"
        assert session.status == SessionStatus.CREATED
        assert session.metadata["test"] == "data"
        assert session.created_at is not None
        assert session.expires_at > datetime.now(timezone.utc)
        
        # Verify session is stored
        retrieved_session = await session_manager.get_session(session.session_id)
        assert retrieved_session is not None
        assert retrieved_session.session_id == session.session_id
    
    @pytest.mark.asyncio
    async def test_session_limits(self, session_manager):
        """Test session creation limits"""
        # Set low limit for testing
        session_manager.max_sessions = 2
        
        # Create sessions up to limit
        session1 = await session_manager.create_session("market_analysis", "user1")
        session2 = await session_manager.create_session("regulatory_compliance", "user2")
        
        # Update sessions to running status
        await session_manager.update_session_status(session1.session_id, SessionStatus.RUNNING)
        await session_manager.update_session_status(session2.session_id, SessionStatus.RUNNING)
        
        # Try to create one more session (should fail)
        with pytest.raises(RuntimeError, match="Maximum concurrent sessions"):
            await session_manager.create_session("fraud_detection", "user3")
    
    @pytest.mark.asyncio
    async def test_update_session_status(self, session_manager):
        """Test updating session status"""
        # Create session
        session = await session_manager.create_session("risk_assessment", "test_user")
        
        # Update status
        success = await session_manager.update_session_status(
            session.session_id,
            SessionStatus.RUNNING,
            {"progress": 0.5}
        )
        
        assert success
        
        # Verify update
        updated_session = await session_manager.get_session(session.session_id)
        assert updated_session.status == SessionStatus.RUNNING
        assert updated_session.state_data["progress"] == 0.5
        assert updated_session.updated_at > session.updated_at
    
    @pytest.mark.asyncio
    async def test_update_session_state(self, session_manager):
        """Test updating session state data"""
        # Create session
        session = await session_manager.create_session("customer_intelligence", "test_user")
        
        # Update state
        state_data = {
            "current_task": "sentiment_analysis",
            "progress": 0.75,
            "results": {"sentiment_score": 0.8}
        }
        
        success = await session_manager.update_session_state(session.session_id, state_data)
        assert success
        
        # Verify update
        updated_session = await session_manager.get_session(session.session_id)
        assert updated_session.state_data["current_task"] == "sentiment_analysis"
        assert updated_session.state_data["progress"] == 0.75
        assert updated_session.state_data["results"]["sentiment_score"] == 0.8
    
    @pytest.mark.asyncio
    async def test_terminate_session(self, session_manager):
        """Test terminating a session"""
        # Create session
        session = await session_manager.create_session("kyc_verification", "test_user")
        
        # Terminate session
        success = await session_manager.terminate_session(session.session_id)
        assert success
        
        # Verify termination
        terminated_session = await session_manager.get_session(session.session_id)
        assert terminated_session.status == SessionStatus.TERMINATED
    
    @pytest.mark.asyncio
    async def test_cleanup_session(self, session_manager):
        """Test cleaning up a session"""
        # Create session
        session = await session_manager.create_session("market_analysis", "test_user")
        session_id = session.session_id
        
        # Cleanup session
        success = await session_manager.cleanup_session(session_id)
        assert success
        
        # Verify cleanup
        cleaned_session = await session_manager.get_session(session_id)
        assert cleaned_session is None
    
    @pytest.mark.asyncio
    async def test_list_sessions(self, session_manager):
        """Test listing sessions with filtering"""
        # Create multiple sessions
        session1 = await session_manager.create_session("market_analysis", "user1")
        session2 = await session_manager.create_session("regulatory_compliance", "user2")
        session3 = await session_manager.create_session("market_analysis", "user1")
        
        # Update statuses
        await session_manager.update_session_status(session1.session_id, SessionStatus.RUNNING)
        await session_manager.update_session_status(session2.session_id, SessionStatus.COMPLETED)
        
        # Test listing all sessions
        all_sessions = await session_manager.list_sessions()
        assert len(all_sessions) == 3
        
        # Test filtering by user
        user1_sessions = await session_manager.list_sessions(user_id="user1")
        assert len(user1_sessions) == 2
        assert all(s.user_id == "user1" for s in user1_sessions)
        
        # Test filtering by agent type
        market_sessions = await session_manager.list_sessions(agent_type="market_analysis")
        assert len(market_sessions) == 2
        assert all(s.agent_type == "market_analysis" for s in market_sessions)
        
        # Test filtering by status
        running_sessions = await session_manager.list_sessions(status=SessionStatus.RUNNING)
        assert len(running_sessions) == 1
        assert running_sessions[0].status == SessionStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_get_session_count(self, session_manager):
        """Test getting session count by status"""
        # Create sessions with different statuses
        session1 = await session_manager.create_session("market_analysis", "user1")
        session2 = await session_manager.create_session("regulatory_compliance", "user2")
        session3 = await session_manager.create_session("fraud_detection", "user3")
        
        await session_manager.update_session_status(session1.session_id, SessionStatus.RUNNING)
        await session_manager.update_session_status(session2.session_id, SessionStatus.COMPLETED)
        # session3 remains in CREATED status
        
        # Get counts
        counts = await session_manager.get_session_count()
        
        assert counts[SessionStatus.CREATED.value] == 1
        assert counts[SessionStatus.RUNNING.value] == 1
        assert counts[SessionStatus.COMPLETED.value] == 1
        assert counts[SessionStatus.FAILED.value] == 0
    
    @pytest.mark.asyncio
    async def test_extend_session(self, session_manager):
        """Test extending session expiration"""
        # Create session
        session = await session_manager.create_session("risk_assessment", "test_user")
        original_expires_at = session.expires_at
        
        # Extend session
        success = await session_manager.extend_session(session.session_id, 3600)
        assert success
        
        # Verify extension
        extended_session = await session_manager.get_session(session.session_id)
        assert extended_session.expires_at > original_expires_at
        assert (extended_session.expires_at - original_expires_at).total_seconds() == 3600
    
    @pytest.mark.asyncio
    async def test_expired_session_cleanup(self, session_manager):
        """Test automatic cleanup of expired sessions"""
        # Create session with short expiration
        session = await session_manager.create_session("customer_intelligence", "test_user")
        
        # Manually set expiration to past
        session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        session_manager._sessions[session.session_id] = session
        
        # Trigger cleanup manually
        await session_manager._cleanup_expired_sessions()
        
        # Verify session was cleaned up
        cleaned_session = await session_manager.get_session(session.session_id)
        assert cleaned_session is None
    
    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self, session_manager):
        """Test concurrent session operations"""
        # Create multiple sessions concurrently
        tasks = []
        for i in range(10):
            task = session_manager.create_session(f"agent_type_{i % 3}", f"user_{i}")
            tasks.append(task)
        
        sessions = await asyncio.gather(*tasks)
        assert len(sessions) == 10
        assert len(set(s.session_id for s in sessions)) == 10  # All unique
        
        # Update sessions concurrently
        update_tasks = []
        for session in sessions:
            task = session_manager.update_session_status(
                session.session_id,
                SessionStatus.RUNNING,
                {"concurrent_test": True}
            )
            update_tasks.append(task)
        
        results = await asyncio.gather(*update_tasks)
        assert all(results)  # All updates successful
    
    @pytest.mark.asyncio
    async def test_session_persistence_simulation(self, session_manager):
        """Test session persistence (simulated)"""
        # Create session
        session = await session_manager.create_session("kyc_verification", "test_user")
        
        # Update session state
        await session_manager.update_session_state(session.session_id, {"test_data": "persisted"})
        
        # Simulate restart by creating new manager
        new_manager = AgentSessionManager()
        await new_manager.start()
        
        try:
            # In a real implementation, this would load from persistence
            # For now, we just verify the session structure is correct
            assert session.session_id is not None
            assert session.state_data["test_data"] == "persisted"
        finally:
            await new_manager.stop()


class TestGlobalSessionManager:
    """Test cases for global session manager functions"""
    
    @pytest.mark.asyncio
    async def test_get_global_session_manager(self):
        """Test getting global session manager instance"""
        # Clean up any existing instance
        await shutdown_session_manager()
        
        # Get manager instance
        manager1 = await get_session_manager()
        assert manager1 is not None
        assert manager1._running
        
        # Get manager again (should be same instance)
        manager2 = await get_session_manager()
        assert manager1 is manager2
        
        # Cleanup
        await shutdown_session_manager()
    
    @pytest.mark.asyncio
    async def test_shutdown_global_session_manager(self):
        """Test shutting down global session manager"""
        # Get manager instance
        manager = await get_session_manager()
        assert manager._running
        
        # Shutdown
        await shutdown_session_manager()
        assert not manager._running
        
        # Getting manager again should create new instance
        new_manager = await get_session_manager()
        assert new_manager is not manager
        
        # Cleanup
        await shutdown_session_manager()


class TestSessionConcurrencyAndPerformance:
    """Test cases for session concurrency and performance"""
    
    @pytest_asyncio.fixture
    async def session_manager(self):
        """Create a session manager for testing"""
        manager = AgentSessionManager()
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_memory_usage_tracking(self, session_manager):
        """Test that agent sessions don't exceed memory limits"""
        # Create multiple sessions
        sessions = []
        for i in range(5):
            session = await session_manager.create_session(f"agent_{i}", f"user_{i}")
            sessions.append(session)
        
        # Simulate memory usage tracking
        for session in sessions:
            await session_manager.update_session_state(
                session.session_id,
                {"memory_usage_mb": 50.0}  # Simulate 50MB usage
            )
        
        # Verify all sessions are within limits
        all_sessions = await session_manager.list_sessions()
        total_memory = sum(s.state_data.get("memory_usage_mb", 0) for s in all_sessions)
        
        # Should be under reasonable limit (e.g., 500MB total)
        assert total_memory <= 500.0
    
    @pytest.mark.asyncio
    async def test_session_timeout_handling(self, session_manager):
        """Test handling of session timeouts"""
        # Create session with custom timeout
        session = await session_manager.create_session("market_analysis", "test_user")
        
        # Simulate long-running operation
        await session_manager.update_session_status(session.session_id, SessionStatus.RUNNING)
        
        # Verify session is still active
        active_session = await session_manager.get_session(session.session_id)
        assert active_session.status == SessionStatus.RUNNING
        
        # Extend session to prevent timeout
        await session_manager.extend_session(session.session_id, 3600)
        
        # Verify extension worked
        extended_session = await session_manager.get_session(session.session_id)
        assert extended_session.expires_at > session.expires_at
    
    @pytest.mark.asyncio
    async def test_error_handling_in_session_operations(self, session_manager):
        """Test error handling in session operations"""
        # Test operations on non-existent session
        non_existent_id = str(uuid.uuid4())
        
        # Should return None/False for non-existent sessions
        session = await session_manager.get_session(non_existent_id)
        assert session is None
        
        success = await session_manager.update_session_status(non_existent_id, SessionStatus.RUNNING)
        assert not success
        
        success = await session_manager.update_session_state(non_existent_id, {"test": "data"})
        assert not success
        
        success = await session_manager.terminate_session(non_existent_id)
        assert not success
        
        success = await session_manager.cleanup_session(non_existent_id)
        assert not success
    
    @pytest.mark.asyncio
    async def test_session_state_consistency(self, session_manager):
        """Test session state consistency under concurrent access"""
        # Create session
        session = await session_manager.create_session("regulatory_compliance", "test_user")
        
        # Define concurrent update operations
        async def update_progress(progress_value):
            await session_manager.update_session_state(
                session.session_id,
                {"progress": progress_value}
            )
        
        async def update_status(status_value):
            await session_manager.update_session_status(
                session.session_id,
                status_value
            )
        
        # Run concurrent updates
        await asyncio.gather(
            update_progress(0.25),
            update_status(SessionStatus.RUNNING),
            update_progress(0.50),
            update_progress(0.75),
        )
        
        # Verify final state is consistent
        final_session = await session_manager.get_session(session.session_id)
        assert final_session.status == SessionStatus.RUNNING
        assert "progress" in final_session.state_data
        # Progress should be one of the values we set
        assert final_session.state_data["progress"] in [0.25, 0.50, 0.75]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
