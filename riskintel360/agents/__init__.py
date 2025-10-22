"""
AI Agents module for RiskIntel360 Platform
Contains specialized agents for fintech risk intelligence and compliance.
"""

from .base_agent import (
    BaseAgent, 
    AgentConfig,
    AgentConfigType,
    MarketResearchAgentConfig,
    RiskAssessmentAgentConfig,
    CustomerIntelligenceAgentConfig
)
from .market_analysis_agent import MarketAnalysisAgent, MarketTrend, MarketAnalysisResult
from .customer_behavior_intelligence_agent import CustomerBehaviorIntelligenceAgent
from .risk_assessment_agent import RiskAssessmentAgent
from .regulatory_compliance_agent import RegulatoryComplianceAgent, RegulatoryComplianceAgentConfig
from .fraud_detection_agent import FraudDetectionAgent, FraudDetectionAgentConfig
from .kyc_verification_agent import KYCVerificationAgent, KYCVerificationAgentConfig
from .agent_factory import AgentFactory, get_agent_factory, create_agent

__all__ = [
    # Base classes
    'BaseAgent',
    'AgentConfig',
    'AgentConfigType',
    
    # Configuration classes
    'MarketResearchAgentConfig',
    'RiskAssessmentAgentConfig',
    'CustomerIntelligenceAgentConfig',
    'RegulatoryComplianceAgentConfig',
    'FraudDetectionAgentConfig',
    'KYCVerificationAgentConfig',
    
    # Agent classes
    'MarketAnalysisAgent',
    'CustomerBehaviorIntelligenceAgent',
    'RiskAssessmentAgent',
    'RegulatoryComplianceAgent',
    'FraudDetectionAgent',
    'KYCVerificationAgent',
    
    # Data models
    'MarketTrend',
    'MarketAnalysisResult',
    
    # Factory
    'AgentFactory',
    'get_agent_factory',
    'create_agent'
]