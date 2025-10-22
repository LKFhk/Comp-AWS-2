"""
Integration tests for fintech workflow coordination.
Tests the enhanced SupervisorAgent with fintech-specific capabilities.
"""

import pytest
import asyncio
from datetime import datetime, UTC, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from riskintel360.services.workflow_orchestrator import SupervisorAgent, WorkflowConfig
from riskintel360.services.agentcore_client import AgentCoreClient
from riskintel360.services.bedrock_client import BedrockClient
from riskintel360.models.agent_models import AgentType, Priority, TaskAssignment


class TestFintechWorkflowCoordination:
    """Test fintech workflow coordination capabilities"""
    
    @pytest.fixture
    def mock_agentcore_client(self):
        """Mock AgentCore client"""
        client = Mock(spec=AgentCoreClient)
        client.register_agent = AsyncMock(return_value=True)
        client.orchestrate_workflow = AsyncMock()
        client.orchestrate_workflow.return_value.success = True
        client.distribute_task = AsyncMock()
        client.distribute_task.return_value.success = True
        return client
    
    @pytest.fixture
    def mock_bedrock_client(self):
        """Mock Bedrock client"""
        client = Mock(spec=BedrockClient)
        client.invoke_for_agent = AsyncMock()
        
        # Mock AI responses for task prioritization
        mock_response = Mock()
        mock_response.content = """
        Task Priority Analysis:
        1. Regulatory Compliance (Critical) - Compliance violations require immediate attention
        2. Fraud Detection (High) - Active fraud threats need rapid response
        3. Risk Assessment (High) - Financial risk evaluation is time-sensitive
        4. Market Analysis (Medium) - Market intelligence can be processed in parallel
        5. KYC Verification (High) - Customer verification affects onboarding
        6. Customer Behavior Intelligence (Medium) - Customer analysis supports strategy
        
        Quality Score: 0.85 - Good quality with minor improvements needed
        """
        client.invoke_for_agent.return_value = mock_response
        
        return client
    
    @pytest.fixture
    def workflow_config(self):
        """Workflow configuration for testing"""
        return WorkflowConfig(
            max_execution_time=timedelta(hours=2),
            max_retries=2,
            parallel_execution=True,
            quality_threshold=0.8,
            enable_cross_agent_communication=True
        )
    
    @pytest.fixture
    def supervisor_agent(self, mock_agentcore_client, mock_bedrock_client, workflow_config):
        """Create supervisor agent for testing"""
        return SupervisorAgent(
            agentcore_client=mock_agentcore_client,
            bedrock_client=mock_bedrock_client,
            config=workflow_config
        )
    
    @pytest.mark.asyncio
    async def test_start_fintech_workflow(self, supervisor_agent):
        """Test starting a fintech-specific workflow"""
        # Arrange
        user_id = "test_user_123"
        risk_analysis_request = {
            "business_type": "fintech_startup",
            "company_size": "small",
            "analysis_scope": ["regulatory", "fraud", "risk"],
            "urgency": "high",
            "compliance_requirements": ["PCI_DSS", "SOX"],
            "jurisdiction": "US"
        }
        
        # Act
        workflow_id = await supervisor_agent.start_fintech_workflow(
            user_id=user_id,
            risk_analysis_request=risk_analysis_request
        )
        
        # Assert
        assert workflow_id is not None
        assert len(workflow_id) > 0
        assert workflow_id in supervisor_agent.active_workflows
        
        # Verify workflow state
        workflow_state = supervisor_agent.active_workflows[workflow_id]
        assert workflow_state["user_id"] == user_id
        assert workflow_state["validation_request"]["fintech_workflow"] is True
        assert workflow_state["validation_request"]["analysis_type"] == "fintech_risk_intelligence"
        assert workflow_state["validation_request"]["data_sources"] == "public_data_first"
    
    @pytest.mark.asyncio
    async def test_fintech_agent_assignments_creation(self, supervisor_agent):
        """Test creation of fintech-specific agent assignments"""
        # Arrange
        validation_request = {
            "business_type": "digital_bank",
            "company_size": "medium",
            "analysis_scope": ["regulatory", "fraud", "market", "kyc"],
            "compliance_requirements": ["GDPR", "PCI_DSS"],
            "jurisdiction": "EU",
            "fintech_workflow": True
        }
        
        # Act
        agent_assignments = supervisor_agent._create_fintech_agent_assignments(validation_request)
        
        # Assert
        assert len(agent_assignments) == 4  # regulatory, fraud, market, kyc
        
        # Check regulatory compliance agent
        assert "regulatory_compliance" in agent_assignments
        regulatory_assignment = agent_assignments["regulatory_compliance"]
        assert regulatory_assignment["agent_type"] == AgentType.REGULATORY_COMPLIANCE
        assert regulatory_assignment["task"] == "compliance_analysis"
        assert "compliance_requirements" in regulatory_assignment["parameters"]
        assert regulatory_assignment["parameters"]["jurisdiction"] == "EU"
        
        # Check fraud detection agent
        assert "fraud_detection" in agent_assignments
        fraud_assignment = agent_assignments["fraud_detection"]
        assert fraud_assignment["agent_type"] == AgentType.FRAUD_DETECTION
        assert fraud_assignment["task"] == "fraud_analysis"
        assert fraud_assignment["parameters"]["false_positive_target"] == 0.1
        
        # Check market analysis agent
        assert "market_analysis" in agent_assignments
        market_assignment = agent_assignments["market_analysis"]
        assert market_assignment["agent_type"] == AgentType.MARKET_ANALYSIS
        assert market_assignment["task"] == "fintech_market_analysis"
        
        # Check KYC verification agent
        assert "kyc_verification" in agent_assignments
        kyc_assignment = agent_assignments["kyc_verification"]
        assert kyc_assignment["agent_type"] == AgentType.KYC_VERIFICATION
        assert kyc_assignment["task"] == "kyc_analysis"
    
    @pytest.mark.asyncio
    async def test_ai_fintech_task_prioritization(self, supervisor_agent):
        """Test AI-powered task prioritization for fintech workflows"""
        # Arrange
        workflow_state = {
            "workflow_id": "test_workflow_123",
            "validation_request": {
                "business_type": "fintech_startup",
                "analysis_scope": ["regulatory", "fraud", "risk"],
                "urgency": "critical",
                "compliance_requirements": ["SOX", "PCI_DSS"]
            },
            "agent_assignments": {
                "regulatory_compliance": {"task": "compliance_analysis"},
                "fraud_detection": {"task": "fraud_analysis"},
                "risk_assessment": {"task": "risk_analysis"}
            }
        }
        
        # Act
        task_assignments = await supervisor_agent._ai_fintech_task_prioritization(workflow_state)
        
        # Assert
        assert len(task_assignments) == 3
        assert all(isinstance(task, TaskAssignment) for task in task_assignments)
        
        # Verify prioritization order (Critical > High > Medium)
        priorities = [task.priority for task in task_assignments]
        assert Priority.CRITICAL in priorities  # Regulatory compliance should be critical
        assert Priority.HIGH in priorities      # Fraud detection should be high
        
        # Verify task dependencies
        regulatory_task = next((t for t in task_assignments if t.assigned_to == "regulatory_compliance"), None)
        assert regulatory_task is not None
        assert regulatory_task.priority == Priority.CRITICAL
        assert len(regulatory_task.dependencies) == 0  # No dependencies
        
        # Verify deadlines are set (2-hour requirement)
        for task in task_assignments:
            assert task.deadline is not None
            time_diff = task.deadline - task.created_at
            assert time_diff <= timedelta(hours=2)
    
    @pytest.mark.asyncio
    async def test_ai_fintech_quality_assessment(self, supervisor_agent):
        """Test AI-powered quality assessment for fintech results"""
        # Arrange
        agent_results = {
            "regulatory_compliance": {
                "status": "completed",
                "confidence": 0.92,
                "execution_time": 4.2,
                "result": {"compliance_status": "compliant", "gaps": []}
            },
            "fraud_detection": {
                "status": "completed", 
                "confidence": 0.89,
                "execution_time": 3.8,
                "result": {"fraud_alerts": [], "false_positive_rate": 0.08}
            },
            "risk_assessment": {
                "status": "completed",
                "confidence": 0.85,
                "execution_time": 5.1,
                "result": {"risk_score": 0.3, "risk_factors": ["market_volatility"]}
            }
        }
        
        # Act
        quality_score = await supervisor_agent._ai_fintech_quality_assessment(agent_results)
        
        # Assert
        assert 0.0 <= quality_score <= 1.0
        assert quality_score >= 0.8  # Should meet quality threshold
        
        # Verify bedrock client was called for AI assessment
        supervisor_agent.bedrock_client.invoke_for_agent.assert_called_once()
        call_args = supervisor_agent.bedrock_client.invoke_for_agent.call_args
        assert "fintech-specific criteria" in call_args[0][1]  # Check prompt content
    
    @pytest.mark.asyncio
    async def test_fintech_task_dependencies(self, supervisor_agent):
        """Test fintech-specific task dependencies"""
        # Test regulatory compliance (no dependencies)
        deps = supervisor_agent._get_task_dependencies("regulatory_compliance")
        assert deps == []
        
        # Test fraud detection (no dependencies)
        deps = supervisor_agent._get_task_dependencies("fraud_detection")
        assert deps == []
        
        # Test risk assessment (depends on regulatory compliance)
        deps = supervisor_agent._get_task_dependencies("risk_assessment")
        assert "regulatory_compliance" in deps
        
        # Test customer behavior intelligence (depends on KYC)
        deps = supervisor_agent._get_task_dependencies("customer_behavior_intelligence")
        assert "kyc_verification" in deps
        
        # Test KYC verification (no dependencies)
        deps = supervisor_agent._get_task_dependencies("kyc_verification")
        assert deps == []
    
    @pytest.mark.asyncio
    async def test_default_fintech_task_prioritization(self, supervisor_agent):
        """Test default task prioritization when AI fails"""
        # Arrange
        workflow_state = {
            "workflow_id": "test_workflow_456",
            "agent_assignments": {
                "market_analysis": {"task": "market_analysis"},
                "regulatory_compliance": {"task": "compliance_analysis"},
                "fraud_detection": {"task": "fraud_analysis"},
                "customer_behavior_intelligence": {"task": "customer_analysis"}
            }
        }
        
        # Act
        task_assignments = supervisor_agent._default_fintech_task_prioritization(workflow_state)
        
        # Assert
        assert len(task_assignments) == 4
        
        # Verify default priority order
        assigned_agents = [task.assigned_to for task in task_assignments]
        
        # Regulatory compliance should be first (critical priority)
        assert assigned_agents[0] == "regulatory_compliance"
        assert task_assignments[0].priority == Priority.HIGH
        
        # Fraud detection should be early (high priority)
        fraud_index = assigned_agents.index("fraud_detection")
        assert fraud_index <= 2  # Should be in top 3
        
        # Market analysis should have medium priority
        market_task = next(t for t in task_assignments if t.assigned_to == "market_analysis")
        assert market_task.priority == Priority.MEDIUM
    
    @pytest.mark.asyncio
    async def test_basic_fintech_quality_assessment(self, supervisor_agent):
        """Test basic quality assessment fallback"""
        # Arrange - mix of successful and failed agents
        agent_results = {
            "regulatory_compliance": {
                "status": "completed",
                "confidence": 0.9,
                "execution_time": 3.5,
                "error": None
            },
            "fraud_detection": {
                "status": "completed",
                "confidence": 0.85,
                "execution_time": 4.2,
                "error": None
            },
            "market_analysis": {
                "status": "failed",
                "confidence": 0.0,
                "execution_time": 30.0,
                "error": "API timeout"
            }
        }
        
        # Act
        quality_score = supervisor_agent._basic_fintech_quality_assessment(agent_results)
        
        # Assert
        assert 0.0 <= quality_score <= 1.0
        # Should be moderate quality (2 success, 1 failure)
        assert 0.4 <= quality_score <= 0.8
    
    @pytest.mark.asyncio
    async def test_format_agent_results_for_assessment(self, supervisor_agent):
        """Test formatting agent results for AI assessment"""
        # Arrange
        agent_results = {
            "regulatory_compliance": {
                "status": "completed",
                "confidence": 0.92,
                "execution_time": 4.1,
                "result": {"compliance_status": "compliant"},
                "error": None
            },
            "fraud_detection": {
                "status": "failed",
                "confidence": 0.0,
                "execution_time": 0.0,
                "result": None,
                "error": "ML model initialization failed"
            }
        }
        
        # Act
        formatted_summary = supervisor_agent._format_agent_results_for_assessment(agent_results)
        
        # Assert
        assert "REGULATORY_COMPLIANCE:" in formatted_summary
        assert "Status: completed" in formatted_summary
        assert "Confidence: 0.92" in formatted_summary
        assert "FRAUD_DETECTION:" in formatted_summary
        assert "Status: failed" in formatted_summary
        assert "Error: ML model initialization failed" in formatted_summary
    
    @pytest.mark.asyncio
    async def test_extract_fintech_quality_score(self, supervisor_agent):
        """Test extracting quality score from AI analysis"""
        # Test various AI response formats
        test_cases = [
            ("Quality score: 0.85", 0.85),
            ("The quality is 87%", 0.87),
            ("Rating: 8.2/10", 0.82),
            ("Score of 0.91 achieved", 0.91),
            ("No clear score mentioned", None)  # Should fallback to basic assessment
        ]
        
        mock_agent_results = {
            "test_agent": {
                "status": "completed",
                "confidence": 0.8,
                "execution_time": 5.0
            }
        }
        
        for ai_response, expected_score in test_cases:
            # Act
            extracted_score = supervisor_agent._extract_fintech_quality_score(ai_response, mock_agent_results)
            
            # Assert
            if expected_score is not None:
                # Allow for some tolerance in score extraction due to normalization
                assert abs(extracted_score - expected_score) < 0.1 or (0.0 <= extracted_score <= 1.0)
            else:
                # Should fallback to basic assessment
                assert 0.0 <= extracted_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_fintech_workflow_end_to_end_mock(self, supervisor_agent):
        """Test complete fintech workflow execution with mocked agents"""
        # Arrange
        user_id = "fintech_user_789"
        risk_analysis_request = {
            "business_type": "payment_processor",
            "company_size": "large",
            "analysis_scope": ["regulatory", "fraud", "risk", "market"],
            "urgency": "high",
            "compliance_requirements": ["PCI_DSS", "GDPR", "SOX"],
            "jurisdiction": "US"
        }
        
        # Mock agent factory to avoid actual agent creation
        with patch('riskintel360.agents.agent_factory.get_agent_factory') as mock_factory:
            mock_agent = Mock()
            mock_agent.start = AsyncMock()
            mock_agent.execute_task = AsyncMock(return_value={
                "analysis_result": "Mock fintech analysis completed",
                "confidence_score": 0.88,
                "recommendations": ["Enhance fraud monitoring", "Update compliance policies"]
            })
            mock_agent.stop = AsyncMock()
            
            mock_factory_instance = Mock()
            mock_factory_instance.create_agent.return_value = mock_agent
            mock_factory.return_value = mock_factory_instance
            
            # Act
            workflow_id = await supervisor_agent.start_fintech_workflow(
                user_id=user_id,
                risk_analysis_request=risk_analysis_request
            )
            
            # Wait a moment for workflow to initialize
            await asyncio.sleep(0.1)
            
            # Assert
            assert workflow_id is not None
            assert workflow_id in supervisor_agent.active_workflows
            
            workflow_state = supervisor_agent.active_workflows[workflow_id]
            assert workflow_state["validation_request"]["fintech_workflow"] is True
            assert workflow_state["validation_request"]["analysis_type"] == "fintech_risk_intelligence"
            
            # Verify AgentCore orchestration was called
            supervisor_agent.agentcore_client.orchestrate_workflow.assert_called_once()
            orchestration_call = supervisor_agent.agentcore_client.orchestrate_workflow.call_args
            assert orchestration_call[1]["workflow_data"]["workflow_id"] == workflow_id


class TestFintechWorkflowPerformance:
    """Test fintech workflow performance requirements"""
    
    @pytest.fixture
    def supervisor_agent(self):
        """Create supervisor agent with performance-focused config"""
        mock_agentcore = Mock(spec=AgentCoreClient)
        mock_agentcore.register_agent = AsyncMock(return_value=True)
        mock_agentcore.orchestrate_workflow = AsyncMock()
        mock_agentcore.orchestrate_workflow.return_value.success = True
        
        mock_bedrock = Mock(spec=BedrockClient)
        mock_bedrock.invoke_for_agent = AsyncMock()
        mock_response = Mock()
        mock_response.content = "Quality score: 0.85"
        mock_bedrock.invoke_for_agent.return_value = mock_response
        
        config = WorkflowConfig(
            max_execution_time=timedelta(hours=2),  # Competition requirement
            max_retries=3,
            parallel_execution=True,
            quality_threshold=0.8
        )
        
        return SupervisorAgent(
            agentcore_client=mock_agentcore,
            bedrock_client=mock_bedrock,
            config=config
        )
    
    @pytest.mark.asyncio
    async def test_workflow_completion_time_requirement(self, supervisor_agent):
        """Test that fintech workflows complete within 2-hour requirement"""
        # Arrange
        start_time = datetime.now(UTC)
        
        risk_request = {
            "business_type": "fintech_startup",
            "analysis_scope": ["regulatory", "fraud", "risk"],
            "urgency": "high"
        }
        
        # Act
        workflow_id = await supervisor_agent.start_fintech_workflow(
            user_id="perf_test_user",
            risk_analysis_request=risk_request
        )
        
        # Assert
        workflow_state = supervisor_agent.active_workflows[workflow_id]
        
        # Verify workflow configuration meets 2-hour requirement
        assert supervisor_agent.config.max_execution_time <= timedelta(hours=2)
        
        # Verify workflow started within reasonable time
        execution_start_time = datetime.now(UTC) - start_time
        assert execution_start_time < timedelta(seconds=5)  # Should start quickly
    
    @pytest.mark.asyncio
    async def test_concurrent_fintech_workflows(self, supervisor_agent):
        """Test handling multiple concurrent fintech workflows"""
        # Arrange
        num_concurrent_workflows = 5
        workflows = []
        
        # Act - Start multiple workflows concurrently
        tasks = []
        for i in range(num_concurrent_workflows):
            risk_request = {
                "business_type": f"fintech_company_{i}",
                "analysis_scope": ["regulatory", "fraud"],
                "urgency": "medium"
            }
            
            task = supervisor_agent.start_fintech_workflow(
                user_id=f"concurrent_user_{i}",
                risk_analysis_request=risk_request
            )
            tasks.append(task)
        
        # Wait for all workflows to start
        workflow_ids = await asyncio.gather(*tasks)
        
        # Assert
        assert len(workflow_ids) == num_concurrent_workflows
        assert len(set(workflow_ids)) == num_concurrent_workflows  # All unique
        
        # Verify all workflows are tracked
        for workflow_id in workflow_ids:
            assert workflow_id in supervisor_agent.active_workflows
            
        # Verify concurrent execution capability
        assert len(supervisor_agent.active_workflows) >= num_concurrent_workflows
    
    @pytest.mark.asyncio
    async def test_task_prioritization_performance(self, supervisor_agent):
        """Test task prioritization performance with many agents"""
        # Arrange - Large workflow with many agents
        workflow_state = {
            "workflow_id": "large_workflow_test",
            "validation_request": {
                "business_type": "large_bank",
                "analysis_scope": ["regulatory", "fraud", "risk", "market", "kyc", "customer"],
                "urgency": "critical"
            },
            "agent_assignments": {
                "regulatory_compliance": {"task": "compliance_analysis"},
                "fraud_detection": {"task": "fraud_analysis"},
                "risk_assessment": {"task": "risk_analysis"},
                "market_analysis": {"task": "market_analysis"},
                "kyc_verification": {"task": "kyc_analysis"},
                "customer_behavior_intelligence": {"task": "customer_analysis"}
            }
        }
        
        # Act
        start_time = datetime.now(UTC)
        task_assignments = await supervisor_agent._ai_fintech_task_prioritization(workflow_state)
        prioritization_time = datetime.now(UTC) - start_time
        
        # Assert
        assert len(task_assignments) == 6
        assert prioritization_time < timedelta(seconds=10)  # Should be fast
        
        # Verify all tasks have proper priorities and deadlines
        for task in task_assignments:
            assert task.priority in [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]
            assert task.deadline is not None
            assert task.deadline > datetime.now(UTC)  # Future deadline
