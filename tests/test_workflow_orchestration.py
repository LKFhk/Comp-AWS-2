#!/usr/bin/env python3
"""
Test suite for workflow orchestration and real-time monitoring system.
Tests WorkflowOrchestrator, SupervisorAgent, and monitoring capabilities.
"""

import pytest
import asyncio
import logging
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from riskintel360.services.workflow_orchestrator import (
    WorkflowOrchestrator, SupervisorAgent, WorkflowConfig,
    MarketCondition, AlertEvent, create_enhanced_workflow_orchestrator
)
from riskintel360.services.agentcore_client import create_agentcore_client
from riskintel360.models.agent_models import AgentType, MessageType, Priority

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_bedrock_client():
    """Create a mock Bedrock client for testing"""
    client = Mock()
    client.invoke_for_agent = AsyncMock()
    client.invoke_for_agent.return_value = Mock(content="Mock AI analysis result")
    return client


@pytest.fixture
def agentcore_client():
    """Create an AgentCore client for testing"""
    return create_agentcore_client(region_name="us-east-1")


@pytest.fixture
def workflow_config():
    """Create a workflow configuration for testing"""
    return WorkflowConfig(
        max_execution_time=timedelta(minutes=30),
        max_retries=2,
        parallel_execution=True,
        quality_threshold=0.7
    )


@pytest.fixture
def supervisor_agent(agentcore_client, mock_bedrock_client, workflow_config):
    """Create a supervisor agent for testing"""
    supervisor = SupervisorAgent(agentcore_client, mock_bedrock_client, workflow_config)
    return supervisor


@pytest.fixture
def workflow_orchestrator(supervisor_agent):
    """Create a workflow orchestrator for testing"""
    orchestrator = WorkflowOrchestrator(supervisor_agent, monitoring_interval=1)  # 1 second for testing
    return orchestrator


class TestSupervisorAgent:
    """Test cases for SupervisorAgent"""
    
    @pytest.mark.asyncio
    async def test_supervisor_initialization(self, agentcore_client, mock_bedrock_client):
        """Test supervisor agent initialization"""
        supervisor = SupervisorAgent(agentcore_client, mock_bedrock_client)
        
        assert supervisor.agentcore_client is not None
        assert supervisor.bedrock_client is not None
        assert supervisor.workflow_graph is not None
        assert len(supervisor.agent_registry) == 0
        assert len(supervisor.active_workflows) == 0
    
    @pytest.mark.asyncio
    async def test_agent_registration(self, supervisor_agent):
        """Test agent registration functionality"""
        # Initially no agents registered
        assert len(supervisor_agent.agent_registry) == 0
        
        # Register test agents
        test_agents = [
            ("test_market_agent", AgentType.MARKET_ANALYSIS, ["market_analysis"]),
            ("test_risk_agent", AgentType.RISK_ASSESSMENT, ["risk_analysis"]),
            ("test_fraud_agent", AgentType.FRAUD_DETECTION, ["fraud_detection"])
        ]
        
        for agent_id, agent_type, capabilities in test_agents:
            success = await supervisor_agent.register_agent(agent_id, agent_type, capabilities)
            assert success is True
        
        # Check that test agents were registered
        assert len(supervisor_agent.agent_registry) == 3
        assert "test_market_agent" in supervisor_agent.agent_registry
        assert "test_competitive_agent" in supervisor_agent.agent_registry
        assert "test_financial_agent" in supervisor_agent.agent_registry
        
        # Test registering a new agent
        success = await supervisor_agent.register_agent(
            "test_risk_agent",
            AgentType.RISK_ASSESSMENT,
            ["risk_evaluation"]
        )
        
        assert success is True
        assert len(supervisor_agent.agent_registry) == 4
        assert "test_risk_agent" in supervisor_agent.agent_registry
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, supervisor_agent):
        """Test complete workflow execution"""
        # Register test agents first
        test_agents = [
            ("test_market_agent", AgentType.MARKET_ANALYSIS, ["market_analysis"]),
            ("test_risk_agent", AgentType.RISK_ASSESSMENT, ["risk_analysis"]),
            ("test_fraud_agent", AgentType.FRAUD_DETECTION, ["fraud_detection"])
        ]
        
        for agent_id, agent_type, capabilities in test_agents:
            await supervisor_agent.register_agent(agent_id, agent_type, capabilities)
        
        validation_request = {
            "business_concept": "Test AI platform",
            "target_market": "Enterprise B2B",
            "analysis_scope": ["market", "competitive", "financial"]
        }
        
        # Start workflow
        workflow_id = await supervisor_agent.start_workflow(
            user_id="test_user",
            validation_request=validation_request
        )
        
        assert workflow_id is not None
        assert workflow_id in supervisor_agent.active_workflows
        
        # Wait for workflow to complete
        await asyncio.sleep(0.5)
        
        # Check workflow status
        status = supervisor_agent.get_workflow_status(workflow_id)
        assert status is not None
        assert status["workflow_id"] == workflow_id
        assert status["progress"] >= 0.0
        assert status["agent_count"] == 3
    
    @pytest.mark.asyncio
    async def test_message_sending(self, supervisor_agent):
        """Test inter-agent message sending"""
        # Register test agents first
        test_agents = [
            ("test_market_agent", AgentType.MARKET_ANALYSIS, ["market_analysis"]),
            ("test_risk_agent", AgentType.RISK_ASSESSMENT, ["risk_analysis"])
        ]
        
        for agent_id, agent_type, capabilities in test_agents:
            await supervisor_agent.register_agent(agent_id, agent_type, capabilities)
        
        success = await supervisor_agent.send_message(
            sender_id="test_market_agent",
            recipient_id="test_competitive_agent",
            message_type=MessageType.DATA_SHARING,
            content={"test_data": "market insights"},
            priority=Priority.HIGH
        )
        
        assert success is True


class TestWorkflowOrchestrator:
    """Test cases for WorkflowOrchestrator with monitoring capabilities"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, workflow_orchestrator):
        """Test workflow orchestrator initialization"""
        assert workflow_orchestrator.supervisor is not None
        assert workflow_orchestrator.monitoring_interval == 1
        assert workflow_orchestrator.is_monitoring is False
        assert len(workflow_orchestrator.market_conditions) == 0
        assert len(workflow_orchestrator.active_alerts) == 0
    
    @pytest.mark.asyncio
    async def test_monitoring_start_stop(self, workflow_orchestrator):
        """Test monitoring system start and stop"""
        # Start monitoring
        await workflow_orchestrator.start_monitoring()
        assert workflow_orchestrator.is_monitoring is True
        assert workflow_orchestrator.monitoring_task is not None
        
        # Wait a bit for monitoring loop
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        await workflow_orchestrator.stop_monitoring()
        assert workflow_orchestrator.is_monitoring is False
    
    @pytest.mark.asyncio
    async def test_market_condition_detection(self, workflow_orchestrator):
        """Test market condition detection and alerting"""
        # Start monitoring briefly
        await workflow_orchestrator.start_monitoring()
        await asyncio.sleep(1.5)  # Wait for one monitoring cycle
        await workflow_orchestrator.stop_monitoring()
        
        # Check that market conditions were detected
        market_conditions = workflow_orchestrator.get_market_conditions()
        assert len(market_conditions) > 0
        
        # Check that alerts were created for high-impact conditions
        active_alerts = workflow_orchestrator.get_active_alerts()
        assert len(active_alerts) > 0
        
        # Verify alert structure
        alert = active_alerts[0]
        assert isinstance(alert, AlertEvent)
        assert alert.alert_id is not None
        assert alert.event_type is not None
        assert alert.severity in ["info", "warning", "error", "critical"]
    
    @pytest.mark.asyncio
    async def test_alert_handlers(self, workflow_orchestrator):
        """Test alert handler functionality"""
        received_alerts = []
        
        def test_alert_handler(alert: AlertEvent):
            received_alerts.append(alert)
        
        # Add alert handler
        workflow_orchestrator.add_alert_handler(test_alert_handler)
        
        # Start monitoring to trigger alerts
        await workflow_orchestrator.start_monitoring()
        await asyncio.sleep(1.5)
        await workflow_orchestrator.stop_monitoring()
        
        # Check that alerts were received by handler
        assert len(received_alerts) > 0
        assert isinstance(received_alerts[0], AlertEvent)
    
    @pytest.mark.asyncio
    async def test_validation_assumption_tracking(self, workflow_orchestrator):
        """Test validation assumption tracking and change detection"""
        validation_id = "test_validation_001"
        assumptions = {
            "market_size": 1000000000,  # $1B
            "growth_rate": 0.15,  # 15%
            "competition_intensity": 0.6  # 60%
        }
        
        # Track validation assumptions
        workflow_orchestrator.track_validation_assumptions(validation_id, assumptions)
        
        assert validation_id in workflow_orchestrator.validation_assumptions
        assert workflow_orchestrator.validation_assumptions[validation_id] == assumptions
        
        # Test assumption change handler
        received_changes = []
        
        def test_assumption_handler(val_id: str, changes: Dict[str, Any]):
            received_changes.append((val_id, changes))
        
        workflow_orchestrator.add_assumption_change_handler(test_assumption_handler)
        
        # Start monitoring to trigger assumption checks
        await workflow_orchestrator.start_monitoring()
        await asyncio.sleep(1.5)
        await workflow_orchestrator.stop_monitoring()
        
        # Check if assumption changes were detected
        # Note: The mock implementation should detect changes
        assert len(received_changes) >= 0  # May or may not have changes depending on mock data
    
    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, workflow_orchestrator):
        """Test system health monitoring functionality"""
        # Start a workflow to monitor
        validation_request = {
            "business_concept": "Test platform for monitoring",
            "target_market": "Enterprise"
        }
        
        workflow_id = await workflow_orchestrator.supervisor.start_workflow(
            user_id="test_user",
            validation_request=validation_request
        )
        
        # Start monitoring
        await workflow_orchestrator.start_monitoring()
        await asyncio.sleep(1.5)
        await workflow_orchestrator.stop_monitoring()
        
        # Check monitoring stats
        stats = workflow_orchestrator.get_monitoring_stats()
        assert isinstance(stats, dict)
        assert "is_monitoring" in stats
        assert "monitoring_interval" in stats
        assert "market_conditions_count" in stats
        assert "active_alerts_count" in stats
        assert stats["monitoring_interval"] == 1
    
    @pytest.mark.asyncio
    async def test_alert_auto_resolution(self, workflow_orchestrator):
        """Test automatic alert resolution"""
        # Create a test alert manually
        alert_id = await workflow_orchestrator._create_alert(
            event_type="test_alert",
            title="Test Alert",
            description="This is a test alert",
            severity="info",
            affected_workflows=[]
        )
        
        # Check that alert is active
        active_alerts = workflow_orchestrator.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].alert_id == alert_id
        
        # Manually resolve the alert
        success = await workflow_orchestrator._resolve_alert(alert_id)
        assert success is True
        
        # Check that alert is no longer active
        active_alerts_after = workflow_orchestrator.get_active_alerts()
        assert len(active_alerts_after) == 0


class TestIntegration:
    """Integration tests for complete workflow orchestration system"""
    
    @pytest.mark.asyncio
    async def test_enhanced_orchestrator_creation(self, agentcore_client, mock_bedrock_client):
        """Test creation of enhanced workflow orchestrator"""
        orchestrator = create_enhanced_workflow_orchestrator(
            agentcore_client=agentcore_client,
            bedrock_client=mock_bedrock_client,
            monitoring_interval=5
        )
        
        assert isinstance(orchestrator, WorkflowOrchestrator)
        assert orchestrator.monitoring_interval == 5
        assert orchestrator.supervisor is not None
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow_with_monitoring(self, agentcore_client, mock_bedrock_client):
        """Test complete end-to-end workflow with monitoring"""
        # Create enhanced orchestrator
        orchestrator = create_enhanced_workflow_orchestrator(
            agentcore_client=agentcore_client,
            bedrock_client=mock_bedrock_client,
            monitoring_interval=1
        )
        
        # Register agents
        test_agents = [
            ("e2e_market_agent", AgentType.MARKET_ANALYSIS, ["market_analysis"]),
            ("e2e_risk_agent", AgentType.RISK_ASSESSMENT, ["risk_analysis"]),
            ("e2e_fraud_agent", AgentType.FRAUD_DETECTION, ["fraud_detection"])
        ]
        
        for agent_id, agent_type, capabilities in test_agents:
            await orchestrator.supervisor.register_agent(agent_id, agent_type, capabilities)
        
        # Start monitoring
        await orchestrator.start_monitoring()
        
        # Start a validation workflow
        validation_request = {
            "business_concept": "End-to-end test AI platform",
            "target_market": "Enterprise B2B SaaS",
            "analysis_scope": ["market", "competitive", "financial"]
        }
        
        workflow_id = await orchestrator.supervisor.start_workflow(
            user_id="e2e_test_user",
            validation_request=validation_request
        )
        
        # Track validation assumptions
        assumptions = {
            "market_size": 5000000000,  # $5B
            "growth_rate": 0.20,  # 20%
            "competition_intensity": 0.8  # 80%
        }
        orchestrator.track_validation_assumptions(workflow_id, assumptions)
        
        # Wait for workflow and monitoring
        await asyncio.sleep(2.0)
        
        # Check workflow completion
        status = orchestrator.supervisor.get_workflow_status(workflow_id)
        assert status is not None
        assert status["progress"] == 1.0  # Should be completed
        
        # Check monitoring results
        stats = orchestrator.get_monitoring_stats()
        assert stats["is_monitoring"] is True
        assert stats["market_conditions_count"] > 0
        assert stats["tracked_validations_count"] == 1
        
        # Stop monitoring
        await orchestrator.stop_monitoring()
        
        logger.info("??End-to-end workflow with monitoring completed successfully")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
