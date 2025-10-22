"""
Integration Tests for Cost Management System
Tests the complete cost management functionality including API endpoints.
"""

import pytest
import pytest_asyncio
import asyncio
import json
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from riskintel360.services.cost_management import (
    CostManagementService,
    CostProfile,
    CostProfileManager,
    CostEstimationEngine,
    CostController
)
from riskintel360.services.credential_manager import SecureCredentialManager
from riskintel360.services.smart_model_selection import (
    ModelSelectionService,
    AgentType,
    TaskComplexity
)
from riskintel360.api.main import app
from riskintel360.auth.auth_decorators import require_auth
from riskintel360.models.core import ValidationRequest, Priority


class TestSecureCredentialManager:
    """Test secure credential management"""
    
    @pytest.fixture
    def credential_manager(self):
        """Create credential manager for testing"""
        return SecureCredentialManager()
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_credential(self, credential_manager):
        """Test storing and retrieving encrypted credentials"""
        service = "test_service"
        key_type = "api_key"
        value = "test_api_key_12345"
        
        # Store credential
        await credential_manager.store_credential(service, key_type, value)
        
        # Retrieve credential
        retrieved = await credential_manager.retrieve_credential(service, key_type)
        
        assert retrieved == value
    
    @pytest.mark.asyncio
    async def test_list_services(self, credential_manager):
        """Test listing services with credentials"""
        # Store multiple credentials
        await credential_manager.store_credential("service1", "api_key", "key1")
        await credential_manager.store_credential("service2", "secret", "secret1")
        
        services = await credential_manager.list_services()
        
        assert "service1" in services
        assert "service2" in services
    
    @pytest.mark.asyncio
    async def test_delete_credential(self, credential_manager):
        """Test deleting stored credentials"""
        service = "test_service"
        key_type = "api_key"
        value = "test_key"
        
        # Store and then delete
        await credential_manager.store_credential(service, key_type, value)
        deleted = await credential_manager.delete_credential(service, key_type)
        
        assert deleted is True
        
        # Verify it's gone
        retrieved = await credential_manager.retrieve_credential(service, key_type)
        assert retrieved is None


class TestCostEstimationEngine:
    """Test cost estimation functionality"""
    
    @pytest.fixture
    def estimation_engine(self):
        """Create cost estimation engine for testing"""
        return CostEstimationEngine()
    
    @pytest.mark.asyncio
    async def test_bedrock_cost_estimation(self, estimation_engine):
        """Test Bedrock cost estimation"""
        model_selection = {
            "market_analysis": "anthropic.claude-3-haiku-20240307-v1:0",
            "kyc_verification": "anthropic.claude-3-opus-20240229-v1:0"
        }
        
        estimated_tokens = {
            "market_analysis": (1000, 500),  # input, output
            "kyc_verification": (2000, 1000)
        }
        
        cost = await estimation_engine.estimate_bedrock_cost(model_selection, estimated_tokens)
        
        assert isinstance(cost, Decimal)
        assert cost > Decimal('0')
        
        # Opus should be more expensive than Haiku
        haiku_cost = (Decimal('1000') / 1000) * Decimal('0.00025') + (Decimal('500') / 1000) * Decimal('0.00125')
        opus_cost = (Decimal('2000') / 1000) * Decimal('0.015') + (Decimal('1000') / 1000) * Decimal('0.075')
        expected_total = haiku_cost + opus_cost
        
        assert abs(cost - expected_total) < Decimal('0.001')
    
    @pytest.mark.asyncio
    async def test_infrastructure_cost_estimation(self, estimation_engine):
        """Test infrastructure cost estimation"""
        duration_hours = Decimal('2.0')
        concurrent_agents = 6
        
        costs = await estimation_engine.estimate_infrastructure_cost(duration_hours, concurrent_agents)
        
        assert costs.ecs_cost > Decimal('0')
        assert costs.aurora_cost > Decimal('0')
        assert costs.elasticache_cost > Decimal('0')
        assert costs.total_cost > Decimal('0')


class TestCostProfileManager:
    """Test cost profile management"""
    
    @pytest.fixture
    def profile_manager(self):
        """Create cost profile manager for testing"""
        estimation_engine = CostEstimationEngine()
        return CostProfileManager(estimation_engine)
    
    @pytest.mark.asyncio
    async def test_profile_configurations(self, profile_manager):
        """Test different profile configurations"""
        for profile in CostProfile:
            config = profile_manager.get_profile_config(profile)
            
            assert "model_selection" in config
            assert "token_limits" in config
            assert "parallel_execution" in config
            assert "caching_enabled" in config
            
            # Verify all agents have model assignments
            model_selection = config["model_selection"]
            expected_agents = [
                "market_analysis", "regulatory_compliance", "fraud_detection",
                "risk_assessment", "customer_behavior_intelligence", "kyc_verification"
            ]
            
            for agent in expected_agents:
                assert agent in model_selection
    
    @pytest.mark.asyncio
    async def test_demo_profile_cost_optimization(self, profile_manager):
        """Test that demo profile uses cheaper models"""
        demo_config = profile_manager.get_profile_config(CostProfile.DEMO)
        production_config = profile_manager.get_profile_config(CostProfile.PRODUCTION)
        
        demo_estimate = await profile_manager.estimate_profile_cost(CostProfile.DEMO)
        production_estimate = await profile_manager.estimate_profile_cost(CostProfile.PRODUCTION)
        
        # Demo should be significantly cheaper
        assert demo_estimate.total_cost < production_estimate.total_cost
        assert demo_estimate.total_cost < production_estimate.total_cost * Decimal('0.5')


class TestCostController:
    """Test cost control and guardrails"""
    
    @pytest.fixture
    def cost_controller(self):
        """Create cost controller for testing"""
        credential_manager = SecureCredentialManager()
        return CostController(credential_manager)
    
    @pytest.mark.asyncio
    async def test_cost_limit_checking(self, cost_controller):
        """Test cost limit validation"""
        # Test within limits
        small_cost = Decimal('10.00')
        result = await cost_controller.check_cost_limits(small_cost)
        
        assert result["allowed"] is True
        assert len(result["warnings"]) == 0
        
        # Test exceeding per-validation limit
        large_cost = Decimal('100.00')  # Exceeds default $50 limit
        result = await cost_controller.check_cost_limits(large_cost)
        
        assert result["allowed"] is False
        assert len(result["warnings"]) > 0
    
    @pytest.mark.asyncio
    async def test_usage_metrics_update(self, cost_controller):
        """Test usage metrics tracking"""
        initial_daily = cost_controller.usage_metrics.current_daily_cost
        initial_monthly = cost_controller.usage_metrics.current_monthly_cost
        
        cost_to_add = Decimal('25.50')
        await cost_controller.update_usage_metrics(cost_to_add)
        
        assert cost_controller.usage_metrics.current_daily_cost == initial_daily + cost_to_add
        assert cost_controller.usage_metrics.current_monthly_cost == initial_monthly + cost_to_add
        assert cost_controller.usage_metrics.validations_today > 0
        assert cost_controller.usage_metrics.validations_this_month > 0


class TestCostManagementService:
    """Test the main cost management service"""
    
    @pytest_asyncio.fixture
    async def cost_service(self):
        """Create cost management service for testing"""
        service = CostManagementService()
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, cost_service):
        """Test service initialization"""
        assert cost_service.current_profile in CostProfile
        assert cost_service.credential_manager is not None
        assert cost_service.estimation_engine is not None
        assert cost_service.profile_manager is not None
        assert cost_service.cost_controller is not None
    
    @pytest.mark.asyncio
    async def test_validation_cost_estimation(self, cost_service):
        """Test validation cost estimation"""
        estimate = await cost_service.estimate_validation_cost()
        
        assert isinstance(estimate.total_cost, Decimal)
        assert estimate.total_cost > Decimal('0')
        assert estimate.confidence_level > 0
        assert estimate.profile_used in CostProfile
        assert len(estimate.model_selection) > 0
    
    @pytest.mark.asyncio
    async def test_profile_switching(self, cost_service):
        """Test switching between cost profiles"""
        original_profile = cost_service.current_profile
        
        # Switch to demo profile
        await cost_service.switch_profile(CostProfile.DEMO)
        assert cost_service.current_profile == CostProfile.DEMO
        
        # Switch back
        await cost_service.switch_profile(original_profile)
        assert cost_service.current_profile == original_profile
    
    @pytest.mark.asyncio
    async def test_model_selection_retrieval(self, cost_service):
        """Test getting model selection for profiles"""
        for profile in CostProfile:
            model_selection = await cost_service.get_model_selection(profile)
            
            assert isinstance(model_selection, dict)
            assert len(model_selection) > 0
            
            # Verify all expected agents are present
            expected_agents = [
                "market_analysis", "regulatory_compliance", "fraud_detection",
                "risk_assessment", "customer_behavior_intelligence", "kyc_verification"
            ]
            
            for agent in expected_agents:
                assert agent in model_selection
    
    @pytest.mark.asyncio
    async def test_credential_management(self, cost_service):
        """Test API key storage and retrieval"""
        service = "test_api"
        key_type = "api_key"
        value = "test_key_value"
        
        # Store credential
        await cost_service.store_api_key(service, key_type, value)
        
        # Retrieve credential
        retrieved = await cost_service.get_api_key(service, key_type)
        assert retrieved == value
        
        # List services
        services = await cost_service.list_configured_services()
        assert service in services


class TestSmartModelSelection:
    """Test smart model selection functionality"""
    
    @pytest_asyncio.fixture
    async def model_service(self):
        """Create model selection service for testing"""
        return ModelSelectionService()
    
    @pytest.mark.asyncio
    async def test_optimal_model_selection(self, model_service):
        """Test optimal model selection for different profiles"""
        for profile in CostProfile:
            models = await model_service.get_optimal_models(cost_profile=profile)
            
            assert isinstance(models, dict)
            assert len(models) > 0
            
            # Verify all agent types are covered
            for agent_type in AgentType:
                assert agent_type.value in models
    
    @pytest.mark.asyncio
    async def test_custom_requirements(self, model_service):
        """Test model selection with custom requirements"""
        custom_requirements = {
            "fraud_detection": {
                "complexity": "critical",
                "quality_priority": 0.9,
                "speed_priority": 0.05,
                "cost_priority": 0.05
            }
        }
        
        models = await model_service.get_optimal_models(
            cost_profile=CostProfile.PRODUCTION,
            custom_requirements=custom_requirements
        )
        
        # Financial validation should use Opus for critical tasks
        assert "opus" in models["fraud_detection"].lower()
    
    @pytest.mark.asyncio
    async def test_demo_profile_cost_optimization(self, model_service):
        """Test that demo profile selects cheaper models"""
        demo_models = await model_service.get_optimal_models(cost_profile=CostProfile.DEMO)
        production_models = await model_service.get_optimal_models(cost_profile=CostProfile.PRODUCTION)
        
        # Demo should prefer Haiku and Sonnet over Opus
        demo_haiku_count = sum(1 for model in demo_models.values() if "haiku" in model.lower())
        production_haiku_count = sum(1 for model in production_models.values() if "haiku" in model.lower())
        
        assert demo_haiku_count >= production_haiku_count


class TestCostManagementAPI:
    """Test cost management API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_auth(self):
        """Mock authentication for testing"""
        def mock_require_auth():
            return {"user_id": "test_user", "roles": ["user"]}
        
        app.dependency_overrides[require_auth] = mock_require_auth
        yield
        # Clean up
        if require_auth in app.dependency_overrides:
            del app.dependency_overrides[require_auth]
    
    @pytest.fixture
    def mock_admin_auth(self):
        """Mock admin authentication for testing"""
        def mock_require_admin():
            return {"user_id": "admin_user", "roles": ["admin"]}
        
        from riskintel360.auth.auth_decorators import RequireAdmin
        app.dependency_overrides[RequireAdmin] = mock_require_admin
        yield
        # Clean up
        if RequireAdmin in app.dependency_overrides:
            del app.dependency_overrides[RequireAdmin]
    
    def test_cost_estimation_endpoint(self, client, mock_auth):
        """Test cost estimation API endpoint"""
        response = client.post(
            "/api/v1/cost/estimate",
            json={"profile": "demo"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_cost" in data
        assert "bedrock_cost" in data
        assert "infrastructure_cost" in data
        assert "profile_used" in data
        assert "model_selection" in data
        assert data["total_cost"] > 0
    
    def test_profile_comparison_endpoint(self, client, mock_auth):
        """Test profile comparison API endpoint"""
        response = client.get("/api/v1/cost/profiles/compare")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "profiles" in data
        profiles = data["profiles"]
        
        # Should have all cost profiles
        for profile in CostProfile:
            assert profile.value in profiles
            
            profile_data = profiles[profile.value]
            assert "total_cost" in profile_data
            assert "model_selection" in profile_data
    
    def test_usage_summary_endpoint(self, client, mock_auth):
        """Test usage summary API endpoint"""
        response = client.get("/api/v1/cost/usage")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "current_profile" in data
        assert "daily_cost" in data
        assert "monthly_cost" in data
        assert "daily_limit" in data
        assert "monthly_limit" in data
        assert "daily_usage_percentage" in data
        assert "monthly_usage_percentage" in data
    
    def test_model_selection_endpoint(self, client, mock_auth):
        """Test model selection API endpoint"""
        response = client.get("/api/v1/cost/models/selection?profile=demo")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "profile" in data
        assert "model_selection" in data
        assert data["profile"] == "demo"
        
        model_selection = data["model_selection"]
        assert len(model_selection) > 0
    
    def test_validation_check_endpoint(self, client, mock_auth):
        """Test validation cost check API endpoint"""
        response = client.post(
            "/api/v1/cost/validation/check",
            json={"profile": "production"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "allowed" in data
        assert "estimated_cost" in data
        assert "warnings" in data
        assert "actions" in data
        assert "profile_used" in data
    
    def test_profile_switch_endpoint(self, client, mock_admin_auth):
        """Test profile switching API endpoint (admin only)"""
        response = client.post(
            "/api/v1/cost/profile/switch",
            json={"profile": "demo"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "demo" in data["message"]
    
    def test_credential_storage_endpoint(self, client, mock_admin_auth):
        """Test credential storage API endpoint (admin only)"""
        response = client.post(
            "/api/v1/cost/credentials/store",
            json={
                "service": "test_service",
                "key_type": "api_key",
                "value": "test_key_12345"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "test_service" in data["message"]
    
    def test_health_endpoint(self, client):
        """Test cost management health check endpoint"""
        response = client.get("/api/v1/cost/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "current_profile" in data
        assert "timestamp" in data


class TestEndToEndIntegration:
    """Test complete end-to-end cost management workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_validation_cost_workflow(self):
        """Test complete validation cost estimation and approval workflow"""
        # Initialize services
        cost_service = CostManagementService()
        await cost_service.initialize()
        
        model_service = ModelSelectionService()
        
        # Step 1: Get optimal models for demo profile
        models = await model_service.get_optimal_models(cost_profile=CostProfile.DEMO)
        assert len(models) > 0
        
        # Step 2: Estimate cost for demo profile
        estimate = await cost_service.estimate_validation_cost(CostProfile.DEMO)
        assert estimate.total_cost > Decimal('0')
        
        # Step 3: Check if validation is allowed
        check_result = await cost_service.check_validation_allowed(estimate.total_cost)
        assert "allowed" in check_result
        
        # Step 4: Switch to production profile and compare
        await cost_service.switch_profile(CostProfile.PRODUCTION)
        production_estimate = await cost_service.estimate_validation_cost()
        
        # Production should be more expensive than demo
        assert production_estimate.total_cost > estimate.total_cost
    
    @pytest.mark.asyncio
    async def test_cost_guardrail_enforcement(self):
        """Test cost guardrail enforcement workflow"""
        cost_service = CostManagementService()
        await cost_service.initialize()
        
        # Test with a very high cost that should trigger guardrails
        high_cost = Decimal('1000.00')  # Much higher than default limits
        
        check_result = await cost_service.check_validation_allowed(high_cost)
        
        # Should be blocked by guardrails
        assert check_result["allowed"] is False
        assert len(check_result["warnings"]) > 0
    
    @pytest.mark.asyncio
    async def test_credential_management_workflow(self):
        """Test complete credential management workflow"""
        cost_service = CostManagementService()
        await cost_service.initialize()
        
        # Store multiple API keys
        test_credentials = [
            ("alpha_vantage", "api_key", "av_test_key"),
            ("news_api", "api_key", "news_test_key"),
            ("crunchbase", "api_key", "cb_test_key")
        ]
        
        for service, key_type, value in test_credentials:
            await cost_service.store_api_key(service, key_type, value)
        
        # Verify all services are listed
        services = await cost_service.list_configured_services()
        for service, _, _ in test_credentials:
            assert service in services
        
        # Verify credentials can be retrieved
        for service, key_type, expected_value in test_credentials:
            retrieved = await cost_service.get_api_key(service, key_type)
            assert retrieved == expected_value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
