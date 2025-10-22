"""
Tests for Competition Demo Service

Comprehensive tests for competition demo scenarios and impact tracking.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from riskintel360.services.competition_demo import (
    CompetitionDemoService,
    DemoScenario,
    ImpactMetrics,
    CompetitionMetrics,
    DemoResult
)
from riskintel360.models.core import ValidationRequest, ValidationResult, Priority


class TestCompetitionDemoService:
    """Test suite for CompetitionDemoService"""
    
    @pytest.fixture
    def demo_service(self):
        """Create a demo service instance for testing"""
        return CompetitionDemoService()
    
    @pytest.fixture
    def mock_validation_result(self):
        """Mock validation result for testing"""
        return ValidationResult(
            request_id="demo-test-001",
            overall_score=78.5,
            confidence_level=0.89,
            market_analysis={"market_size": "Large", "growth_rate": 0.15},
            competitive_analysis={"competitors": 5, "intensity": "High"},
            financial_analysis={"revenue_projection": 10000000, "roi": 0.25},
            risk_analysis={"risk_score": 0.3, "barriers": ["Regulatory"]},
            customer_analysis={"segments": 3, "demand": "High"},
            strategic_recommendations=["Proceed with Series A", "Focus on enterprise"],
            supporting_data={},
            generated_at=datetime.now(timezone.utc)
        )
    
    def test_demo_service_initialization(self, demo_service):
        """Test that demo service initializes correctly"""
        assert demo_service is not None
        assert len(demo_service.demo_scenarios) == 4
        assert DemoScenario.SAAS_STARTUP in demo_service.demo_scenarios
        assert DemoScenario.FINTECH_EXPANSION in demo_service.demo_scenarios
        assert DemoScenario.ECOMMERCE_LAUNCH in demo_service.demo_scenarios
        assert DemoScenario.AI_PLATFORM in demo_service.demo_scenarios
    
    def test_demo_scenarios_structure(self, demo_service):
        """Test that demo scenarios have correct structure"""
        for scenario, request in demo_service.demo_scenarios.items():
            assert isinstance(request, ValidationRequest)
            assert request.business_concept is not None
            assert request.target_market is not None
            assert request.analysis_scope == ["market", "competitive", "financial", "risk", "customer"]
            assert request.priority == Priority.HIGH
            assert "industry" in request.custom_parameters
    
    @pytest.mark.asyncio
    async def test_get_demo_scenarios(self, demo_service):
        """Test getting available demo scenarios"""
        scenarios = await demo_service.get_demo_scenarios()
        
        assert len(scenarios) == 4
        for scenario in scenarios:
            assert "id" in scenario
            assert "name" in scenario
            assert "description" in scenario
            assert "target_market" in scenario
            assert "industry" in scenario
            assert "estimated_duration" in scenario
            assert "complexity" in scenario
    
    @pytest.mark.asyncio
    async def test_get_competition_showcase_data(self, demo_service):
        """Test getting competition showcase data"""
        showcase = await demo_service.get_competition_showcase_data()
        
        assert "aws_services_used" in showcase
        assert "agentcore_primitives" in showcase
        assert "reasoning_capabilities" in showcase
        assert "autonomy_features" in showcase
        assert "integration_points" in showcase
        assert "measurable_outcomes" in showcase
        
        # Verify AWS services include required competition services
        aws_services = showcase["aws_services_used"]
        assert any("Bedrock Nova" in service for service in aws_services)
        assert any("AgentCore" in service for service in aws_services)
    
    @pytest.mark.asyncio
    @patch('riskintel360.services.competition_demo.WorkflowOrchestrator')
    async def test_run_demo_scenario(self, mock_orchestrator, demo_service, mock_validation_result):
        """Test running a complete demo scenario"""
        # Mock the workflow orchestrator
        mock_orchestrator_instance = AsyncMock()
        mock_orchestrator_instance.execute_validation.return_value = mock_validation_result
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Run demo scenario
        result = await demo_service.run_demo_scenario(DemoScenario.SAAS_STARTUP)
        
        # Verify result structure
        assert isinstance(result, DemoResult)
        assert result.scenario == DemoScenario.SAAS_STARTUP
        assert result.validation_result == mock_validation_result
        assert isinstance(result.impact_metrics, ImpactMetrics)
        assert isinstance(result.competition_metrics, CompetitionMetrics)
        assert len(result.execution_timeline) > 0
        assert len(result.agent_decision_log) > 0
        assert result.before_after_comparison is not None
    
    def test_calculate_impact_metrics(self, demo_service):
        """Test impact metrics calculation"""
        start_time = 1000.0  # Mock start time
        competition_metrics = CompetitionMetrics(
            bedrock_nova_usage={"claude-3-haiku": 2, "claude-3-opus": 2},
            agentcore_primitives_used=["task_distribution", "agent_coordination"],
            external_api_integrations=8,
            autonomous_decisions_made=24,
            reasoning_steps_completed=156,
            inter_agent_communications=42,
            total_processing_time=2.5,
            peak_concurrency=6
        )
        
        with patch('time.time', return_value=1002.5):  # 2.5 seconds later
            metrics = demo_service._calculate_impact_metrics(
                DemoScenario.SAAS_STARTUP, start_time, competition_metrics
            )
        
        # Verify metrics meet competition requirements
        assert metrics.time_reduction_percentage >= 95.0  # Must meet 95% target
        assert metrics.cost_savings_percentage >= 80.0   # Must meet 80% target
        assert metrics.confidence_score > 0.8
        assert metrics.automation_level > 0.9
        assert metrics.ai_time_hours > 0
        assert metrics.traditional_cost_usd > metrics.ai_cost_usd
    
    def test_generate_before_after_comparison(self, demo_service):
        """Test before/after comparison generation"""
        metrics = ImpactMetrics(
            time_reduction_percentage=95.2,
            cost_savings_percentage=82.1,
            traditional_time_weeks=6,
            ai_time_hours=1.5,
            traditional_cost_usd=45000,
            ai_cost_usd=87.50,
            confidence_score=0.89,
            data_quality_score=0.92,
            automation_level=0.96,
            decision_speed_improvement=0.952
        )
        
        comparison = demo_service._generate_before_after_comparison(
            DemoScenario.SAAS_STARTUP, metrics
        )
        
        # Verify comparison structure
        assert "traditional_process" in comparison
        assert "ai_powered_process" in comparison
        assert "improvements" in comparison
        
        # Verify traditional process details
        traditional = comparison["traditional_process"]
        assert "duration" in traditional
        assert "cost" in traditional
        assert "team_size" in traditional
        assert "manual_tasks" in traditional
        assert "limitations" in traditional
        
        # Verify AI process details
        ai_process = comparison["ai_powered_process"]
        assert "duration" in ai_process
        assert "cost" in ai_process
        assert "team_size" in ai_process
        assert "automated_capabilities" in ai_process
        assert "advantages" in ai_process
        
        # Verify improvements
        improvements = comparison["improvements"]
        assert "time_saved" in improvements
        assert "cost_reduced" in improvements
        assert "95.2%" in improvements["time_saved"]
        assert "82.1%" in improvements["cost_reduced"]
    
    @pytest.mark.asyncio
    @patch('riskintel360.services.competition_demo.WorkflowOrchestrator')
    async def test_execute_tracked_workflow(self, mock_orchestrator, demo_service, mock_validation_result):
        """Test workflow execution with comprehensive tracking"""
        # Mock the workflow orchestrator
        mock_orchestrator_instance = AsyncMock()
        mock_orchestrator_instance.execute_validation.return_value = mock_validation_result
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Prepare tracking structures
        timeline = []
        decision_log = []
        metrics = CompetitionMetrics(
            bedrock_nova_usage={},
            agentcore_primitives_used=[],
            external_api_integrations=0,
            autonomous_decisions_made=0,
            reasoning_steps_completed=0,
            inter_agent_communications=0,
            total_processing_time=0.0,
            peak_concurrency=0
        )
        
        request = demo_service.demo_scenarios[DemoScenario.SAAS_STARTUP]
        
        # Execute tracked workflow
        result = await demo_service._execute_tracked_workflow(
            request, timeline, decision_log, metrics
        )
        
        # Verify tracking data was populated
        assert len(timeline) > 0
        assert len(decision_log) > 0
        assert len(metrics.agentcore_primitives_used) > 0
        assert len(metrics.bedrock_nova_usage) > 0
        assert metrics.autonomous_decisions_made > 0
        assert metrics.reasoning_steps_completed > 0
        
        # Verify timeline events
        timeline_events = [event["event"] for event in timeline]
        assert "agentcore_initialization" in timeline_events
        assert any("bedrock_nova_invocation" in event for event in timeline_events)
        
        # Verify decision log structure
        for decision in decision_log:
            assert "timestamp" in decision
            assert "agent" in decision
            assert "decision" in decision
            assert "reasoning" in decision
            assert "confidence" in decision
            assert 0 <= decision["confidence"] <= 1
    
    def test_scenario_specific_benchmarks(self, demo_service):
        """Test that different scenarios have appropriate benchmarks"""
        scenarios_to_test = [
            (DemoScenario.SAAS_STARTUP, 6, 45000),
            (DemoScenario.FINTECH_EXPANSION, 12, 85000),
            (DemoScenario.ECOMMERCE_LAUNCH, 8, 55000),
            (DemoScenario.AI_PLATFORM, 16, 120000)
        ]
        
        for scenario, expected_weeks, expected_cost in scenarios_to_test:
            metrics = demo_service._calculate_impact_metrics(
                scenario, 1000.0, CompetitionMetrics(
                    bedrock_nova_usage={},
                    agentcore_primitives_used=[],
                    external_api_integrations=0,
                    autonomous_decisions_made=0,
                    reasoning_steps_completed=0,
                    inter_agent_communications=0,
                    total_processing_time=0.0,
                    peak_concurrency=0
                )
            )
            
            assert metrics.traditional_time_weeks == expected_weeks
            assert metrics.traditional_cost_usd == expected_cost
    
    @pytest.mark.asyncio
    async def test_demo_scenario_error_handling(self, demo_service):
        """Test error handling in demo scenario execution"""
        with patch.object(demo_service, '_execute_tracked_workflow', side_effect=Exception("Test error")):
            with pytest.raises(Exception, match="Test error"):
                await demo_service.run_demo_scenario(DemoScenario.SAAS_STARTUP)
    
    def test_competition_metrics_structure(self):
        """Test CompetitionMetrics dataclass structure"""
        metrics = CompetitionMetrics(
            bedrock_nova_usage={"claude-3-haiku": 2, "claude-3-opus": 1},
            agentcore_primitives_used=["task_distribution", "message_routing"],
            external_api_integrations=5,
            autonomous_decisions_made=15,
            reasoning_steps_completed=89,
            inter_agent_communications=23,
            total_processing_time=125.5,
            peak_concurrency=4
        )
        
        assert isinstance(metrics.bedrock_nova_usage, dict)
        assert isinstance(metrics.agentcore_primitives_used, list)
        assert isinstance(metrics.external_api_integrations, int)
        assert isinstance(metrics.autonomous_decisions_made, int)
        assert isinstance(metrics.reasoning_steps_completed, int)
        assert isinstance(metrics.inter_agent_communications, int)
        assert isinstance(metrics.total_processing_time, float)
        assert isinstance(metrics.peak_concurrency, int)
    
    def test_impact_metrics_structure(self):
        """Test ImpactMetrics dataclass structure"""
        metrics = ImpactMetrics(
            time_reduction_percentage=95.5,
            cost_savings_percentage=83.2,
            traditional_time_weeks=8,
            ai_time_hours=1.2,
            traditional_cost_usd=55000,
            ai_cost_usd=80.0,
            confidence_score=0.91,
            data_quality_score=0.94,
            automation_level=0.97,
            decision_speed_improvement=0.955
        )
        
        # Verify all fields are present and have correct types
        assert isinstance(metrics.time_reduction_percentage, float)
        assert isinstance(metrics.cost_savings_percentage, float)
        assert isinstance(metrics.traditional_time_weeks, float)
        assert isinstance(metrics.ai_time_hours, float)
        assert isinstance(metrics.traditional_cost_usd, float)
        assert isinstance(metrics.ai_cost_usd, float)
        assert isinstance(metrics.confidence_score, float)
        assert isinstance(metrics.data_quality_score, float)
        assert isinstance(metrics.automation_level, float)
        assert isinstance(metrics.decision_speed_improvement, float)
        
        # Verify percentage values are reasonable
        assert 0 <= metrics.confidence_score <= 1
        assert 0 <= metrics.data_quality_score <= 1
        assert 0 <= metrics.automation_level <= 1
        assert 0 <= metrics.decision_speed_improvement <= 1


class TestCompetitionDemoIntegration:
    """Integration tests for competition demo functionality"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_demo_workflow(self):
        """Test complete end-to-end demo workflow"""
        # This test would require actual service integration
        # For now, we'll test the structure and flow
        
        demo_service = CompetitionDemoService()
        
        # Verify all required components are available
        assert hasattr(demo_service, 'workflow_orchestrator')
        assert hasattr(demo_service, 'bedrock_client')
        assert hasattr(demo_service, 'agentcore_client')
        assert hasattr(demo_service, 'demo_scenarios')
        
        # Verify all demo scenarios are properly configured
        scenarios = await demo_service.get_demo_scenarios()
        assert len(scenarios) == 4
        
        for scenario in scenarios:
            assert scenario['estimated_duration'] == '1.5-2 hours'
            assert scenario['complexity'] in ['Medium', 'High']
    
    @pytest.mark.asyncio
    async def test_competition_requirements_coverage(self):
        """Test that all AWS AI Agent Competition requirements are covered"""
        demo_service = CompetitionDemoService()
        showcase = await demo_service.get_competition_showcase_data()
        
        # Verify required AWS services
        aws_services = showcase["aws_services_used"]
        required_services = [
            "Amazon Bedrock Nova",
            "Amazon Bedrock AgentCore",
            "Amazon ECS Fargate",
            "Amazon Aurora Serverless"
        ]
        
        for service in required_services:
            assert any(service in aws_service for aws_service in aws_services), f"Missing required service: {service}"
        
        # Verify AgentCore primitives
        primitives = showcase["agentcore_primitives"]
        required_primitives = [
            "Task Distribution",
            "Agent Coordination",
            "Message Routing"
        ]
        
        for primitive in required_primitives:
            assert primitive in primitives, f"Missing required primitive: {primitive}"
        
        # Verify measurable outcomes meet competition targets
        outcomes = showcase["measurable_outcomes"]
        assert any("95%" in outcome for outcome in outcomes), "Missing 95% time reduction target"
        assert any("80%" in outcome for outcome in outcomes), "Missing 80% cost savings target"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
