"""
Unit tests for Enhanced Market Analysis Agent fintech capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, UTC

from riskintel360.agents.market_analysis_agent import MarketAnalysisAgent
from riskintel360.agents.base_agent import EnhancedMarketAnalysisAgentConfig
from riskintel360.models.agent_models import AgentType
from riskintel360.services.bedrock_client import BedrockClient


@pytest.fixture
def mock_bedrock_client():
    """Create a mock Bedrock client for testing"""
    client = Mock(spec=BedrockClient)
    client.invoke_for_agent = AsyncMock()
    return client


@pytest.fixture
def enhanced_market_agent_config(mock_bedrock_client):
    """Create enhanced market analysis agent configuration"""
    return EnhancedMarketAnalysisAgentConfig(
        agent_id="test_enhanced_market_agent",
        agent_type=AgentType.MARKET_ANALYSIS,
        bedrock_client=mock_bedrock_client,
        alpha_vantage_api_key="test_key",
        yahoo_finance_enabled=True,
        macroeconomic_analysis_enabled=True,
        competitive_analysis_enabled=True,
        investment_insights_enabled=True
    )


@pytest.fixture
def enhanced_market_agent(enhanced_market_agent_config):
    """Create enhanced market analysis agent instance"""
    return MarketAnalysisAgent(enhanced_market_agent_config)


class TestEnhancedMarketAnalysisAgent:
    """Test suite for Enhanced Market Analysis Agent fintech capabilities"""
    
    @pytest.mark.asyncio
    async def test_enhanced_fintech_market_analysis(self, enhanced_market_agent, mock_bedrock_client):
        """Test enhanced fintech market analysis execution"""
        # Mock LLM responses for enhanced analysis
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"trend_direction": "bullish", "confidence_score": 0.8, "annual_growth_rate": 0.18, "volatility_level": 0.35, "key_drivers": ["Digital transformation", "Regulatory support"], "forecast_12m_growth": 0.18, "forecast_24m_growth": 0.28}'
        )
        
        # Test parameters
        parameters = {
            'market_segment': 'fintech',
            'region': 'US'
        }
        
        # Execute enhanced analysis
        result = await enhanced_market_agent._perform_fintech_market_analysis(parameters)
        
        # Verify enhanced capabilities
        assert result is not None
        assert 'analysis_result' in result
        assert 'metadata' in result
        assert result['metadata']['fintech_focus'] is True
        assert result['metadata']['enhanced_capabilities'] is True
        
        # Verify analysis result structure
        analysis_result = result['analysis_result']
        assert 'market_size_usd' in analysis_result
        assert 'growth_trends' in analysis_result
        assert 'competitive_intensity' in analysis_result
        assert 'confidence_score' in analysis_result
        
        # Verify enhanced data sources
        assert 'data_sources_used' in analysis_result
        data_sources = analysis_result['data_sources_used']
        assert len(data_sources) > 0
    
    @pytest.mark.asyncio
    async def test_enhanced_financial_metrics_fetch(self, enhanced_market_agent):
        """Test enhanced financial metrics fetching"""
        # Test enhanced financial metrics
        metrics = await enhanced_market_agent._fetch_enhanced_financial_metrics('fintech')
        
        assert metrics is not None
        assert 'sector_performance' in metrics
        assert 'investment_metrics' in metrics
        assert 'regulatory_impact' in metrics
        
        # Verify sector performance metrics
        sector_perf = metrics['sector_performance']
        assert 'revenue_growth_yoy' in sector_perf
        assert 'profit_margin_avg' in sector_perf
        assert 'customer_acquisition_cost' in sector_perf
        assert 'lifetime_value' in sector_perf
        
        # Verify investment metrics
        investment_metrics = metrics['investment_metrics']
        assert 'total_funding_2023' in investment_metrics
        assert 'average_valuation_multiple' in investment_metrics
    
    @pytest.mark.asyncio
    async def test_macroeconomic_indicators_fetch(self, enhanced_market_agent):
        """Test macroeconomic indicators fetching"""
        # Test macroeconomic indicators
        indicators = await enhanced_market_agent._fetch_macroeconomic_indicators()
        
        assert indicators is not None
        assert 'interest_rates' in indicators
        assert 'economic_growth' in indicators
        assert 'financial_stability' in indicators
        assert 'consumer_metrics' in indicators
        
        # Verify interest rates
        interest_rates = indicators['interest_rates']
        assert 'federal_funds_rate' in interest_rates
        assert 'prime_rate' in interest_rates
        assert 'treasury_10y' in interest_rates
        
        # Verify economic growth metrics
        economic_growth = indicators['economic_growth']
        assert 'gdp_growth_rate' in economic_growth
        assert 'unemployment_rate' in economic_growth
        assert 'inflation_rate' in economic_growth
    
    @pytest.mark.asyncio
    async def test_advanced_trend_analysis(self, enhanced_market_agent, mock_bedrock_client):
        """Test advanced fintech trend analysis"""
        # Mock LLM response for trend analysis
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"trend_direction": "bullish", "confidence_score": 0.85, "annual_growth_rate": 0.20, "volatility_level": 0.30, "key_drivers": ["AI adoption", "Regulatory clarity"], "forecast_12m_growth": 0.20, "forecast_24m_growth": 0.30}'
        )
        
        # Test market data with enhanced metrics
        market_data = {
            'market_size': 100e9,
            'growth_rate': 0.15,
            'financial_performance': {
                'sector_performance': {'revenue_growth_yoy': 0.25}
            },
            'macroeconomic_indicators': {
                'interest_rates': {'federal_funds_rate': 5.25}
            }
        }
        
        # Execute advanced trend analysis
        trends = await enhanced_market_agent._analyze_advanced_fintech_market_trends(market_data)
        
        assert trends is not None
        assert len(trends) >= 1
        
        # Verify trend structure
        trend = trends[0]
        assert hasattr(trend, 'trend_direction')
        assert hasattr(trend, 'confidence_score')
        assert hasattr(trend, 'growth_rate')
        assert hasattr(trend, 'volatility')
        assert hasattr(trend, 'key_drivers')
        
        # Verify trend values
        assert trend.confidence_score >= 0.7
        assert trend.growth_rate > 0
        assert len(trend.key_drivers) > 0
    
    @pytest.mark.asyncio
    async def test_competitive_landscape_analysis(self, enhanced_market_agent, mock_bedrock_client):
        """Test fintech competitive landscape analysis"""
        # Mock LLM response for competitive analysis
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"market_concentration": "moderately_concentrated", "competitive_intensity": "high", "key_players": [{"name": "Company A", "market_share": 0.15}], "barriers_to_entry": ["Regulatory compliance"], "differentiation_opportunities": ["AI features"], "competitive_threats": ["Big tech entry"], "market_gaps": ["SMB segment"], "innovation_trends": ["AI/ML adoption"]}'
        )
        
        # Execute competitive analysis
        competitive_analysis = await enhanced_market_agent._analyze_fintech_competitive_landscape('fintech', 'US')
        
        assert competitive_analysis is not None
        assert 'concentration' in competitive_analysis
        assert 'intensity' in competitive_analysis
        assert 'key_players' in competitive_analysis
        assert 'entry_barriers' in competitive_analysis
        assert 'differentiation_opportunities' in competitive_analysis
        assert 'threats' in competitive_analysis
        assert 'market_gaps' in competitive_analysis
        assert 'innovation_trends' in competitive_analysis
        
        # Verify competitive intensity
        assert competitive_analysis['intensity'] in ['low', 'medium', 'high', 'very_high']
    
    @pytest.mark.asyncio
    async def test_investment_insights_generation(self, enhanced_market_agent, mock_bedrock_client):
        """Test fintech investment insights generation"""
        # Mock LLM response for investment insights
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"investment_attractiveness": "high", "risk_level": "medium", "expected_roi_range": {"min": 0.15, "max": 0.35}, "investment_horizon": "medium_term", "key_value_drivers": ["Market growth"], "investment_risks": ["Regulatory changes"], "funding_availability": "moderate", "exit_opportunities": ["acquisition"], "valuation_multiples": {"revenue": 8.5, "ebitda": 15.0}}'
        )
        
        # Test data
        market_data = {'market_size': 50e9, 'growth_rate': 0.15}
        trends = []
        regulatory_analysis = {'environment': 'neutral'}
        
        # Execute investment insights generation
        investment_insights = await enhanced_market_agent._generate_fintech_investment_insights(
            market_data, trends, regulatory_analysis
        )
        
        assert investment_insights is not None
        assert 'attractiveness' in investment_insights
        assert 'risk_level' in investment_insights
        assert 'expected_roi' in investment_insights
        assert 'investment_horizon' in investment_insights
        assert 'value_drivers' in investment_insights
        assert 'investment_risks' in investment_insights
        assert 'funding_availability' in investment_insights
        assert 'exit_opportunities' in investment_insights
        assert 'valuation_multiples' in investment_insights
        
        # Verify investment attractiveness levels
        assert investment_insights['attractiveness'] in ['very_high', 'high', 'medium', 'low', 'very_low']
        assert investment_insights['risk_level'] in ['low', 'medium', 'high', 'very_high']
    
    @pytest.mark.asyncio
    async def test_enhanced_confidence_score_calculation(self, enhanced_market_agent):
        """Test enhanced confidence score calculation"""
        # Test data with various quality levels
        high_quality_data = {
            'sources': ['yahoo_finance', 'fred', 'enhanced_financial_metrics', 'macroeconomic_data'],
            'financial_performance': {'sector_performance': {}},
            'macroeconomic_indicators': {'interest_rates': {}}
        }
        
        trends = [Mock(), Mock()]  # Multiple trends
        regulatory_analysis = {'complexity': 'medium', 'stability': 'evolving'}
        
        # Calculate enhanced confidence score
        confidence_score = enhanced_market_agent._calculate_enhanced_confidence_score(
            high_quality_data, trends, regulatory_analysis
        )
        
        assert confidence_score >= 0.6
        assert confidence_score <= 0.95
        
        # Test with minimal data
        minimal_data = {'sources': ['llm_generated']}
        minimal_trends = []
        minimal_regulatory = {}
        
        minimal_confidence = enhanced_market_agent._calculate_enhanced_confidence_score(
            minimal_data, minimal_trends, minimal_regulatory
        )
        
        assert minimal_confidence < confidence_score
        assert minimal_confidence >= 0.6
    
    def test_enhanced_agent_capabilities(self, enhanced_market_agent):
        """Test enhanced agent capabilities"""
        capabilities = enhanced_market_agent.get_capabilities()
        
        # Verify fintech-specific capabilities
        expected_capabilities = [
            "fintech_market_analysis",
            "financial_trend_forecasting",
            "regulatory_impact_analysis",
            "economic_indicator_monitoring",
            "real_time_market_monitoring",
            "fintech_competitive_analysis"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
    
    @pytest.mark.asyncio
    async def test_enhanced_market_insights_generation(self, enhanced_market_agent, mock_bedrock_client):
        """Test enhanced market insights generation"""
        # Mock LLM response for comprehensive insights
        mock_bedrock_client.invoke_for_agent.return_value = Mock(
            content='{"strategic_opportunities": ["Digital transformation"], "market_risks": ["Regulatory changes"], "competitive_advantages": ["Technology innovation"], "growth_strategies": ["Market expansion"], "technology_trends": ["AI/ML adoption"], "customer_insights": ["Mobile preference"], "regulatory_recommendations": ["Proactive compliance"], "investment_recommendations": ["Focus on scalability"], "market_outlook": "positive", "key_success_factors": ["Regulatory compliance"]}'
        )
        
        # Test data
        market_data = {'market_size': 50e9}
        trends = []
        regulatory_analysis = {'environment': 'neutral'}
        competitive_analysis = {'intensity': 'high'}
        investment_insights = {'attractiveness': 'medium'}
        
        # Execute enhanced insights generation
        insights = await enhanced_market_agent._generate_enhanced_fintech_market_insights(
            market_data, trends, regulatory_analysis, competitive_analysis, investment_insights
        )
        
        assert insights is not None
        assert 'opportunities' in insights
        assert 'risks' in insights
        assert 'competitive_advantages' in insights
        assert 'growth_strategies' in insights
        assert 'technology_trends' in insights
        assert 'customer_insights' in insights
        assert 'regulatory_recommendations' in insights
        assert 'investment_recommendations' in insights
        assert 'market_outlook' in insights
        assert 'success_factors' in insights
        
        # Verify market outlook
        assert insights['market_outlook'] in ['very_positive', 'positive', 'neutral', 'negative', 'very_negative']


class TestEnhancedMarketAnalysisAgentConfig:
    """Test suite for Enhanced Market Analysis Agent Configuration"""
    
    def test_enhanced_config_creation(self, mock_bedrock_client):
        """Test enhanced configuration creation"""
        config = EnhancedMarketAnalysisAgentConfig(
            agent_id="test_enhanced_agent",
            agent_type=AgentType.MARKET_ANALYSIS,
            bedrock_client=mock_bedrock_client,
            macroeconomic_analysis_enabled=True,
            competitive_analysis_enabled=True,
            investment_insights_enabled=True
        )
        
        assert config.agent_id == "test_enhanced_agent"
        assert config.agent_type == AgentType.MARKET_ANALYSIS
        assert config.macroeconomic_analysis_enabled is True
        assert config.competitive_analysis_enabled is True
        assert config.investment_insights_enabled is True
    
    def test_enhanced_config_validation(self, mock_bedrock_client):
        """Test enhanced configuration validation"""
        # Test invalid agent type
        with pytest.raises(ValueError):
            EnhancedMarketAnalysisAgentConfig(
                agent_id="test_agent",
                agent_type=AgentType.FRAUD_DETECTION,  # Wrong type
                bedrock_client=mock_bedrock_client
            )


if __name__ == "__main__":
    pytest.main([__file__])
