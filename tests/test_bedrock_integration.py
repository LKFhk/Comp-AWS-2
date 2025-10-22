"""
Unit tests for Amazon Bedrock Nova integration.
Tests model selection, retry logic, authentication, and response handling.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock, PropertyMock
from botocore.exceptions import ClientError, BotoCoreError
from tenacity import RetryError

from riskintel360.services.bedrock_client import (
    BedrockClient,
    ModelType,
    AgentType,
    BedrockRequest,
    BedrockResponse,
    BedrockClientError,
    BedrockAuthenticationError,
    BedrockRateLimitError,
    create_bedrock_client
)


class TestBedrockClient:
    """Test suite for BedrockClient class"""
    
    @pytest.fixture
    def mock_boto3_session(self):
        """Mock boto3 session and client"""
        with patch('riskintel360.services.bedrock_client.boto3.Session') as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client
            yield mock_session, mock_client
    
    @pytest.fixture
    def bedrock_client(self, mock_boto3_session):
        """Create BedrockClient instance with mocked dependencies"""
        mock_session, mock_client = mock_boto3_session
        client = BedrockClient(region_name="us-east-1")
        return client
    
    def test_bedrock_client_initialization(self, mock_boto3_session):
        """Test BedrockClient initialization with different credential scenarios"""
        mock_session, mock_client = mock_boto3_session
        
        # Test with default credentials
        client = BedrockClient()
        assert client.region_name == "us-east-1"
        mock_session.assert_called_with(region_name="us-east-1")
        
        # Test with explicit credentials
        client = BedrockClient(
            region_name="us-west-2",
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret"
        )
        assert client.region_name == "us-west-2"
        mock_session.assert_called_with(
            region_name="us-west-2",
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret"
        )
    
    def test_bedrock_client_initialization_failure(self):
        """Test BedrockClient initialization failure handling"""
        with patch('riskintel360.services.bedrock_client.boto3.Session') as mock_session:
            mock_session.side_effect = Exception("AWS credentials not found")
            
            with pytest.raises(BedrockAuthenticationError) as exc_info:
                BedrockClient()
            
            assert "Failed to initialize Bedrock client" in str(exc_info.value)
    
    def test_model_selection_for_agents(self, bedrock_client):
        """Test model selection logic for different agent types"""
        # Test all agent type mappings
        expected_mappings = {
            AgentType.MARKET_ANALYSIS: ModelType.HAIKU,
            AgentType.RISK_ASSESSMENT: ModelType.SONNET,
            AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE: ModelType.HAIKU,
            AgentType.REGULATORY_COMPLIANCE: ModelType.HAIKU,
            AgentType.FRAUD_DETECTION: ModelType.OPUS,
        }
        
        for agent_type, expected_model in expected_mappings.items():
            selected_model = bedrock_client.get_model_for_agent(agent_type)
            assert selected_model == expected_model, f"Wrong model for {agent_type}"
    
    def test_claude_request_preparation(self, bedrock_client):
        """Test Claude-3 request formatting"""
        request = BedrockRequest(
            prompt="Test prompt",
            max_tokens=1000,
            temperature=0.5,
            system_prompt="You are a helpful assistant"
        )
        
        body = bedrock_client._prepare_model_request(request, ModelType.HAIKU)
        
        assert body["anthropic_version"] == "bedrock-2023-05-31"
        assert body["max_tokens"] == 1000
        assert body["temperature"] == 0.5
        assert body["system"] == "You are a helpful assistant"
        assert len(body["messages"]) == 1
        assert body["messages"][0]["role"] == "user"
        assert body["messages"][0]["content"] == "Test prompt"
    
    @pytest.mark.asyncio
    async def test_successful_model_invocation(self, bedrock_client):
        """Test successful model invocation"""
        # Mock successful response
        mock_response = {
            "body": Mock(),
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }
        
        response_body = {
            "results": [{"outputText": "This is a test response", "tokenCount": 20, "completionReason": "FINISH"}],
            "inputTextTokenCount": 10
        }
        
        mock_response["body"].read.return_value = json.dumps(response_body)
        
        with patch.object(bedrock_client, 'bedrock_runtime') as mock_runtime:
            mock_runtime.invoke_model.return_value = mock_response
            
            request = BedrockRequest(prompt="Test prompt")
            response = await bedrock_client.invoke_model(request, ModelType.HAIKU)
            
            assert isinstance(response, BedrockResponse)
            assert response.content == "This is a test response"
            assert response.model_id == ModelType.HAIKU.value
            assert response.input_tokens == 10
            assert response.output_tokens == 20
            assert response.stop_reason == "end_turn"
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, bedrock_client):
        """Test authentication error handling and retry logic"""
        auth_error = ClientError(
            error_response={
                "Error": {
                    "Code": "AccessDenied",
                    "Message": "User is not authorized to perform this action"
                }
            },
            operation_name="InvokeModel"
        )
        
        with patch.object(bedrock_client, 'bedrock_runtime') as mock_runtime:
            mock_runtime.invoke_model.side_effect = auth_error
            
            request = BedrockRequest(prompt="Test prompt")
            
            with pytest.raises(BedrockAuthenticationError) as exc_info:
                await bedrock_client.invoke_model(request, ModelType.HAIKU)
            
            assert "Authentication failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self, bedrock_client):
        """Test rate limiting error handling and retry logic"""
        rate_limit_error = ClientError(
            error_response={
                "Error": {
                    "Code": "ThrottlingException",
                    "Message": "Rate exceeded"
                }
            },
            operation_name="InvokeModel"
        )
        
        with patch.object(bedrock_client, 'bedrock_runtime') as mock_runtime:
            # First two calls fail with rate limit, third succeeds
            mock_response = {
                "body": Mock(),
                "ResponseMetadata": {"HTTPStatusCode": 200}
            }
            response_body = {
                "content": [{"text": "Success after retry"}],
                "usage": {"input_tokens": 5, "output_tokens": 10},
                "stop_reason": "end_turn"
            }
            mock_response["body"].read.return_value = json.dumps(response_body)
            
            mock_runtime.invoke_model.side_effect = [
                rate_limit_error,
                rate_limit_error,
                mock_response
            ]
            
            request = BedrockRequest(prompt="Test prompt")
            response = await bedrock_client.invoke_model(request, ModelType.HAIKU)
            
            # Should succeed after retries
            assert response.content == "Success after retry"
            assert mock_runtime.invoke_model.call_count == 3
    
    @pytest.mark.asyncio
    async def test_max_retry_exceeded(self, bedrock_client):
        """Test behavior when max retries are exceeded"""
        rate_limit_error = ClientError(
            error_response={
                "Error": {
                    "Code": "ThrottlingException",
                    "Message": "Rate exceeded"
                }
            },
            operation_name="InvokeModel"
        )
        
        with patch.object(bedrock_client, 'bedrock_runtime') as mock_runtime:
            # Always fail with rate limit
            mock_runtime.invoke_model.side_effect = rate_limit_error
            
            request = BedrockRequest(prompt="Test prompt")
            
            # Tenacity raises RetryError when max retries exceeded
            with pytest.raises(RetryError):
                await bedrock_client.invoke_model(request, ModelType.HAIKU)
            
            # Should have tried 3 times (initial + 2 retries)
            assert mock_runtime.invoke_model.call_count == 3
    
    @pytest.mark.asyncio
    async def test_invoke_for_agent_convenience_method(self, bedrock_client):
        """Test the convenience method for agent-specific invocation"""
        mock_response = {
            "body": Mock(),
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }
        
        response_body = {
            "content": [{"text": "Agent response"}],
            "usage": {"input_tokens": 15, "output_tokens": 25},
            "stop_reason": "end_turn"
        }
        
        mock_response["body"].read.return_value = json.dumps(response_body)
        
        with patch.object(bedrock_client, 'bedrock_runtime') as mock_runtime:
            mock_runtime.invoke_model.return_value = mock_response
            
            response = await bedrock_client.invoke_for_agent(
                agent_type=AgentType.MARKET_ANALYSIS,
                prompt="Analyze market trends",
                system_prompt="You are a market research expert",
                max_tokens=2000,
                temperature=0.3
            )
            
            assert response.content == "Agent response"
            assert response.model_id == ModelType.HAIKU.value  # Market research uses Haiku
    
    def test_connection_test_success(self, bedrock_client):
        """Test successful connection test"""
        with patch.object(bedrock_client, 'bedrock_runtime') as mock_runtime:
            mock_runtime.list_foundation_models.return_value = {
                "modelSummaries": [{"modelId": "test-model"}]
            }
            
            result = bedrock_client.test_connection()
            assert result is True
    
    def test_connection_test_failure(self, bedrock_client):
        """Test failed connection test"""
        with patch.object(bedrock_client, 'bedrock_runtime') as mock_runtime:
            # Mock the _service_model attribute to raise an exception when accessed
            type(mock_runtime)._service_model = PropertyMock(side_effect=Exception("Connection failed"))
            
            result = bedrock_client.test_connection()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_available_models(self, bedrock_client):
        """Test getting available models"""
        mock_models = {
            "modelSummaries": [
                {"modelId": "anthropic.claude-3-haiku-20240307-v1:0", "modelName": "Claude 3 Haiku"},
                {"modelId": "anthropic.claude-3-sonnet-20240229-v1:0", "modelName": "Claude 3 Sonnet"},
                {"modelId": "other.model-v1:0", "modelName": "Other Model"}
            ]
        }
        
        # Mock the session.client method to return a mock bedrock client
        with patch.object(bedrock_client.session, 'client') as mock_client_factory:
            mock_bedrock_client = Mock()
            mock_bedrock_client.list_foundation_models.return_value = mock_models
            mock_client_factory.return_value = mock_bedrock_client
            
            models = await bedrock_client.get_available_models()
            
            # Should only return Claude models
            assert len(models) == 2
            assert all("claude" in model["modelId"].lower() for model in models)
            
            # Verify the correct client was created
            mock_client_factory.assert_called_with("bedrock")
    
    @pytest.mark.asyncio
    async def test_malformed_response_handling(self, bedrock_client):
        """Test handling of malformed API responses"""
        mock_response = {
            "body": Mock(),
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }
        
        # Malformed response missing required fields
        response_body = {"invalid": "response"}
        mock_response["body"].read.return_value = json.dumps(response_body)
        
        with patch.object(bedrock_client, 'bedrock_runtime') as mock_runtime:
            mock_runtime.invoke_model.return_value = mock_response
            
            request = BedrockRequest(prompt="Test prompt")
            
            with pytest.raises(BedrockClientError) as exc_info:
                await bedrock_client.invoke_model(request, ModelType.HAIKU)
            
            assert "Failed to parse model response" in str(exc_info.value)


class TestBedrockClientFactory:
    """Test suite for BedrockClient factory function"""
    
    @patch('riskintel360.services.bedrock_client.BedrockClient')
    def test_create_bedrock_client_default(self, mock_bedrock_client):
        """Test factory function with default parameters"""
        create_bedrock_client()
        
        mock_bedrock_client.assert_called_once_with(
            region_name="us-east-1",
            aws_access_key_id=None,
            aws_secret_access_key=None,
            aws_session_token=None
        )
    
    @patch('riskintel360.services.bedrock_client.BedrockClient')
    def test_create_bedrock_client_with_credentials(self, mock_bedrock_client):
        """Test factory function with explicit credentials"""
        create_bedrock_client(
            region_name="us-west-2",
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            aws_session_token="test_token"
        )
        
        mock_bedrock_client.assert_called_once_with(
            region_name="us-west-2",
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            aws_session_token="test_token"
        )


class TestBedrockDataClasses:
    """Test suite for Bedrock data classes"""
    
    def test_bedrock_request_creation(self):
        """Test BedrockRequest data class"""
        request = BedrockRequest(
            prompt="Test prompt",
            max_tokens=1000,
            temperature=0.5,
            stop_sequences=["STOP"]
        )
        
        assert request.prompt == "Test prompt"
        assert request.max_tokens == 1000
        assert request.temperature == 0.5
        assert request.stop_sequences == ["STOP"]
        assert request.system_prompt is None  # Default value
    
    def test_bedrock_response_creation(self):
        """Test BedrockResponse data class"""
        response = BedrockResponse(
            content="Response content",
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            input_tokens=10,
            output_tokens=20,
            stop_reason="end_turn",
            raw_response={"test": "data"}
        )
        
        assert response.content == "Response content"
        assert response.model_id == "anthropic.claude-3-haiku-20240307-v1:0"
        assert response.input_tokens == 10
        assert response.output_tokens == 20
        assert response.stop_reason == "end_turn"
        assert response.raw_response == {"test": "data"}


class TestBedrockEnums:
    """Test suite for Bedrock enums"""
    
    def test_model_type_enum(self):
        """Test ModelType enum values"""
        assert ModelType.HAIKU.value == "anthropic.claude-3-haiku-20240307-v1:0"
        assert ModelType.SONNET.value == "anthropic.claude-3-5-sonnet-20241022-v2:0"
        assert ModelType.OPUS.value == "anthropic.claude-3-opus-20240229-v1:0"
    
    def test_agent_type_enum(self):
        """Test AgentType enum values"""
        assert AgentType.MARKET_ANALYSIS.value == "market_analysis"
        assert AgentType.RISK_ASSESSMENT.value == "risk_assessment"
        assert AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE.value == "customer_behavior_intelligence"
        assert AgentType.REGULATORY_COMPLIANCE.value == "regulatory_compliance"
        assert AgentType.FRAUD_DETECTION.value == "fraud_detection"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
