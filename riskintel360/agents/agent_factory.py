"""
Agent Factory for RiskIntel360 Platform
Provides centralized agent creation and configuration management.
"""

import logging
from typing import Dict, Any, Optional, Type, Union
from datetime import datetime, UTC

from .base_agent import (
    BaseAgent, 
    AgentConfig, 
    AgentConfigType,
    MarketResearchAgentConfig,
    RiskAssessmentAgentConfig,
    CustomerIntelligenceAgentConfig,
    EnhancedMarketAnalysisAgentConfig,
    EnhancedRiskAssessmentAgentConfig,
    EnhancedCustomerIntelligenceAgentConfig
)
from .market_analysis_agent import MarketAnalysisAgent
from .customer_behavior_intelligence_agent import CustomerBehaviorIntelligenceAgent
from .risk_assessment_agent import RiskAssessmentAgent
from .regulatory_compliance_agent import RegulatoryComplianceAgent, RegulatoryComplianceAgentConfig
from .fraud_detection_agent import FraudDetectionAgent, FraudDetectionAgentConfig
from .kyc_verification_agent import KYCVerificationAgent, KYCVerificationAgentConfig
from ..models.agent_models import AgentType
from ..services.bedrock_client import BedrockClient, create_bedrock_client
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory class for creating and configuring agents.
    
    Provides centralized agent creation with proper configuration management,
    error handling, and consistent initialization across the system.
    """
    
    def __init__(self, bedrock_client: Optional[BedrockClient] = None):
        """
        Initialize the agent factory.
        
        Args:
            bedrock_client: Optional Bedrock client (will create default if not provided)
        """
        self.settings = get_settings()
        self.bedrock_client = bedrock_client or self._create_default_bedrock_client()
        
        # Agent class registry - Only fintech agents
        self._agent_classes: Dict[AgentType, Type[BaseAgent]] = {
            AgentType.MARKET_ANALYSIS: MarketAnalysisAgent,  # Renamed for fintech focus
            AgentType.RISK_ASSESSMENT: RiskAssessmentAgent,
            AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE: CustomerBehaviorIntelligenceAgent,  # Renamed for fintech focus
            AgentType.REGULATORY_COMPLIANCE: RegulatoryComplianceAgent,  # NEW: Added regulatory compliance agent
            AgentType.FRAUD_DETECTION: FraudDetectionAgent,  # NEW: Added fraud detection agent
            AgentType.KYC_VERIFICATION: KYCVerificationAgent,  # NEW: Added KYC verification agent
        }
        
        # Configuration class registry - Only fintech agents
        self._config_classes: Dict[AgentType, Type[AgentConfig]] = {
            AgentType.MARKET_ANALYSIS: MarketResearchAgentConfig,  # Renamed for fintech focus
            AgentType.RISK_ASSESSMENT: RiskAssessmentAgentConfig,
            AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE: CustomerIntelligenceAgentConfig,  # Renamed for fintech focus
            AgentType.REGULATORY_COMPLIANCE: RegulatoryComplianceAgentConfig,  # NEW: Added regulatory compliance config
            AgentType.FRAUD_DETECTION: FraudDetectionAgentConfig,  # NEW: Added fraud detection config
            AgentType.KYC_VERIFICATION: KYCVerificationAgentConfig,  # NEW: Added KYC verification config
        }
        
        # Enhanced configuration class registry for fintech capabilities
        self._enhanced_config_classes: Dict[AgentType, Type[AgentConfig]] = {
            AgentType.MARKET_ANALYSIS: EnhancedMarketAnalysisAgentConfig,
            AgentType.RISK_ASSESSMENT: EnhancedRiskAssessmentAgentConfig,
            AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE: EnhancedCustomerIntelligenceAgentConfig,
        }
        
        logger.info(f"?­ Agent factory initialized with {len(self._agent_classes)} agent types")
    
    def _create_default_bedrock_client(self) -> BedrockClient:
        """Create a default Bedrock client using application settings"""
        try:
            return create_bedrock_client(region_name="us-east-1")
        except Exception as e:
            logger.error(f"??Failed to create default Bedrock client: {e}")
            raise
    
    def create_enhanced_agent_config(
        self,
        agent_type: AgentType,
        agent_id: Optional[str] = None,
        **config_params
    ) -> AgentConfigType:
        """
        Create enhanced agent configuration with fintech capabilities.
        
        Args:
            agent_type: The type of agent to create config for
            agent_id: Optional agent ID (auto-generated if not provided)
            **config_params: Additional configuration parameters
            
        Returns:
            AgentConfigType: Enhanced configured agent config object
            
        Raises:
            ValueError: If agent type is not supported for enhancement
        """
        if agent_type not in self._enhanced_config_classes:
            # Fall back to regular config if enhanced not available
            return self.create_agent_config(agent_type, agent_id, **config_params)
        
        config_class = self._enhanced_config_classes[agent_type]
        
        # Generate agent ID if not provided
        if agent_id is None:
            timestamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S_%f')[:-3]
            agent_id = f"enhanced_{agent_type.value}_{timestamp}"
        
        # Base configuration parameters
        base_params = {
            'agent_id': agent_id,
            'agent_type': agent_type,
            'bedrock_client': self.bedrock_client,
            'max_retries': config_params.get('max_retries', 3),
            'timeout_seconds': config_params.get('timeout_seconds', 300),
            'memory_limit_mb': config_params.get('memory_limit_mb', 500)
        }
        
        # Add enhanced fintech-specific configuration
        if agent_type == AgentType.MARKET_ANALYSIS:
            base_params.update({
                'alpha_vantage_api_key': self.settings.external_apis.alpha_vantage_api_key,
                'yahoo_finance_enabled': self.settings.external_apis.yahoo_finance_enabled,
                'data_cache_ttl_minutes': config_params.get('data_cache_ttl_minutes', 15),
                'fred_api_key': config_params.get('fred_api_key'),
                'treasury_api_enabled': config_params.get('treasury_api_enabled', True),
                'macroeconomic_analysis_enabled': config_params.get('macroeconomic_analysis_enabled', True),
                'competitive_analysis_enabled': config_params.get('competitive_analysis_enabled', True),
                'investment_insights_enabled': config_params.get('investment_insights_enabled', True)
            })
        elif agent_type == AgentType.RISK_ASSESSMENT:
            base_params.update({
                'regulatory_data_sources': config_params.get('regulatory_data_sources', ["SEC", "FINRA", "CFPB"]),
                'compliance_frameworks': config_params.get('compliance_frameworks', ["SOX", "GDPR", "PCI-DSS"]),
                'financial_risk_analysis_enabled': config_params.get('financial_risk_analysis_enabled', True),
                'cybersecurity_risk_analysis_enabled': config_params.get('cybersecurity_risk_analysis_enabled', True),
                'market_credit_risk_analysis_enabled': config_params.get('market_credit_risk_analysis_enabled', True),
                'enhanced_monitoring_enabled': config_params.get('enhanced_monitoring_enabled', True)
            })
        elif agent_type == AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE:
            base_params.update({
                'twitter_api_key': self.settings.external_apis.twitter_api_key,
                'reddit_api_key': self.settings.external_apis.reddit_api_key,
                'sentiment_analysis_enabled': config_params.get('sentiment_analysis_enabled', True),
                'behavioral_analytics_enabled': config_params.get('behavioral_analytics_enabled', True),
                'clv_analysis_enabled': config_params.get('clv_analysis_enabled', True),
                'personalization_enabled': config_params.get('personalization_enabled', True),
                'financial_behavior_analysis_enabled': config_params.get('financial_behavior_analysis_enabled', True),
                'clv_modeling_enabled': config_params.get('clv_modeling_enabled', True),
                'advanced_segmentation_enabled': config_params.get('advanced_segmentation_enabled', True),
                'behavioral_prediction_enabled': config_params.get('behavioral_prediction_enabled', True)
            })
        
        # Override with any provided config parameters
        base_params.update(config_params)
        
        try:
            config = config_class(**base_params)
            logger.info(f"✨ Created enhanced configuration for {agent_type.value} agent: {agent_id}")
            return config
        except Exception as e:
            logger.error(f"❌ Failed to create enhanced configuration for {agent_type.value}: {e}")
            raise ValueError(f"Failed to create enhanced agent configuration: {e}")
    
    def create_agent_config(
        self,
        agent_type: AgentType,
        agent_id: Optional[str] = None,
        **config_params
    ) -> AgentConfigType:
        """
        Create agent configuration for the specified agent type.
        
        Args:
            agent_type: The type of agent to create config for
            agent_id: Optional agent ID (auto-generated if not provided)
            **config_params: Additional configuration parameters
            
        Returns:
            AgentConfigType: Configured agent config object
            
        Raises:
            ValueError: If agent type is not supported
        """
        if agent_type not in self._config_classes:
            raise ValueError(f"Unsupported agent type: {agent_type}")
        
        config_class = self._config_classes[agent_type]
        
        # Generate agent ID if not provided
        if agent_id is None:
            timestamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S_%f')[:-3]
            agent_id = f"{agent_type.value}_{timestamp}"
        
        # Base configuration parameters
        base_params = {
            'agent_id': agent_id,
            'agent_type': agent_type,
            'bedrock_client': self.bedrock_client,
            'max_retries': config_params.get('max_retries', 3),
            'timeout_seconds': config_params.get('timeout_seconds', 300),
            'memory_limit_mb': config_params.get('memory_limit_mb', 500)
        }
        
        # Add agent-specific configuration from settings for fintech agents
        if agent_type == AgentType.MARKET_ANALYSIS:
            base_params.update({
                'alpha_vantage_api_key': self.settings.external_apis.alpha_vantage_api_key,
                'yahoo_finance_enabled': self.settings.external_apis.yahoo_finance_enabled,
                'data_cache_ttl_minutes': config_params.get('data_cache_ttl_minutes', 15)
            })
        elif agent_type == AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE:
            base_params.update({
                'twitter_api_key': self.settings.external_apis.twitter_api_key,
                'reddit_api_key': self.settings.external_apis.reddit_api_key,
                'sentiment_analysis_enabled': config_params.get('sentiment_analysis_enabled', True)
            })
        elif agent_type == AgentType.REGULATORY_COMPLIANCE:
            base_params.update({
                'regulatory_sources': config_params.get('regulatory_sources', ["SEC", "FINRA", "CFPB"]),
                'jurisdiction': config_params.get('jurisdiction', 'US'),
                'compliance_frameworks': config_params.get('compliance_frameworks', ["SOX", "GDPR", "PCI-DSS", "CCPA"]),
                'monitoring_interval_hours': config_params.get('monitoring_interval_hours', 24),
                'alert_threshold': config_params.get('alert_threshold', 0.8)
            })
        elif agent_type == AgentType.FRAUD_DETECTION:
            base_params.update({
                'ml_model_types': config_params.get('ml_model_types', ["isolation_forest", "autoencoder", "clustering"]),
                'anomaly_threshold': config_params.get('anomaly_threshold', 0.8),
                'false_positive_target': config_params.get('false_positive_target', 0.1),
                'confidence_threshold': config_params.get('confidence_threshold', 0.7),
                'real_time_processing': config_params.get('real_time_processing', True),
                'batch_size': config_params.get('batch_size', 1000),
                'model_retrain_interval_hours': config_params.get('model_retrain_interval_hours', 24),
                'alert_priority_threshold': config_params.get('alert_priority_threshold', 0.9)
            })
        elif agent_type == AgentType.KYC_VERIFICATION:
            base_params.update({
                'verification_level': config_params.get('verification_level', 'enhanced'),
                'sanctions_lists': config_params.get('sanctions_lists', ["OFAC_SDN", "UN_Consolidated", "EU_Sanctions", "UK_HMT", "FATF_High_Risk"]),
                'risk_threshold': config_params.get('risk_threshold', 0.7),
                'auto_approve_threshold': config_params.get('auto_approve_threshold', 0.9),
                'manual_review_threshold': config_params.get('manual_review_threshold', 0.5),
                'pep_screening_enabled': config_params.get('pep_screening_enabled', True),
                'document_verification_enabled': config_params.get('document_verification_enabled', True)
            })
        
        # Override with any provided config parameters
        base_params.update(config_params)
        
        try:
            config = config_class(**base_params)
            logger.info(f"??Created configuration for {agent_type.value} agent: {agent_id}")
            return config
        except Exception as e:
            logger.error(f"??Failed to create configuration for {agent_type.value}: {e}")
            raise ValueError(f"Failed to create agent configuration: {e}")
    
    def create_agent(
        self,
        agent_type: AgentType,
        agent_id: Optional[str] = None,
        config: Optional[AgentConfigType] = None,
        **config_params
    ) -> BaseAgent:
        """
        Create an agent instance of the specified type.
        
        Args:
            agent_type: The type of agent to create
            agent_id: Optional agent ID (auto-generated if not provided)
            config: Optional pre-configured agent config
            **config_params: Additional configuration parameters (ignored if config provided)
            
        Returns:
            BaseAgent: Initialized agent instance
            
        Raises:
            ValueError: If agent type is not supported
            RuntimeError: If agent creation fails
        """
        if agent_type not in self._agent_classes:
            raise ValueError(f"Unsupported agent type: {agent_type}")
        
        agent_class = self._agent_classes[agent_type]
        
        # Create configuration if not provided
        if config is None:
            config = self.create_agent_config(agent_type, agent_id, **config_params)
        
        try:
            # Create agent instance
            agent = agent_class(config)
            logger.info(f"??Created {agent_type.value} agent: {config.agent_id}")
            return agent
        except Exception as e:
            logger.error(f"??Failed to create {agent_type.value} agent: {e}")
            raise RuntimeError(f"Failed to create agent: {e}")
    
    def create_enhanced_market_analysis_agent(
        self,
        agent_id: Optional[str] = None,
        alpha_vantage_api_key: Optional[str] = None,
        fred_api_key: Optional[str] = None,
        **config_params
    ) -> MarketAnalysisAgent:
        """
        Convenience method to create an Enhanced Market Analysis Agent with fintech capabilities.
        
        Args:
            agent_id: Optional agent ID
            alpha_vantage_api_key: Optional Alpha Vantage API key
            fred_api_key: Optional FRED API key
            **config_params: Additional configuration parameters
            
        Returns:
            MarketAnalysisAgent: Enhanced market analysis agent for fintech
        """
        if alpha_vantage_api_key:
            config_params['alpha_vantage_api_key'] = alpha_vantage_api_key
        if fred_api_key:
            config_params['fred_api_key'] = fred_api_key
        
        enhanced_config = self.create_enhanced_agent_config(
            AgentType.MARKET_ANALYSIS,
            agent_id=agent_id,
            **config_params
        )
        
        return self.create_agent(
            AgentType.MARKET_ANALYSIS,
            agent_id=agent_id,
            config=enhanced_config
        )
    
    def create_enhanced_risk_assessment_agent(
        self,
        agent_id: Optional[str] = None,
        **config_params
    ) -> RiskAssessmentAgent:
        """
        Convenience method to create an Enhanced Risk Assessment Agent with fintech capabilities.
        
        Args:
            agent_id: Optional agent ID
            **config_params: Additional configuration parameters
            
        Returns:
            RiskAssessmentAgent: Enhanced risk assessment agent for fintech
        """
        enhanced_config = self.create_enhanced_agent_config(
            AgentType.RISK_ASSESSMENT,
            agent_id=agent_id,
            **config_params
        )
        
        return self.create_agent(
            AgentType.RISK_ASSESSMENT,
            agent_id=agent_id,
            config=enhanced_config
        )
    
    def create_enhanced_customer_behavior_intelligence_agent(
        self,
        agent_id: Optional[str] = None,
        **config_params
    ) -> CustomerBehaviorIntelligenceAgent:
        """
        Convenience method to create an Enhanced Customer Behavior Intelligence Agent with fintech capabilities.
        
        Args:
            agent_id: Optional agent ID
            **config_params: Additional configuration parameters
            
        Returns:
            CustomerBehaviorIntelligenceAgent: Enhanced customer behavior intelligence agent for fintech
        """
        enhanced_config = self.create_enhanced_agent_config(
            AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE,
            agent_id=agent_id,
            **config_params
        )
        
        return self.create_agent(
            AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE,
            agent_id=agent_id,
            config=enhanced_config
        )
    
    def create_market_analysis_agent(
        self,
        agent_id: Optional[str] = None,
        alpha_vantage_api_key: Optional[str] = None,
        **config_params
    ) -> MarketAnalysisAgent:
        """
        Convenience method to create a Market Analysis Agent (fintech-focused).
        
        Args:
            agent_id: Optional agent ID
            alpha_vantage_api_key: Optional Alpha Vantage API key
            **config_params: Additional configuration parameters
            
        Returns:
            MarketAnalysisAgent: Configured market analysis agent for fintech
        """
        if alpha_vantage_api_key:
            config_params['alpha_vantage_api_key'] = alpha_vantage_api_key
        
        return self.create_agent(
            AgentType.MARKET_ANALYSIS,
            agent_id=agent_id,
            **config_params
        )
    
    def create_fraud_detection_agent(
        self,
        agent_id: Optional[str] = None,
        anomaly_threshold: Optional[float] = None,
        false_positive_target: Optional[float] = None,
        **config_params
    ) -> FraudDetectionAgent:
        """
        Convenience method to create a Fraud Detection Agent with ML capabilities.
        
        Args:
            agent_id: Optional agent ID
            anomaly_threshold: Optional anomaly detection threshold (0-1)
            false_positive_target: Optional false positive target rate (0-1)
            **config_params: Additional configuration parameters
            
        Returns:
            FraudDetectionAgent: Configured fraud detection agent with ML engine
        """
        if anomaly_threshold is not None:
            config_params['anomaly_threshold'] = anomaly_threshold
        
        if false_positive_target is not None:
            config_params['false_positive_target'] = false_positive_target
        
        return self.create_agent(
            AgentType.FRAUD_DETECTION,
            agent_id=agent_id,
            **config_params
        )
    
    def create_kyc_verification_agent(
        self,
        agent_id: Optional[str] = None,
        verification_level: Optional[str] = None,
        risk_threshold: Optional[float] = None,
        **config_params
    ) -> KYCVerificationAgent:
        """
        Convenience method to create a KYC Verification Agent.
        
        Args:
            agent_id: Optional agent ID
            verification_level: Optional verification level ('basic', 'enhanced', 'simplified')
            risk_threshold: Optional risk threshold for decision making (0-1)
            **config_params: Additional configuration parameters
            
        Returns:
            KYCVerificationAgent: Configured KYC verification agent
        """
        if verification_level is not None:
            config_params['verification_level'] = verification_level
        
        if risk_threshold is not None:
            config_params['risk_threshold'] = risk_threshold
        
        return self.create_agent(
            AgentType.KYC_VERIFICATION,
            agent_id=agent_id,
            **config_params
        )
    
    def get_supported_agent_types(self) -> list[AgentType]:
        """
        Get list of supported agent types.
        
        Returns:
            List of supported AgentType values
        """
        return list(self._agent_classes.keys())
    
    def is_agent_type_supported(self, agent_type: AgentType) -> bool:
        """
        Check if an agent type is supported.
        
        Args:
            agent_type: Agent type to check
            
        Returns:
            bool: True if supported, False otherwise
        """
        return agent_type in self._agent_classes
    
    def validate_agent_config(self, config: AgentConfigType) -> bool:
        """
        Validate an agent configuration.
        
        Args:
            config: Agent configuration to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check if agent type is supported
            if not self.is_agent_type_supported(config.agent_type):
                logger.error(f"??Unsupported agent type: {config.agent_type}")
                return False
            
            # Check required fields
            if not config.agent_id:
                logger.error("??Agent ID is required")
                return False
            
            if not config.bedrock_client:
                logger.error("??Bedrock client is required")
                return False
            
            # Validate configuration parameters
            if config.max_retries < 0:
                logger.error("??Max retries must be non-negative")
                return False
            
            if config.timeout_seconds <= 0:
                logger.error("??Timeout must be positive")
                return False
            
            if config.memory_limit_mb <= 0:
                logger.error("??Memory limit must be positive")
                return False
            
            logger.info(f"??Agent configuration is valid: {config.agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"??Configuration validation failed: {e}")
            return False
    
    async def store_analysis_result(self, analysis_id: str, user_id: str, result: Any) -> None:
        """
        Store analysis result for later retrieval.
        
        Args:
            analysis_id: Unique analysis identifier
            user_id: User who requested the analysis
            result: Analysis result to store
        """
        try:
            # For now, store in memory (in production, use database)
            if not hasattr(self, '_analysis_results'):
                self._analysis_results = {}
            
            self._analysis_results[analysis_id] = {
                'user_id': user_id,
                'result': result,
                'stored_at': datetime.now(UTC),
                'status': 'completed'
            }
            
            logger.info(f"✅ Stored analysis result for {analysis_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store analysis result {analysis_id}: {e}")
            raise
    
    async def store_analysis_error(self, analysis_id: str, user_id: str, error_message: str) -> None:
        """
        Store analysis error for later retrieval.
        
        Args:
            analysis_id: Unique analysis identifier
            user_id: User who requested the analysis
            error_message: Error message to store
        """
        try:
            # For now, store in memory (in production, use database)
            if not hasattr(self, '_analysis_results'):
                self._analysis_results = {}
            
            self._analysis_results[analysis_id] = {
                'user_id': user_id,
                'error': error_message,
                'stored_at': datetime.now(UTC),
                'status': 'failed'
            }
            
            logger.info(f"✅ Stored analysis error for {analysis_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store analysis error {analysis_id}: {e}")
            raise
    
    async def get_analysis_result(self, analysis_id: str, user_id: str) -> Optional[Any]:
        """
        Retrieve analysis result by ID.
        
        Args:
            analysis_id: Unique analysis identifier
            user_id: User who requested the analysis
            
        Returns:
            Analysis result if found, None otherwise
        """
        try:
            if not hasattr(self, '_analysis_results'):
                return None
            
            stored_data = self._analysis_results.get(analysis_id)
            if not stored_data:
                return None
            
            # Check user access
            if stored_data['user_id'] != user_id:
                logger.warning(f"❌ Access denied for analysis {analysis_id} by user {user_id}")
                return None
            
            if stored_data['status'] == 'completed':
                return stored_data['result']
            elif stored_data['status'] == 'failed':
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=500,
                    detail=f"Analysis failed: {stored_data['error']}"
                )
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get analysis result {analysis_id}: {e}")
            raise


# Global factory instance
_factory_instance: Optional[AgentFactory] = None


def get_agent_factory(bedrock_client: Optional[BedrockClient] = None) -> AgentFactory:
    """
    Get the global agent factory instance.
    
    Args:
        bedrock_client: Optional Bedrock client for factory initialization
        
    Returns:
        AgentFactory: Global factory instance
    """
    global _factory_instance
    
    if _factory_instance is None:
        _factory_instance = AgentFactory(bedrock_client)
    
    return _factory_instance


def create_agent(
    agent_type: AgentType,
    agent_id: Optional[str] = None,
    bedrock_client: Optional[BedrockClient] = None,
    **config_params
) -> BaseAgent:
    """
    Convenience function to create an agent using the global factory.
    
    Args:
        agent_type: The type of agent to create
        agent_id: Optional agent ID
        bedrock_client: Optional Bedrock client
        **config_params: Additional configuration parameters
        
    Returns:
        BaseAgent: Initialized agent instance
    """
    factory = get_agent_factory(bedrock_client)
    return factory.create_agent(agent_type, agent_id, **config_params)
