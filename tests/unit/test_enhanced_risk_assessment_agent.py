"""
Unit tests for Enhanced Risk Assessment Agent fintech capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, UTC

from riskintel360.agents.risk_assessment_agent import RiskAssessmentAgent, BusinessRisk
from riskintel360.agents.base_agent import EnhancedRiskAssessmentAgentConfig
from riskintel360.models.agent_models import AgentType
from riskintel360.services.bedrock_client import BedrockClient


@pytest.fixture
def mock_bedrock_client():
    """Create a mock Bedrock client for testing"""
    client = Mock(spec=BedrockClient)
    client.invoke_for_agent = AsyncMock()
    return client


@pytest.fixture
def enhanced_risk_agent_config(mock_bedrock_client):
    """Create enhanced risk assessment agent configuration"""
    return EnhancedRiskAssessmentAgentConfig(
        agent_id="test_enhanced_risk_agent",
        agent_type=AgentType.RISK_ASSESSMENT,
        bedrock_client=mock_bedrock_client,
        financial_risk_analysis_enabled=True,
        cybersecurity_risk_analysis_enabled=True,
        market_credit_risk_analysis_enabled=True,
        enhanced_monitoring_enabled=True
    )


@pytest.fixture
def enhanced_risk_agent(enhanced_risk_agent_config):
    """Create enhanced risk assessment agent instance"""
    return RiskAssessmentAgent(enhanced_risk_agent_config)


class TestEnhancedRiskAssessmentAgent:
    """Test suite for Enhanced Risk Assessment Agent fintech capabilities"""
    
    @pytest.mark.asyncio
    async def test_enhanced_fintech_risk_assessment(self, enhanced_risk_agent, mock_bedrock_client):
        """Test enhanced fintech risk assessment execution"""
        # Mock LLM responses for enhanced analysis
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"risks": [{"risk_category": "credit", "risk_level": "medium", "probability": 0.4, "impact_score": 7.0, "description": "Credit risk from defaults", "mitigation_strategies": ["Credit scoring"], "monitoring_indicators": ["Default rates"]}]}'
        )
        
        # Test parameters
        parameters = {
            'business_model': 'fintech',
            'industry': 'financial_services',
            'target_markets': ['US']
        }
        
        # Execute enhanced analysis
        result = await enhanced_risk_agent._perform_enhanced_fintech_risk_assessment(parameters)
        
        # Verify enhanced capabilities
        assert result is not None
        assert 'assessment_result' in result
        assert 'metadata' in result
        assert result['metadata']['fintech_enhanced'] is True
        
        # Verify assessment result structure
        assessment_result = result['assessment_result']
        assert 'overall_risk_score' in assessment_result
        assert 'risk_level' in assessment_result
        assert 'financial_risks' in assessment_result
        assert 'regulatory_risks' in assessment_result
        assert 'operational_risks' in assessment_result
        assert 'market_credit_risks' in assessment_result
        assert 'cybersecurity_technology_risks' in assessment_result
        assert 'fintech_specific_insights' in assessment_result
        
        # Verify confidence score
        assert 'confidence_score' in assessment_result
        assert assessment_result['confidence_score'] >= 0.7
    
    @pytest.mark.asyncio
    async def test_enhanced_financial_risks_evaluation(self, enhanced_risk_agent, mock_bedrock_client):
        """Test enhanced financial risks evaluation"""
        # Mock LLM response for financial risks
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"risks": [{"risk_category": "credit", "risk_level": "medium", "probability": 0.4, "impact_score": 7.0, "description": "Credit risk from loan defaults", "financial_impact_usd": 1000000, "mitigation_strategies": ["Credit scoring models", "Diversified portfolio"], "monitoring_indicators": ["Default rates", "Credit scores"], "regulatory_implications": ["Basel III compliance"]}]}'
        )
        
        # Test parameters
        parameters = {
            'business_model': 'fintech',
            'industry': 'financial_services'
        }
        
        # Execute enhanced financial risk evaluation
        financial_risks = await enhanced_risk_agent._evaluate_enhanced_financial_risks(parameters)
        
        assert financial_risks is not None
        assert len(financial_risks) > 0
        
        # Verify risk structure
        risk = financial_risks[0]
        assert isinstance(risk, BusinessRisk)
        assert risk.risk_category == 'credit'
        assert risk.risk_level == 'medium'
        assert risk.probability == 0.4
        assert risk.impact_score == 7.0
        assert abs(risk.risk_score - 2.8) < 0.01  # probability * impact_score (allow for floating point precision)
        assert len(risk.mitigation_strategies) > 0
        assert len(risk.monitoring_indicators) > 0
    
    @pytest.mark.asyncio
    async def test_regulatory_compliance_risks_assessment(self, enhanced_risk_agent, mock_bedrock_client):
        """Test regulatory compliance risks assessment"""
        # Mock LLM response for regulatory risks
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"risks": [{"risk_category": "kyc_aml", "risk_level": "high", "probability": 0.4, "impact_score": 9.0, "description": "KYC/AML compliance failures", "regulatory_body": "FINRA", "potential_penalties": "Significant fines", "mitigation_strategies": ["Automated KYC systems"], "monitoring_indicators": ["Compliance violations"]}]}'
        )
        
        # Test parameters
        parameters = {
            'business_model': 'fintech',
            'target_markets': ['US']
        }
        
        # Execute regulatory compliance risk assessment
        regulatory_risks = await enhanced_risk_agent._assess_regulatory_compliance_risks(parameters)
        
        assert regulatory_risks is not None
        assert len(regulatory_risks) > 0
        
        # Verify regulatory risk structure
        risk = regulatory_risks[0]
        assert isinstance(risk, BusinessRisk)
        assert risk.risk_category == 'kyc_aml'
        assert risk.risk_level == 'high'
        assert risk.probability == 0.4
        assert risk.impact_score == 9.0
        assert len(risk.mitigation_strategies) > 0
    
    @pytest.mark.asyncio
    async def test_fintech_operational_risks_analysis(self, enhanced_risk_agent, mock_bedrock_client):
        """Test fintech operational risks analysis"""
        # Mock LLM response for operational risks
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"risks": [{"risk_category": "technology", "risk_level": "high", "probability": 0.5, "impact_score": 7.0, "description": "Technology infrastructure failures", "operational_impact": "Service disruptions", "mitigation_strategies": ["Redundant systems"], "monitoring_indicators": ["System uptime"]}]}'
        )
        
        # Test parameters
        parameters = {
            'business_model': 'fintech'
        }
        
        # Execute operational risk analysis
        operational_risks = await enhanced_risk_agent._analyze_fintech_operational_risks(parameters)
        
        assert operational_risks is not None
        assert len(operational_risks) > 0
        
        # Verify operational risk structure
        risk = operational_risks[0]
        assert isinstance(risk, BusinessRisk)
        assert risk.risk_category == 'technology'
        assert risk.risk_level == 'high'
        assert risk.probability == 0.5
        assert risk.impact_score == 7.0
        assert len(risk.mitigation_strategies) > 0
    
    @pytest.mark.asyncio
    async def test_market_and_credit_risks_assessment(self, enhanced_risk_agent, mock_bedrock_client):
        """Test market and credit risks assessment"""
        # Mock LLM response for market and credit risks
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"risks": [{"risk_category": "market_volatility", "risk_level": "medium", "probability": 0.5, "impact_score": 6.0, "description": "Market volatility affecting business", "financial_impact": "Valuation fluctuations", "mitigation_strategies": ["Diversification"], "monitoring_indicators": ["Market indices"]}]}'
        )
        
        # Test parameters
        parameters = {
            'business_model': 'fintech'
        }
        
        # Execute market and credit risk assessment
        market_credit_risks = await enhanced_risk_agent._assess_market_and_credit_risks(parameters)
        
        assert market_credit_risks is not None
        assert len(market_credit_risks) > 0
        
        # Verify market/credit risk structure
        risk = market_credit_risks[0]
        assert isinstance(risk, BusinessRisk)
        assert risk.risk_category == 'market_volatility'
        assert risk.risk_level == 'medium'
        assert risk.probability == 0.5
        assert risk.impact_score == 6.0
        assert len(risk.mitigation_strategies) > 0
    
    @pytest.mark.asyncio
    async def test_cybersecurity_technology_risks_evaluation(self, enhanced_risk_agent, mock_bedrock_client):
        """Test cybersecurity and technology risks evaluation"""
        # Mock LLM response for cybersecurity risks
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"risks": [{"risk_category": "cyber_attack", "risk_level": "high", "probability": 0.6, "impact_score": 9.0, "description": "Cyber attacks targeting financial data", "security_impact": "Data breaches", "mitigation_strategies": ["Multi-factor authentication"], "monitoring_indicators": ["Security incidents"]}]}'
        )
        
        # Test parameters
        parameters = {
            'business_model': 'fintech'
        }
        
        # Execute cybersecurity and technology risk evaluation
        cyber_tech_risks = await enhanced_risk_agent._evaluate_cybersecurity_technology_risks(parameters)
        
        assert cyber_tech_risks is not None
        assert len(cyber_tech_risks) > 0
        
        # Verify cybersecurity risk structure
        risk = cyber_tech_risks[0]
        assert isinstance(risk, BusinessRisk)
        assert risk.risk_category == 'cyber_attack'
        assert risk.risk_level == 'high'
        assert risk.probability == 0.6
        assert risk.impact_score == 9.0
        assert abs(risk.risk_score - 5.4) < 0.01  # probability * impact_score (allow for floating point precision)
        assert len(risk.mitigation_strategies) > 0
    
    def test_enhanced_overall_risk_score_calculation(self, enhanced_risk_agent):
        """Test enhanced overall risk score calculation"""
        # Create sample risks for each category
        financial_risks = [
            BusinessRisk('credit', 'medium', 0.4, 7.0, 2.8, 'Credit risk', [], [])
        ]
        regulatory_risks = [
            BusinessRisk('kyc_aml', 'high', 0.4, 9.0, 3.6, 'Regulatory risk', [], [])
        ]
        operational_risks = [
            BusinessRisk('technology', 'high', 0.5, 7.0, 3.5, 'Operational risk', [], [])
        ]
        market_credit_risks = [
            BusinessRisk('market_volatility', 'medium', 0.5, 6.0, 3.0, 'Market risk', [], [])
        ]
        cyber_tech_risks = [
            BusinessRisk('cyber_attack', 'high', 0.6, 9.0, 5.4, 'Cyber risk', [], [])
        ]
        
        # Calculate enhanced overall risk score
        overall_score = enhanced_risk_agent._calculate_enhanced_overall_risk_score(
            financial_risks, regulatory_risks, operational_risks, market_credit_risks, cyber_tech_risks
        )
        
        assert overall_score >= 0.0
        assert overall_score <= 100.0
        
        # Verify weighted calculation
        expected_score = (
            2.8 * 0.25 +  # financial
            3.6 * 0.25 +  # regulatory
            3.5 * 0.20 +  # operational
            3.0 * 0.15 +  # market_credit
            5.4 * 0.15    # cyber_tech
        ) * 10
        
        assert abs(overall_score - expected_score) < 0.1
    
    def test_enhanced_risk_level_determination(self, enhanced_risk_agent):
        """Test enhanced risk level determination"""
        # Test different risk score ranges
        assert enhanced_risk_agent._determine_enhanced_risk_level(90) == 'critical'
        assert enhanced_risk_agent._determine_enhanced_risk_level(70) == 'high'
        assert enhanced_risk_agent._determine_enhanced_risk_level(50) == 'medium'
        assert enhanced_risk_agent._determine_enhanced_risk_level(30) == 'low'
        assert enhanced_risk_agent._determine_enhanced_risk_level(10) == 'very_low'
    
    def test_enhanced_confidence_score_calculation(self, enhanced_risk_agent):
        """Test enhanced confidence score calculation"""
        # Test with fintech-specific parameters
        fintech_parameters = {
            'business_model': 'fintech_lending',
            'target_markets': ['US', 'EU']
        }
        
        confidence_score = enhanced_risk_agent._calculate_enhanced_confidence_score(fintech_parameters)
        
        assert confidence_score >= 0.7
        assert confidence_score <= 0.95
        
        # Test with minimal parameters
        minimal_parameters = {}
        
        minimal_confidence = enhanced_risk_agent._calculate_enhanced_confidence_score(minimal_parameters)
        
        assert minimal_confidence < confidence_score
        assert minimal_confidence >= 0.7
    
    def test_enhanced_risk_recommendation_generation(self, enhanced_risk_agent):
        """Test enhanced risk recommendation generation"""
        # Test different risk levels
        critical_result = {'overall_risk_score': 90}
        critical_recommendation = enhanced_risk_agent._generate_enhanced_risk_recommendation('critical', critical_result)
        assert 'CRITICAL' in critical_recommendation
        assert 'Immediate action required' in critical_recommendation
        
        high_result = {'overall_risk_score': 70}
        high_recommendation = enhanced_risk_agent._generate_enhanced_risk_recommendation('high', high_result)
        assert 'HIGH' in high_recommendation
        assert 'Significant risks identified' in high_recommendation
        
        medium_result = {'overall_risk_score': 50}
        medium_recommendation = enhanced_risk_agent._generate_enhanced_risk_recommendation('medium', medium_result)
        assert 'MEDIUM' in medium_recommendation
        assert 'Manageable risks' in medium_recommendation
        
        low_result = {'overall_risk_score': 30}
        low_recommendation = enhanced_risk_agent._generate_enhanced_risk_recommendation('low', low_result)
        assert 'LOW' in low_recommendation
        assert 'Well-managed' in low_recommendation
        
        very_low_result = {'overall_risk_score': 10}
        very_low_recommendation = enhanced_risk_agent._generate_enhanced_risk_recommendation('very_low', very_low_result)
        assert 'VERY LOW' in very_low_recommendation
        assert 'Excellent' in very_low_recommendation


class TestEnhancedRiskAssessmentAgentConfig:
    """Test suite for Enhanced Risk Assessment Agent Configuration"""
    
    def test_enhanced_config_creation(self, mock_bedrock_client):
        """Test enhanced configuration creation"""
        config = EnhancedRiskAssessmentAgentConfig(
            agent_id="test_enhanced_risk_agent",
            agent_type=AgentType.RISK_ASSESSMENT,
            bedrock_client=mock_bedrock_client,
            financial_risk_analysis_enabled=True,
            cybersecurity_risk_analysis_enabled=True,
            market_credit_risk_analysis_enabled=True,
            enhanced_monitoring_enabled=True
        )
        
        assert config.agent_id == "test_enhanced_risk_agent"
        assert config.agent_type == AgentType.RISK_ASSESSMENT
        assert config.financial_risk_analysis_enabled is True
        assert config.cybersecurity_risk_analysis_enabled is True
        assert config.market_credit_risk_analysis_enabled is True
        assert config.enhanced_monitoring_enabled is True
    
    def test_enhanced_config_validation(self, mock_bedrock_client):
        """Test enhanced configuration validation"""
        # Test invalid agent type
        with pytest.raises(ValueError):
            EnhancedRiskAssessmentAgentConfig(
                agent_id="test_agent",
                agent_type=AgentType.MARKET_ANALYSIS,  # Wrong type
                bedrock_client=mock_bedrock_client
            )


if __name__ == "__main__":
    pytest.main([__file__])
