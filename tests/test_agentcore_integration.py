"""
Test AWS Bedrock AgentCore Integration
Validates AgentCore client functionality and multi-agent coordination primitives.
"""

import pytest
import asyncio
from datetime import datetime, UTC

from riskintel360.services.agentcore_client import (
    AgentCoreClient,
    create_agentcore_client,
    AgentCorePrimitive,
    AgentCoreRequest,
    AgentCoreResponse
)
from riskintel360.models.agent_models import (
    AgentType,
    AgentMessage,
    MessageType,
    Priority
)


class TestAgentCoreClient:
    """Test AgentCore client initialization and basic operations"""
    
    @pytest.fixture
    def agentcore_client(self):
        """Create AgentCore client for testing (simulation mode)"""
        return create_agentcore_client(
            region_name="us-east-1",
            enable_real_bedrock_agents=False  # Use simulation for tests
        )
    
    def test_client_initialization(self, agentcore_client):
        """Test that AgentCore client initializes correctly"""
        assert agentcore_client is not None
        assert agentcore_client.region_name == "us-east-1"
        assert agentcore_client.enable_real_bedrock_agents is False
        assert agentcore_client.bedrock_agent is not None
        assert agentcore_client.bedrock_agent_runtime is not None
    
    def test_agent_registration(self, agentcore_client):
        """Test agent registration with AgentCore"""
        success = agentcore_client.register_agent(
            agent_id="test_fraud_agent",
            agent_type=AgentType.FRAUD_DETECTION,
            capabilities=["anomaly_detection", "pattern_analysis"]
        )
        
        assert success is True
        assert agentcore_client.is_agent_registered("test_fraud_agent")
        
        # Verify agent info
        agents = agentcore_client.get_registered_agents()
        assert "test_fraud_agent" in agents
        assert agents["test_fraud_agent"]["agent_type"] == AgentType.FRAUD_DETECTION.value
    
    def test_agent_unregistration(self, agentcore_client):
        """Test agent unregistration"""
        # Register first
        agentcore_client.register_agent(
            agent_id="temp_agent",
            agent_type=AgentType.RISK_ASSESSMENT,
            capabilities=["risk_analysis"]
        )
        
        assert agentcore_client.is_agent_registered("temp_agent")
        
        # Unregister
        success = agentcore_client.unregister_agent("temp_agent")
        assert success is True
        assert not agentcore_client.is_agent_registered("temp_agent")
    
    def test_coordination_stats(self, agentcore_client):
        """Test coordination statistics"""
        # Register some agents
        agentcore_client.register_agent(
            "agent1", AgentType.FRAUD_DETECTION, ["fraud"]
        )
        agentcore_client.register_agent(
            "agent2", AgentType.RISK_ASSESSMENT, ["risk"]
        )
        
        stats = agentcore_client.get_coordination_stats()
        
        assert stats["registered_agents"] >= 2
        assert stats["real_bedrock_enabled"] is False
        assert stats["region"] == "us-east-1"
        assert "active_workflows" in stats
        assert "shared_memory_keys" in stats


class TestAgentCorePrimitives:
    """Test AgentCore coordination primitives"""
    
    @pytest.fixture
    def agentcore_client(self):
        """Create AgentCore client with registered agents"""
        client = create_agentcore_client(enable_real_bedrock_agents=False)
        
        # Register test agents
        client.register_agent(
            "supervisor", AgentType.SUPERVISOR, ["orchestration"]
        )
        client.register_agent(
            "fraud_agent", AgentType.FRAUD_DETECTION, ["fraud_detection"]
        )
        client.register_agent(
            "risk_agent", AgentType.RISK_ASSESSMENT, ["risk_analysis"]
        )
        
        return client
    
    @pytest.mark.asyncio
    async def test_message_routing(self, agentcore_client):
        """Test message routing primitive"""
        message = AgentMessage(
            message_id="msg_001",
            sender_id="supervisor",
            recipient_id="fraud_agent",
            message_type=MessageType.TASK_ASSIGNMENT,
            content={"task": "analyze_transaction"},
            priority=Priority.HIGH,
            timestamp=datetime.now(UTC)
        )
        
        response = await agentcore_client.route_message(
            sender_id="supervisor",
            recipient_id="fraud_agent",
            message=message,
            correlation_id="test_correlation"
        )
        
        assert response.success is True
        assert response.primitive == AgentCorePrimitive.MESSAGE_ROUTING
        assert response.result["routed"] is True
        assert response.result["recipient_id"] == "fraud_agent"
    
    @pytest.mark.asyncio
    async def test_task_distribution(self, agentcore_client):
        """Test task distribution primitive"""
        task_data = {
            "task_id": "task_001",
            "task_type": "fraud_analysis",
            "parameters": {"threshold": 0.8}
        }
        
        response = await agentcore_client.distribute_task(
            supervisor_id="supervisor",
            task_data=task_data,
            target_agents=["fraud_agent", "risk_agent"],
            correlation_id="test_workflow"
        )
        
        assert response.success is True
        assert response.primitive == AgentCorePrimitive.TASK_DISTRIBUTION
        assert response.result["distributed"] is True
        assert len(response.result["distributed_to"]) == 2
    
    @pytest.mark.asyncio
    async def test_state_synchronization(self, agentcore_client):
        """Test state synchronization primitive"""
        state_data = {
            "workflow_id": "wf_001",
            "progress": 0.5,
            "version": 1
        }
        
        response = await agentcore_client.synchronize_state(
            agent_id="supervisor",
            state_data=state_data,
            sync_agents=["fraud_agent", "risk_agent"],
            correlation_id="test_sync"
        )
        
        assert response.success is True
        assert response.primitive == AgentCorePrimitive.STATE_SYNCHRONIZATION
        assert response.result["synchronized"] is True
    
    @pytest.mark.asyncio
    async def test_workflow_orchestration(self, agentcore_client):
        """Test workflow orchestration primitive"""
        workflow_data = {
            "workflow_id": "wf_fintech_001",
            "workflow_type": "fintech_risk_analysis",
            "agents": ["fraud_agent", "risk_agent"]
        }
        
        response = await agentcore_client.orchestrate_workflow(
            supervisor_id="supervisor",
            workflow_data=workflow_data,
            correlation_id="test_orchestration"
        )
        
        assert response.success is True
        assert response.primitive == AgentCorePrimitive.WORKFLOW_ORCHESTRATION
        assert response.result["orchestrated"] is True
        assert response.result["workflow_id"] == "wf_fintech_001"
        
        # Verify workflow state is stored
        workflow_state = agentcore_client.get_workflow_state("wf_fintech_001")
        assert workflow_state is not None
        assert workflow_state["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_shared_memory(self, agentcore_client):
        """Test shared memory operations"""
        # Set shared memory
        await agentcore_client.set_shared_memory(
            key="market_data",
            value={"sp500": 4500, "vix": 15.2}
        )
        
        # Get shared memory
        market_data = await agentcore_client.get_shared_memory("market_data")
        
        assert market_data is not None
        assert market_data["sp500"] == 4500
        assert market_data["vix"] == 15.2
    
    @pytest.mark.asyncio
    async def test_workflow_state_management(self, agentcore_client):
        """Test workflow state management"""
        workflow_id = "wf_test_001"
        
        # Create workflow
        await agentcore_client.orchestrate_workflow(
            supervisor_id="supervisor",
            workflow_data={"workflow_id": workflow_id}
        )
        
        # Get workflow state
        state = agentcore_client.get_workflow_state(workflow_id)
        assert state is not None
        assert state["workflow_id"] == workflow_id
        
        # Update workflow state
        success = agentcore_client.update_workflow_state(
            workflow_id,
            {"progress": 0.75, "status": "processing"}
        )
        assert success is True
        
        # Verify update
        updated_state = agentcore_client.get_workflow_state(workflow_id)
        assert updated_state["progress"] == 0.75
        assert updated_state["status"] == "processing"


class TestBedrockAgentIntegration:
    """Test Bedrock Agent ID registration and linking"""
    
    @pytest.fixture
    def agentcore_client(self):
        """Create AgentCore client"""
        return create_agentcore_client(enable_real_bedrock_agents=False)
    
    def test_bedrock_agent_id_registration(self, agentcore_client):
        """Test registering Bedrock Agent IDs"""
        # Register agent
        agentcore_client.register_agent(
            "fraud_agent", AgentType.FRAUD_DETECTION, ["fraud"]
        )
        
        # Link Bedrock Agent ID
        agentcore_client.register_bedrock_agent_id(
            agent_id="fraud_agent",
            bedrock_agent_id="BEDROCK_AGENT_123"
        )
        
        # Verify in stats
        stats = agentcore_client.get_coordination_stats()
        assert stats["bedrock_agents_linked"] >= 1


class TestAgentCoreErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def agentcore_client(self):
        """Create AgentCore client"""
        return create_agentcore_client(enable_real_bedrock_agents=False)
    
    @pytest.mark.asyncio
    async def test_message_routing_to_unregistered_agent(self, agentcore_client):
        """Test routing message to unregistered agent"""
        message = AgentMessage(
            message_id="msg_002",
            sender_id="supervisor",
            recipient_id="nonexistent_agent",
            message_type=MessageType.TASK_ASSIGNMENT,
            content={},
            priority=Priority.MEDIUM,
            timestamp=datetime.now(UTC)
        )
        
        # Should not raise error, but handle gracefully
        response = await agentcore_client.route_message(
            sender_id="supervisor",
            recipient_id="nonexistent_agent",
            message=message
        )
        
        # Should still succeed (message routing doesn't require registration)
        assert response.success is True
    
    def test_unregister_nonexistent_agent(self, agentcore_client):
        """Test unregistering agent that doesn't exist"""
        success = agentcore_client.unregister_agent("nonexistent_agent")
        # Should succeed (idempotent operation)
        assert success is True
    
    def test_get_nonexistent_workflow_state(self, agentcore_client):
        """Test getting state for nonexistent workflow"""
        state = agentcore_client.get_workflow_state("nonexistent_workflow")
        assert state is None
    
    def test_update_nonexistent_workflow_state(self, agentcore_client):
        """Test updating state for nonexistent workflow"""
        success = agentcore_client.update_workflow_state(
            "nonexistent_workflow",
            {"progress": 0.5}
        )
        assert success is False


@pytest.mark.integration
class TestAgentCoreWithSupervisor:
    """Integration tests with SupervisorAgent"""
    
    @pytest.mark.asyncio
    async def test_supervisor_uses_agentcore(self):
        """Test that SupervisorAgent properly uses AgentCore"""
        from riskintel360.services.workflow_orchestrator import SupervisorAgent
        from riskintel360.services.bedrock_client import create_bedrock_client
        
        # Create clients
        agentcore = create_agentcore_client(enable_real_bedrock_agents=False)
        bedrock = create_bedrock_client(region_name="us-east-1")
        
        # Create supervisor
        supervisor = SupervisorAgent(
            agentcore_client=agentcore,
            bedrock_client=bedrock
        )
        
        # Verify supervisor has AgentCore client
        assert supervisor.agentcore_client is not None
        assert supervisor.agentcore_client == agentcore
        
        # Register an agent through supervisor
        success = await supervisor.register_agent(
            agent_id="test_agent",
            agent_type=AgentType.FRAUD_DETECTION,
            capabilities=["fraud_detection"]
        )
        
        assert success is True
        assert agentcore.is_agent_registered("test_agent")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
