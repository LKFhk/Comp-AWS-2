"""
Base Agent Class for RiskIntel360 Platform
Provides common functionality for all specialized agents.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field

from ..services.bedrock_client import BedrockClient, BedrockRequest
from ..models.agent_models import AgentState, SessionStatus, AgentMessage, MessageType, Priority, AgentType


logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Base configuration for agent initialization"""
    agent_id: str
    agent_type: AgentType
    bedrock_client: BedrockClient
    max_retries: int = 3
    timeout_seconds: int = 300
    memory_limit_mb: int = 500
    
    @classmethod
    def create_for_agent_type(
        cls, 
        agent_type: AgentType, 
        bedrock_client: BedrockClient,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> "AgentConfig":
        """
        Create agent configuration for a specific agent type.
        
        Args:
            agent_type: The type of agent to create config for
            bedrock_client: Bedrock client instance
            agent_id: Optional agent ID (auto-generated if not provided)
            **kwargs: Additional configuration parameters
            
        Returns:
            AgentConfig: Configured agent config object
        """
        if agent_id is None:
            agent_id = f"{agent_type.value}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        
        return cls(
            agent_id=agent_id,
            agent_type=agent_type,
            bedrock_client=bedrock_client,
            max_retries=kwargs.get('max_retries', 3),
            timeout_seconds=kwargs.get('timeout_seconds', 300),
            memory_limit_mb=kwargs.get('memory_limit_mb', 500)
        )


@dataclass
class MarketResearchAgentConfig(AgentConfig):
    """Configuration specific to Market Analysis Agent (fintech-focused)"""
    alpha_vantage_api_key: Optional[str] = None
    yahoo_finance_enabled: bool = True
    data_cache_ttl_minutes: int = 15
    
    def __post_init__(self):
        if self.agent_type != AgentType.MARKET_ANALYSIS:
            raise ValueError(f"Invalid agent type for MarketResearchAgentConfig: {self.agent_type}")


@dataclass
class RiskAssessmentAgentConfig(AgentConfig):
    """Configuration specific to Risk Assessment Agent (fintech-focused)"""
    regulatory_data_sources: List[str] = field(default_factory=lambda: ["SEC", "FINRA", "CFPB"])
    compliance_frameworks: List[str] = field(default_factory=lambda: ["SOX", "GDPR", "PCI-DSS"])
    
    def __post_init__(self):
        if self.agent_type != AgentType.RISK_ASSESSMENT:
            raise ValueError(f"Invalid agent type for RiskAssessmentAgentConfig: {self.agent_type}")


@dataclass
class CustomerIntelligenceAgentConfig(AgentConfig):
    """Configuration specific to Customer Behavior Intelligence Agent (fintech-focused)"""
    twitter_api_key: Optional[str] = None
    reddit_api_key: Optional[str] = None
    sentiment_analysis_enabled: bool = True
    behavioral_analytics_enabled: bool = True
    clv_analysis_enabled: bool = True
    personalization_enabled: bool = True
    
    def __post_init__(self):
        if self.agent_type != AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE:
            raise ValueError(f"Invalid agent type for CustomerIntelligenceAgentConfig: {self.agent_type}")


@dataclass
class EnhancedMarketAnalysisAgentConfig(MarketResearchAgentConfig):
    """Enhanced configuration for Market Analysis Agent with fintech capabilities"""
    fred_api_key: Optional[str] = None
    treasury_api_enabled: bool = True
    macroeconomic_analysis_enabled: bool = True
    competitive_analysis_enabled: bool = True
    investment_insights_enabled: bool = True
    
    def __post_init__(self):
        super().__post_init__()


@dataclass
class EnhancedRiskAssessmentAgentConfig(RiskAssessmentAgentConfig):
    """Enhanced configuration for Risk Assessment Agent with fintech capabilities"""
    financial_risk_analysis_enabled: bool = True
    cybersecurity_risk_analysis_enabled: bool = True
    market_credit_risk_analysis_enabled: bool = True
    enhanced_monitoring_enabled: bool = True
    
    def __post_init__(self):
        super().__post_init__()


@dataclass
class EnhancedCustomerIntelligenceAgentConfig(CustomerIntelligenceAgentConfig):
    """Enhanced configuration for Customer Behavior Intelligence Agent with fintech capabilities"""
    financial_behavior_analysis_enabled: bool = True
    clv_modeling_enabled: bool = True
    advanced_segmentation_enabled: bool = True
    behavioral_prediction_enabled: bool = True
    
    def __post_init__(self):
        super().__post_init__()


# Type alias for all agent config types (fintech agents only)
AgentConfigType = Union[
    AgentConfig,
    MarketResearchAgentConfig,
    RiskAssessmentAgentConfig,
    CustomerIntelligenceAgentConfig,
    "RegulatoryComplianceAgentConfig"  # Forward reference for circular import
]


class BaseAgent(ABC):
    """
    Base class for all RiskIntel360 agents.
    
    Provides common functionality including:
    - Bedrock integration
    - State management
    - Error handling
    - Logging
    - Message communication
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize base agent with configuration.
        
        Args:
            config: Agent configuration object
        """
        self.config = config
        self.agent_id = config.agent_id
        self.agent_type = config.agent_type
        self.bedrock_client = config.bedrock_client
        
        # Initialize state
        self.state = AgentState(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=SessionStatus.CREATED
        )
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{self.agent_type.value}")
        self.logger.info(f"🤖 Initialized {self.agent_type.value} agent: {self.agent_id}")
        
        # Message queue for inter-agent communication
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
        # Task tracking
        self.current_task: Optional[str] = None
        self.task_results: Dict[str, Any] = {}
        
    async def start(self) -> None:
        """Start the agent and set status to running"""
        self.state.status = SessionStatus.RUNNING
        self.state.last_activity = datetime.now(UTC)
        self.logger.info(f"▶️ Agent {self.agent_id} started")
    
    async def stop(self) -> None:
        """Stop the agent and cleanup resources"""
        self.state.status = SessionStatus.TERMINATED
        self.state.last_activity = datetime.now(UTC)
        self.logger.info(f"⏹️ Agent {self.agent_id} stopped")
    
    async def pause(self) -> None:
        """Pause agent execution"""
        self.state.status = SessionStatus.PAUSED
        self.state.last_activity = datetime.now(UTC)
        self.logger.info(f"⏸️ Agent {self.agent_id} paused")
    
    async def resume(self) -> None:
        """Resume agent execution"""
        self.state.status = SessionStatus.RUNNING
        self.state.last_activity = datetime.now(UTC)
        self.logger.info(f"▶️ Agent {self.agent_id} resumed")
    
    async def send_message(self, recipient_id: str, message_type: MessageType, content: Dict[str, Any], priority: Priority = Priority.MEDIUM) -> None:
        """
        Send message to another agent.
        
        Args:
            recipient_id: Target agent ID
            message_type: Type of message
            content: Message content
            priority: Message priority
        """
        message = AgentMessage(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
            priority=priority
        )
        
        # In a real implementation, this would use a message broker
        # For now, we'll log the message
        self.logger.info(f"📤 Sending {message_type.value} message to {recipient_id}")
        self.logger.debug(f"Message content: {content}")
    
    async def receive_message(self, message: AgentMessage) -> None:
        """
        Receive and process a message from another agent.
        
        Args:
            message: The received message
        """
        await self.message_queue.put(message)
        self.logger.info(f"📥 Received {message.message_type.value} message from {message.sender_id}")
    
    async def process_messages(self) -> None:
        """Process messages in the queue"""
        while not self.message_queue.empty():
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self.handle_message(message)
                self.message_queue.task_done()
            except asyncio.TimeoutError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error processing message: {e}")
    
    async def handle_message(self, message: AgentMessage) -> None:
        """
        Handle a received message. Override in subclasses.
        
        Args:
            message: The message to handle
        """
        self.logger.info(f"🔄 Handling {message.message_type.value} message")
    
    async def invoke_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> str:
        """
        Invoke the LLM for this agent type.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            str: The LLM response content
        """
        try:
            self.logger.debug(f"🧠 Invoking LLM for {self.agent_type.value}")
            
            response = await self.bedrock_client.invoke_for_agent(
                agent_type=self.agent_type,
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            self.logger.info(f"✅ LLM response received ({response.input_tokens} input, {response.output_tokens} output tokens)")
            return response.content
            
        except Exception as e:
            self.logger.error(f"❌ LLM invocation failed: {e}")
            raise
    
    async def invoke_fintech_llm(
        self,
        prompt: str,
        financial_context: Optional[Dict[str, Any]] = None,
        compliance_requirements: Optional[List[str]] = None,
        risk_tolerance: str = "moderate",
        company_size: str = "medium",
        max_tokens: int = 4000,
        temperature: Optional[float] = None
    ) -> str:
        """
        Invoke the LLM with fintech-specific optimizations and prompting.
        
        This method provides enhanced prompting specifically designed for fintech use cases:
        - Fintech-specific system prompts with compliance and regulatory context
        - Financial accuracy optimizations (lower temperature, enhanced validation)
        - Comprehensive context building for financial decision-making
        - Specialized prompt templates for different fintech agent types
        
        Args:
            prompt: User prompt for financial analysis
            financial_context: Optional financial context data (company info, market conditions, etc.)
            compliance_requirements: Optional list of specific compliance requirements to consider
            risk_tolerance: Risk tolerance level ("low", "moderate", "high")
            company_size: Company size context ("small", "medium", "large", "enterprise")
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (auto-optimized for fintech if None)
            
        Returns:
            str: The LLM response content with fintech-optimized analysis
        """
        try:
            self.logger.debug(f"🏦 Invoking fintech-optimized LLM for {self.agent_type.value}")
            
            response = await self.bedrock_client.invoke_for_fintech_agent(
                agent_type=self.agent_type,
                prompt=prompt,
                financial_context=financial_context,
                compliance_requirements=compliance_requirements,
                risk_tolerance=risk_tolerance,
                company_size=company_size,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            self.logger.info(f"✅ Fintech LLM response received ({response.input_tokens} input, {response.output_tokens} output tokens)")
            self.logger.debug(f"🎯 Fintech optimization: temp={response.raw_response.get('fintech_metadata', {}).get('temperature_used', 'N/A')}, risk={risk_tolerance}")
            
            return response.content
            
        except Exception as e:
            self.logger.error(f"❌ Fintech LLM invocation failed: {e}")
            raise
    
    def update_progress(self, progress: float) -> None:
        """
        Update task progress.
        
        Args:
            progress: Progress value between 0.0 and 1.0
        """
        self.state.progress = max(0.0, min(1.0, progress))
        self.state.last_activity = datetime.now(UTC)
        self.logger.debug(f"📊 Progress updated: {progress:.1%}")
    
    def get_state(self) -> AgentState:
        """Get current agent state"""
        return self.state
    
    def is_healthy(self) -> bool:
        """Check if agent is healthy"""
        return (
            self.state.status in [SessionStatus.RUNNING, SessionStatus.PAUSED] and
            self.state.error_count < 5 and
            self.state.memory_usage_mb < self.config.memory_limit_mb
        )
    
    @abstractmethod
    async def execute_task(self, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific task. Must be implemented by subclasses.
        
        Args:
            task_type: Type of task to execute
            parameters: Task parameters
            
        Returns:
            Dict containing task results
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of capabilities this agent supports.
        
        Returns:
            List of capability names
        """
        pass
