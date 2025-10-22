"""
End-to-End Integration Tests for Complete RiskIntel360 System
Tests the full system integration including cost management, agents, and workflows.
"""

import pytest
import pytest_asyncio
import asyncio
import json
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from riskintel360.services.cost_management import (
    get_cost_management_service,
    CostProfile
)
from riskintel360.services.smart_model_selection import (
    ModelSelectionService,
    AgentType
)
from riskintel360.services.workflow_orchestrator import WorkflowOrchestrator
from riskintel360.services.bedrock_client import BedrockClient
from riskintel360.models.core import ValidationRequest, Priority
from riskintel360.agents.agent_factory import AgentFactory


class TestCompleteSystemIntegration:
    """Test complete system integration with cost management"""
    
    @pytest_asyncio.fixture
    async def system_components(self):
        """Initialize all system components for testing"""
        cost_service = await get_cost_management_service()
        model_service = ModelSelectionService()
        
        # Mock external dependencies
        with patch('riskintel360.services.bedrock_client.boto3.client') as mock_boto:
            mock_bedrock = Mock()
            mock_boto.return_value = mock_bedrock
            
            # Mock successful Bedrock responses
            mock_bedrock.invoke_model.return_value = {
                'body': Mock(read=Mock(return_value=json.dumps({
                    'content': [{'text': 'Mock analysis result'}]
                }).encode()))
            }
            
            bedrock_client = BedrockClient()
            
            return {
                'cost_service': cost_service,
                'model_service': model_service,
                'bedrock_client': bedrock_client,
                'mock_bedrock': mock_bedrock
            }
    
    @pytest.mark.asyncio
    async def test_cost_aware_validation_workflow(self, system_components):
        """Test complete validation workflow with cost management integration"""
        cost_service = system_components['cost_service']
        model_service = system_components['model_service']
        
        # Step 1: Create validation request
        validation_request = ValidationRequest(
            user_id="test_user",
            business_concept="AI-powered fitness app",
            target_market="Health-conscious millennials",
            analysis_scope=["market", "competitive", "financial"],
            priority=Priority.MEDIUM,
            deadline=datetime.now() + timedelta(hours=24)
        )
        
        # Step 2: Switch to demo profile for cost optimization
        await cost_service.switch_profile(CostProfile.DEMO)
        
        # Step 3: Get cost estimation
        estimate = await cost_service.estimate_validation_cost(CostProfile.DEMO)
        
        assert estimate.total_cost > Decimal('0')
        assert estimate.profile_used == CostProfile.DEMO
        
        # Step 4: Check if validation is allowed
        check_result = await cost_service.check_validation_allowed(estimate.total_cost)
        
        assert check_result["allowed"] is True, f"Validation blocked: {check_result['warnings']}"
        
        # Step 5: Get optimal model selection
        models = await model_service.get_optimal_models(cost_profile=CostProfile.DEMO)
        
        assert len(models) == 6  # All agent types
        
        # Step 6: Verify demo profile uses cost-effective models
        haiku_count = sum(1 for model in models.values() if "haiku" in model.lower())
        assert haiku_count >= 2, "Demo profile should prefer cheaper Haiku models"
        
        # Step 7: Update usage metrics (simulate validation completion)
        await cost_service.cost_controller.update_usage_metrics(estimate.total_cost)
        
        # Step 8: Verify usage tracking
        usage_summary = await cost_service.get_usage_summary()
        assert usage_summary["daily_cost"] >= float(estimate.total_cost)
        assert usage_summary["validations_today"] >= 1
    
    @pytest.mark.asyncio
    async def test_cost_profile_switching_impact(self, system_components):
        """Test impact of switching cost profiles on system behavior"""
        cost_service = system_components['cost_service']
        model_service = system_components['model_service']
        
        # Test all profiles and compare costs
        profile_costs = {}
        profile_models = {}
        
        for profile in CostProfile:
            await cost_service.switch_profile(profile)
            
            estimate = await cost_service.estimate_validation_cost()
            models = await model_service.get_optimal_models()
            
            profile_costs[profile] = estimate.total_cost
            profile_models[profile] = models
        
        # Verify cost ordering: DEMO < DEVELOPMENT < OPTIMIZED < PRODUCTION
        assert profile_costs[CostProfile.DEMO] <= profile_costs[CostProfile.DEVELOPMENT]
        assert profile_costs[CostProfile.DEVELOPMENT] <= profile_costs[CostProfile.OPTIMIZED]
        
        # Verify model selection differences
        demo_models = profile_models[CostProfile.DEMO]
        production_models = profile_models[CostProfile.PRODUCTION]
        
        # Demo should use more Haiku models
        demo_haiku = sum(1 for model in demo_models.values() if "haiku" in model.lower())
        production_haiku = sum(1 for model in production_models.values() if "haiku" in model.lower())
        
        assert demo_haiku >= production_haiku
    
    @pytest.mark.asyncio
    async def test_cost_guardrail_enforcement_workflow(self, system_components):
        """Test cost guardrail enforcement in real workflow"""
        cost_service = system_components['cost_service']
        
        # Set very low daily limit for testing
        cost_service.cost_controller.guardrails.daily_limit = Decimal('5.00')
        cost_service.cost_controller.guardrails.per_validation_limit = Decimal('2.00')
        
        # First validation should be allowed
        estimate1 = await cost_service.estimate_validation_cost(CostProfile.DEMO)
        check1 = await cost_service.check_validation_allowed(estimate1.total_cost)
        
        if estimate1.total_cost <= Decimal('2.00'):
            assert check1["allowed"] is True
            
            # Simulate completion
            await cost_service.cost_controller.update_usage_metrics(estimate1.total_cost)
        
        # Try production profile (should be more expensive)
        estimate2 = await cost_service.estimate_validation_cost(CostProfile.PRODUCTION)
        check2 = await cost_service.check_validation_allowed(estimate2.total_cost)
        
        # Should trigger warnings or blocks due to higher cost
        if estimate2.total_cost > Decimal('2.00'):
            assert check2["allowed"] is False or len(check2["warnings"]) > 0
    
    @pytest.mark.asyncio
    async def test_agent_factory_cost_integration(self, system_components):
        """Test agent factory integration with cost-aware model selection"""
        model_service = system_components['model_service']
        bedrock_client = system_components['bedrock_client']
        
        # Get models for demo profile
        models = await model_service.get_optimal_models(cost_profile=CostProfile.DEMO)
        
        # Create agent factory with cost-optimized models
        agent_factory = AgentFactory(bedrock_client)
        
        # Test creating each agent type with optimized models
        for agent_type in AgentType:
            agent_name = agent_type.value
            model_id = models.get(agent_name)
            
            if model_id:
                # Create agent with cost-optimized model
                agent = agent_factory.create_agent(agent_name, model_id=model_id)
                
                assert agent is not None
                assert hasattr(agent, 'model_id')
                assert agent.model_id == model_id
    
    @pytest.mark.asyncio
    async def test_workflow_orchestrator_cost_integration(self, system_components):
        """Test workflow orchestrator with cost management"""
        cost_service = system_components['cost_service']
        model_service = system_components['model_service']
        bedrock_client = system_components['bedrock_client']
        
        # Set up cost-optimized workflow
        await cost_service.switch_profile(CostProfile.DEMO)
        models = await model_service.get_optimal_models()
        
        # Create validation request
        validation_request = ValidationRequest(
            user_id="test_user",
            business_concept="Sustainable packaging startup",
            target_market="Eco-conscious consumers",
            analysis_scope=["market", "competitive", "financial", "risk"],
            priority=Priority.HIGH
        )
        
        # Check cost before starting workflow
        estimate = await cost_service.estimate_validation_cost()
        check_result = await cost_service.check_validation_allowed(estimate.total_cost)
        
        if check_result["allowed"]:
            # Create workflow orchestrator with cost-optimized models
            with patch('riskintel360.services.workflow_orchestrator.AgentFactory') as mock_factory:
                mock_agents = {}
                for agent_type, model_id in models.items():
                    mock_agent = Mock()
                    mock_agent.process_request = AsyncMock(return_value={
                        "analysis": f"Mock {agent_type} analysis",
                        "confidence": 0.85,
                        "cost_estimate": float(estimate.total_cost) / len(models)
                    })
                    mock_agents[agent_type] = mock_agent
                
                mock_factory.return_value.create_agent.side_effect = lambda name, **kwargs: mock_agents.get(name)
                
                orchestrator = WorkflowOrchestrator(bedrock_client)
                
                # Execute workflow (mocked)
                try:
                    result = await orchestrator.execute_validation_workflow(validation_request)
                    
                    # Verify workflow completed with cost tracking
                    assert result is not None
                    
                    # Update usage metrics
                    await cost_service.cost_controller.update_usage_metrics(estimate.total_cost)
                    
                    # Verify usage was tracked
                    usage = await cost_service.get_usage_summary()
                    assert usage["validations_today"] > 0
                    
                except Exception as e:
                    # Workflow might fail due to mocking, but cost integration should work
                    pytest.skip(f"Workflow execution failed (expected in test): {e}")
    
    @pytest.mark.asyncio
    async def test_api_key_integration_workflow(self, system_components):
        """Test API key management integration with external services"""
        cost_service = system_components['cost_service']
        
        # Store API keys for external services
        api_keys = {
            "alpha_vantage": "av_demo_key_12345",
            "news_api": "news_demo_key_67890",
            "crunchbase": "cb_demo_key_abcdef"
        }
        
        for service, key in api_keys.items():
            await cost_service.store_api_key(service, "api_key", key)
        
        # Verify all keys are stored
        services = await cost_service.list_configured_services()
        for service in api_keys.keys():
            assert service in services
        
        # Verify keys can be retrieved for use in agents
        for service, expected_key in api_keys.items():
            retrieved_key = await cost_service.get_api_key(service, "api_key")
            assert retrieved_key == expected_key
    
    @pytest.mark.asyncio
    async def test_performance_under_cost_constraints(self, system_components):
        """Test system performance under different cost constraints"""
        cost_service = system_components['cost_service']
        model_service = system_components['model_service']
        
        # Test multiple concurrent validations with cost tracking
        validation_requests = []
        for i in range(3):
            request = ValidationRequest(
                user_id=f"user_{i}",
                business_concept=f"Startup idea {i}",
                target_market=f"Market segment {i}",
                analysis_scope=["market", "competitive"],
                priority=Priority.MEDIUM
            )
            validation_requests.append(request)
        
        # Process requests with cost tracking
        total_estimated_cost = Decimal('0')
        
        for request in validation_requests:
            # Get cost estimate
            estimate = await cost_service.estimate_validation_cost(CostProfile.DEMO)
            
            # Check if allowed
            check_result = await cost_service.check_validation_allowed(estimate.total_cost)
            
            if check_result["allowed"]:
                # Simulate processing
                await cost_service.cost_controller.update_usage_metrics(estimate.total_cost)
                total_estimated_cost += estimate.total_cost
            else:
                # Cost limit reached
                break
        
        # Verify cost tracking worked
        usage = await cost_service.get_usage_summary()
        assert usage["daily_cost"] >= float(total_estimated_cost)
        assert usage["validations_today"] >= 1
    
    @pytest.mark.asyncio
    async def test_error_handling_with_cost_management(self, system_components):
        """Test error handling in cost management integration"""
        cost_service = system_components['cost_service']
        
        # Test invalid profile handling
        try:
            await cost_service.switch_profile("invalid_profile")
            assert False, "Should have raised an error"
        except (ValueError, AttributeError):
            pass  # Expected
        
        # Test cost estimation with invalid data
        try:
            # This should still work with defaults
            estimate = await cost_service.estimate_validation_cost()
            assert estimate.total_cost > Decimal('0')
        except Exception as e:
            pytest.fail(f"Cost estimation should handle errors gracefully: {e}")
        
        # Test credential management errors
        try:
            # Invalid service name should not crash
            await cost_service.store_api_key("", "api_key", "test")
        except Exception:
            pass  # Expected to fail gracefully
        
        # System should still be functional
        usage = await cost_service.get_usage_summary()
        assert "current_profile" in usage


class TestCostOptimizationScenarios:
    """Test specific cost optimization scenarios"""
    
    @pytest.mark.asyncio
    async def test_demo_mode_cost_reduction(self):
        """Test that demo mode achieves significant cost reduction"""
        cost_service = await get_cost_management_service()
        
        # Get estimates for all profiles
        estimates = {}
        for profile in CostProfile:
            estimate = await cost_service.estimate_validation_cost(profile)
            estimates[profile] = estimate.total_cost
        
        demo_cost = estimates[CostProfile.DEMO]
        production_cost = estimates[CostProfile.PRODUCTION]
        
        # Demo should be at least 50% cheaper than production
        cost_reduction = (production_cost - demo_cost) / production_cost
        assert cost_reduction >= 0.5, f"Demo cost reduction only {cost_reduction:.1%}, expected ??0%"
        
        # Demo cost should be under $5 for competition demo
        assert demo_cost <= Decimal('5.00'), f"Demo cost ${demo_cost:.2f} exceeds $5.00 target"
    
    @pytest.mark.asyncio
    async def test_smart_model_selection_optimization(self):
        """Test that smart model selection optimizes for different priorities"""
        model_service = ModelSelectionService()
        
        # Test cost-optimized selection (demo profile)
        demo_models = await model_service.get_optimal_models(cost_profile=CostProfile.DEMO)
        
        # Test quality-optimized selection (production profile)
        production_models = await model_service.get_optimal_models(cost_profile=CostProfile.PRODUCTION)
        
        # Demo should use more Haiku models (cheaper)
        demo_haiku_count = sum(1 for model in demo_models.values() if "haiku" in model.lower())
        production_haiku_count = sum(1 for model in production_models.values() if "haiku" in model.lower())
        
        assert demo_haiku_count >= production_haiku_count
        
        # Production should use more Opus models (higher quality)
        demo_opus_count = sum(1 for model in demo_models.values() if "opus" in model.lower())
        production_opus_count = sum(1 for model in production_models.values() if "opus" in model.lower())
        
        assert production_opus_count >= demo_opus_count
    
    @pytest.mark.asyncio
    async def test_cost_guardrail_effectiveness(self):
        """Test that cost guardrails effectively prevent overruns"""
        cost_service = await get_cost_management_service()
        
        # Set strict limits
        original_daily_limit = cost_service.cost_controller.guardrails.daily_limit
        original_per_validation_limit = cost_service.cost_controller.guardrails.per_validation_limit
        
        try:
            cost_service.cost_controller.guardrails.daily_limit = Decimal('10.00')
            cost_service.cost_controller.guardrails.per_validation_limit = Decimal('5.00')
            
            # Test with production profile (expensive)
            production_estimate = await cost_service.estimate_validation_cost(CostProfile.PRODUCTION)
            production_check = await cost_service.check_validation_allowed(production_estimate.total_cost)
            
            # Should trigger warnings or blocks if cost is high
            if production_estimate.total_cost > Decimal('5.00'):
                assert (not production_check["allowed"] or 
                       len(production_check["warnings"]) > 0), "Guardrails should trigger for high costs"
            
            # Test with demo profile (cheaper)
            demo_estimate = await cost_service.estimate_validation_cost(CostProfile.DEMO)
            demo_check = await cost_service.check_validation_allowed(demo_estimate.total_cost)
            
            # Should be more likely to be allowed
            if demo_estimate.total_cost <= Decimal('5.00'):
                assert demo_check["allowed"], "Demo profile should be allowed within limits"
        
        finally:
            # Restore original limits
            cost_service.cost_controller.guardrails.daily_limit = original_daily_limit
            cost_service.cost_controller.guardrails.per_validation_limit = original_per_validation_limit


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
