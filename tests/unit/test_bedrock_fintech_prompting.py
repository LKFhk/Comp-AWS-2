"""
Unit tests for BedrockClient fintech-specific prompting capabilities.
Tests the new invoke_for_fintech_agent method and FintechPromptTemplates.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from riskintel360.services.bedrock_client import (
    BedrockClient,
    BedrockResponse,
    FintechPromptTemplates,
    ModelType
)
from riskintel360.models.agent_models import AgentType


class TestFintechPromptTemplates:
    """Test fintech-specific prompt templates"""
    
    def test_get_system_prompt_regulatory_compliance(self):
        """Test regulatory compliance system prompt"""
        prompt = FintechPromptTemplates.get_system_prompt(AgentType.REGULATORY_COMPLIANCE)
        
        assert "Regulatory Compliance AI agent" in prompt
        assert "SEC, FINRA, CFPB" in prompt
        assert "compliance requirements" in prompt
        assert "regulatory references" in prompt
        assert "confidence scores" in prompt
    
    def test_get_system_prompt_fraud_detection(self):
        """Test fraud detection system prompt"""
        prompt = FintechPromptTemplates.get_system_prompt(AgentType.FRAUD_DETECTION)
        
        assert "Fraud Detection AI agent" in prompt
        assert "machine learning" in prompt
        assert "anomaly detection" in prompt
        assert "Suspicious Activity Reports" in prompt
        assert "false positives" in prompt
        assert "AML/BSA" in prompt
    
    def test_get_system_prompt_risk_assessment(self):
        """Test risk assessment system prompt"""
        prompt = FintechPromptTemplates.get_system_prompt(AgentType.RISK_ASSESSMENT)
        
        assert "Risk Assessment AI agent" in prompt
        assert "credit risk, market risk, operational risk" in prompt
        assert "Value at Risk" in prompt
        assert "stress testing" in prompt
        assert "risk mitigation" in prompt
    
    def test_get_system_prompt_market_analysis(self):
        """Test market analysis system prompt"""
        prompt = FintechPromptTemplates.get_system_prompt(AgentType.MARKET_ANALYSIS)
        
        assert "Market Analysis AI agent" in prompt
        assert "market trends" in prompt
        assert "economic indicators" in prompt
        assert "investment opportunities" in prompt
        assert "Yahoo Finance, FRED" in prompt
    
    def test_get_system_prompt_kyc_verification(self):
        """Test KYC verification system prompt"""
        prompt = FintechPromptTemplates.get_system_prompt(AgentType.KYC_VERIFICATION)
        
        assert "KYC" in prompt
        assert "customer due diligence" in prompt
        assert "identity documents" in prompt
        assert "sanctions lists" in prompt
        assert "OFAC, UN, EU" in prompt
        assert "AML" in prompt
    
    def test_get_system_prompt_customer_behavior(self):
        """Test customer behavior intelligence system prompt"""
        prompt = FintechPromptTemplates.get_system_prompt(AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE)
        
        assert "Customer Behavior Intelligence" in prompt
        assert "transaction patterns" in prompt
        assert "customer segments" in prompt
        assert "GDPR, CCPA" in prompt
        assert "privacy" in prompt
    
    def test_get_system_prompt_unknown_agent(self):
        """Test fallback prompt for unknown agent types"""
        # Use supervisor agent type as it should get default prompt
        prompt = FintechPromptTemplates.get_system_prompt(AgentType.SUPERVISOR)
        
        assert "financial AI agent" in prompt
        assert "accurate, compliant, and actionable" in prompt
    
    def test_build_fintech_context_full(self):
        """Test building comprehensive fintech context"""
        financial_context = {
            "company_type": "fintech_startup",
            "revenue": "$5M",
            "employees": 50
        }
        compliance_requirements = ["SOX", "PCI-DSS", "GDPR"]
        
        context = FintechPromptTemplates.build_fintech_context(
            financial_context=financial_context,
            compliance_requirements=compliance_requirements,
            risk_tolerance="low",
            company_size="small"
        )
        
        assert "Financial Context:" in context
        assert "fintech_startup" in context
        assert "Compliance Requirements: SOX, PCI-DSS, GDPR" in context
        assert "Risk Tolerance: low" in context
        assert "Company Size: small" in context
        assert "regulatory compliance" in context
        assert "confidence scores" in context
        assert "audit trails" in context
    
    def test_build_fintech_context_minimal(self):
        """Test building fintech context with minimal parameters"""
        context = FintechPromptTemplates.build_fintech_context()
        
        assert "Risk Tolerance: moderate" in context
        assert "Company Size: medium" in context
        assert "accuracy, regulatory compliance" in context
        assert "confidence scores" in context
    
    def test_build_fintech_context_partial(self):
        """Test building fintech context with partial parameters"""
        compliance_requirements = ["FINRA", "SEC"]
        
        context = FintechPromptTemplates.build_fintech_context(
            compliance_requirements=compliance_requirements,
            risk_tolerance="high"
        )
        
        assert "Compliance Requirements: FINRA, SEC" in context
        assert "Risk Tolerance: high" in context
        assert "Company Size: medium" in context  # Default value


class TestBedrockClientFintechPrompting:
    """Test BedrockClient fintech-specific prompting methods"""
    
    @pytest.fixture
    def mock_bedrock_client(self):
        """Create a mock BedrockClient for testing"""
        with patch('riskintel360.services.bedrock_client.boto3.Session'):
            client = BedrockClient()
            return client
    
    @pytest.fixture
    def sample_bedrock_response(self):
        """Sample BedrockResponse for testing"""
        return BedrockResponse(
            content="Sample fintech analysis response",
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            input_tokens=100,
            output_tokens=200,
            stop_reason="end_turn",
            raw_response={
                "content": [{"text": "Sample fintech analysis response"}],
                "usage": {"input_tokens": 100, "output_tokens": 200},
                "stop_reason": "end_turn"
            }
        )
    
    @pytest.mark.asyncio
    async def test_invoke_for_fintech_agent_basic(self, mock_bedrock_client, sample_bedrock_response):
        """Test basic fintech agent invocation"""
        # Mock the invoke_model method
        mock_bedrock_client.invoke_model = AsyncMock(return_value=sample_bedrock_response)
        
        response = await mock_bedrock_client.invoke_for_fintech_agent(
            agent_type=AgentType.REGULATORY_COMPLIANCE,
            prompt="Analyze compliance requirements for a fintech startup"
        )
        
        # Verify response
        assert response.content == "Sample fintech analysis response"
        assert response.model_id == "anthropic.claude-3-haiku-20240307-v1:0"
        
        # Verify fintech metadata was added
        assert "fintech_metadata" in response.raw_response
        metadata = response.raw_response["fintech_metadata"]
        assert metadata["agent_type"] == "regulatory_compliance"
        assert metadata["risk_tolerance"] == "moderate"
        assert metadata["company_size"] == "medium"
        assert metadata["fintech_optimized"] is True
        
        # Verify invoke_model was called with correct parameters
        mock_bedrock_client.invoke_model.assert_called_once()
        call_args = mock_bedrock_client.invoke_model.call_args
        request = call_args[0][0]  # First positional argument (BedrockRequest)
        
        # Check that prompt was enhanced
        assert "accuracy & compliance" in request.prompt.lower()
        assert "confidence scoring" in request.prompt.lower()
        assert "risk assessment" in request.prompt.lower()
        
        # Check that system prompt includes fintech context
        assert "Regulatory Compliance AI agent" in request.system_prompt
        assert "Risk Tolerance: moderate" in request.system_prompt
        assert "Company Size: medium" in request.system_prompt
    
    @pytest.mark.asyncio
    async def test_invoke_for_fintech_agent_with_context(self, mock_bedrock_client, sample_bedrock_response):
        """Test fintech agent invocation with full context"""
        mock_bedrock_client.invoke_model = AsyncMock(return_value=sample_bedrock_response)
        
        financial_context = {
            "company_type": "digital_bank",
            "assets": "$100M",
            "customers": 50000
        }
        compliance_requirements = ["FDIC", "OCC", "CFPB"]
        
        response = await mock_bedrock_client.invoke_for_fintech_agent(
            agent_type=AgentType.FRAUD_DETECTION,
            prompt="Analyze transaction patterns for fraud detection",
            financial_context=financial_context,
            compliance_requirements=compliance_requirements,
            risk_tolerance="low",
            company_size="large",
            temperature=0.1
        )
        
        # Verify fintech metadata includes all context
        metadata = response.raw_response["fintech_metadata"]
        assert metadata["agent_type"] == "fraud_detection"
        assert metadata["risk_tolerance"] == "low"
        assert metadata["company_size"] == "large"
        assert metadata["compliance_requirements"] == ["FDIC", "OCC", "CFPB"]
        assert metadata["temperature_used"] == 0.1
        
        # Verify system prompt includes context
        call_args = mock_bedrock_client.invoke_model.call_args
        request = call_args[0][0]
        
        assert "digital_bank" in request.system_prompt
        assert "FDIC, OCC, CFPB" in request.system_prompt
        assert "Risk Tolerance: low" in request.system_prompt
        assert "Company Size: large" in request.system_prompt
        assert "Fraud Detection AI agent" in request.system_prompt
    
    @pytest.mark.asyncio
    async def test_temperature_optimization_by_agent_type(self, mock_bedrock_client, sample_bedrock_response):
        """Test that temperature is optimized based on agent type"""
        mock_bedrock_client.invoke_model = AsyncMock(return_value=sample_bedrock_response)
        
        # Test different agent types and their expected temperatures
        agent_temperature_tests = [
            (AgentType.REGULATORY_COMPLIANCE, 0.2),  # Highest accuracy
            (AgentType.FRAUD_DETECTION, 0.3),        # High accuracy
            (AgentType.RISK_ASSESSMENT, 0.3),        # High accuracy
            (AgentType.KYC_VERIFICATION, 0.2),       # Highest accuracy
            (AgentType.MARKET_ANALYSIS, 0.4),        # Moderate creativity
            (AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE, 0.4),  # Moderate creativity
        ]
        
        for agent_type, expected_temp in agent_temperature_tests:
            mock_bedrock_client.invoke_model.reset_mock()
            
            await mock_bedrock_client.invoke_for_fintech_agent(
                agent_type=agent_type,
                prompt="Test prompt"
            )
            
            # Verify temperature was set correctly
            call_args = mock_bedrock_client.invoke_model.call_args
            request = call_args[0][0]
            assert request.temperature == expected_temp, f"Agent {agent_type} should use temperature {expected_temp}"
    
    @pytest.mark.asyncio
    async def test_custom_temperature_override(self, mock_bedrock_client, sample_bedrock_response):
        """Test that custom temperature overrides default optimization"""
        mock_bedrock_client.invoke_model = AsyncMock(return_value=sample_bedrock_response)
        
        custom_temperature = 0.8
        
        await mock_bedrock_client.invoke_for_fintech_agent(
            agent_type=AgentType.REGULATORY_COMPLIANCE,
            prompt="Test prompt",
            temperature=custom_temperature
        )
        
        # Verify custom temperature was used instead of default
        call_args = mock_bedrock_client.invoke_model.call_args
        request = call_args[0][0]
        assert request.temperature == custom_temperature
    
    @pytest.mark.asyncio
    async def test_prompt_enhancement_structure(self, mock_bedrock_client, sample_bedrock_response):
        """Test that prompts are properly enhanced with fintech requirements"""
        mock_bedrock_client.invoke_model = AsyncMock(return_value=sample_bedrock_response)
        
        original_prompt = "Analyze market conditions"
        
        await mock_bedrock_client.invoke_for_fintech_agent(
            agent_type=AgentType.MARKET_ANALYSIS,
            prompt=original_prompt
        )
        
        call_args = mock_bedrock_client.invoke_model.call_args
        request = call_args[0][0]
        enhanced_prompt = request.prompt
        
        # Verify original prompt is included
        assert original_prompt in enhanced_prompt
        
        # Verify fintech-specific requirements are added
        required_sections = [
            "Accuracy & Compliance",
            "Confidence Scoring",
            "Risk Assessment", 
            "Actionable Insights",
            "Audit Trail",
            "Uncertainty Handling"
        ]
        
        for section in required_sections:
            assert section in enhanced_prompt, f"Enhanced prompt should include {section}"
    
    @pytest.mark.asyncio
    async def test_model_selection_for_fintech_agents(self, mock_bedrock_client, sample_bedrock_response):
        """Test that correct models are selected for different fintech agent types"""
        mock_bedrock_client.invoke_model = AsyncMock(return_value=sample_bedrock_response)
        
        # Test model selection for each agent type
        expected_models = {
            AgentType.REGULATORY_COMPLIANCE: ModelType.HAIKU,
            AgentType.FRAUD_DETECTION: ModelType.OPUS,
            AgentType.RISK_ASSESSMENT: ModelType.SONNET,
            AgentType.MARKET_ANALYSIS: ModelType.HAIKU,
            AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE: ModelType.HAIKU,
            AgentType.KYC_VERIFICATION: ModelType.SONNET,
        }
        
        for agent_type, expected_model in expected_models.items():
            mock_bedrock_client.invoke_model.reset_mock()
            
            await mock_bedrock_client.invoke_for_fintech_agent(
                agent_type=agent_type,
                prompt="Test prompt"
            )
            
            # Verify correct model was selected
            call_args = mock_bedrock_client.invoke_model.call_args
            kwargs = call_args[1]
            assert kwargs["agent_type"] == agent_type
            
            # Verify model mapping
            selected_model = mock_bedrock_client.get_model_for_agent(agent_type)
            assert selected_model == expected_model
    
    @pytest.mark.asyncio
    async def test_error_handling_in_fintech_prompting(self, mock_bedrock_client):
        """Test error handling in fintech prompting method"""
        from riskintel360.services.bedrock_client import BedrockClientError
        
        # Mock invoke_model to raise an error
        mock_bedrock_client.invoke_model = AsyncMock(side_effect=BedrockClientError("Test error"))
        
        with pytest.raises(BedrockClientError, match="Test error"):
            await mock_bedrock_client.invoke_for_fintech_agent(
                agent_type=AgentType.REGULATORY_COMPLIANCE,
                prompt="Test prompt"
            )
    
    def test_fintech_agent_model_mapping_completeness(self, mock_bedrock_client):
        """Test that all fintech agent types have model mappings"""
        fintech_agent_types = [
            AgentType.REGULATORY_COMPLIANCE,
            AgentType.FRAUD_DETECTION,
            AgentType.RISK_ASSESSMENT,
            AgentType.MARKET_ANALYSIS,
            AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE,
            AgentType.KYC_VERIFICATION,
        ]
        
        for agent_type in fintech_agent_types:
            model = mock_bedrock_client.get_model_for_agent(agent_type)
            assert model is not None, f"Agent type {agent_type} should have a model mapping"
            assert isinstance(model, ModelType), f"Model for {agent_type} should be a ModelType enum"


class TestFintechPromptingIntegration:
    """Integration tests for fintech prompting functionality"""
    
    @pytest.mark.asyncio
    async def test_fintech_prompting_end_to_end_flow(self):
        """Test complete end-to-end fintech prompting flow"""
        with patch('riskintel360.services.bedrock_client.boto3.Session'):
            client = BedrockClient()
            
            # Mock the actual AWS call
            mock_response_body = {
                "content": [{"text": "Comprehensive regulatory analysis completed"}],
                "usage": {"input_tokens": 150, "output_tokens": 300},
                "stop_reason": "end_turn"
            }
            
            with patch.object(client, '_invoke_model_with_retry', new_callable=AsyncMock) as mock_invoke:
                mock_invoke.return_value = mock_response_body
                
                response = await client.invoke_for_fintech_agent(
                    agent_type=AgentType.REGULATORY_COMPLIANCE,
                    prompt="Analyze SEC compliance requirements for digital asset trading",
                    financial_context={"business_type": "crypto_exchange"},
                    compliance_requirements=["SEC", "CFTC", "FinCEN"],
                    risk_tolerance="low",
                    company_size="large"
                )
                
                # Verify response structure
                assert response.content == "Comprehensive regulatory analysis completed"
                assert response.input_tokens == 150
                assert response.output_tokens == 300
                
                # Verify fintech metadata
                assert "fintech_metadata" in response.raw_response
                metadata = response.raw_response["fintech_metadata"]
                assert metadata["fintech_optimized"] is True
                assert metadata["agent_type"] == "regulatory_compliance"
                
                # Verify the invoke call was made with enhanced parameters
                mock_invoke.assert_called_once()
                call_args = mock_invoke.call_args[0]
                model_id, body = call_args
                
                # Verify model selection
                assert model_id == ModelType.HAIKU.value
                
                # Verify enhanced prompt structure
                messages = body["messages"]
                assert len(messages) == 1
                user_message = messages[0]["content"]
                assert "SEC compliance requirements" in user_message
                assert "Accuracy & Compliance" in user_message
                
                # Verify system prompt enhancement
                system_prompt = body["system"]
                assert "Regulatory Compliance AI agent" in system_prompt
                assert "crypto_exchange" in system_prompt
                assert "SEC, CFTC, FinCEN" in system_prompt


class TestBaseAgentFintechIntegration:
    """Test BaseAgent integration with fintech prompting"""
    
    @pytest.fixture
    def mock_base_agent(self):
        """Create a mock agent for testing fintech integration"""
        from riskintel360.agents.regulatory_compliance_agent import RegulatoryComplianceAgent, RegulatoryComplianceAgentConfig
        
        with patch('riskintel360.services.bedrock_client.boto3.Session'):
            bedrock_client = BedrockClient()
            
            config = RegulatoryComplianceAgentConfig(
                agent_id="test_agent",
                agent_type=AgentType.REGULATORY_COMPLIANCE,
                bedrock_client=bedrock_client
            )
            
            agent = RegulatoryComplianceAgent(config)
            return agent
    
    @pytest.mark.asyncio
    async def test_base_agent_invoke_fintech_llm(self, mock_base_agent):
        """Test BaseAgent invoke_fintech_llm method"""
        # Mock the bedrock client method
        mock_response = BedrockResponse(
            content="Fintech compliance analysis complete",
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            input_tokens=120,
            output_tokens=250,
            stop_reason="end_turn",
            raw_response={
                "fintech_metadata": {
                    "temperature_used": 0.2,
                    "fintech_optimized": True
                }
            }
        )
        
        mock_base_agent.bedrock_client.invoke_for_fintech_agent = AsyncMock(return_value=mock_response)
        
        # Test the fintech LLM invocation
        result = await mock_base_agent.invoke_fintech_llm(
            prompt="Analyze regulatory compliance requirements",
            financial_context={"company_type": "fintech_startup"},
            compliance_requirements=["SEC", "FINRA"],
            risk_tolerance="low",
            company_size="small"
        )
        
        # Verify result
        assert result == "Fintech compliance analysis complete"
        
        # Verify the bedrock client was called with correct parameters
        mock_base_agent.bedrock_client.invoke_for_fintech_agent.assert_called_once_with(
            agent_type=AgentType.REGULATORY_COMPLIANCE,
            prompt="Analyze regulatory compliance requirements",
            financial_context={"company_type": "fintech_startup"},
            compliance_requirements=["SEC", "FINRA"],
            risk_tolerance="low",
            company_size="small",
            max_tokens=4000,
            temperature=None
        )
    
    @pytest.mark.asyncio
    async def test_base_agent_fintech_llm_with_custom_params(self, mock_base_agent):
        """Test BaseAgent fintech LLM with custom parameters"""
        mock_response = BedrockResponse(
            content="Custom fintech analysis",
            model_id="anthropic.claude-3-sonnet-20241022-v2:0",
            input_tokens=100,
            output_tokens=200,
            stop_reason="end_turn",
            raw_response={"fintech_metadata": {"temperature_used": 0.5}}
        )
        
        mock_base_agent.bedrock_client.invoke_for_fintech_agent = AsyncMock(return_value=mock_response)
        
        result = await mock_base_agent.invoke_fintech_llm(
            prompt="Custom analysis",
            max_tokens=2000,
            temperature=0.5
        )
        
        assert result == "Custom fintech analysis"
        
        # Verify custom parameters were passed
        call_args = mock_base_agent.bedrock_client.invoke_for_fintech_agent.call_args
        assert call_args[1]["max_tokens"] == 2000
        assert call_args[1]["temperature"] == 0.5
    
    @pytest.mark.asyncio
    async def test_base_agent_fintech_llm_error_handling(self, mock_base_agent):
        """Test error handling in BaseAgent fintech LLM method"""
        from riskintel360.services.bedrock_client import BedrockClientError
        
        # Mock an error
        mock_base_agent.bedrock_client.invoke_for_fintech_agent = AsyncMock(
            side_effect=BedrockClientError("Fintech LLM error")
        )
        
        with pytest.raises(BedrockClientError, match="Fintech LLM error"):
            await mock_base_agent.invoke_fintech_llm(
                prompt="Test prompt"
            )
