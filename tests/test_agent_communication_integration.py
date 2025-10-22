"""
Integration tests for agent communication system fixes.
Tests the specific issues that were fixed in Task 38.
"""

import pytest
import asyncio
from datetime import datetime, UTC, timedelta
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

from riskintel360.services.agentcore_client import create_agentcore_client
from riskintel360.services.agent_communication import (
    AgentCommunicationManager, CommunicationProtocol, MessageStatus,
    create_communication_manager
)
from riskintel360.models.agent_models import (
    AgentMessage, MessageType, Priority, AgentType
)


class TestAgentCommunicationFixes:
    """Test the specific fixes implemented in Task 38"""
    
    @pytest.fixture
    def agentcore_client(self):
        """Create AgentCore client for testing"""
        return create_agentcore_client(region_name="us-east-1")
    
    @pytest.fixture
    def communication_manager(self, agentcore_client):
        """Create communication manager with short intervals for testing"""
        return create_communication_manager(
            agentcore_client, 
            cleanup_interval=1,  # 1 second for testing
            message_process_interval=0.05  # 50ms for testing
        )
    
    @pytest.mark.asyncio
    async def test_lifecycle_management_fix(self, communication_manager):
        """Test that lifecycle management properly cancels and waits for tasks"""
        # Start communication manager
        await communication_manager.start()
        
        # Verify background tasks are running
        assert communication_manager._cleanup_task is not None
        assert communication_manager._message_processor_task is not None
        assert not communication_manager._cleanup_task.done()
        assert not communication_manager._message_processor_task.done()
        
        # Stop communication manager
        await communication_manager.stop()
        
        # Verify tasks are properly cancelled and completed
        assert communication_manager._cleanup_task.cancelled() or communication_manager._cleanup_task.done()
        assert communication_manager._message_processor_task.cancelled() or communication_manager._message_processor_task.done()
    
    @pytest.mark.asyncio
    async def test_message_type_enum_serialization_fix(self, communication_manager):
        """Test that message type enums are properly serialized and compared"""
        await communication_manager.start()
        
        try:
            # Register agents
            sender_id = "test_sender"
            recipient_id = "test_recipient"
            
            communication_manager.register_agent(sender_id, AgentType.SUPERVISOR)
            communication_manager.register_agent(recipient_id, AgentType.MARKET_ANALYSIS)
            
            # Send message with enum type
            message_id = await communication_manager.send_message(
                sender_id=sender_id,
                recipient_id=recipient_id,
                message_type=MessageType.TASK_ASSIGNMENT,  # Enum object
                content={"task": "test_enum_serialization"},
                priority=Priority.HIGH  # Enum object
            )
            
            assert message_id is not None
            
            # Get messages and verify enum comparison works
            messages = await communication_manager.get_messages(recipient_id, timeout=0.5)
            assert len(messages) == 1
            
            message = messages[0]
            # This should work now (was failing before the fix)
            assert message.message_type == MessageType.TASK_ASSIGNMENT
            assert message.priority == Priority.HIGH
            
            # Test that enum values are preserved as enum objects, not strings
            assert isinstance(message.message_type, MessageType)
            assert isinstance(message.priority, Priority)
            
        finally:
            await communication_manager.stop()
    
    @pytest.mark.asyncio
    async def test_message_serialization_consistency_fix(self, communication_manager):
        """Test that message serialization/deserialization is consistent"""
        await communication_manager.start()
        
        try:
            # Create a custom message handler to capture serialized data
            received_messages = []
            
            async def test_handler(message_data: Dict[str, Any]):
                received_messages.append(message_data)
            
            # Register agents with custom handler
            sender_id = "serialization_sender"
            recipient_id = "serialization_recipient"
            
            communication_manager.register_agent(sender_id, AgentType.SUPERVISOR)
            communication_manager.register_agent(recipient_id, AgentType.MARKET_ANALYSIS, test_handler)
            
            # Send message
            test_content = {
                "task_type": "serialization_test",
                "parameters": {"test_param": "test_value"},
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            message_id = await communication_manager.send_message(
                sender_id=sender_id,
                recipient_id=recipient_id,
                message_type=MessageType.DATA_SHARING,
                content=test_content,
                priority=Priority.MEDIUM
            )
            
            # Get messages to trigger handler execution
            messages = await communication_manager.get_messages(recipient_id, timeout=0.5)
            
            # Wait a bit for handler to be called
            await asyncio.sleep(0.1)
            
            # Verify message was processed by handler (might be called twice due to AgentCore)
            assert len(received_messages) >= 1
            assert len(messages) == 1
            
            # Use the first message for testing
            serialized_message = received_messages[0]
            
            # Verify serialization format
            assert "message_id" in serialized_message
            assert "sender_id" in serialized_message
            assert "recipient_id" in serialized_message
            assert "message_type" in serialized_message
            assert "content" in serialized_message
            assert "priority" in serialized_message
            
            # Verify enum values are properly serialized
            assert serialized_message["message_type"] == MessageType.DATA_SHARING.value
            assert serialized_message["priority"] == Priority.MEDIUM.value
            
            # Verify content is preserved
            assert serialized_message["content"] == test_content
            
        finally:
            await communication_manager.stop()
    
    @pytest.mark.asyncio
    async def test_async_task_cleanup_fix(self, communication_manager):
        """Test that async tasks are properly cleaned up without hanging"""
        # Start and stop multiple times to test cleanup
        for i in range(3):
            await communication_manager.start()
            
            # Register some agents to create activity
            agent_id = f"cleanup_test_agent_{i}"
            communication_manager.register_agent(agent_id, AgentType.MARKET_ANALYSIS)
            
            # Send a message to create some activity
            await communication_manager.send_message(
                sender_id=agent_id,
                recipient_id=agent_id,
                message_type=MessageType.STATUS_UPDATE,
                content={"status": f"test_iteration_{i}"}
            )
            
            # Stop should complete quickly without hanging
            start_time = asyncio.get_event_loop().time()
            await communication_manager.stop()
            stop_time = asyncio.get_event_loop().time()
            
            # Should complete within 2 seconds (was hanging before the fix)
            assert (stop_time - start_time) < 2.0
    
    @pytest.mark.asyncio
    async def test_message_routing_reliability_fix(self, communication_manager):
        """Test that message routing works reliably without race conditions"""
        await communication_manager.start()
        
        try:
            # Register multiple agents
            agents = [f"reliable_agent_{i}" for i in range(5)]
            for agent_id in agents:
                communication_manager.register_agent(agent_id, AgentType.MARKET_ANALYSIS)
            
            # Send multiple messages concurrently
            message_tasks = []
            for i in range(10):
                sender = agents[i % len(agents)]
                recipient = agents[(i + 1) % len(agents)]
                
                task = communication_manager.send_message(
                    sender_id=sender,
                    recipient_id=recipient,
                    message_type=MessageType.DATA_SHARING,
                    content={"message_number": i, "test": "reliability"}
                )
                message_tasks.append(task)
            
            # Wait for all messages to be sent
            message_ids = await asyncio.gather(*message_tasks)
            
            # Verify all messages were sent successfully
            assert len(message_ids) == 10
            assert all(msg_id is not None for msg_id in message_ids)
            
            # Wait for message processing
            await asyncio.sleep(0.5)
            
            # Verify messages were delivered
            total_messages_received = 0
            for agent_id in agents:
                messages = await communication_manager.get_messages(agent_id, timeout=0.1)
                total_messages_received += len(messages)
            
            # Should have received all messages
            assert total_messages_received == 10
            
        finally:
            await communication_manager.stop()
    
    @pytest.mark.asyncio
    async def test_performance_improvement_fix(self, communication_manager):
        """Test that performance improvements are working (shorter intervals)"""
        # Verify that the communication manager uses the configured short intervals
        assert communication_manager.cleanup_interval == 1  # 1 second
        assert communication_manager.message_process_interval == 0.05  # 50ms
        
        await communication_manager.start()
        
        try:
            # Register agent
            agent_id = "performance_test_agent"
            communication_manager.register_agent(agent_id, AgentType.MARKET_ANALYSIS)
            
            # Send message and measure response time
            start_time = asyncio.get_event_loop().time()
            
            message_id = await communication_manager.send_message(
                sender_id=agent_id,
                recipient_id=agent_id,
                message_type=MessageType.STATUS_UPDATE,
                content={"performance_test": True}
            )
            
            # Get message (should be fast due to short processing interval)
            messages = await communication_manager.get_messages(agent_id, timeout=0.2)
            
            end_time = asyncio.get_event_loop().time()
            
            # Should complete quickly
            assert (end_time - start_time) < 1.0
            assert len(messages) == 1
            assert messages[0].content["performance_test"] is True
            
        finally:
            await communication_manager.stop()


class TestIntegrationReliability:
    """Test overall integration reliability after fixes"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_communication_reliability(self):
        """Test complete end-to-end communication workflow"""
        agentcore_client = create_agentcore_client(region_name="us-east-1")
        comm_manager = create_communication_manager(
            agentcore_client,
            cleanup_interval=1,
            message_process_interval=0.05
        )
        
        await comm_manager.start()
        
        try:
            # Simulate a realistic multi-agent workflow
            agents = {
                "supervisor": AgentType.SUPERVISOR,
                "MARKET_ANALYSIS": AgentType.MARKET_ANALYSIS,
                "regulatory_compliance": AgentType.REGULATORY_COMPLIANCE,
                "FRAUD_DETECTION": AgentType.FRAUD_DETECTION
            }
            
            # Register all agents
            for agent_id, agent_type in agents.items():
                success = comm_manager.register_agent(agent_id, agent_type)
                assert success
            
            # Supervisor assigns tasks to agents
            task_assignments = [
                ("supervisor", "MARKET_ANALYSIS", MessageType.TASK_ASSIGNMENT, {"task": "analyze_market"}),
                ("supervisor", "regulatory_compliance", MessageType.TASK_ASSIGNMENT, {"task": "analyze_competitors"}),
                ("supervisor", "FRAUD_DETECTION", MessageType.TASK_ASSIGNMENT, {"task": "validate_financials"})
            ]
            
            # Send task assignments
            for sender, recipient, msg_type, content in task_assignments:
                message_id = await comm_manager.send_message(
                    sender_id=sender,
                    recipient_id=recipient,
                    message_type=msg_type,
                    content=content,
                    priority=Priority.HIGH
                )
                assert message_id is not None
            
            # Agents share data with each other
            data_sharing = [
                ("MARKET_ANALYSIS", "regulatory_compliance", {"market_data": "growth_trends"}),
                ("regulatory_compliance", "FRAUD_DETECTION", {"competitor_data": "pricing_analysis"}),
                ("FRAUD_DETECTION", "supervisor", {"financial_results": "validation_complete"})
            ]
            
            for sender, recipient, content in data_sharing:
                message_id = await comm_manager.send_message(
                    sender_id=sender,
                    recipient_id=recipient,
                    message_type=MessageType.DATA_SHARING,
                    content=content,
                    priority=Priority.MEDIUM
                )
                assert message_id is not None
            
            # Wait for all messages to be processed
            await asyncio.sleep(0.5)
            
            # Verify all agents received their messages
            for agent_id in agents.keys():
                messages = await comm_manager.get_messages(agent_id, timeout=0.1)
                # Each agent should have received at least one message
                if agent_id != "supervisor":  # Supervisor sends but also receives final result
                    assert len(messages) >= 1
            
            # Verify communication statistics
            stats = comm_manager.get_communication_stats()
            assert stats["messages_sent"] >= 6  # 3 task assignments + 3 data sharing
            assert stats["active_agents"] == 4
            assert stats["messages_failed"] == 0
            
        finally:
            await comm_manager.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
