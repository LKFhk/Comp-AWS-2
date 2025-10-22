"""
Complete End-to-End Integration Test for RiskIntel360 Platform
Tests the full validation workflow with all components working together.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from riskintel360.services.cost_management import AWSCostManager, CostProfile
from riskintel360.services.credential_manager import SecureCredentialManager, CredentialConfig
from riskintel360.services.workflow_orchestrator import WorkflowOrchestrator
from riskintel360.models import ValidationRequest, Priority

class TestCompleteIntegration:
    """Complete integration test suite"""
    
    @pytest.fixture
    def cost_manager(self):
        """Cost manager fixture"""
        return AWSCostManager(CostProfile.DEMO)
    
    @pytest.fixture
    def credential_manager(self):
        """Credential manager fixture"""
        return SecureCredentialManager("test-key")
    
    @pytest.fixture
    def sample_validation_request(self):
        """Sample validation request"""
        return ValidationRequest(
            user_id="test-user",
            business_concept="AI-powered customer service automation platform",
            target_market="Small to medium businesses in North America",
            analysis_scope=["market", "competitive", "financial", "risk", "customer"],
            priority=Priority.MEDIUM
        )
    
    @pytest.mark.asyncio
    async def test_cost_estimation_workflow(self, cost_manager, sample_validation_request):
        """Test complete cost estimation workflow"""
        
        # Test cost estimation
        estimate = await cost_manager.estimate_validation_cost(
            business_concept=sample_validation_request.business_concept,
            analysis_scope=sample_validation_request.analysis_scope,
            target_market=sample_validation_request.target_market
        )
        
        # Verify estimate structure
        assert estimate.total_cost_usd > 0
        assert estimate.bedrock_cost > 0
        assert estimate.compute_cost > 0
        assert estimate.estimated_duration_minutes > 0
        assert estimate.confidence_score > 0
        assert estimate.profile == CostProfile.DEMO
        
        # Test cost guardrails
        can_proceed, message = await cost_manager.check_cost_guardrails(estimate.total_cost_usd)
        assert can_proceed is True
        assert "Within cost limits" in message
        
        # Test model selection
        optimal_model = cost_manager.get_optimal_model_selection(
            complexity=2.0, 
            budget=estimate.total_cost_usd
        )
        assert optimal_model in ['claude-3-haiku', 'claude-3-sonnet', 'claude-3-opus']
        
        print(f"??Cost estimation: ${estimate.total_cost_usd:.4f} for {estimate.estimated_duration_minutes}min")
    
    def test_credential_management_workflow(self, credential_manager):
        """Test complete credential management workflow"""
        
        # Test storing AWS credentials
        credential_manager.setup_aws_credentials(
            access_key_id="AKIA_TEST_KEY",
            secret_access_key="test_secret_key",
            region="us-east-1"
        )
        
        # Test retrieving credentials
        aws_config = credential_manager.get_aws_config()
        assert aws_config is not None
        assert aws_config['aws_access_key_id'] == "AKIA_TEST_KEY"
        assert aws_config['region_name'] == "us-east-1"
        
        # Test credential validation
        is_valid = credential_manager.validate_credentials('aws')
        assert is_valid is True
        
        # Test listing services
        services = credential_manager.list_services()
        assert 'aws' in services
        
        print("??Credential management working correctly")
    
    @pytest.mark.asyncio
    async def test_cost_profile_switching(self, cost_manager, sample_validation_request):
        """Test switching between cost profiles"""
        
        # Test Demo profile
        demo_manager = AWSCostManager(CostProfile.DEMO)
        demo_estimate = await demo_manager.estimate_validation_cost(
            business_concept=sample_validation_request.business_concept,
            analysis_scope=sample_validation_request.analysis_scope,
            target_market=sample_validation_request.target_market
        )
        
        # Test Production profile
        prod_manager = AWSCostManager(CostProfile.PRODUCTION)
        prod_estimate = await prod_manager.estimate_validation_cost(
            business_concept=sample_validation_request.business_concept,
            analysis_scope=sample_validation_request.analysis_scope,
            target_market=sample_validation_request.target_market
        )
        
        # Production should be more expensive than demo
        assert prod_estimate.total_cost_usd > demo_estimate.total_cost_usd
        assert prod_estimate.estimated_duration_minutes >= demo_estimate.estimated_duration_minutes
        
        print(f"??Profile switching: Demo=${demo_estimate.total_cost_usd:.4f}, Prod=${prod_estimate.total_cost_usd:.4f}")
    
    @pytest.mark.asyncio
    async def test_cost_guardrails_enforcement(self, cost_manager):
        """Test cost guardrails enforcement"""
        
        # Test exceeding per-validation limit
        high_cost = cost_manager.guardrails.max_per_validation + 1.0
        can_proceed, message = await cost_manager.check_cost_guardrails(high_cost)
        assert can_proceed is False
        assert "exceeds per-validation limit" in message
        
        # Test approaching daily limit
        cost_manager.current_spend['daily'] = cost_manager.guardrails.max_daily_spend * 0.85
        moderate_cost = 1.0
        can_proceed, message = await cost_manager.check_cost_guardrails(moderate_cost)
        assert can_proceed is True
        assert "Warning" in message
        
        print("??Cost guardrails enforcing limits correctly")
    
    def test_optimization_recommendations(self, cost_manager):
        """Test cost optimization recommendations"""
        
        recommendations = cost_manager.get_cost_optimization_recommendations()
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Demo profile should have specific recommendations
        assert any("Demo profile active" in rec for rec in recommendations)
        
        print(f"??Generated {len(recommendations)} optimization recommendations")
    
    @pytest.mark.asyncio
    async def test_model_selection_optimization(self, cost_manager):
        """Test intelligent model selection based on complexity and budget"""
        
        # Low complexity, low budget -> Basic model
        basic_model = cost_manager.get_optimal_model_selection(complexity=1.0, budget=0.01)
        assert basic_model == 'claude-3-haiku'
        
        # High complexity, high budget -> Premium model
        premium_model = cost_manager.get_optimal_model_selection(complexity=3.0, budget=1.0)
        assert premium_model in ['claude-3-sonnet', 'claude-3-opus']
        
        print("??Model selection optimizing based on complexity and budget")
    
    @pytest.mark.asyncio
    async def test_complete_validation_cost_workflow(self, cost_manager, sample_validation_request):
        """Test complete validation workflow with cost tracking"""
        
        # Step 1: Estimate cost
        estimate = await cost_manager.estimate_validation_cost(
            business_concept=sample_validation_request.business_concept,
            analysis_scope=sample_validation_request.analysis_scope,
            target_market=sample_validation_request.target_market
        )
        
        # Step 2: Check guardrails
        can_proceed, message = await cost_manager.check_cost_guardrails(estimate.total_cost_usd)
        assert can_proceed is True
        
        # Step 3: Select optimal model
        optimal_model = cost_manager.get_optimal_model_selection(
            complexity=2.0,
            budget=estimate.total_cost_usd
        )
        
        # Step 4: Record actual cost (simulate)
        actual_cost = estimate.total_cost_usd * 0.95  # Slightly under estimate
        await cost_manager.record_actual_cost("test-validation-1", actual_cost)
        
        # Verify cost tracking
        assert cost_manager.current_spend['daily'] == actual_cost
        assert cost_manager.current_spend['monthly'] == actual_cost
        
        print(f"??Complete workflow: Estimated=${estimate.total_cost_usd:.4f}, Actual=${actual_cost:.4f}, Model={optimal_model}")
    
    def test_credential_encryption_security(self, credential_manager):
        """Test credential encryption and security"""
        
        # Store sensitive credential
        test_config = CredentialConfig(
            service_name="test_service",
            api_key="super_secret_key_123",
            region="us-west-2",
            additional_config={"secret": "very_secret_value"}
        )
        
        credential_manager.store_credential("test_service", test_config)
        
        # Verify credential is encrypted on disk
        import os
        if os.path.exists(credential_manager.credentials_file):
            with open(credential_manager.credentials_file, 'rb') as f:
                encrypted_content = f.read()
            
            # Should not contain plaintext secrets
            assert b"super_secret_key_123" not in encrypted_content
            assert b"very_secret_value" not in encrypted_content
        
        # Verify we can retrieve and decrypt
        retrieved = credential_manager.get_credential("test_service")
        assert retrieved is not None
        assert retrieved.api_key == "super_secret_key_123"
        assert retrieved.additional_config["secret"] == "very_secret_value"
        
        print("??Credential encryption working securely")
    
    @pytest.mark.asyncio
    async def test_integration_with_mock_agents(self, cost_manager, credential_manager):
        """Test integration with mock agent workflow"""
        
        # Mock agent execution with cost tracking
        validation_id = "integration-test-1"
        
        # Estimate cost for 6-agent workflow
        total_estimate = 0.0
        agent_estimates = []
        
        for agent_name in ["market", "competitive", "financial", "risk", "customer", "synthesis"]:
            estimate = await cost_manager.estimate_validation_cost(
                business_concept=f"Test concept for {agent_name} analysis",
                analysis_scope=[agent_name],
                target_market="Test market"
            )
            agent_estimates.append((agent_name, estimate.total_cost_usd))
            total_estimate += estimate.total_cost_usd
        
        # Check total cost against guardrails
        can_proceed, message = await cost_manager.check_cost_guardrails(total_estimate)
        
        if can_proceed:
            # Simulate agent execution and cost recording
            for agent_name, estimated_cost in agent_estimates:
                actual_cost = estimated_cost * (0.9 + (hash(agent_name) % 20) / 100)  # ±10% variance
                await cost_manager.record_actual_cost(f"{validation_id}-{agent_name}", actual_cost)
        
        print(f"??Multi-agent integration: Total estimated=${total_estimate:.4f}, Can proceed={can_proceed}")
        
        # Verify total spend tracking
        expected_total = sum(est * (0.9 + (hash(name) % 20) / 100) for name, est in agent_estimates)
        assert abs(cost_manager.current_spend['daily'] - expected_total) < 0.01

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])
