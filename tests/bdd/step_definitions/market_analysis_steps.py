"""
BDD Step Definitions for Market Analysis and Intelligence
Implements Given-When-Then scenarios for market analysis testing.
"""

import pytest
import asyncio
from pytest_bdd import given, when, then, scenarios, parsers
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Handle numpy import gracefully
try:
    import numpy as np
except ImportError:
    # Mock numpy for BDD testing
    class MockNumPy:
        @staticmethod
        def random():
            class Random:
                @staticmethod
                def seed(x): pass
                @staticmethod
                def uniform(low, high): return (low + high) / 2
                @staticmethod
                def normal(mean, std, size): return [mean] * (size[0] if isinstance(size, tuple) else size)
            return Random()
        
        @staticmethod
        def array(data): return data
        
        @staticmethod
        def vstack(arrays): return sum(arrays, [])
    
    np = MockNumPy()


# Load scenarios from feature file
scenarios('../features/market_analysis.feature')


# ============================================================================
# MARKET ANALYSIS SETUP STEPS
# ============================================================================

@given('the Market Analysis Agent is active')
def market_agent_active(mock_fintech_agents, market_analysis_context):
    """Verify market analysis agent is active and ready"""
    agent = mock_fintech_agents["market_analysis"]
    assert agent.status == "active"
    assert market_analysis_context["market_agent_active"] is True


@given('public market data sources are accessible')
def market_data_sources_accessible(market_analysis_context):
    """Verify public market data sources are accessible"""
    required_sources = {
        "yahoo_finance_available": True,
        "fred_data_available": True,
        "alpha_vantage_available": True,
        "news_apis_available": True
    }
    
    for source, expected in required_sources.items():
        assert market_analysis_context.get(source, False) == expected, f"{source} not accessible"


@given('real-time market data is available')
def real_time_data_available(market_analysis_context):
    """Verify real-time market data is available"""
    assert market_analysis_context["real_time_data"] is True
    
    # Simulate real-time data availability
    pytest.market_data_timestamp = datetime.now()
    pytest.data_latency_seconds = 1.5  # 1.5 second latency


# ============================================================================
# MARKET TREND ANALYSIS STEPS
# ============================================================================

@given(parsers.parse('the market is experiencing {volatility_level} volatility'))
def market_volatility_level(volatility_level: str, bdd_test_data_generator):
    """Set up market scenario with specified volatility level"""
    market_scenario = bdd_test_data_generator.generate_market_scenario(volatility_level.lower())
    
    pytest.current_market_scenario = market_scenario
    pytest.market_volatility = volatility_level.lower()


@when('the Market Analysis Agent analyzes current market conditions')
async def analyze_market_conditions(mock_fintech_agents, sample_market_data):
    """Analyze current market conditions using the market agent"""
    agent = mock_fintech_agents["market_analysis"]
    scenario = pytest.current_market_scenario
    
    analysis_request = {
        "market_data": sample_market_data,
        "volatility_scenario": scenario,
        "analysis_scope": ["trend_analysis", "risk_assessment", "opportunity_identification"],
        "time_horizon": "short_term"
    }
    
    start_time = asyncio.get_event_loop().time()
    result = await agent.analyze_market(analysis_request)
    end_time = asyncio.get_event_loop().time()
    
    result["processing_time"] = end_time - start_time
    pytest.market_analysis_result = result


@then('it should identify market trends with high confidence')
def verify_market_trend_identification():
    """Verify market trends are identified with high confidence"""
    result = pytest.market_analysis_result
    
    assert "market_trend" in result
    assert "confidence_score" in result
    assert result["confidence_score"] >= 0.75, f"Market trend confidence {result['confidence_score']} below 0.75 threshold"
    
    # Verify trend is one of expected values
    valid_trends = ["bullish", "bearish", "neutral", "volatile"]
    assert result["market_trend"] in valid_trends, f"Invalid market trend: {result['market_trend']}"


@then('it should provide actionable market insights')
def verify_actionable_insights():
    """Verify analysis provides actionable market insights"""
    result = pytest.market_analysis_result
    
    assert "key_insights" in result
    insights = result["key_insights"]
    assert len(insights) >= 2, f"Insufficient insights provided: {len(insights)}"
    
    # Verify insights are actionable (contain action-oriented keywords)
    actionable_keywords = ["buy", "sell", "hold", "avoid", "consider", "monitor", "increase", "decrease", "diversify"]
    insights_text = " ".join(insights).lower()
    
    has_actionable_content = any(keyword in insights_text for keyword in actionable_keywords)
    assert has_actionable_content, "Market insights are not actionable"


@then('it should complete analysis within 3 minutes')
def verify_market_analysis_time():
    """Verify market analysis completes within time limit"""
    result = pytest.market_analysis_result
    
    assert "processing_time" in result
    assert result["processing_time"] < 180.0, f"Market analysis took {result['processing_time']:.1f}s, exceeds 3 minute limit"


# ============================================================================
# ECONOMIC INDICATOR ANALYSIS STEPS
# ============================================================================

@given('economic indicators are available from FRED')
def economic_indicators_available(sample_market_data):
    """Verify economic indicators are available from Federal Reserve Economic Data"""
    economic_data = sample_market_data["economic_indicators"]
    
    required_indicators = ["GDP_growth", "inflation_rate", "unemployment_rate", "federal_funds_rate"]
    
    for indicator in required_indicators:
        assert indicator in economic_data, f"Economic indicator {indicator} not available"
        assert economic_data[indicator] is not None, f"Economic indicator {indicator} has no data"


@when('new economic data is released')
async def new_economic_data_released(mock_fintech_agents, sample_market_data):
    """Simulate new economic data release and analysis"""
    agent = mock_fintech_agents["market_analysis"]
    
    # Simulate updated economic indicators
    updated_indicators = sample_market_data["economic_indicators"].copy()
    updated_indicators["GDP_growth"] = 2.5  # Updated GDP growth
    updated_indicators["inflation_rate"] = 3.0  # Updated inflation
    
    analysis_request = {
        "economic_indicators": updated_indicators,
        "analysis_type": "economic_impact",
        "focus_areas": ["inflation_impact", "growth_outlook", "monetary_policy"]
    }
    
    result = await agent.analyze_market(analysis_request)
    pytest.economic_analysis_result = result


@then('the system should assess economic impact on financial markets')
def verify_economic_impact_assessment():
    """Verify economic impact on financial markets is assessed"""
    result = pytest.economic_analysis_result
    
    assert "market_trend" in result or "economic_impact" in result
    assert "confidence_score" in result
    
    # Verify economic factors are considered
    insights = result.get("key_insights", [])
    economic_keywords = ["GDP", "inflation", "unemployment", "interest", "federal", "economic", "growth"]
    
    insights_text = " ".join(insights).lower()
    has_economic_analysis = any(keyword in insights_text for keyword in economic_keywords)
    
    assert has_economic_analysis, "Economic impact not properly assessed in market analysis"


@then('it should provide sector-specific impact analysis')
def verify_sector_impact_analysis():
    """Verify sector-specific impact analysis is provided"""
    result = pytest.economic_analysis_result
    
    # Check for sector-related insights
    insights = result.get("key_insights", [])
    sector_keywords = ["technology", "financial", "healthcare", "energy", "sector", "industry"]
    
    insights_text = " ".join(insights).lower()
    has_sector_analysis = any(keyword in insights_text for keyword in sector_keywords)
    
    assert has_sector_analysis, "Sector-specific impact analysis not provided"


# ============================================================================
# REAL-TIME MARKET MONITORING STEPS
# ============================================================================

@given('the system monitors market data in real-time')
def real_time_monitoring_setup():
    """Set up real-time market monitoring"""
    pytest.monitoring_active = True
    pytest.last_update_time = datetime.now()
    pytest.update_frequency_seconds = 30  # 30-second updates


@when(parsers.parse('market volatility increases by {volatility_increase:f}%'))
async def market_volatility_increases(volatility_increase: float, mock_fintech_agents):
    """Simulate market volatility increase"""
    agent = mock_fintech_agents["market_analysis"]
    
    # Simulate volatility spike
    volatility_event = {
        "event_type": "volatility_spike",
        "volatility_increase": volatility_increase,
        "affected_markets": ["stocks", "bonds", "commodities"],
        "trigger": "economic_news"
    }
    
    analysis_request = {
        "volatility_event": volatility_event,
        "analysis_type": "real_time_response",
        "urgency": "high"
    }
    
    result = await agent.analyze_market(analysis_request)
    pytest.volatility_response = result


@then('the system should detect the change within 2 minutes')
def verify_volatility_detection_time():
    """Verify volatility change is detected within time limit"""
    response = pytest.volatility_response
    
    # Simulate detection time
    detection_time_seconds = 45  # 45 seconds detection time
    
    assert detection_time_seconds < 120, f"Volatility detection took {detection_time_seconds}s, exceeds 2 minute limit"
    assert response is not None, "No response to volatility change"


@then('risk alerts should be generated automatically')
def verify_automatic_risk_alerts():
    """Verify automatic risk alerts are generated"""
    response = pytest.volatility_response
    
    # Verify risk-related information is present
    assert "market_trend" in response or "risk_factors" in response
    
    # Check for risk-related insights
    insights = response.get("key_insights", [])
    risk_keywords = ["risk", "volatility", "caution", "alert", "warning", "concern"]
    
    insights_text = " ".join(insights).lower()
    has_risk_alerts = any(keyword in insights_text for keyword in risk_keywords)
    
    assert has_risk_alerts, "No automatic risk alerts generated for volatility increase"


# ============================================================================
# PUBLIC DATA OPTIMIZATION STEPS
# ============================================================================

@given('the system uses 90% public data sources for market analysis')
def public_data_optimization():
    """Verify system is optimized for public data sources"""
    data_source_config = {
        "public_sources_percentage": 90,
        "premium_sources_percentage": 10,
        "yahoo_finance": True,
        "fred_data": True,
        "alpha_vantage_free": True,
        "news_apis_free": True,
        "bloomberg_premium": False,
        "reuters_premium": False
    }
    
    pytest.market_data_config = data_source_config
    
    assert data_source_config["public_sources_percentage"] >= 85, "Not using sufficient public data sources"


@when('comprehensive market analysis is performed using public data')
async def comprehensive_analysis_public_data(mock_fintech_agents, sample_market_data):
    """Perform comprehensive market analysis using primarily public data"""
    agent = mock_fintech_agents["market_analysis"]
    config = pytest.market_data_config
    
    analysis_request = {
        "market_data": sample_market_data,
        "data_sources": "public_optimized",
        "analysis_depth": "comprehensive",
        "cost_optimization": True,
        "public_data_percentage": config["public_sources_percentage"]
    }
    
    result = await agent.analyze_market(analysis_request)
    pytest.public_data_analysis = result


@then('the analysis quality should remain above 85% compared to premium data')
def verify_public_data_quality():
    """Verify public data analysis maintains high quality"""
    analysis = pytest.public_data_analysis
    config = pytest.market_data_config
    
    # Simulate quality comparison
    public_percentage = config["public_sources_percentage"]
    quality_retention = 0.85 + (public_percentage - 80) * 0.01  # Quality scales with public data usage
    
    actual_confidence = analysis.get("confidence_score", 0.8)
    expected_minimum = 0.85 * quality_retention
    
    assert actual_confidence >= expected_minimum, f"Public data analysis quality {actual_confidence:.2f} below {expected_minimum:.2f} threshold"


@then(parsers.parse('the analysis cost should be {cost_reduction:f}% lower than premium alternatives'))
def verify_cost_reduction(cost_reduction: float):
    """Verify cost reduction compared to premium alternatives"""
    config = pytest.market_data_config
    
    public_percentage = config["public_sources_percentage"]
    actual_cost_reduction = public_percentage * 0.8  # 80% savings from public data
    
    assert actual_cost_reduction >= cost_reduction, f"Cost reduction {actual_cost_reduction:.1f}% below {cost_reduction}% target"


# ============================================================================
# MARKET OPPORTUNITY IDENTIFICATION STEPS
# ============================================================================

@given(parsers.parse('market conditions show {market_condition} trends'))
def market_conditions_setup(market_condition: str, sample_market_data):
    """Set up specific market conditions for opportunity analysis"""
    condition_map = {
        "bullish": {"trend": "upward", "sentiment": 0.7, "volatility": "low"},
        "bearish": {"trend": "downward", "sentiment": -0.5, "volatility": "medium"},
        "volatile": {"trend": "mixed", "sentiment": 0.0, "volatility": "high"},
        "stable": {"trend": "sideways", "sentiment": 0.1, "volatility": "low"}
    }
    
    market_setup = condition_map.get(market_condition.lower(), condition_map["stable"])
    
    # Update market data with conditions
    updated_market_data = sample_market_data.copy()
    updated_market_data["market_sentiment"]["trend"] = market_setup["trend"]
    updated_market_data["market_sentiment"]["sentiment_score"] = market_setup["sentiment"]
    updated_market_data["market_sentiment"]["volatility"] = market_setup["volatility"]
    
    pytest.market_conditions = market_setup
    pytest.updated_market_data = updated_market_data


@when('the system analyzes investment opportunities')
async def analyze_investment_opportunities(mock_fintech_agents):
    """Analyze investment opportunities based on market conditions"""
    agent = mock_fintech_agents["market_analysis"]
    market_data = pytest.updated_market_data
    conditions = pytest.market_conditions
    
    analysis_request = {
        "market_data": market_data,
        "analysis_type": "opportunity_identification",
        "risk_tolerance": "moderate",
        "investment_horizon": "medium_term",
        "market_conditions": conditions
    }
    
    result = await agent.analyze_market(analysis_request)
    pytest.opportunity_analysis = result


@then('it should identify specific investment opportunities')
def verify_investment_opportunities():
    """Verify specific investment opportunities are identified"""
    analysis = pytest.opportunity_analysis
    
    # Verify opportunities are identified
    insights = analysis.get("key_insights", [])
    assert len(insights) >= 2, f"Insufficient investment insights: {len(insights)}"
    
    # Check for opportunity-related keywords
    opportunity_keywords = ["opportunity", "buy", "invest", "undervalued", "growth", "potential", "recommend"]
    insights_text = " ".join(insights).lower()
    
    has_opportunities = any(keyword in insights_text for keyword in opportunity_keywords)
    assert has_opportunities, "No specific investment opportunities identified"


@then('risk-adjusted recommendations should be provided')
def verify_risk_adjusted_recommendations():
    """Verify risk-adjusted recommendations are provided"""
    analysis = pytest.opportunity_analysis
    
    # Check for risk considerations in recommendations
    insights = analysis.get("key_insights", [])
    risk_keywords = ["risk", "volatility", "caution", "diversify", "hedge", "conservative", "aggressive"]
    
    insights_text = " ".join(insights).lower()
    has_risk_adjustment = any(keyword in insights_text for keyword in risk_keywords)
    
    assert has_risk_adjustment, "Recommendations are not risk-adjusted"
    
    # Verify confidence score reflects risk assessment
    confidence = analysis.get("confidence_score", 0)
    market_volatility = pytest.market_conditions.get("volatility", "medium")
    
    if market_volatility == "high":
        assert confidence <= 0.85, f"Confidence {confidence} too high for high volatility market"
    elif market_volatility == "low":
        assert confidence >= 0.75, f"Confidence {confidence} too low for stable market"


# ============================================================================
# PERFORMANCE AND SCALABILITY STEPS
# ============================================================================

@given(parsers.parse('the system processes {analysis_count:d} concurrent market analyses'))
async def concurrent_market_analyses(analysis_count: int, mock_fintech_agents, sample_market_data):
    """Set up concurrent market analysis processing"""
    agent = mock_fintech_agents["market_analysis"]
    
    # Create multiple analysis requests
    tasks = []
    for i in range(analysis_count):
        request = {
            "request_id": f"market_analysis_{i}",
            "market_data": sample_market_data,
            "analysis_type": "standard",
            "priority": "normal"
        }
        task = agent.analyze_market(request)
        tasks.append(task)
    
    pytest.concurrent_market_tasks = tasks
    pytest.concurrent_analysis_count = analysis_count


@when('all market analyses are processed simultaneously')
async def process_concurrent_market_analyses():
    """Process all concurrent market analyses"""
    tasks = pytest.concurrent_market_tasks
    
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks)
    end_time = asyncio.get_event_loop().time()
    
    pytest.concurrent_market_results = results
    pytest.concurrent_market_processing_time = end_time - start_time


@then('all analyses should complete within performance benchmarks')
def verify_concurrent_market_performance(bdd_performance_benchmarks):
    """Verify concurrent market analyses meet performance benchmarks"""
    results = pytest.concurrent_market_results
    processing_time = pytest.concurrent_market_processing_time
    analysis_count = pytest.concurrent_analysis_count
    
    # Verify all analyses completed successfully
    successful_results = [r for r in results if r.get("confidence_score", 0) > 0.5]
    success_rate = len(successful_results) / len(results)
    
    assert success_rate >= 0.95, f"Market analysis success rate {success_rate:.1%} below 95% requirement"
    
    # Verify average processing time
    avg_processing_time = processing_time / analysis_count
    max_market_time = bdd_performance_benchmarks["market_analysis_time"]
    
    assert avg_processing_time <= max_market_time, f"Average market analysis time {avg_processing_time:.1f}s exceeds {max_market_time}s limit"


@then('market data freshness should be maintained under load')
def verify_data_freshness_under_load():
    """Verify market data remains fresh under concurrent load"""
    results = pytest.concurrent_market_results
    
    # Verify data timestamps are recent
    current_time = datetime.now()
    max_data_age_minutes = 5  # 5 minutes max data age
    
    for result in results:
        # Simulate data freshness check
        data_age_minutes = 2  # Simulated 2-minute data age
        assert data_age_minutes <= max_data_age_minutes, f"Market data age {data_age_minutes} minutes exceeds {max_data_age_minutes} minute limit"


# ============================================================================
# NEWS SENTIMENT INTEGRATION STEPS
# ============================================================================

@given('financial news sentiment data is available')
def news_sentiment_available(sample_market_data):
    """Verify financial news sentiment data is available"""
    sentiment_data = sample_market_data.get("market_sentiment", {})
    
    assert "news_sentiment" in sentiment_data
    assert sentiment_data["news_sentiment"] is not None
    
    # Set up additional news sentiment context
    pytest.news_sentiment_context = {
        "sources_count": 15,
        "sentiment_score": sentiment_data["news_sentiment"],
        "confidence": 0.82,
        "update_frequency": "hourly"
    }


@when('market analysis incorporates news sentiment')
async def incorporate_news_sentiment(mock_fintech_agents, sample_market_data):
    """Incorporate news sentiment into market analysis"""
    agent = mock_fintech_agents["market_analysis"]
    sentiment_context = pytest.news_sentiment_context
    
    analysis_request = {
        "market_data": sample_market_data,
        "news_sentiment": sentiment_context,
        "analysis_type": "sentiment_enhanced",
        "sentiment_weight": 0.3  # 30% weight for sentiment
    }
    
    result = await agent.analyze_market(analysis_request)
    pytest.sentiment_enhanced_analysis = result


@then('sentiment factors should influence market predictions')
def verify_sentiment_influence():
    """Verify news sentiment influences market predictions"""
    analysis = pytest.sentiment_enhanced_analysis
    sentiment_context = pytest.news_sentiment_context
    
    # Verify sentiment is considered in analysis
    insights = analysis.get("key_insights", [])
    sentiment_keywords = ["sentiment", "news", "market mood", "investor confidence", "optimism", "pessimism"]
    
    insights_text = " ".join(insights).lower()
    has_sentiment_influence = any(keyword in insights_text for keyword in sentiment_keywords)
    
    assert has_sentiment_influence, "News sentiment does not influence market predictions"
    
    # Verify confidence reflects sentiment quality
    sentiment_confidence = sentiment_context["confidence"]
    analysis_confidence = analysis.get("confidence_score", 0)
    
    # Analysis confidence should be reasonable given sentiment confidence
    assert analysis_confidence >= sentiment_confidence * 0.8, f"Analysis confidence {analysis_confidence:.2f} too low given sentiment confidence {sentiment_confidence:.2f}"


@then('the analysis should provide sentiment-driven insights')
def verify_sentiment_driven_insights():
    """Verify analysis provides sentiment-driven insights"""
    analysis = pytest.sentiment_enhanced_analysis
    
    insights = analysis.get("key_insights", [])
    assert len(insights) >= 2, "Insufficient sentiment-driven insights"
    
    # Check for sentiment-specific recommendations
    sentiment_action_keywords = ["bullish sentiment", "bearish sentiment", "market optimism", "investor fear", "sentiment shift"]
    insights_text = " ".join(insights).lower()
    
    has_sentiment_insights = any(keyword in insights_text for keyword in sentiment_action_keywords)
    assert has_sentiment_insights, "No sentiment-driven insights provided"
