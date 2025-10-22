"""
Test suite for AWS Credentials Management System
Tests the secure credential management, validation, and cost estimation features.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from riskintel360.api.main import app
from riskintel360.services.credential_manager import credential_manager, CredentialConfig
from riskintel360.services.cost_management import AWSCostManager, CostProfile


class TestCredentialsAPI:
    """Test the credentials management API endpoints"""
    
    def setup_method(self):
        """Setup test client and mock authentication"""
        self.client = TestClient(app)
        
        # Mock authentication
        self.mock_user = {
            "id": "test-user-123",
            "email": "test@RiskIntel360.com",
            "name": "Test User",
            "role": "analyst"
        }
    
    @patch('riskintel360.api.credentials.get_current_user')
    @patch('riskintel360.services.credential_manager.credential_manager')
    def test_setup_aws_credentials_success(self, mock_credential_manager, mock_get_user):
        """Test successful AWS credentials setup"""
        mock_get_user.return_value = self.mock_user
        mock_credential_manager.setup_aws_credentials = Mock()
        
        # Mock successful validation
        with patch('riskintel360.api.credentials.validate_aws_credentials') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "account_id": "123456789012",
                "user_arn": "arn:aws:iam::123456789012:user/test-user",
                "permissions": ["sts:GetCallerIdentity", "bedrock:ListFoundationModels"]
            }
            
            # Mock cost estimation
            with patch('riskintel360.services.cost_management.AWSCostManager') as mock_cost_manager:
                mock_cost_instance = Mock()
                mock_cost_instance.estimate_validation_cost = AsyncMock(return_value=Mock(
                    to_dict=Mock(return_value={
                        "total_cost_usd": 5.25,
                        "estimated_duration_minutes": 45
                    })
                ))
                mock_cost_manager.return_value = mock_cost_instance
                
                response = self.client.post(
                    "/api/v1/credentials/aws/setup",
                    json={
                        "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                        "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                        "region": "us-east-1"
                    }
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert data["service_name"] == "aws"
        assert data["region"] == "us-east-1"
        assert "permissions" in data
        assert "cost_estimate" in data
    
    @patch('riskintel360.api.credentials.get_current_user')
    def test_setup_aws_credentials_invalid_format(self, mock_get_user):
        """Test AWS credentials setup with invalid format"""
        mock_get_user.return_value = self.mock_user
        
        response = self.client.post(
            "/api/v1/credentials/aws/setup",
            json={
                "access_key_id": "INVALID_KEY_FORMAT",
                "secret_access_key": "short",
                "region": "us-east-1"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('riskintel360.api.credentials.get_current_user')
    @patch('riskintel360.services.credential_manager.credential_manager')
    def test_setup_external_api_key_success(self, mock_credential_manager, mock_get_user):
        """Test successful external API key setup"""
        mock_get_user.return_value = self.mock_user
        mock_credential_manager.store_credential = Mock()
        
        with patch('riskintel360.api.credentials.validate_external_api_key') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "message": "API key format is valid for alpha_vantage"
            }
            
            response = self.client.post(
                "/api/v1/credentials/external/setup",
                json={
                    "service_name": "alpha_vantage",
                    "api_key": "DEMO_API_KEY_12345678"
                }
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert data["service_name"] == "alpha_vantage"
    
    @patch('riskintel360.api.credentials.get_current_user')
    @patch('riskintel360.services.credential_manager.credential_manager')
    def test_list_configured_services(self, mock_credential_manager, mock_get_user):
        """Test listing configured services"""
        mock_get_user.return_value = self.mock_user
        mock_credential_manager.list_services.return_value = [
            "aws", "bedrock", "alpha_vantage", "news_api"
        ]
        
        response = self.client.get("/api/v1/credentials/list")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "aws_services" in data
        assert "external_services" in data
        assert "total_count" in data
        assert data["total_count"] == 4
    
    @patch('riskintel360.api.credentials.get_current_user')
    def test_cost_estimation(self, mock_get_user):
        """Test cost estimation endpoint"""
        mock_get_user.return_value = self.mock_user
        
        with patch('riskintel360.services.cost_management.AWSCostManager') as mock_cost_manager:
            mock_cost_instance = Mock()
            mock_cost_instance.estimate_validation_cost = AsyncMock(return_value=Mock(
                to_dict=Mock(return_value={
                    "total_cost_usd": 8.75,
                    "bedrock_cost": 6.50,
                    "compute_cost": 1.25,
                    "storage_cost": 0.75,
                    "data_transfer_cost": 0.25,
                    "estimated_duration_minutes": 60,
                    "confidence_score": 0.85,
                    "profile": "development"
                })
            ))
            mock_cost_instance.get_cost_optimization_recommendations.return_value = [
                "Consider using Demo profile for testing",
                "Enable auto-scaling to optimize compute costs"
            ]
            mock_cost_manager.return_value = mock_cost_instance
            
            response = self.client.post(
                "/api/v1/credentials/cost/estimate",
                json={
                    "profile": "development",
                    "business_concept": "AI-powered SaaS platform",
                    "analysis_scope": ["market", "competitive", "financial"],
                    "target_market": "Enterprise B2B"
                }
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "estimate" in data
        assert "recommendations" in data
        assert data["estimate"]["total_cost_usd"] == 8.75
    
    @patch('riskintel360.api.credentials.get_current_user')
    @patch('riskintel360.services.credential_manager.credential_manager')
    def test_budget_limits_management(self, mock_credential_manager, mock_get_user):
        """Test budget limits setting and retrieval"""
        mock_get_user.return_value = self.mock_user
        mock_credential_manager.store_credential = Mock()
        mock_credential_manager.get_credential.return_value = Mock(
            additional_config={
                "max_daily_spend": 25.0,
                "max_monthly_spend": 250.0,
                "max_per_validation": 10.0,
                "alert_threshold_percent": 80.0,
                "auto_throttle_enabled": True,
                "user_id": "test-user-123"
            }
        )
        
        # Test setting budget limits
        response = self.client.post(
            "/api/v1/credentials/budget/set",
            json={
                "max_daily_spend": 25.0,
                "max_monthly_spend": 250.0,
                "max_per_validation": 10.0,
                "alert_threshold_percent": 80.0,
                "auto_throttle_enabled": True
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "limits" in data
        
        # Test getting current budget usage
        response = self.client.get("/api/v1/credentials/budget/current")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "limits" in data
        assert "usage" in data
        assert "alerts" in data


class TestCredentialManager:
    """Test the credential manager service"""
    
    def setup_method(self):
        """Setup test environment"""
        self.credential_manager = credential_manager
    
    def test_store_and_retrieve_credential(self):
        """Test storing and retrieving credentials"""
        config = CredentialConfig(
            service_name="test_service",
            api_key="test_api_key_12345",
            region="us-east-1",
            additional_config={"test_param": "test_value"}
        )
        
        # Store credential
        self.credential_manager.store_credential("test_service", config)
        
        # Retrieve credential
        retrieved = self.credential_manager.get_credential("test_service")
        
        assert retrieved is not None
        assert retrieved.service_name == "test_service"
        assert retrieved.api_key == "test_api_key_12345"
        assert retrieved.region == "us-east-1"
        assert retrieved.additional_config["test_param"] == "test_value"
    
    def test_aws_credentials_setup(self):
        """Test AWS credentials setup"""
        self.credential_manager.setup_aws_credentials(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-west-2"
        )
        
        aws_config = self.credential_manager.get_aws_config()
        
        assert aws_config is not None
        assert aws_config["aws_access_key_id"] == "AKIAIOSFODNN7EXAMPLE"
        assert aws_config["region_name"] == "us-west-2"
    
    def test_credential_validation(self):
        """Test credential validation"""
        # Test valid credential
        config = CredentialConfig(
            service_name="aws",
            api_key="AKIAIOSFODNN7EXAMPLE",
            region="us-east-1",
            additional_config={"secret_access_key": "valid_secret_key"}
        )
        self.credential_manager.store_credential("aws", config)
        
        assert self.credential_manager.validate_credentials("aws") is True
        
        # Test invalid credential (missing secret key)
        invalid_config = CredentialConfig(
            service_name="invalid_aws",
            api_key="AKIAIOSFODNN7EXAMPLE",
            region="us-east-1"
        )
        self.credential_manager.store_credential("invalid_aws", invalid_config)
        
        assert self.credential_manager.validate_credentials("invalid_aws") is False
    
    def test_delete_credential(self):
        """Test credential deletion"""
        config = CredentialConfig(
            service_name="delete_test",
            api_key="test_key",
            region="us-east-1"
        )
        
        # Store and verify
        self.credential_manager.store_credential("delete_test", config)
        assert self.credential_manager.get_credential("delete_test") is not None
        
        # Delete and verify
        success = self.credential_manager.delete_credential("delete_test")
        assert success is True
        assert self.credential_manager.get_credential("delete_test") is None


class TestCostManagement:
    """Test the cost management functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.cost_manager = AWSCostManager(CostProfile.DEVELOPMENT)
    
    @pytest.mark.asyncio
    async def test_cost_estimation(self):
        """Test cost estimation for validation requests"""
        estimate = await self.cost_manager.estimate_validation_cost(
            business_concept="AI-powered SaaS platform for enterprise productivity",
            analysis_scope=["market", "competitive", "financial", "risk"],
            target_market="Enterprise B2B (Fortune 500)"
        )
        
        assert estimate.total_cost_usd > 0
        assert estimate.bedrock_cost > 0
        assert estimate.compute_cost > 0
        assert estimate.estimated_duration_minutes > 0
        assert 0 <= estimate.confidence_score <= 1
        assert estimate.profile == CostProfile.DEVELOPMENT
    
    def test_cost_profile_comparison(self):
        """Test different cost profiles"""
        demo_manager = AWSCostManager(CostProfile.DEMO)
        dev_manager = AWSCostManager(CostProfile.DEVELOPMENT)
        prod_manager = AWSCostManager(CostProfile.PRODUCTION)
        
        # Demo should have lowest cost multiplier
        demo_config = demo_manager.config
        dev_config = dev_manager.config
        prod_config = prod_manager.config
        
        assert demo_config['compute_scale'] < dev_config['compute_scale']
        assert dev_config['compute_scale'] < prod_config['compute_scale']
        assert demo_config['max_concurrent_agents'] <= dev_config['max_concurrent_agents']
        assert dev_config['max_concurrent_agents'] <= prod_config['max_concurrent_agents']
    
    @pytest.mark.asyncio
    async def test_cost_guardrails(self):
        """Test cost guardrails functionality"""
        # Test within limits
        result = await self.cost_manager.check_cost_guardrails(5.0)
        assert result[0] is True  # Should be allowed
        
        # Test exceeding per-validation limit
        result = await self.cost_manager.check_cost_guardrails(100.0)
        assert result[0] is False  # Should be blocked
        assert "per-validation limit" in result[1]
    
    def test_model_selection_optimization(self):
        """Test optimal model selection based on complexity and budget"""
        # High complexity, high budget -> Opus
        model = self.cost_manager.get_optimal_model_selection(2.5, 20.0)
        assert "opus" in model.lower()
        
        # Medium complexity, medium budget -> Sonnet
        model = self.cost_manager.get_optimal_model_selection(1.8, 5.0)
        assert "sonnet" in model.lower()
        
        # Low complexity, low budget -> Haiku
        model = self.cost_manager.get_optimal_model_selection(1.2, 1.0)
        assert "haiku" in model.lower()
    
    def test_cost_optimization_recommendations(self):
        """Test cost optimization recommendations"""
        recommendations = self.cost_manager.get_cost_optimization_recommendations()
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should contain profile-specific recommendations
        if self.cost_manager.profile == CostProfile.DEVELOPMENT:
            assert any("Demo profile" in rec for rec in recommendations)


class TestCredentialsIntegration:
    """Integration tests for the complete credentials management system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_aws_setup(self):
        """Test complete AWS credentials setup flow"""
        # This would be a more comprehensive test that:
        # 1. Sets up AWS credentials
        # 2. Validates them
        # 3. Estimates costs
        # 4. Sets budget limits
        # 5. Validates the complete flow
        
        # Mock the external AWS calls
        with patch('boto3.Session') as mock_session:
            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {
                "Account": "123456789012",
                "Arn": "arn:aws:iam::123456789012:user/test-user"
            }
            
            mock_bedrock = Mock()
            mock_bedrock.list_foundation_models.return_value = {
                "modelSummaries": []
            }
            
            mock_session_instance = Mock()
            mock_session_instance.client.side_effect = lambda service, **kwargs: {
                'sts': mock_sts,
                'bedrock': mock_bedrock
            }[service]
            mock_session.return_value = mock_session_instance
            
            # Test the validation function
            from riskintel360.api.credentials import validate_aws_credentials
            
            result = await validate_aws_credentials(
                "AKIAIOSFODNN7EXAMPLE",
                "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "us-east-1"
            )
            
            assert result["valid"] is True
            assert "account_id" in result
            assert "permissions" in result
    
    def test_security_features(self):
        """Test security features of credential management"""
        # Test encryption
        config = CredentialConfig(
            service_name="security_test",
            api_key="sensitive_api_key_12345",
            region="us-east-1",
            additional_config={"secret": "very_secret_value"}
        )
        
        credential_manager.store_credential("security_test", config)
        
        # Verify credentials are encrypted in storage
        # (This would check the actual file to ensure it's encrypted)
        
        # Verify retrieval works correctly
        retrieved = credential_manager.get_credential("security_test")
        assert retrieved.api_key == "sensitive_api_key_12345"
        assert retrieved.additional_config["secret"] == "very_secret_value"
    
    def test_error_handling(self):
        """Test error handling in credential management"""
        # Test invalid service name
        result = credential_manager.get_credential("non_existent_service")
        assert result is None
        
        # Test invalid credential format
        assert not credential_manager.validate_credentials("non_existent_service")
        
        # Test deletion of non-existent credential
        success = credential_manager.delete_credential("non_existent_service")
        assert success is False


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
