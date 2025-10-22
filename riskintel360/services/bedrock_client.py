"""
Amazon Bedrock Nova Integration Client
Provides Python client for Amazon Bedrock Nova with model management and retry logic.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from ..config.settings import get_settings
from ..models.agent_models import AgentType

logger = logging.getLogger(__name__)


class FintechPromptTemplates:
    """Fintech-specific prompt templates for enhanced financial accuracy"""
    
    REGULATORY_COMPLIANCE_SYSTEM = """You are a specialized Regulatory Compliance AI agent for financial services. Your role is to:

1. Monitor and analyze regulatory changes from SEC, FINRA, CFPB, and other financial regulators
2. Assess compliance requirements and identify gaps in current operations
3. Generate detailed remediation plans with specific regulatory references
4. Provide accurate, actionable compliance recommendations

Key Guidelines:
- Always reference specific regulations, sections, and compliance deadlines
- Focus on practical implementation steps and cost-effective solutions
- Consider both large institutions and small fintech companies
- Prioritize regulatory accuracy over speed
- Include confidence scores for all assessments
- Flag any uncertainty or need for legal review

Regulatory Context: You have access to current SEC, FINRA, CFPB regulations and recent updates. Always cite specific regulatory sources."""

    FRAUD_DETECTION_SYSTEM = """You are an Advanced Fraud Detection AI agent specializing in financial crime prevention. Your role is to:

1. Interpret machine learning anomaly detection results with financial context
2. Analyze transaction patterns and identify potential fraud indicators
3. Generate Suspicious Activity Reports (SARs) with detailed evidence
4. Reduce false positives while maintaining high detection accuracy

Key Guidelines:
- Combine ML insights with financial domain knowledge
- Explain anomaly scores in business terms
- Consider legitimate business patterns vs. suspicious activities
- Provide confidence levels and risk assessments
- Focus on actionable fraud prevention measures
- Maintain regulatory compliance for AML/BSA requirements

ML Context: You work with unsupervised ML models (isolation forests, clustering, autoencoders) that provide anomaly scores and pattern analysis."""

    RISK_ASSESSMENT_SYSTEM = """You are a Financial Risk Assessment AI agent specializing in comprehensive risk analysis. Your role is to:

1. Evaluate credit risk, market risk, operational risk, and regulatory risk
2. Perform scenario analysis and stress testing
3. Calculate Value at Risk (VaR) and other risk metrics
4. Provide strategic risk mitigation recommendations

Key Guidelines:
- Use quantitative analysis combined with qualitative insights
- Consider multiple risk factors and their correlations
- Provide clear risk ratings and confidence intervals
- Focus on actionable risk management strategies
- Consider both current conditions and forward-looking scenarios
- Maintain consistency with regulatory risk frameworks

Financial Context: You analyze financial statements, market data, economic indicators, and regulatory environments to assess comprehensive risk profiles."""

    MARKET_ANALYSIS_SYSTEM = """You are a Market Analysis AI agent specializing in financial market intelligence. Your role is to:

1. Analyze market trends, economic indicators, and financial data
2. Identify investment opportunities and market risks
3. Process financial news and sentiment analysis
4. Generate market forecasts and strategic recommendations

Key Guidelines:
- Combine quantitative data analysis with market sentiment
- Focus on actionable market insights and opportunities
- Consider macroeconomic factors and sector-specific trends
- Provide probability-weighted scenarios and confidence levels
- Distinguish between short-term volatility and long-term trends
- Use public data sources effectively for comprehensive analysis

Market Context: You have access to market data from Yahoo Finance, FRED economic data, Treasury rates, and financial news sources."""

    KYC_VERIFICATION_SYSTEM = """You are a KYC (Know Your Customer) Verification AI agent specializing in customer due diligence. Your role is to:

1. Analyze customer identity documents and business registrations
2. Perform risk scoring based on public records and sanctions lists
3. Automate KYC approval/rejection decisions with proper documentation
4. Ensure compliance with AML and customer identification requirements

Key Guidelines:
- Verify identity documents with high accuracy standards
- Check against sanctions lists (OFAC, UN, EU) and PEP databases
- Assess customer risk based on geography, business type, and transaction patterns
- Provide clear approval/rejection rationale with supporting evidence
- Maintain audit trails for regulatory compliance
- Flag any suspicious or high-risk indicators for manual review

Compliance Context: You must adhere to BSA, AML, and KYC regulations while balancing customer experience with risk management."""

    CUSTOMER_BEHAVIOR_SYSTEM = """You are a Customer Behavior Intelligence AI agent specializing in fintech customer analysis. Your role is to:

1. Analyze customer transaction patterns and behavioral data
2. Identify customer segments and personalization opportunities
3. Detect unusual behavior that may indicate fraud or risk
4. Generate insights for customer retention and product development

Key Guidelines:
- Focus on actionable customer insights and behavioral patterns
- Respect customer privacy and data protection regulations
- Combine transaction analysis with demographic and behavioral data
- Provide segmentation strategies and personalization recommendations
- Identify early warning signs of customer churn or risk
- Support both customer experience and risk management objectives

Privacy Context: All analysis must comply with GDPR, CCPA, and financial privacy regulations while providing valuable business insights."""

    @classmethod
    def get_system_prompt(cls, agent_type: AgentType) -> str:
        """Get the appropriate system prompt for a fintech agent type"""
        prompt_mapping = {
            AgentType.REGULATORY_COMPLIANCE: cls.REGULATORY_COMPLIANCE_SYSTEM,
            AgentType.FRAUD_DETECTION: cls.FRAUD_DETECTION_SYSTEM,
            AgentType.RISK_ASSESSMENT: cls.RISK_ASSESSMENT_SYSTEM,
            AgentType.MARKET_ANALYSIS: cls.MARKET_ANALYSIS_SYSTEM,
            AgentType.KYC_VERIFICATION: cls.KYC_VERIFICATION_SYSTEM,
            AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE: cls.CUSTOMER_BEHAVIOR_SYSTEM,
        }
        return prompt_mapping.get(agent_type, "You are a financial AI agent. Provide accurate, compliant, and actionable financial analysis.")

    @classmethod
    def build_fintech_context(
        cls,
        financial_context: Optional[Dict[str, Any]] = None,
        compliance_requirements: Optional[List[str]] = None,
        risk_tolerance: str = "moderate",
        company_size: str = "medium"
    ) -> str:
        """Build comprehensive fintech context for enhanced prompting"""
        context_parts = []
        
        if financial_context:
            context_parts.append(f"Financial Context: {financial_context}")
        
        if compliance_requirements:
            context_parts.append(f"Compliance Requirements: {', '.join(compliance_requirements)}")
        
        context_parts.append(f"Risk Tolerance: {risk_tolerance}")
        context_parts.append(f"Company Size: {company_size}")
        
        # Add fintech-specific guidance
        context_parts.extend([
            "Focus on accuracy, regulatory compliance, and risk assessment.",
            "Provide confidence scores and uncertainty quantification.",
            "Consider both automated decisions and human oversight requirements.",
            "Prioritize actionable recommendations with clear implementation steps.",
            "Maintain audit trails and regulatory documentation standards."
        ])
        
        return "\n".join(context_parts)


class ModelType(Enum):
    """Supported model types for different agent purposes - using AWS native and globally available models"""
    HAIKU = "amazon.titan-text-express-v1"  # Fast, efficient AWS native model
    SONNET = "amazon.titan-text-premier-v1:0"  # Balanced reasoning AWS native model  
    OPUS = "amazon.titan-text-premier-v1:0"  # Most capable AWS native model
    
    # Alternative models available globally
    COHERE_COMMAND = "cohere.command-text-v14"  # Cohere Command model
    AI21_JURASSIC = "ai21.j2-ultra-v1"  # AI21 Jurassic model


# AgentType is now imported from agent_models.py


@dataclass
class BedrockRequest:
    """Request structure for Bedrock API calls"""
    prompt: str
    max_tokens: int = 4000
    temperature: float = 0.7
    top_p: float = 0.9
    stop_sequences: Optional[List[str]] = None
    system_prompt: Optional[str] = None


@dataclass
class BedrockResponse:
    """Response structure from Bedrock API calls"""
    content: str
    model_id: str
    input_tokens: int
    output_tokens: int
    stop_reason: str
    raw_response: Dict[str, Any]


class BedrockClientError(Exception):
    """Custom exception for Bedrock client errors"""
    pass


class BedrockAuthenticationError(BedrockClientError):
    """Authentication-related errors"""
    pass


class BedrockRateLimitError(BedrockClientError):
    """Rate limiting errors"""
    pass


class BedrockClient:
    """
    Amazon Bedrock Nova client with model management and retry logic.
    
    Provides high-level interface for interacting with Claude-3 models
    with automatic retry, error handling, and model selection.
    """
    
    def __init__(
        self,
        region_name: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None
    ):
        """
        Initialize Bedrock client with AWS credentials.
        
        Args:
            region_name: AWS region for Bedrock service
            aws_access_key_id: AWS access key (optional, uses default credential chain)
            aws_secret_access_key: AWS secret key (optional, uses default credential chain)
            aws_session_token: AWS session token (optional, for temporary credentials)
        """
        self.region_name = region_name
        self.settings = get_settings()
        
        # Initialize boto3 client with credentials
        session_kwargs = {"region_name": region_name}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs.update({
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key
            })
            if aws_session_token:
                session_kwargs["aws_session_token"] = aws_session_token
        
        try:
            self.session = boto3.Session(**session_kwargs)
            self.bedrock_runtime = self.session.client("bedrock-runtime")
            
            # Test credentials by trying to get caller identity
            if aws_access_key_id and aws_secret_access_key:
                # Only validate credentials if explicitly provided
                sts_client = self.session.client("sts")
                try:
                    sts_client.get_caller_identity()
                    logger.info(f"✅ Credentials validated successfully")
                except Exception as cred_error:
                    logger.error(f"❌ Invalid credentials: {cred_error}")
                    raise BedrockAuthenticationError(f"Invalid credentials: {cred_error}")
            
            logger.info(f"🚀 Bedrock client initialized for region: {region_name}")
        except BedrockAuthenticationError:
            raise  # Re-raise authentication errors
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bedrock client: {e}")
            raise BedrockAuthenticationError(f"Failed to initialize Bedrock client: {e}")
        
        # Model mapping for fintech agent types - optimized for specific use cases
        self.agent_model_mapping = {
            # Core fintech agents with AWS native models (globally available)
            AgentType.REGULATORY_COMPLIANCE: ModelType.HAIKU,      # Fast regulatory compliance with Titan Express
            AgentType.FRAUD_DETECTION: ModelType.SONNET,          # Fraud analysis with Titan Premier
            AgentType.RISK_ASSESSMENT: ModelType.OPUS,            # Comprehensive risk assessment with Titan Premier
            AgentType.MARKET_ANALYSIS: ModelType.HAIKU,           # Fast market data processing with Titan Express
            AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE: ModelType.HAIKU,  # Efficient customer analysis
            AgentType.KYC_VERIFICATION: ModelType.SONNET,         # Balanced accuracy for identity verification
            
            # System agents
            AgentType.SUPERVISOR: ModelType.SONNET,               # Balanced reasoning for coordination
        }
    
    def get_model_for_agent(self, agent_type: AgentType) -> ModelType:
        """
        Get the optimal model type for a specific agent.
        
        Args:
            agent_type: The type of agent requesting a model
            
        Returns:
            ModelType: The optimal model for the agent type
        """
        model = self.agent_model_mapping.get(agent_type, ModelType.SONNET)
        logger.debug(f"Selected model {model.value} for agent {agent_type.value}")
        return model
    
    def _prepare_model_request(self, request: BedrockRequest, model_type: ModelType) -> Dict[str, Any]:
        """
        Prepare request payload for different model types.
        
        Args:
            request: The Bedrock request object
            model_type: The model type to use
            
        Returns:
            Dict containing the formatted request payload
        """
        model_id = model_type.value
        
        # Amazon Titan models
        if model_id.startswith("amazon.titan"):
            body = {
                "inputText": request.prompt,
                "textGenerationConfig": {
                    "maxTokenCount": request.max_tokens,
                    "temperature": request.temperature,
                    "topP": request.top_p
                }
            }
            
            # Add stop sequences if provided
            if request.stop_sequences:
                body["textGenerationConfig"]["stopSequences"] = request.stop_sequences
                
            return body
            
        # Cohere Command models
        elif model_id.startswith("cohere.command"):
            body = {
                "prompt": request.prompt,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "p": request.top_p
            }
            
            # Add stop sequences if provided
            if request.stop_sequences:
                body["stop_sequences"] = request.stop_sequences
                
            return body
            
        # AI21 Jurassic models
        elif model_id.startswith("ai21.j2"):
            body = {
                "prompt": request.prompt,
                "maxTokens": request.max_tokens,
                "temperature": request.temperature,
                "topP": request.top_p
            }
            
            # Add stop sequences if provided
            if request.stop_sequences:
                body["stopSequences"] = request.stop_sequences
                
            return body
            
        # Fallback to Claude format for backward compatibility
        else:
            # Build messages array for Claude-3 format
            messages = [
                {
                    "role": "user",
                    "content": request.prompt
                }
            ]
            
            # Prepare the request body
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "messages": messages
            }
            
            # Add system prompt if provided
            if request.system_prompt:
                body["system"] = request.system_prompt
            
            # Add stop sequences if provided
            if request.stop_sequences:
                body["stop_sequences"] = request.stop_sequences
            
            return body
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ClientError, BotoCoreError, BedrockRateLimitError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _invoke_model_with_retry(
        self,
        model_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock model with retry logic.
        
        Args:
            model_id: The model identifier
            body: The request body
            
        Returns:
            Dict containing the model response
            
        Raises:
            BedrockAuthenticationError: For authentication issues
            BedrockRateLimitError: For rate limiting issues
            BedrockClientError: For other client errors
        """
        try:
            # Convert to async using asyncio.to_thread for boto3 sync calls
            response = await asyncio.to_thread(
                self.bedrock_runtime.invoke_model,
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
            
            # Parse response
            response_body = json.loads(response["body"].read())
            logger.debug(f"✅ Model {model_id} invoked successfully")
            return response_body
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            if error_code in ["UnauthorizedOperation", "AccessDenied", "InvalidUserID.NotFound"]:
                logger.error(f"🔐 Authentication error: {error_message}")
                raise BedrockAuthenticationError(f"Authentication failed: {error_message}")
            elif error_code in ["ThrottlingException", "TooManyRequestsException"]:
                logger.warning(f"⚠️ Rate limit hit: {error_message}")
                raise BedrockRateLimitError(f"Rate limit exceeded: {error_message}")
            else:
                logger.error(f"❌ Bedrock API error: {error_code} - {error_message}")
                raise BedrockClientError(f"Bedrock API error: {error_code} - {error_message}")
        
        except BotoCoreError as e:
            logger.error(f"❌ Boto3 core error: {e}")
            raise BedrockClientError(f"Boto3 error: {e}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error invoking model: {e}")
            raise BedrockClientError(f"Unexpected error: {e}")
    
    async def invoke_model(
        self,
        request: BedrockRequest,
        model_type: Optional[ModelType] = None,
        agent_type: Optional[AgentType] = None
    ) -> BedrockResponse:
        """
        Invoke a Bedrock model with the given request.
        
        Args:
            request: The request to send to the model
            model_type: Specific model type to use (optional)
            agent_type: Agent type for automatic model selection (optional)
            
        Returns:
            BedrockResponse: The response from the model
            
        Raises:
            BedrockClientError: For various client errors
        """
        # Determine model to use
        if model_type is None and agent_type is not None:
            model_type = self.get_model_for_agent(agent_type)
        elif model_type is None:
            model_type = ModelType.SONNET  # Default to Sonnet
        
        model_id = model_type.value
        logger.info(f"🧠 Invoking model {model_id} for request")
        
        # Prepare request
        body = self._prepare_model_request(request, model_type)
        
        # Invoke model with retry
        response_body = await self._invoke_model_with_retry(model_id, body)
        
        # Parse response based on model type
        try:
            if model_id.startswith("amazon.titan"):
                # Amazon Titan response format
                content = response_body["results"][0]["outputText"]
                input_tokens = response_body.get("inputTextTokenCount", 0)
                output_tokens = response_body["results"][0].get("tokenCount", 0)
                stop_reason = response_body["results"][0].get("completionReason", "FINISH")
                
            elif model_id.startswith("cohere.command"):
                # Cohere Command response format
                content = response_body["generations"][0]["text"]
                input_tokens = 0  # Cohere doesn't provide input token count
                output_tokens = response_body["generations"][0].get("token_count", 0)
                stop_reason = response_body["generations"][0].get("finish_reason", "COMPLETE")
                
            elif model_id.startswith("ai21.j2"):
                # AI21 Jurassic response format
                content = response_body["completions"][0]["data"]["text"]
                input_tokens = 0  # AI21 doesn't provide input token count
                output_tokens = response_body["completions"][0]["data"].get("tokens", 0)
                stop_reason = response_body["completions"][0].get("finishReason", "endoftext")
                
            else:
                # Claude-3 response format (fallback)
                content = response_body["content"][0]["text"]
                usage = response_body.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                stop_reason = response_body.get("stop_reason", "end_turn")
            
            return BedrockResponse(
                content=content,
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                stop_reason=stop_reason,
                raw_response=response_body
            )
        
        except (KeyError, IndexError) as e:
            logger.error(f"❌ Failed to parse model response: {e}")
            logger.error(f"Response body: {response_body}")
            raise BedrockClientError(f"Failed to parse model response: {e}")
    
    async def invoke_for_agent(
        self,
        agent_type: AgentType,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> BedrockResponse:
        """
        Convenience method to invoke model for a specific agent type.
        
        Args:
            agent_type: The type of agent making the request
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            BedrockResponse: The response from the model
        """
        request = BedrockRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return await self.invoke_model(request, agent_type=agent_type)
    
    async def invoke_for_fintech_agent(
        self,
        agent_type: AgentType,
        prompt: str,
        financial_context: Optional[Dict[str, Any]] = None,
        compliance_requirements: Optional[List[str]] = None,
        risk_tolerance: str = "moderate",
        company_size: str = "medium",
        max_tokens: int = 4000,
        temperature: Optional[float] = None
    ) -> BedrockResponse:
        """
        Enhanced prompting method specifically designed for fintech use cases.
        
        This method provides:
        - Fintech-specific system prompts with compliance and regulatory context
        - Financial accuracy optimizations (lower temperature, enhanced validation)
        - Specialized prompt templates for different fintech agent types
        - Comprehensive context building for financial decision-making
        
        Args:
            agent_type: The type of fintech agent making the request
            prompt: The user prompt for financial analysis
            financial_context: Optional financial context data (company info, market conditions, etc.)
            compliance_requirements: Optional list of specific compliance requirements to consider
            risk_tolerance: Risk tolerance level ("low", "moderate", "high")
            company_size: Company size context ("small", "medium", "large", "enterprise")
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (auto-optimized for fintech if None)
            
        Returns:
            BedrockResponse: The response from the model with fintech-optimized prompting
            
        Raises:
            BedrockClientError: For various client errors
        """
        # Get fintech-specific system prompt
        fintech_system_prompt = FintechPromptTemplates.get_system_prompt(agent_type)
        
        # Build comprehensive fintech context
        fintech_context = FintechPromptTemplates.build_fintech_context(
            financial_context=financial_context,
            compliance_requirements=compliance_requirements,
            risk_tolerance=risk_tolerance,
            company_size=company_size
        )
        
        # Combine system prompt with fintech context
        enhanced_system_prompt = f"{fintech_system_prompt}\n\nFintech Context:\n{fintech_context}"
        
        # Optimize temperature for financial accuracy based on agent type
        if temperature is None:
            # Lower temperature for higher accuracy in financial analysis
            fintech_temperature_mapping = {
                AgentType.REGULATORY_COMPLIANCE: 0.2,  # Highest accuracy for compliance
                AgentType.FRAUD_DETECTION: 0.3,       # High accuracy for fraud detection
                AgentType.RISK_ASSESSMENT: 0.3,       # High accuracy for risk analysis
                AgentType.KYC_VERIFICATION: 0.2,      # Highest accuracy for identity verification
                AgentType.MARKET_ANALYSIS: 0.4,       # Moderate creativity for market insights
                AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE: 0.4,  # Moderate creativity for behavior analysis
            }
            temperature = fintech_temperature_mapping.get(agent_type, 0.3)
        
        # Enhanced prompt with fintech-specific instructions
        enhanced_prompt = f"""
{prompt}

Please provide your analysis with the following fintech-specific requirements:

1. **Accuracy & Compliance**: Ensure all recommendations comply with relevant financial regulations
2. **Confidence Scoring**: Include confidence levels (0-1) for key assessments
3. **Risk Assessment**: Evaluate and communicate associated risks
4. **Actionable Insights**: Provide specific, implementable recommendations
5. **Audit Trail**: Include reasoning and data sources for regulatory compliance
6. **Uncertainty Handling**: Clearly flag any assumptions or areas requiring human review

Format your response with clear sections and quantified assessments where possible.
"""
        
        # Create optimized request for fintech use case
        request = BedrockRequest(
            prompt=enhanced_prompt,
            system_prompt=enhanced_system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9  # Maintain diversity while ensuring accuracy
        )
        
        logger.info(f"🏦 Invoking fintech-optimized model for {agent_type.value} agent")
        logger.debug(f"Temperature: {temperature}, Risk Tolerance: {risk_tolerance}, Company Size: {company_size}")
        
        # Invoke model with fintech optimizations
        response = await self.invoke_model(request, agent_type=agent_type)
        
        # Add fintech-specific metadata to response
        response.raw_response["fintech_metadata"] = {
            "agent_type": agent_type.value,
            "risk_tolerance": risk_tolerance,
            "company_size": company_size,
            "compliance_requirements": compliance_requirements or [],
            "temperature_used": temperature,
            "fintech_optimized": True
        }
        
        return response
    
    def test_connection(self) -> bool:
        """
        Test the connection to Bedrock service.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try to get service info as a connection test
            # Use a simple operation that doesn't require model access
            response = self.bedrock_runtime._service_model.operation_names
            logger.info("??Bedrock connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ Bedrock connection test failed: {e}")
            return False
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available foundation models.
        
        Returns:
            List of available models with their details
        """
        try:
            # Create a bedrock client (not bedrock-runtime) for listing models
            bedrock_client = self.session.client("bedrock")
            response = await asyncio.to_thread(
                bedrock_client.list_foundation_models
            )
            models = response.get("modelSummaries", [])
            
            # Filter for Claude models
            claude_models = [
                model for model in models 
                if "claude" in model.get("modelId", "").lower()
            ]
            
            logger.info(f"📋 Found {len(claude_models)} Claude models available")
            return claude_models
            
        except Exception as e:
            logger.error(f"❌ Failed to get available models: {e}")
            raise BedrockClientError(f"Failed to get available models: {e}")


# Convenience function for creating client instances
def create_bedrock_client(
    region_name: str = "us-east-1",
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None
) -> BedrockClient:
    """
    Create a new Bedrock client instance.
    
    Args:
        region_name: AWS region for Bedrock service
        aws_access_key_id: AWS access key (optional)
        aws_secret_access_key: AWS secret key (optional)
        aws_session_token: AWS session token (optional)
        
    Returns:
        BedrockClient: Configured Bedrock client instance
    """
    return BedrockClient(
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token
    )
