"""
Integration tests for Amazon Bedrock AgentCore multi-agent coordination.
Tests AgentCore primitives, workflow orchestration, and agent communication.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from riskintel360.services.agentcore_client import (
    AgentCoreClient, AgentCorePrimitive, AgentCoreRequest, AgentCoreResponse
)
from riskintel360.services.workflow_orchestrator import (
    SupervisorAgent, WorkflowConfig, WorkflowPhase, AgentWorkflowState
)
from riskintel360.services.agent_communication import (
    AgentCommunicationManager, CommunicationProtocol, MessageStatus
)
from riskintel360.models.agent_models import (
    AgentMessage, MessageType, Priority, AgentType, SessionStatus
)
from riskintel360.agents.agent_factory import AgentFactory


class TestAgentCoreCoordination:
    """Integration tests for AgentCore coordination primitives"""
    
    @pytest.fixture
    def agentcore_client(self):
        """Create AgentCore client for testing"""
        # Mock the AgentCore client since we don't have real AWS AgentCore access
        mock_client = Mock(spec=AgentCoreClient)
        mock_client.region_name = "us-east-1"
        mock_client.session = Mock()
        mock_client.bedrock_agent = Mock()
        mock_client.agent_registry = {}
        mock_client.message_queues = {}
        return mock_client
    
    @pytest.fixture
    def agent_factory(self):
        """Create agent factory for testing"""
        return AgentFactory()
    
    @pytest.fixture
    def sample_agents(self):
        """Sample agent configurations for testing"""
        return [
            {
                "agent_id": "regulatory_compliance_001",
                "agent_type": AgentType.REGULATORY_COMPLIANCE,
                "capabilities": ["sec_analysis", "finra_monitoring", "cfpb_compliance"]
            },
            {
                "agent_id": "fraud_detection_001", 
                "agent_type": AgentType.FRAUD_DETECTION,
                "capabilities": ["ml_anomaly_detection", "pattern_recognition", "risk_scoring"]
            },
            {
                "agent_id": "risk_assessment_001",
                "agent_type": AgentType.RISK_ASSESSMENT,
                "capabilities": ["credit_risk", "market_risk", "operational_risk"]
            },
            {
                "agent_id": "market_analysis_001",
                "agent_type": AgentType.MARKET_ANALYSIS,
                "capabilities": ["trend_analysis", "volatility_assessment", "opportunity_identification"]
            },
            {
                "agent_id": "kyc_verification_001",
                "agent_type": AgentType.KYC_VERIFICATION,
                "capabilities": ["identity_verification", "document_analysis", "sanctions_screening"]
            }
        ]
    
    @pytest.mark.integration
    def test_agent_registration_with_agentcore(self, agentcore_client, sample_agents):
        """Test agent registration with AgentCore primitives"""
        # Mock registration responses
        def mock_register_agent(agent_id, agent_type, capabilities):
            agentcore_client.agent_registry[agent_id] = {
                "agent_type": agent_type,
                "capabilities": capabilities,
                "status": "active",
                "registered_at": datetime.now(timezone.utc)
            }
            return True
        
        agentcore_client.register_agent = mock_register_agent
        agentcore_client.is_agent_registered = lambda agent_id: agent_id in agentcore_client.agent_registry
        agentcore_client.get_registered_agents = lambda: agentcore_client.agent_registry
        
        # Register all fintech agents
        for agent_config in sample_agents:
            success = agentcore_client.register_agent(
                agent_id=agent_config["agent_id"],
                agent_type=agent_config["agent_type"],
                capabilities=agent_config["capabilities"]
            )
            
            assert success is True
            assert agentcore_client.is_agent_registered(agent_config["agent_id"]) is True
        
        # Verify all agents are registered
        registered_agents = agentcore_client.get_registered_agents()
        assert len(registered_agents) == len(sample_agents)
        
        # Verify agent types are correctly registered
        for agent_config in sample_agents:
            agent_id = agent_config["agent_id"]
            assert registered_agents[agent_id]["agent_type"] == agent_config["agent_type"]
            assert registered_agents[agent_id]["capabilities"] == agent_config["capabilities"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_message_routing_primitive(self, agentcore_client, sample_agents):
        """Test AgentCore message routing primitive for fintech workflows"""
        # Setup agent registry
        for agent_config in sample_agents:
            agentcore_client.agent_registry[agent_config["agent_id"]] = agent_config
        
        # Mock message routing
        async def mock_route_message(sender_id, recipient_id, message):
            return AgentCoreResponse(
                success=True,
                primitive=AgentCorePrimitive.MESSAGE_ROUTING,
                result={
                    "routed": True,
                    "sender_id": sender_id,
                    "recipient_id": recipient_id,
                    "message_id": f"msg_{datetime.now().timestamp()}",
                    "routing_time": 0.05
                }
            )
        
        agentcore_client.route_message = mock_route_message
        
        # Test regulatory compliance to fraud detection communication
        sender_id = "regulatory_compliance_001"
        recipient_id = "fraud_detection_001"
        
        message = AgentMessage(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=MessageType.DATA_SHARING,
            content={
                "regulatory_alerts": [
                    {
                        "regulation": "BSA_AML",
                        "alert_type": "suspicious_activity_threshold",
                        "threshold": 10000,
                        "currency": "USD"
                    }
                ],
                "correlation_id": "workflow_001"
            }
        )
        
        response = await agentcore_client.route_message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message=message
        )
        
        # Verify routing success
        assert response.success is True
        assert response.primitive == AgentCorePrimitive.MESSAGE_ROUTING
        assert response.result["routed"] is True
        assert response.result["sender_id"] == sender_id
        assert response.result["recipient_id"] == recipient_id
        assert response.result["routing_time"] < 1.0  # Should be fast
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_task_distribution_primitive(self, agentcore_client, sample_agents):
        """Test AgentCore task distribution for fintech risk analysis"""
        # Setup agent registry
        for agent_config in sample_agents:
            agentcore_client.agent_registry[agent_config["agent_id"]] = agent_config
        
        # Mock task distribution
        async def mock_distribute_task(supervisor_id, task_data, target_agents):
            return AgentCoreResponse(
                success=True,
                primitive=AgentCorePrimitive.TASK_DISTRIBUTION,
                result={
                    "distributed": True,
                    "task_id": task_data["task_id"],
                    "supervisor_id": supervisor_id,
                    "distributed_to": target_agents,
                    "distribution_time": 0.1,
                    "agent_assignments": {
                        agent_id: {
                            "task_type": task_data["type"],
                            "parameters": task_data["parameters"],
                            "priority": task_data.get("priority", "medium"),
                            "assigned_at": datetime.now(timezone.utc).isoformat()
                        }
                        for agent_id in target_agents
                    }
                }
            )
        
        agentcore_client.distribute_task = mock_distribute_task
        
        # Test comprehensive fintech risk analysis task distribution
        supervisor_id = "supervisor_001"
        target_agents = [agent["agent_id"] for agent in sample_agents]
        
        task_data = {
            "task_id": "fintech_risk_analysis_001",
            "type": "comprehensive_risk_analysis",
            "priority": "high",
            "parameters": {
                "entity_id": "fintech_startup_123",
                "entity_type": "payment_processor",
                "analysis_scope": ["regulatory", "fraud", "market", "credit", "kyc"],
                "urgency": "high",
                "compliance_requirements": ["SEC", "FINRA", "CFPB", "BSA"],
                "deadline": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
            }
        }
        
        response = await agentcore_client.distribute_task(
            supervisor_id=supervisor_id,
            task_data=task_data,
            target_agents=target_agents
        )
        
        # Verify task distribution
        assert response.success is True
        assert response.primitive == AgentCorePrimitive.TASK_DISTRIBUTION
        assert response.result["distributed"] is True
        assert response.result["task_id"] == task_data["task_id"]
        assert len(response.result["distributed_to"]) == len(target_agents)
        assert len(response.result["agent_assignments"]) == len(target_agents)
        
        # Verify each agent received appropriate task assignment
        for agent_id in target_agents:
            assignment = response.result["agent_assignments"][agent_id]
            assert assignment["task_type"] == "comprehensive_risk_analysis"
            assert assignment["priority"] == "high"
            assert "assigned_at" in assignment
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_state_synchronization_primitive(self, agentcore_client, sample_agents):
        """Test AgentCore state synchronization for shared fintech context"""
        # Setup agent registry
        for agent_config in sample_agents:
            agentcore_client.agent_registry[agent_config["agent_id"]] = agent_config
        
        # Mock state synchronization
        async def mock_synchronize_state(agent_id, state_data, sync_agents):
            return AgentCoreResponse(
                success=True,
                primitive=AgentCorePrimitive.STATE_SYNCHRONIZATION,
                result={
                    "synchronized": True,
                    "state_version": state_data["version"],
                    "initiator_agent": agent_id,
                    "synchronized_agents": sync_agents,
                    "sync_time": 0.2,
                    "state_hash": f"hash_{state_data['version']}",
                    "conflicts_resolved": 0
                }
            )
        
        agentcore_client.synchronize_state = mock_synchronize_state
        
        # Test synchronizing shared fintech context
        initiator_agent = "regulatory_compliance_001"
        sync_agents = ["fraud_detection_001", "risk_assessment_001", "kyc_verification_001"]
        
        shared_state = {
            "version": 3,
            "shared_context": {
                "entity_profile": {
                    "entity_id": "fintech_startup_123",
                    "business_type": "payment_processor",
                    "jurisdiction": "US",
                    "regulatory_status": "registered",
                    "risk_profile": "medium"
                },
                "regulatory_updates": [
                    {
                        "regulation": "CFPB_1033",
                        "effective_date": "2024-04-01",
                        "impact": "high",
                        "compliance_required": True
                    }
                ],
                "market_conditions": {
                    "volatility_index": 0.35,
                    "trend_direction": "bullish",
                    "last_updated": datetime.now(timezone.utc).isoformat()
                },
                "fraud_indicators": {
                    "current_threat_level": "medium",
                    "active_patterns": ["geographic_velocity", "amount_anomaly"],
                    "model_version": "v2.1"
                }
            }
        }
        
        response = await agentcore_client.synchronize_state(
            agent_id=initiator_agent,
            state_data=shared_state,
            sync_agents=sync_agents
        )
        
        # Verify state synchronization
        assert response.success is True
        assert response.primitive == AgentCorePrimitive.STATE_SYNCHRONIZATION
        assert response.result["synchronized"] is True
        assert response.result["state_version"] == shared_state["version"]
        assert response.result["initiator_agent"] == initiator_agent
        assert set(response.result["synchronized_agents"]) == set(sync_agents)
        assert response.result["sync_time"] < 1.0  # Should be efficient
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_orchestration_primitive(self, agentcore_client, sample_agents):
        """Test AgentCore workflow orchestration for fintech analysis"""
        # Setup agent registry
        for agent_config in sample_agents:
            agentcore_client.agent_registry[agent_config["agent_id"]] = agent_config
        
        # Mock workflow orchestration
        async def mock_orchestrate_workflow(supervisor_id, workflow_data):
            return AgentCoreResponse(
                success=True,
                primitive=AgentCorePrimitive.WORKFLOW_ORCHESTRATION,
                result={
                    "orchestrated": True,
                    "workflow_id": workflow_data["workflow_id"],
                    "supervisor_id": supervisor_id,
                    "workflow_type": workflow_data["type"],
                    "participating_agents": workflow_data["agents"],
                    "orchestration_time": 0.15,
                    "workflow_phases": [
                        "initialization",
                        "task_distribution", 
                        "parallel_execution",
                        "result_synthesis",
                        "quality_assessment",
                        "completion"
                    ],
                    "estimated_completion": (datetime.now(timezone.utc) + timedelta(hours=1.5)).isoformat()
                }
            )
        
        agentcore_client.orchestrate_workflow = mock_orchestrate_workflow
        
        # Test comprehensive fintech workflow orchestration
        supervisor_id = "supervisor_001"
        
        workflow_data = {
            "workflow_id": "fintech_comprehensive_analysis_001",
            "type": "comprehensive_fintech_analysis",
            "priority": "high",
            "agents": [agent["agent_id"] for agent in sample_agents],
            "workflow_config": {
                "max_execution_time": "2h",
                "parallel_execution": True,
                "quality_threshold": 0.8,
                "retry_policy": "exponential_backoff"
            },
            "analysis_request": {
                "entity_id": "fintech_startup_123",
                "analysis_scope": ["regulatory", "fraud", "market", "credit", "kyc"],
                "urgency": "high",
                "business_context": {
                    "industry": "payments",
                    "stage": "series_a",
                    "geography": "US"
                }
            }
        }
        
        response = await agentcore_client.orchestrate_workflow(
            supervisor_id=supervisor_id,
            workflow_data=workflow_data
        )
        
        # Verify workflow orchestration
        assert response.success is True
        assert response.primitive == AgentCorePrimitive.WORKFLOW_ORCHESTRATION
        assert response.result["orchestrated"] is True
        assert response.result["workflow_id"] == workflow_data["workflow_id"]
        assert response.result["workflow_type"] == "comprehensive_fintech_analysis"
        assert len(response.result["participating_agents"]) == len(sample_agents)
        assert len(response.result["workflow_phases"]) == 6  # Expected phases
        assert "estimated_completion" in response.result


class TestMultiAgentCoordinationScenarios:
    """Integration tests for complex multi-agent coordination scenarios"""
    
    @pytest.fixture
    def workflow_orchestrator(self):
        """Create workflow orchestrator with mocked dependencies"""
        mock_agentcore = Mock(spec=AgentCoreClient)
        mock_bedrock = Mock()
        mock_bedrock.invoke_for_agent = AsyncMock()
        
        config = WorkflowConfig(
            max_execution_time=timedelta(hours=2),
            max_retries=3,
            parallel_execution=True,
            quality_threshold=0.8
        )
        
        orchestrator = SupervisorAgent(
            agentcore_client=mock_agentcore,
            bedrock_client=mock_bedrock,
            config=config
        )
        
        return orchestrator
    
    @pytest.fixture
    def communication_manager(self):
        """Create communication manager with mocked AgentCore"""
        mock_agentcore = Mock(spec=AgentCoreClient)
        return AgentCommunicationManager(agentcore_client=mock_agentcore)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fintech_fraud_detection_coordination(self, workflow_orchestrator, communication_manager):
        """Test coordinated fraud detection workflow across multiple agents"""
        # Start communication manager
        await communication_manager.start()
        
        try:
            # Register agents for fraud detection workflow
            agents = [
                ("fraud_detection_001", AgentType.FRAUD_DETECTION),
                ("regulatory_compliance_001", AgentType.REGULATORY_COMPLIANCE),
                ("risk_assessment_001", AgentType.RISK_ASSESSMENT),
                ("kyc_verification_001", AgentType.KYC_VERIFICATION)
            ]
            
            for agent_id, agent_type in agents:
                await workflow_orchestrator.register_agent(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    capabilities=["fraud_analysis", "coordination"]
                )
                communication_manager.register_agent(agent_id, agent_type)
            
            # Mock workflow execution
            workflow_orchestrator.start_workflow = AsyncMock(return_value="fraud_workflow_001")
            workflow_orchestrator.get_workflow_status = Mock(return_value={
                "workflow_id": "fraud_workflow_001",
                "status": "in_progress",
                "progress": 0.75,
                "current_phase": "result_synthesis"
            })
            
            # Start fraud detection workflow
            fraud_request = {
                "transaction_batch": "batch_001",
                "transaction_count": 1000,
                "priority": "high",
                "analysis_scope": ["ml_detection", "regulatory_check", "risk_assessment", "kyc_validation"]
            }
            
            workflow_id = await workflow_orchestrator.start_workflow(
                user_id="fraud_analyst_001",
                validation_request=fraud_request
            )
            
            assert workflow_id == "fraud_workflow_001"
            
            # Test inter-agent coordination messages
            coordination_messages = [
                {
                    "sender": "fraud_detection_001",
                    "recipient": "regulatory_compliance_001",
                    "content": {"suspicious_patterns": ["velocity_anomaly"], "requires_sar": True}
                },
                {
                    "sender": "regulatory_compliance_001", 
                    "recipient": "risk_assessment_001",
                    "content": {"compliance_status": "violation_detected", "regulation": "BSA"}
                },
                {
                    "sender": "risk_assessment_001",
                    "recipient": "kyc_verification_001", 
                    "content": {"risk_escalation": True, "enhanced_due_diligence": True}
                }
            ]
            
            # Send coordination messages
            for msg in coordination_messages:
                message_id = await communication_manager.send_message(
                    sender_id=msg["sender"],
                    recipient_id=msg["recipient"],
                    message_type=MessageType.DATA_SHARING,
                    content=msg["content"]
                )
                assert message_id is not None
            
            # Verify workflow progress
            status = workflow_orchestrator.get_workflow_status(workflow_id)
            assert status["progress"] > 0.5
            assert status["status"] in ["in_progress", "completed"]
            
        finally:
            await communication_manager.stop()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_regulatory_compliance_coordination(self, workflow_orchestrator, communication_manager):
        """Test coordinated regulatory compliance monitoring across agents"""
        await communication_manager.start()
        
        try:
            # Register agents for compliance workflow
            agents = [
                ("regulatory_compliance_001", AgentType.REGULATORY_COMPLIANCE),
                ("risk_assessment_001", AgentType.RISK_ASSESSMENT),
                ("market_analysis_001", AgentType.MARKET_ANALYSIS),
                ("kyc_verification_001", AgentType.KYC_VERIFICATION)
            ]
            
            for agent_id, agent_type in agents:
                await workflow_orchestrator.register_agent(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    capabilities=["compliance_monitoring", "coordination"]
                )
                communication_manager.register_agent(agent_id, agent_type)
            
            # Mock compliance workflow
            workflow_orchestrator.start_workflow = AsyncMock(return_value="compliance_workflow_001")
            
            # Start compliance monitoring workflow
            compliance_request = {
                "monitoring_scope": "comprehensive",
                "regulations": ["SEC", "FINRA", "CFPB", "BSA"],
                "entity_type": "fintech_startup",
                "priority": "high"
            }
            
            workflow_id = await workflow_orchestrator.start_workflow(
                user_id="compliance_officer_001",
                validation_request=compliance_request
            )
            
            assert workflow_id == "compliance_workflow_001"
            
            # Test regulatory update propagation
            regulatory_update = {
                "regulation": "CFPB_1033",
                "update_type": "new_requirement",
                "effective_date": "2024-04-01",
                "impact_assessment": "high",
                "affected_areas": ["data_sharing", "consumer_rights"]
            }
            
            # Broadcast regulatory update to all agents
            message_id = await communication_manager.send_message(
                sender_id="regulatory_compliance_001",
                recipient_id="all",
                message_type=MessageType.STATUS_UPDATE,
                content=regulatory_update,
                protocol=CommunicationProtocol.BROADCAST
            )
            
            assert message_id is not None
            
            # Verify all agents received the update
            for agent_id, _ in agents[1:]:  # Skip sender
                messages = await communication_manager.get_messages(agent_id, timeout=0.5)
                assert len(messages) >= 1
                assert messages[0].content["regulation"] == "CFPB_1033"
            
        finally:
            await communication_manager.stop()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_market_risk_coordination(self, workflow_orchestrator, communication_manager):
        """Test coordinated market risk analysis across agents"""
        await communication_manager.start()
        
        try:
            # Register agents for market risk workflow
            agents = [
                ("market_analysis_001", AgentType.MARKET_ANALYSIS),
                ("risk_assessment_001", AgentType.RISK_ASSESSMENT),
                ("regulatory_compliance_001", AgentType.REGULATORY_COMPLIANCE),
                ("fraud_detection_001", AgentType.FRAUD_DETECTION)
            ]
            
            for agent_id, agent_type in agents:
                await workflow_orchestrator.register_agent(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    capabilities=["market_analysis", "risk_coordination"]
                )
                communication_manager.register_agent(agent_id, agent_type)
            
            # Subscribe agents to market updates topic
            market_topic = "market_risk_updates"
            for agent_id, _ in agents[1:]:  # All except market analysis agent
                await communication_manager.subscribe_to_topic(agent_id, market_topic)
            
            # Publish market risk alert
            market_alert = {
                "alert_type": "volatility_spike",
                "market_segment": "fintech_stocks",
                "volatility_level": 0.85,
                "risk_factors": ["regulatory_uncertainty", "market_correction"],
                "recommended_actions": ["increase_monitoring", "review_risk_limits"]
            }
            
            message_id = await communication_manager.send_message(
                sender_id="market_analysis_001",
                recipient_id=market_topic,
                message_type=MessageType.DATA_SHARING,
                content=market_alert,
                protocol=CommunicationProtocol.PUBLISH_SUBSCRIBE
            )
            
            assert message_id is not None
            
            # Verify subscribers received the alert
            for agent_id, _ in agents[1:]:
                messages = await communication_manager.get_messages(agent_id, timeout=0.5)
                assert len(messages) >= 1
                assert messages[0].content["alert_type"] == "volatility_spike"
            
        finally:
            await communication_manager.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
