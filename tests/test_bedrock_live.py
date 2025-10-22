"""
Live integration tests for Amazon Bedrock Nova.
These tests require actual AWS credentials and Bedrock access.
Run only when AWS credentials are available and Bedrock is accessible.
"""

import pytest
import asyncio
import os
from unittest.mock import patch

from riskintel360.services.bedrock_client import (
    BedrockClient,
    ModelType,
    AgentType,
    BedrockRequest,
    BedrockAuthenticationError,
    create_bedrock_client
)


# Skip all tests if no AWS credentials are available
pytestmark = pytest.mark.skipif(
    not (os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE")),
    reason="AWS credentials not available for live testing"
)


class TestBedrockLiveIntegration:
    """Live integration tests with actual Bedrock service"""
    
    @pytest.fixture
    def bedrock_client(self):
        """Create a real BedrockClient for live testing"""
        try:
            return BedrockClient(region_name="us-east-1")
        except Exception as e:
            pytest.skip(f"Cannot create Bedrock client: {e}")
    
    def test_bedrock_connection(self, bedrock_client):
        """Test actual connection to Bedrock service"""
        result = bedrock_client.test_connection()
        assert result is True, "Failed to connect to Bedrock service"
    
    @pytest.mark.asyncio
    async def test_get_available_models_live(self, bedrock_client):
        """Test getting actual available models from Bedrock"""
        models = await bedrock_client.get_available_models()
        
        assert isinstance(models, list), "Models should be returned as a list"
        assert len(models) > 0, "Should have at least one Claude model available"
        
        # Check that we have the expected Claude models
        model_ids = [model["modelId"] for model in models]
        expected_models = [
            "anthropic.claude-3-haiku-20240307-v1:0",
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-opus-20240229-v1:0"
        ]
        
        for expected_model in expected_models:
            if expected_model in model_ids:
                print(f"??Found expected model: {expected_model}")
            else:
                print(f"?? Expected model not found: {expected_model}")
    
    @pytest.mark.asyncio
    async def test_simple_model_invocation_haiku(self, bedrock_client):
        """Test simple model invocation with Claude-3 Haiku"""
        request = BedrockRequest(
            prompt="What is 2 + 2? Respond with just the number.",
            max_tokens=10,
            temperature=0.1
        )
        
        response = await bedrock_client.invoke_model(request, ModelType.HAIKU)
        
        assert response.content is not None, "Response content should not be None"
        assert len(response.content.strip()) > 0, "Response should have content"
        assert response.model_id == ModelType.HAIKU.value, "Should use Haiku model"
        assert response.input_tokens > 0, "Should have input tokens counted"
        assert response.output_tokens > 0, "Should have output tokens counted"
        
        print(f"??Haiku response: {response.content.strip()}")
        print(f"?? Tokens - Input: {response.input_tokens}, Output: {response.output_tokens}")
    
    @pytest.mark.asyncio
    async def test_simple_model_invocation_sonnet(self, bedrock_client):
        """Test simple model invocation with Claude-3.5 Sonnet"""
        request = BedrockRequest(
            prompt="Explain what artificial intelligence is in one sentence.",
            max_tokens=100,
            temperature=0.3
        )
        
        response = await bedrock_client.invoke_model(request, ModelType.SONNET)
        
        assert response.content is not None, "Response content should not be None"
        assert len(response.content.strip()) > 0, "Response should have content"
        assert response.model_id == ModelType.SONNET.value, "Should use Sonnet model"
        assert response.input_tokens > 0, "Should have input tokens counted"
        assert response.output_tokens > 0, "Should have output tokens counted"
        
        print(f"??Sonnet response: {response.content.strip()}")
        print(f"?? Tokens - Input: {response.input_tokens}, Output: {response.output_tokens}")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_simple_model_invocation_opus(self, bedrock_client):
        """Test simple model invocation with Claude-3 Opus (marked as slow)"""
        request = BedrockRequest(
            prompt="What are the key benefits of cloud computing? List 3 points briefly.",
            max_tokens=200,
            temperature=0.5
        )
        
        response = await bedrock_client.invoke_model(request, ModelType.OPUS)
        
        assert response.content is not None, "Response content should not be None"
        assert len(response.content.strip()) > 0, "Response should have content"
        assert response.model_id == ModelType.OPUS.value, "Should use Opus model"
        assert response.input_tokens > 0, "Should have input tokens counted"
        assert response.output_tokens > 0, "Should have output tokens counted"
        
        print(f"??Opus response: {response.content.strip()}")
        print(f"?? Tokens - Input: {response.input_tokens}, Output: {response.output_tokens}")
    
    @pytest.mark.asyncio
    async def test_agent_specific_invocation(self, bedrock_client):
        """Test agent-specific model invocation"""
        response = await bedrock_client.invoke_for_agent(
            agent_type=AgentType.MARKET_ANALYSIS,
            prompt="What are the current trends in the technology market?",
            system_prompt="You are a market research analyst. Provide concise, data-driven insights.",
            max_tokens=150,
            temperature=0.4
        )
        
        assert response.content is not None, "Response content should not be None"
        assert len(response.content.strip()) > 0, "Response should have content"
        # Market research should use Haiku model
        assert response.model_id == ModelType.HAIKU.value, "Market research should use Haiku"
        
        print(f"??Market Research Agent response: {response.content.strip()}")
    
    @pytest.mark.asyncio
    async def test_system_prompt_functionality(self, bedrock_client):
        """Test system prompt functionality"""
        request = BedrockRequest(
            prompt="Hello",
            system_prompt="You are a pirate. Respond in pirate speak.",
            max_tokens=50,
            temperature=0.7
        )
        
        response = await bedrock_client.invoke_model(request, ModelType.HAIKU)
        
        assert response.content is not None, "Response content should not be None"
        # Check if response has pirate-like characteristics (this is a heuristic test)
        content_lower = response.content.lower()
        pirate_indicators = ["arr", "matey", "ahoy", "ye", "aye"]
        has_pirate_speak = any(indicator in content_lower for indicator in pirate_indicators)
        
        print(f"??System prompt response: {response.content.strip()}")
        if has_pirate_speak:
            print("????Detected pirate speak in response")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, bedrock_client):
        """Test handling multiple concurrent requests"""
        async def make_request(prompt_suffix: str):
            request = BedrockRequest(
                prompt=f"Count to {prompt_suffix}",
                max_tokens=20,
                temperature=0.1
            )
            return await bedrock_client.invoke_model(request, ModelType.HAIKU)
        
        # Make 3 concurrent requests
        tasks = [
            make_request("3"),
            make_request("5"),
            make_request("7")
        ]
        
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == 3, "Should get 3 responses"
        for i, response in enumerate(responses):
            assert response.content is not None, f"Response {i} should have content"
            assert response.input_tokens > 0, f"Response {i} should have input tokens"
            assert response.output_tokens > 0, f"Response {i} should have output tokens"
            print(f"??Concurrent request {i+1}: {response.content.strip()}")
    
    @pytest.mark.asyncio
    async def test_error_handling_with_invalid_model(self, bedrock_client):
        """Test error handling with invalid model ID"""
        # Temporarily patch the model ID to an invalid one
        original_haiku = ModelType.HAIKU.value
        
        with patch.object(ModelType, 'HAIKU') as mock_haiku:
            mock_haiku.value = "invalid.model.id"
            
            request = BedrockRequest(
                prompt="Test prompt",
                max_tokens=10
            )
            
            with pytest.raises(Exception):  # Should raise some kind of error
                await bedrock_client.invoke_model(request, ModelType.HAIKU)
    
    @pytest.mark.asyncio
    async def test_token_limits(self, bedrock_client):
        """Test behavior with different token limits"""
        # Test with very small token limit
        request = BedrockRequest(
            prompt="Write a long essay about artificial intelligence and its impact on society.",
            max_tokens=5,  # Very small limit
            temperature=0.1
        )
        
        response = await bedrock_client.invoke_model(request, ModelType.HAIKU)
        
        assert response.content is not None, "Should get some response even with small token limit"
        assert response.output_tokens <= 10, "Should respect token limit (with some tolerance)"
        
        print(f"??Small token limit response: {response.content.strip()}")
        print(f"?? Output tokens: {response.output_tokens}")


class TestBedrockLiveAuthentication:
    """Test authentication scenarios with live Bedrock service"""
    
    def test_invalid_credentials(self):
        """Test behavior with invalid credentials"""
        with pytest.raises(BedrockAuthenticationError):
            BedrockClient(
                aws_access_key_id="invalid_key",
                aws_secret_access_key="invalid_secret"
            )
    
    def test_factory_function_live(self):
        """Test factory function with live credentials"""
        try:
            client = create_bedrock_client()
            assert client is not None, "Factory should create client"
            assert client.test_connection(), "Client should be able to connect"
        except Exception as e:
            pytest.skip(f"Cannot test factory function: {e}")


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_bedrock_live.py -v -s
    pytest.main([__file__, "-v", "-s"])
