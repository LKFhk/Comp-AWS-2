"""
Unit tests for Enhanced Customer Behavior Intelligence Agent fintech capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, UTC

from riskintel360.agents.customer_behavior_intelligence_agent import (
    CustomerBehaviorIntelligenceAgent, 
    CustomerSegment, 
    BehaviorAnalysis
)
from riskintel360.agents.base_agent import EnhancedCustomerIntelligenceAgentConfig
from riskintel360.models.agent_models import AgentType
from riskintel360.services.bedrock_client import BedrockClient


@pytest.fixture
def mock_bedrock_client():
    """Create a mock Bedrock client for testing"""
    client = Mock(spec=BedrockClient)
    client.invoke_for_agent = AsyncMock()
    return client


@pytest.fixture
def enhanced_customer_agent_config(mock_bedrock_client):
    """Create enhanced customer behavior intelligence agent configuration"""
    return EnhancedCustomerIntelligenceAgentConfig(
        agent_id="test_enhanced_customer_agent",
        agent_type=AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE,
        bedrock_client=mock_bedrock_client,
        behavioral_analytics_enabled=True,
        clv_analysis_enabled=True,
        personalization_enabled=True,
        financial_behavior_analysis_enabled=True,
        clv_modeling_enabled=True,
        advanced_segmentation_enabled=True,
        behavioral_prediction_enabled=True
    )


@pytest.fixture
def enhanced_customer_agent(enhanced_customer_agent_config):
    """Create enhanced customer behavior intelligence agent instance"""
    return CustomerBehaviorIntelligenceAgent(enhanced_customer_agent_config)


class TestEnhancedCustomerBehaviorIntelligenceAgent:
    """Test suite for Enhanced Customer Behavior Intelligence Agent fintech capabilities"""
    
    @pytest.mark.asyncio
    async def test_enhanced_fintech_customer_analysis(self, enhanced_customer_agent, mock_bedrock_client):
        """Test enhanced fintech customer analysis execution"""
        # Mock LLM responses for enhanced analysis
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"segments": [{"segment_name": "Digital Natives", "size_percentage": 0.3, "characteristics": ["Tech-savvy"], "financial_behaviors": ["Mobile banking"], "risk_profile": "medium", "preferred_channels": ["Mobile app"], "spending_power": "medium", "engagement_level": "high"}]}'
        )
        
        # Test parameters
        parameters = {
            'product_type': 'digital_banking',
            'target_market': 'retail'
        }
        
        # Execute enhanced analysis
        result = await enhanced_customer_agent._perform_enhanced_fintech_customer_analysis(parameters)
        
        # Verify enhanced capabilities
        assert result is not None
        assert 'analysis_result' in result
        assert 'financial_behavior_analysis' in result
        assert 'clv_analysis' in result
        assert 'metadata' in result
        assert result['metadata']['fintech_focus'] is True
        assert result['metadata']['enhanced_capabilities'] is True
        
        # Verify analysis result structure
        analysis_result = result['analysis_result']
        assert 'customer_segments' in analysis_result
        assert 'behavior_analysis' in analysis_result
        assert 'market_demand_level' in analysis_result
        assert 'confidence_score' in analysis_result
        
        # Verify enhanced data sources
        assert 'data_sources_used' in analysis_result
        data_sources = analysis_result['data_sources_used']
        assert 'enhanced_llm_analysis' in data_sources
        assert 'behavioral_models' in data_sources
        assert 'fintech_patterns' in data_sources
    
    @pytest.mark.asyncio
    async def test_advanced_fintech_customer_segments(self, enhanced_customer_agent, mock_bedrock_client):
        """Test advanced fintech customer segmentation"""
        # Mock LLM response for advanced segmentation
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"segments": [{"segment_name": "Digital-Native Millennials", "size_percentage": 0.30, "characteristics": ["Mobile-first", "Tech-savvy"], "financial_behaviors": ["Frequent mobile banking", "P2P payments"], "risk_profile": "medium", "preferred_channels": ["Mobile app"], "spending_power": "medium", "engagement_level": "high", "digital_maturity": "advanced", "financial_goals": ["Wealth building"], "pain_points": ["High fees"], "value_drivers": ["Convenience"]}]}'
        )
        
        # Execute advanced segmentation
        segments = await enhanced_customer_agent._analyze_advanced_fintech_customer_segments('digital_banking', 'retail')
        
        assert segments is not None
        assert len(segments) > 0
        
        # Verify segment structure
        segment = segments[0]
        assert isinstance(segment, CustomerSegment)
        assert segment.segment_name == "Digital-Native Millennials"
        assert segment.size_percentage == 0.30
        assert len(segment.characteristics) > 0
        assert len(segment.financial_behaviors) > 0
        assert segment.risk_profile in ['low', 'medium', 'high']
        assert segment.engagement_level in ['low', 'medium', 'high']
    
    @pytest.mark.asyncio
    async def test_enhanced_customer_behavior_analysis(self, enhanced_customer_agent, mock_bedrock_client):
        """Test enhanced customer behavior analysis"""
        # Mock LLM response for enhanced behavior analysis
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"behavior_patterns": ["Mobile-first usage", "Micro-transactions"], "risk_indicators": ["Irregular patterns"], "engagement_score": 0.75, "loyalty_score": 0.65, "churn_risk": "medium", "financial_health_score": 0.70, "preferred_products": ["Mobile banking"], "usage_patterns": {"peak_usage_times": ["Morning"], "transaction_frequency": "high", "feature_adoption": "fast", "session_duration": "medium", "cross_selling_potential": "high"}, "behavioral_triggers": ["Convenience"], "personalization_opportunities": ["Custom offers"], "retention_factors": ["User experience"], "confidence_level": 0.80}'
        )
        
        # Create sample customer segments
        segments = [
            CustomerSegment(
                segment_name="Test Segment",
                size_percentage=0.5,
                characteristics=["Tech-savvy"],
                financial_behaviors=["Mobile banking"],
                risk_profile="medium",
                preferred_channels=["Mobile app"],
                spending_power="medium",
                engagement_level="high"
            )
        ]
        
        # Execute enhanced behavior analysis
        behavior_analysis = await enhanced_customer_agent._analyze_enhanced_customer_behavior(segments, 'digital_banking')
        
        assert behavior_analysis is not None
        assert isinstance(behavior_analysis, BehaviorAnalysis)
        assert behavior_analysis.engagement_score == 0.75
        assert behavior_analysis.loyalty_score == 0.65
        assert behavior_analysis.churn_risk == 'medium'
        assert behavior_analysis.financial_health_score == 0.70
        assert behavior_analysis.confidence_level == 0.80
        assert len(behavior_analysis.behavior_patterns) > 0
        assert len(behavior_analysis.preferred_products) > 0
        
        # Verify usage patterns
        usage_patterns = behavior_analysis.usage_patterns
        assert 'peak_usage_times' in usage_patterns
        assert 'transaction_frequency' in usage_patterns
        assert 'cross_selling_potential' in usage_patterns
    
    @pytest.mark.asyncio
    async def test_financial_behavior_patterns_analysis(self, enhanced_customer_agent, mock_bedrock_client):
        """Test financial behavior patterns analysis"""
        # Mock LLM response for financial behavior patterns
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"spending_patterns": {"average_transaction_size": 85.0, "transaction_frequency_monthly": 45, "seasonal_variations": ["Holiday spikes"], "category_preferences": ["Food & dining"]}, "savings_behavior": {"savings_rate": 0.12, "goal_oriented_saving": "medium", "automated_savings_adoption": 0.35, "emergency_fund_adequacy": "medium"}, "investment_behavior": {"risk_tolerance": "moderate", "investment_frequency": "medium", "diversification_level": "medium", "robo_advisor_adoption": 0.25}, "credit_behavior": {"credit_utilization": 0.30, "payment_timeliness": "good", "credit_seeking_frequency": "low", "debt_management": "fair"}, "digital_adoption": {"mobile_banking_usage": 0.85, "contactless_payment_adoption": 0.70, "financial_app_usage": 0.60, "ai_feature_acceptance": 0.40}}'
        )
        
        # Create sample segments
        segments = [CustomerSegment("Test", 0.5, [], [], "medium", [], "medium", "high")]
        
        # Execute financial behavior analysis
        financial_behavior = await enhanced_customer_agent._analyze_financial_behavior_patterns(segments, 'digital_banking')
        
        assert financial_behavior is not None
        assert 'spending_patterns' in financial_behavior
        assert 'savings_behavior' in financial_behavior
        assert 'investment_behavior' in financial_behavior
        assert 'credit_behavior' in financial_behavior
        assert 'digital_adoption' in financial_behavior
        
        # Verify spending patterns
        spending = financial_behavior['spending_patterns']
        assert 'average_transaction_size' in spending
        assert 'transaction_frequency_monthly' in spending
        assert spending['average_transaction_size'] == 85.0
        
        # Verify digital adoption
        digital = financial_behavior['digital_adoption']
        assert 'mobile_banking_usage' in digital
        assert 'contactless_payment_adoption' in digital
        assert digital['mobile_banking_usage'] == 0.85
    
    @pytest.mark.asyncio
    async def test_customer_lifetime_value_analysis(self, enhanced_customer_agent, mock_bedrock_client):
        """Test customer lifetime value analysis"""
        # Mock LLM response for CLV analysis
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"average_clv": 2500.0, "clv_by_segment": {"high_value": 5000.0, "medium_value": 2500.0, "low_value": 1000.0}, "revenue_drivers": ["Transaction fees", "Subscription revenue"], "cost_factors": ["Customer acquisition", "Servicing costs"], "profitability_timeline": {"break_even_months": 8, "peak_value_months": 24, "decline_phase_months": 48}, "retention_impact": {"retention_rate_improvement": 0.10, "clv_increase_potential": 0.25}, "cross_sell_opportunities": ["Investment products", "Insurance"], "churn_cost_impact": 500.0}'
        )
        
        # Create sample segments and behavior analysis
        segments = [CustomerSegment("Test", 0.5, [], [], "medium", [], "medium", "high")]
        behavior_analysis = BehaviorAnalysis([], [], 0.7, 0.6, 'medium', 0.7, [], {}, 0.7)
        
        # Execute CLV analysis
        clv_analysis = await enhanced_customer_agent._analyze_customer_lifetime_value(segments, behavior_analysis)
        
        assert clv_analysis is not None
        assert 'average_clv' in clv_analysis
        assert 'clv_by_segment' in clv_analysis
        assert 'revenue_drivers' in clv_analysis
        assert 'cost_factors' in clv_analysis
        assert 'profitability_timeline' in clv_analysis
        assert 'retention_impact' in clv_analysis
        assert 'cross_sell_opportunities' in clv_analysis
        assert 'churn_cost_impact' in clv_analysis
        
        # Verify CLV values
        assert clv_analysis['average_clv'] == 2500.0
        assert clv_analysis['churn_cost_impact'] == 500.0
        
        # Verify CLV by segment
        clv_segments = clv_analysis['clv_by_segment']
        assert 'high_value' in clv_segments
        assert 'medium_value' in clv_segments
        assert 'low_value' in clv_segments
        
        # Verify profitability timeline
        timeline = clv_analysis['profitability_timeline']
        assert 'break_even_months' in timeline
        assert 'peak_value_months' in timeline
        assert timeline['break_even_months'] == 8
    
    @pytest.mark.asyncio
    async def test_enhanced_market_demand_assessment(self, enhanced_customer_agent, mock_bedrock_client):
        """Test enhanced market demand assessment"""
        # Mock LLM response for enhanced demand analysis
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"demand_level": "high", "demand_score": 0.75, "growth_trajectory": "growing", "demand_drivers": ["Digital transformation"], "behavioral_demand_factors": ["Mobile-first preference"], "market_gaps": ["Underserved demographics"], "target_segments": ["Millennials"], "seasonal_patterns": ["Holiday spending"], "competitive_demand_pressure": "high", "unmet_needs": ["Better UX"], "adoption_barriers": ["Trust concerns"], "confidence_score": 0.7}'
        )
        
        # Create sample behavior analysis
        behavior_analysis = BehaviorAnalysis([], [], 0.7, 0.6, 'medium', 0.7, [], {}, 0.7)
        
        # Execute enhanced demand assessment
        demand_analysis = await enhanced_customer_agent._assess_enhanced_market_demand(
            'digital_banking', 'retail', behavior_analysis
        )
        
        assert demand_analysis is not None
        assert 'demand_level' in demand_analysis
        assert 'demand_score' in demand_analysis
        assert 'growth_trajectory' in demand_analysis
        assert 'behavioral_demand_factors' in demand_analysis
        assert 'unmet_needs' in demand_analysis
        assert 'adoption_barriers' in demand_analysis
        
        # Verify demand level and score
        assert demand_analysis['demand_level'] == 'high'
        assert demand_analysis['demand_score'] == 0.75
        assert demand_analysis['growth_trajectory'] == 'growing'
        
        # Verify behavioral factors
        assert len(demand_analysis['behavioral_demand_factors']) > 0
        assert len(demand_analysis['unmet_needs']) > 0
    
    @pytest.mark.asyncio
    async def test_enhanced_customer_insights_generation(self, enhanced_customer_agent, mock_bedrock_client):
        """Test enhanced customer insights generation"""
        # Mock LLM response for comprehensive insights
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"key_insights": ["Strong mobile adoption"], "strategic_recommendations": ["Enhance mobile experience"], "personalization_strategies": ["Behavioral targeting"], "retention_strategies": ["Loyalty programs"], "acquisition_strategies": ["Referral programs"], "product_development_priorities": ["Mobile optimization"], "revenue_optimization": ["Cross-selling automation"], "risk_mitigation": ["Fraud detection"], "competitive_advantages": ["Superior UX"], "technology_investments": ["AI/ML capabilities"]}'
        )
        
        # Create sample data
        segments = [CustomerSegment("Test", 0.5, [], [], "medium", [], "medium", "high")]
        behavior_analysis = BehaviorAnalysis([], [], 0.7, 0.6, 'medium', 0.7, [], {}, 0.7)
        financial_behavior = {'digital_adoption': {'mobile_banking_usage': 0.85}}
        clv_analysis = {'average_clv': 2500.0}
        demand_analysis = {'demand_level': 'high'}
        
        # Execute enhanced insights generation
        insights = await enhanced_customer_agent._generate_enhanced_customer_insights(
            segments, behavior_analysis, financial_behavior, clv_analysis, demand_analysis
        )
        
        assert insights is not None
        assert 'insights' in insights
        assert 'recommendations' in insights
        assert 'personalization_strategies' in insights
        assert 'retention_strategies' in insights
        assert 'acquisition_strategies' in insights
        assert 'product_priorities' in insights
        assert 'revenue_optimization' in insights
        assert 'risk_mitigation' in insights
        assert 'competitive_advantages' in insights
        assert 'technology_investments' in insights
        
        # Verify insights content
        assert len(insights['insights']) > 0
        assert len(insights['recommendations']) > 0
        assert len(insights['personalization_strategies']) > 0
    
    def test_enhanced_confidence_score_calculation(self, enhanced_customer_agent):
        """Test enhanced confidence score calculation"""
        # Create sample data with high quality
        segments = [
            CustomerSegment("Segment1", 0.3, [], [], "medium", [], "medium", "high"),
            CustomerSegment("Segment2", 0.3, [], [], "medium", [], "medium", "high"),
            CustomerSegment("Segment3", 0.2, [], [], "medium", [], "medium", "high"),
            CustomerSegment("Segment4", 0.2, [], [], "medium", [], "medium", "high")
        ]
        
        behavior_analysis = BehaviorAnalysis(
            behavior_patterns=["Pattern1", "Pattern2", "Pattern3", "Pattern4"],
            risk_indicators=[],
            engagement_score=0.8,
            loyalty_score=0.7,
            churn_risk='low',
            financial_health_score=0.8,
            preferred_products=[],
            usage_patterns={},
            confidence_level=0.85
        )
        
        financial_behavior = {
            'spending_patterns': {},
            'savings_behavior': {},
            'investment_behavior': {},
            'credit_behavior': {},
            'digital_adoption': {}
        }
        
        # Calculate enhanced confidence score
        confidence_score = enhanced_customer_agent._calculate_enhanced_confidence_score(
            segments, behavior_analysis, financial_behavior
        )
        
        assert confidence_score >= 0.7
        assert confidence_score <= 0.95
        
        # Test with minimal data
        minimal_segments = [CustomerSegment("Test", 0.5, [], [], "medium", [], "medium", "high")]
        minimal_behavior = BehaviorAnalysis([], [], 0.5, 0.5, 'medium', 0.5, [], {}, 0.5)
        minimal_financial = {}
        
        minimal_confidence = enhanced_customer_agent._calculate_enhanced_confidence_score(
            minimal_segments, minimal_behavior, minimal_financial
        )
        
        assert minimal_confidence < confidence_score
        assert minimal_confidence >= 0.7
    
    def test_enhanced_agent_capabilities(self, enhanced_customer_agent):
        """Test enhanced agent capabilities"""
        capabilities = enhanced_customer_agent.get_capabilities()
        
        # Verify fintech-specific capabilities
        expected_capabilities = [
            "fintech_customer_segmentation",
            "behavioral_risk_analysis",
            "customer_engagement_analysis",
            "churn_prediction",
            "financial_health_scoring",
            "market_demand_validation"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities


class TestEnhancedCustomerIntelligenceAgentConfig:
    """Test suite for Enhanced Customer Behavior Intelligence Agent Configuration"""
    
    def test_enhanced_config_creation(self, mock_bedrock_client):
        """Test enhanced configuration creation"""
        config = EnhancedCustomerIntelligenceAgentConfig(
            agent_id="test_enhanced_customer_agent",
            agent_type=AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE,
            bedrock_client=mock_bedrock_client,
            behavioral_analytics_enabled=True,
            clv_analysis_enabled=True,
            personalization_enabled=True,
            financial_behavior_analysis_enabled=True,
            clv_modeling_enabled=True,
            advanced_segmentation_enabled=True,
            behavioral_prediction_enabled=True
        )
        
        assert config.agent_id == "test_enhanced_customer_agent"
        assert config.agent_type == AgentType.CUSTOMER_BEHAVIOR_INTELLIGENCE
        assert config.behavioral_analytics_enabled is True
        assert config.clv_analysis_enabled is True
        assert config.personalization_enabled is True
        assert config.financial_behavior_analysis_enabled is True
        assert config.clv_modeling_enabled is True
        assert config.advanced_segmentation_enabled is True
        assert config.behavioral_prediction_enabled is True
    
    def test_enhanced_config_validation(self, mock_bedrock_client):
        """Test enhanced configuration validation"""
        # Test invalid agent type
        with pytest.raises(ValueError):
            EnhancedCustomerIntelligenceAgentConfig(
                agent_id="test_agent",
                agent_type=AgentType.FRAUD_DETECTION,  # Wrong type
                bedrock_client=mock_bedrock_client
            )


if __name__ == "__main__":
    pytest.main([__file__])
