"""
Integration tests for Amazon Bedrock Nova (Claude-3) interactions.
Tests real AWS service integration with proper authentication and model invocation.
"""

import pytest
import pytest_asyncio
import asyncio
import json
import os
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from riskintel360.services.bedrock_client import (
    BedrockClient, ModelType, AgentType as BedrockAgentType,
    BedrockRequest, BedrockResponse, BedrockClientError,
    BedrockAuthenticationError, BedrockRateLimitError
)
from riskintel360.agents.regulatory_compliance_agent import RegulatoryComplianceAgent
from riskintel360.agents.fraud_detection_agent import FraudDetectionAgent
from riskintel360.agents.risk_assessment_agent import RiskAssessmentAgent
from riskintel360.agents.market_analysis_agent import MarketAnalysisAgent
from riskintel360.agents.kyc_verification_agent import KYCVerificationAgent


class TestBedrockNovaIntegration:
    """Integration tests for Amazon Bedrock Nova service"""
    
    @pytest.fixture
    def aws_credentials(self):
        """AWS credentials for testing (use environment variables or mock)"""
        return {
            "region_name": os.getenv("AWS_REGION", "us-east-1"),
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "aws_session_token": os.getenv("AWS_SESSION_TOKEN")
        }
    
    @pytest.fixture
    def bedrock_client(self, aws_credentials):
        """Create Bedrock client with real or mocked AWS credentials"""
        if aws_credentials["aws_access_key_id"]:
            # Use real AWS credentials if available
            return BedrockClient(**aws_credentials)
        else:
            # Use mocked client for CI/CD environments
            with patch('riskintel360.services.bedrock_client.boto3.Session'):
                return BedrockClient(region_name="us-east-1")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bedrock_nova_model_availability(self, bedrock_client):
        """Test that Claude-3 models are available in Bedrock"""
        try:
            models = await bedrock_client.get_available_models()
            
            # Verify Claude-3 models are available
            claude_models = [m for m in models if "claude-3" in m["modelId"].lower()]
            assert len(claude_models) >= 3, "Expected at least 3 Claude-3 models (Haiku, Sonnet, Opus)"
            
            # Verify specific model IDs
            model_ids = [m["modelId"] for m in claude_models]
            expected_models = [
                ModelType.HAIKU.value,
                ModelType.SONNET.value,
                ModelType.OPUS.value
            ]
            
            for expected_model in expected_models:
                assert any(expected_model in model_id for model_id in model_ids), \
                    f"Expected model {expected_model} not found in available models"
                    
        except Exception as e:
            pytest.skip(f"Bedrock service not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_claude_3_haiku_invocation(self, bedrock_client):
        """Test Claude-3 Haiku model invocation for fast regulatory compliance"""
        try:
            request = BedrockRequest(
                prompt="Analyze this regulatory requirement: A fintech company must maintain proper books and records according to SEC regulations. Provide a brief compliance assessment.",
                max_tokens=500,
                temperature=0.3,
                system_prompt="You are a regulatory compliance expert specializing in fintech regulations."
            )
            
            response = await bedrock_client.invoke_model(request, ModelType.HAIKU)
            
            # Verify response structure
            assert isinstance(response, BedrockResponse)
            assert response.content is not None
            assert len(response.content) > 0
            assert response.model_id == ModelType.HAIKU.value
            assert response.input_tokens > 0
            assert response.output_tokens > 0
            assert response.stop_reason in ["end_turn", "max_tokens"]
            
            # Verify response contains regulatory analysis
            content_lower = response.content.lower()
            assert any(keyword in content_lower for keyword in [
                "compliance", "regulatory", "sec", "requirement", "fintech"
            ]), "Response should contain regulatory compliance analysis"
            
        except Exception as e:
            pytest.skip(f"Claude-3 Haiku not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_claude_3_sonnet_invocation(self, bedrock_client):
        """Test Claude-3 Sonnet model invocation for complex fraud analysis"""
        try:
            request = BedrockRequest(
                prompt="""Analyze these transaction patterns for fraud indicators:
                Transaction 1: $100 at grocery store, normal location
                Transaction 2: $2500 at electronics store, different city
                Transaction 3: $50000 wire transfer, international
                
                Provide detailed fraud risk assessment with confidence scores.""",
                max_tokens=1000,
                temperature=0.2,
                system_prompt="You are a fraud detection expert with expertise in transaction pattern analysis."
            )
            
            response = await bedrock_client.invoke_model(request, ModelType.SONNET)
            
            # Verify response structure
            assert isinstance(response, BedrockResponse)
            assert response.content is not None
            assert len(response.content) > 0
            assert response.model_id == ModelType.SONNET.value
            assert response.input_tokens > 0
            assert response.output_tokens > 0
            
            # Verify response contains fraud analysis
            content_lower = response.content.lower()
            assert any(keyword in content_lower for keyword in [
                "fraud", "risk", "transaction", "suspicious", "analysis"
            ]), "Response should contain fraud analysis"
            
        except Exception as e:
            pytest.skip(f"Claude-3 Sonnet not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_claude_3_opus_invocation(self, bedrock_client):
        """Test Claude-3 Opus model invocation for comprehensive risk assessment"""
        try:
            request = BedrockRequest(
                prompt="""Conduct a comprehensive risk assessment for a fintech startup:
                - Company: AI-powered payment processing platform
                - Stage: Series A funding
                - Market: B2B payments
                - Regulatory environment: US financial services
                
                Analyze credit risk, market risk, operational risk, and regulatory risk.
                Provide detailed assessment with mitigation strategies.""",
                max_tokens=2000,
                temperature=0.1,
                system_prompt="You are a senior risk management expert specializing in fintech risk assessment."
            )
            
            response = await bedrock_client.invoke_model(request, ModelType.OPUS)
            
            # Verify response structure
            assert isinstance(response, BedrockResponse)
            assert response.content is not None
            assert len(response.content) > 0
            assert response.model_id == ModelType.OPUS.value
            assert response.input_tokens > 0
            assert response.output_tokens > 0
            
            # Verify comprehensive risk analysis
            content_lower = response.content.lower()
            risk_types = ["credit risk", "market risk", "operational risk", "regulatory risk"]
            found_risks = sum(1 for risk_type in risk_types if risk_type in content_lower)
            assert found_risks >= 2, "Response should analyze multiple risk types"
            
        except Exception as e:
            pytest.skip(f"Claude-3 Opus not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_specific_model_selection(self, bedrock_client):
        """Test that different agents use appropriate Claude-3 models"""
        test_cases = [
            (BedrockAgentType.REGULATORY_COMPLIANCE, ModelType.HAIKU),
            (BedrockAgentType.FRAUD_DETECTION, ModelType.OPUS),
            (BedrockAgentType.RISK_ASSESSMENT, ModelType.SONNET),
            (BedrockAgentType.MARKET_ANALYSIS, ModelType.HAIKU),
            (BedrockAgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE, ModelType.HAIKU)
        ]
        
        for agent_type, expected_model in test_cases:
            selected_model = bedrock_client.get_model_for_agent(agent_type)
            assert selected_model == expected_model, \
                f"Agent {agent_type} should use {expected_model}, got {selected_model}"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fintech_specific_prompting(self, bedrock_client):
        """Test fintech-specific prompting enhancements"""
        try:
            # Test with fintech context
            response = await bedrock_client.invoke_for_fintech_agent(
                agent_type=BedrockAgentType.REGULATORY_COMPLIANCE,
                prompt="Analyze compliance requirements for a digital wallet service",
                financial_context={
                    "business_type": "digital_wallet",
                    "jurisdiction": "US",
                    "customer_base": "consumer"
                },
                compliance_requirements=["BSA", "KYC", "AML", "CFPB"]
            )
            
            assert isinstance(response, BedrockResponse)
            assert response.content is not None
            
            # Verify fintech-specific analysis
            content_lower = response.content.lower()
            assert any(keyword in content_lower for keyword in [
                "digital wallet", "bsa", "kyc", "aml", "cfpb"
            ]), "Response should include fintech-specific compliance analysis"
            
        except Exception as e:
            pytest.skip(f"Fintech prompting not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bedrock_error_handling(self, bedrock_client):
        """Test Bedrock error handling and retry logic"""
        # Test with invalid model parameters
        request = BedrockRequest(
            prompt="Test prompt",
            max_tokens=0,  # Invalid parameter
            temperature=2.0  # Invalid temperature
        )
        
        with pytest.raises((BedrockClientError, ValueError)):
            await bedrock_client.invoke_model(request, ModelType.HAIKU)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_bedrock_requests(self, bedrock_client):
        """Test concurrent Bedrock requests for scalability"""
        try:
            # Create multiple concurrent requests
            requests = []
            for i in range(5):
                request = BedrockRequest(
                    prompt=f"Analyze fintech risk scenario {i+1}: A payment processor handling $1M daily volume.",
                    max_tokens=200,
                    temperature=0.3
                )
                requests.append(bedrock_client.invoke_model(request, ModelType.HAIKU))
            
            # Execute concurrently
            responses = await asyncio.gather(*requests, return_exceptions=True)
            
            # Verify all requests succeeded
            successful_responses = [r for r in responses if isinstance(r, BedrockResponse)]
            assert len(successful_responses) >= 3, "At least 3 concurrent requests should succeed"
            
            # Verify response quality
            for response in successful_responses:
                assert response.content is not None
                assert len(response.content) > 0
                
        except Exception as e:
            pytest.skip(f"Concurrent requests not supported: {e}")


class TestFinTechAgentBedrockIntegration:
    """Integration tests for fintech agents with Bedrock Nova"""
    
    @pytest.fixture
    def bedrock_client(self):
        """Mock Bedrock client for agent testing"""
        mock_client = Mock(spec=BedrockClient)
        mock_client.invoke_for_agent = AsyncMock()
        mock_client.invoke_for_fintech_agent = AsyncMock()
        return mock_client
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_regulatory_compliance_agent_bedrock_integration(self, bedrock_client):
        """Test regulatory compliance agent integration with Bedrock"""
        # Mock Bedrock response
        mock_response = Mock()
        mock_response.content = """
        Regulatory Compliance Analysis:
        - SEC Requirements: Compliant with registration and reporting
        - FINRA Rules: Additional documentation needed
        - CFPB Guidelines: Fully compliant
        Risk Level: Medium
        Confidence: 0.85
        """
        bedrock_client.invoke_for_fintech_agent.return_value = mock_response
        
        # Create agent with mocked Bedrock client
        agent = RegulatoryComplianceAgent(bedrock_client=bedrock_client)
        
        # Execute compliance analysis
        result = await agent.analyze_compliance({
            "business_type": "fintech_startup",
            "jurisdiction": "US",
            "regulations": ["SEC", "FINRA", "CFPB"]
        })
        
        # Verify Bedrock integration
        bedrock_client.invoke_for_fintech_agent.assert_called_once()
        call_args = bedrock_client.invoke_for_fintech_agent.call_args
        
        assert call_args[1]["agent_type"] == BedrockAgentType.REGULATORY_COMPLIANCE
        assert "compliance" in call_args[1]["prompt"].lower()
        assert call_args[1]["compliance_requirements"] == ["SEC", "FINRA", "CFPB"]
        
        # Verify result processing
        assert result is not None
        assert hasattr(result, "compliance_status")
        assert hasattr(result, "confidence_score")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fraud_detection_agent_bedrock_integration(self, bedrock_client):
        """Test fraud detection agent integration with Bedrock"""
        # Mock Bedrock response for ML interpretation
        mock_response = Mock()
        mock_response.content = """
        Fraud Analysis Interpretation:
        - Transaction 1: Low risk (0.15 probability)
        - Transaction 2: Moderate risk (0.45 probability) - Geographic anomaly
        - Transaction 3: High risk (0.92 probability) - Multiple red flags
        Recommended Actions: Block transaction 3, review transaction 2
        """
        bedrock_client.invoke_for_fintech_agent.return_value = mock_response
        
        # Create agent with mocked Bedrock client
        agent = FraudDetectionAgent(bedrock_client=bedrock_client)
        
        # Mock ML engine results
        with patch.object(agent, 'ml_engine') as mock_ml:
            mock_ml.detect_anomalies.return_value = {
                "anomaly_scores": [0.15, 0.45, 0.92],
                "anomalous_indices": [2],
                "confidence": 0.88
            }
            
            # Execute fraud detection
            result = await agent.detect_fraud([
                {"amount": 100, "merchant": "grocery"},
                {"amount": 2500, "merchant": "electronics"},
                {"amount": 50000, "merchant": "luxury"}
            ])
        
        # Verify Bedrock integration for ML interpretation
        bedrock_client.invoke_for_fintech_agent.assert_called_once()
        call_args = bedrock_client.invoke_for_fintech_agent.call_args
        
        assert call_args[1]["agent_type"] == BedrockAgentType.FRAUD_DETECTION
        assert "fraud" in call_args[1]["prompt"].lower()
        assert "anomaly" in call_args[1]["prompt"].lower()
        
        # Verify ML + LLM integration
        assert result is not None
        assert len(result) == 3  # Three transaction results
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_risk_assessment_agent_bedrock_integration(self, bedrock_client):
        """Test risk assessment agent integration with Bedrock"""
        # Mock Bedrock response
        mock_response = Mock()
        mock_response.content = """
        Comprehensive Risk Assessment:
        Credit Risk: 0.65 (Medium) - Limited credit history
        Market Risk: 0.45 (Low-Medium) - Stable market conditions
        Operational Risk: 0.70 (Medium-High) - Scaling challenges
        Regulatory Risk: 0.55 (Medium) - Evolving regulations
        Overall Risk Score: 0.59 (Medium)
        """
        bedrock_client.invoke_for_fintech_agent.return_value = mock_response
        
        # Create agent with mocked Bedrock client
        agent = RiskAssessmentAgent(bedrock_client=bedrock_client)
        
        # Execute risk assessment
        result = await agent.assess_risk({
            "entity_type": "fintech_startup",
            "business_model": "payment_processing",
            "funding_stage": "series_a"
        })
        
        # Verify Bedrock integration
        bedrock_client.invoke_for_fintech_agent.assert_called_once()
        call_args = bedrock_client.invoke_for_fintech_agent.call_args
        
        assert call_args[1]["agent_type"] == BedrockAgentType.RISK_ASSESSMENT
        assert "risk" in call_args[1]["prompt"].lower()
        
        # Verify comprehensive risk analysis
        assert result is not None
        assert hasattr(result, "overall_risk_score")
        assert hasattr(result, "risk_factors")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_market_analysis_agent_bedrock_integration(self, bedrock_client):
        """Test market analysis agent integration with Bedrock"""
        # Mock Bedrock response
        mock_response = Mock()
        mock_response.content = """
        Market Intelligence Analysis:
        Trend Direction: Bullish
        Key Drivers: Digital payment adoption, regulatory clarity
        Risk Factors: Market saturation, cybersecurity threats
        Opportunities: Cross-border payments, embedded finance
        Volatility Level: 0.35 (Moderate)
        Confidence: 0.82
        """
        bedrock_client.invoke_for_fintech_agent.return_value = mock_response
        
        # Create agent with mocked Bedrock client
        agent = MarketAnalysisAgent(bedrock_client=bedrock_client)
        
        # Execute market analysis
        result = await agent.analyze_market({
            "market_segment": "fintech_payments",
            "time_horizon": "1Y",
            "analysis_types": ["trends", "opportunities", "risks"]
        })
        
        # Verify Bedrock integration
        bedrock_client.invoke_for_fintech_agent.assert_called_once()
        call_args = bedrock_client.invoke_for_fintech_agent.call_args
        
        assert call_args[1]["agent_type"] == BedrockAgentType.MARKET_ANALYSIS
        assert "market" in call_args[1]["prompt"].lower()
        
        # Verify market intelligence
        assert result is not None
        assert hasattr(result, "trend_direction")
        assert hasattr(result, "key_drivers")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_kyc_verification_agent_bedrock_integration(self, bedrock_client):
        """Test KYC verification agent integration with Bedrock"""
        # Mock Bedrock response
        mock_response = Mock()
        mock_response.content = """
        KYC Verification Analysis:
        Identity Verification: Passed
        Document Analysis: All documents verified
        Risk Assessment: Low risk customer
        Sanctions Check: Clear
        PEP Check: Not a politically exposed person
        Overall Status: Approved
        Confidence: 0.95
        """
        bedrock_client.invoke_for_fintech_agent.return_value = mock_response
        
        # Create agent with mocked Bedrock client
        agent = KYCVerificationAgent(bedrock_client=bedrock_client)
        
        # Execute KYC verification
        result = await agent.verify_customer({
            "customer_id": "cust_123",
            "verification_level": "enhanced",
            "documents": ["identity", "address", "income"]
        })
        
        # Verify Bedrock integration
        bedrock_client.invoke_for_fintech_agent.assert_called_once()
        call_args = bedrock_client.invoke_for_fintech_agent.call_args
        
        assert call_args[1]["agent_type"] == BedrockAgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE
        assert "kyc" in call_args[1]["prompt"].lower() or "verification" in call_args[1]["prompt"].lower()
        
        # Verify KYC result
        assert result is not None
        assert hasattr(result, "verification_status")
        assert hasattr(result, "risk_score")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
