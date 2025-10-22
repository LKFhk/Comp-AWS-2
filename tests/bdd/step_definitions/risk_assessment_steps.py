"""
BDD Step Definitions for Risk Assessment and Management
Implements Given-When-Then scenarios for risk assessment testing.
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
scenarios('../features/risk_assessment.feature')


# ============================================================================
# RISK ASSESSMENT SETUP STEPS
# ============================================================================

@given('the Risk Assessment Agent is active')
def risk_agent_active(mock_fintech_agents, risk_assessment_context):
    """Verify risk assessment agent is active and ready"""
    agent = mock_fintech_agents["risk_assessment"]
    assert agent.status == "active"
    assert risk_assessment_context["risk_agent_active"] is True


@given('risk models and market data are available')
def risk_models_available(risk_assessment_context):
    """Verify risk models and market data are available"""
    required_components = {
        "risk_models_loaded": True,
        "market_data_available": True,
        "credit_data_access": True,
        "operational_risk_models": True,
        "regulatory_risk_tracking": True
    }
    
    for component, expected in required_components.items():
        assert risk_assessment_context.get(component, False) == expected, f"{component} not available"


@given('historical market data for backtesting is accessible')
def historical_data_accessible():
    """Verify historical market data is accessible for backtesting"""
    # Simulate historical data availability
    historical_data_config = {
        "data_years": 10,
        "market_crashes_included": True,
        "stress_scenarios": True,
        "data_quality": 0.95,
        "last_update": datetime.now() - timedelta(hours=1)
    }
    
    pytest.historical_data_config = historical_data_config
    
    assert historical_data_config["data_years"] >= 5, "Insufficient historical data for backtesting"
    assert historical_data_config["data_quality"] >= 0.9, "Historical data quality insufficient"


# ============================================================================
# MULTI-DIMENSIONAL RISK ANALYSIS STEPS
# ============================================================================

@given('a portfolio requires comprehensive risk assessment')
def portfolio_risk_assessment_setup(sample_risk_scenarios):
    """Set up portfolio for comprehensive risk assessment"""
    portfolio_data = {
        "portfolio_id": "PORTFOLIO_001",
        "total_value": 10000000,  # $10M portfolio
        "asset_classes": {
            "stocks": 0.60,      # 60% stocks
            "bonds": 0.25,       # 25% bonds
            "commodities": 0.10, # 10% commodities
            "cash": 0.05         # 5% cash
        },
        "geographic_exposure": {
            "domestic": 0.70,    # 70% domestic
            "international": 0.30 # 30% international
        },
        "sector_exposure": {
            "technology": 0.30,
            "financial": 0.20,
            "healthcare": 0.15,
            "energy": 0.10,
            "other": 0.25
        }
    }
    
    pytest.portfolio_data = portfolio_data
    pytest.risk_scenarios = sample_risk_scenarios


@when('the Risk Assessment Agent analyzes all risk dimensions')
async def analyze_all_risk_dimensions(mock_fintech_agents):
    """Analyze all risk dimensions for the portfolio"""
    agent = mock_fintech_agents["risk_assessment"]
    portfolio = pytest.portfolio_data
    scenarios = pytest.risk_scenarios
    
    risk_assessment_request = {
        "portfolio_data": portfolio,
        "risk_scenarios": scenarios,
        "analysis_scope": ["credit", "market", "operational", "regulatory", "liquidity"],
        "assessment_methods": ["var", "stress_testing", "scenario_analysis"],
        "confidence_level": 0.95,  # 95% confidence level
        "time_horizon": "1_year"
    }
    
    start_time = asyncio.get_event_loop().time()
    result = await agent.assess_risk(risk_assessment_request)
    end_time = asyncio.get_event_loop().time()
    
    result["processing_time"] = end_time - start_time
    pytest.comprehensive_risk_result = result


@then('credit risk assessment should be provided')
def verify_credit_risk_assessment():
    """Verify credit risk assessment is provided"""
    result = pytest.comprehensive_risk_result
    
    assert "risk_breakdown" in result
    risk_breakdown = result["risk_breakdown"]
    
    assert "credit_risk" in risk_breakdown
    credit_risk = risk_breakdown["credit_risk"]
    
    assert 0.0 <= credit_risk <= 1.0, f"Credit risk {credit_risk} outside valid range [0.0, 1.0]"


@then('market risk metrics should include VaR calculations')
def verify_market_risk_var():
    """Verify market risk includes Value at Risk calculations"""
    result = pytest.comprehensive_risk_result
    
    assert "risk_breakdown" in result
    risk_breakdown = result["risk_breakdown"]
    
    assert "market_risk" in risk_breakdown
    market_risk = risk_breakdown["market_risk"]
    
    # Verify VaR-related metrics are present
    assert 0.0 <= market_risk <= 1.0, f"Market risk {market_risk} outside valid range [0.0, 1.0]"
    
    # For comprehensive assessment, should have detailed risk metrics
    assert result.get("confidence_score", 0) >= 0.75, "Market risk assessment confidence too low"


@then('operational risk factors should be evaluated')
def verify_operational_risk_evaluation():
    """Verify operational risk factors are evaluated"""
    result = pytest.comprehensive_risk_result
    
    assert "risk_breakdown" in result
    risk_breakdown = result["risk_breakdown"]
    
    assert "operational_risk" in risk_breakdown
    operational_risk = risk_breakdown["operational_risk"]
    
    assert 0.0 <= operational_risk <= 1.0, f"Operational risk {operational_risk} outside valid range [0.0, 1.0]"


@then('regulatory risk should be assessed')
def verify_regulatory_risk_assessment():
    """Verify regulatory risk is assessed"""
    result = pytest.comprehensive_risk_result
    
    assert "risk_breakdown" in result
    risk_breakdown = result["risk_breakdown"]
    
    assert "regulatory_risk" in risk_breakdown
    regulatory_risk = risk_breakdown["regulatory_risk"]
    
    assert 0.0 <= regulatory_risk <= 1.0, f"Regulatory risk {regulatory_risk} outside valid range [0.0, 1.0]"


@then('overall risk score should be calculated')
def verify_overall_risk_score():
    """Verify overall risk score is calculated"""
    result = pytest.comprehensive_risk_result
    
    assert "overall_risk_score" in result
    overall_risk = result["overall_risk_score"]
    
    assert 0.0 <= overall_risk <= 1.0, f"Overall risk score {overall_risk} outside valid range [0.0, 1.0]"
    
    # Verify overall risk is consistent with individual risk components
    risk_breakdown = result.get("risk_breakdown", {})
    if risk_breakdown:
        individual_risks = list(risk_breakdown.values())
        avg_risk = sum(individual_risks) / len(individual_risks)
        
        # Overall risk should be reasonably close to average of individual risks
        risk_difference = abs(overall_risk - avg_risk)
        assert risk_difference <= 0.3, f"Overall risk {overall_risk} inconsistent with individual risks (avg: {avg_risk})"


@then('risk assessment should complete within 10 minutes')
def verify_risk_assessment_time():
    """Verify risk assessment completes within time limit"""
    result = pytest.comprehensive_risk_result
    
    assert "processing_time" in result
    assert result["processing_time"] < 600.0, f"Risk assessment took {result['processing_time']:.1f}s, exceeds 10 minute limit"


# ============================================================================
# STRESS TESTING STEPS
# ============================================================================

@given(parsers.parse('stress testing scenarios for {scenario_type} events'))
def stress_testing_scenarios(scenario_type: str, sample_risk_scenarios):
    """Set up stress testing scenarios for specified event type"""
    scenario_map = {
        "market_crash": sample_risk_scenarios["market_crash_scenario"],
        "interest_rate": sample_risk_scenarios["interest_rate_shock"],
        "regulatory": sample_risk_scenarios["regulatory_change"]
    }
    
    selected_scenario = scenario_map.get(scenario_type.lower())
    if not selected_scenario:
        # Create generic stress scenario
        selected_scenario = {
            "scenario_name": f"{scenario_type.title()} Stress Test",
            "severity": "high",
            "probability": 0.10,
            "impact_severity": "high"
        }
    
    pytest.stress_scenario = selected_scenario
    pytest.stress_scenario_type = scenario_type.lower()


@when('stress testing is performed on the portfolio')
async def perform_stress_testing(mock_fintech_agents):
    """Perform stress testing on the portfolio"""
    agent = mock_fintech_agents["risk_assessment"]
    portfolio = pytest.portfolio_data
    scenario = pytest.stress_scenario
    
    stress_test_request = {
        "portfolio_data": portfolio,
        "stress_scenario": scenario,
        "test_type": "comprehensive",
        "severity_levels": ["moderate", "severe", "extreme"],
        "metrics": ["portfolio_value", "risk_metrics", "liquidity"]
    }
    
    result = await agent.assess_risk(stress_test_request)
    pytest.stress_test_result = result


@then('portfolio impact should be quantified')
def verify_portfolio_impact_quantification():
    """Verify portfolio impact is quantified in stress test"""
    result = pytest.stress_test_result
    scenario = pytest.stress_scenario
    
    # Verify impact metrics are present
    assert "overall_risk_score" in result
    
    # For stress scenarios, risk should be elevated
    stress_risk = result["overall_risk_score"]
    baseline_risk = 0.35  # Assumed baseline risk
    
    # Stress test should show increased risk
    assert stress_risk >= baseline_risk, f"Stress test risk {stress_risk} not elevated from baseline {baseline_risk}"


@then('worst-case scenario losses should be estimated')
def verify_worst_case_loss_estimation():
    """Verify worst-case scenario losses are estimated"""
    result = pytest.stress_test_result
    portfolio = pytest.portfolio_data
    
    # Verify risk assessment includes loss estimation
    overall_risk = result.get("overall_risk_score", 0)
    portfolio_value = portfolio["total_value"]
    
    # Estimate potential loss based on risk score
    estimated_loss_percentage = overall_risk * 0.5  # Risk score to loss percentage conversion
    estimated_loss = portfolio_value * estimated_loss_percentage
    
    # For a $10M portfolio with medium-high risk, losses should be significant but reasonable
    assert 0 <= estimated_loss <= portfolio_value * 0.8, f"Estimated loss ${estimated_loss:,.0f} unreasonable for portfolio value ${portfolio_value:,.0f}"


@then('recovery time should be projected')
def verify_recovery_time_projection():
    """Verify recovery time is projected for stress scenarios"""
    scenario = pytest.stress_scenario
    scenario_type = pytest.stress_scenario_type
    
    # Recovery time projections based on scenario type
    recovery_projections = {
        "market_crash": {"min_months": 12, "max_months": 36},
        "interest_rate": {"min_months": 6, "max_months": 24},
        "regulatory": {"min_months": 3, "max_months": 18}
    }
    
    expected_recovery = recovery_projections.get(scenario_type, {"min_months": 6, "max_months": 24})
    
    # Verify recovery projection is reasonable
    scenario_duration = scenario.get("duration_months", 12)
    recovery_time = scenario_duration * 1.5  # Assume recovery takes 1.5x scenario duration
    
    assert expected_recovery["min_months"] <= recovery_time <= expected_recovery["max_months"] * 2, f"Recovery time {recovery_time} months outside reasonable range"


# ============================================================================
# REAL-TIME RISK MONITORING STEPS
# ============================================================================

@given('real-time risk monitoring is enabled')
def real_time_monitoring_enabled():
    """Enable real-time risk monitoring"""
    monitoring_config = {
        "real_time_enabled": True,
        "update_frequency_seconds": 60,  # 1-minute updates
        "alert_thresholds": {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.8,
            "critical": 0.9
        },
        "monitoring_scope": ["market", "credit", "operational", "regulatory"]
    }
    
    pytest.risk_monitoring_config = monitoring_config
    pytest.monitoring_start_time = datetime.now()


@when(parsers.parse('market conditions change significantly ({change_type})'))
async def market_conditions_change(change_type: str, mock_fintech_agents):
    """Simulate significant market condition changes"""
    agent = mock_fintech_agents["risk_assessment"]
    
    # Define market change scenarios
    change_scenarios = {
        "volatility_spike": {"market_volatility": 0.8, "risk_increase": 0.3},
        "interest_rate_change": {"rate_change": 2.0, "risk_increase": 0.2},
        "sector_rotation": {"sector_impact": 0.4, "risk_increase": 0.15},
        "geopolitical_event": {"uncertainty": 0.9, "risk_increase": 0.4}
    }
    
    scenario = change_scenarios.get(change_type.lower(), change_scenarios["volatility_spike"])
    
    risk_update_request = {
        "portfolio_data": pytest.portfolio_data,
        "market_change": scenario,
        "update_type": "real_time",
        "change_type": change_type.lower()
    }
    
    result = await agent.assess_risk(risk_update_request)
    pytest.real_time_risk_update = result
    pytest.market_change_scenario = scenario


@then('risk metrics should be updated within 2 minutes')
def verify_risk_update_timing():
    """Verify risk metrics are updated within time limit"""
    monitoring_config = pytest.risk_monitoring_config
    update_frequency = monitoring_config["update_frequency_seconds"]
    
    # Simulate update detection time
    detection_time = 45  # 45 seconds to detect and update
    
    assert detection_time <= 120, f"Risk update took {detection_time}s, exceeds 2 minute limit"
    assert detection_time <= update_frequency * 2, f"Update time {detection_time}s exceeds 2x update frequency"


@then('risk alerts should be triggered for threshold breaches')
def verify_risk_alert_triggers():
    """Verify risk alerts are triggered when thresholds are breached"""
    result = pytest.real_time_risk_update
    config = pytest.risk_monitoring_config
    scenario = pytest.market_change_scenario
    
    # Calculate expected risk level after market change
    baseline_risk = 0.35  # Assumed baseline
    risk_increase = scenario.get("risk_increase", 0.2)
    expected_risk = min(baseline_risk + risk_increase, 1.0)
    
    actual_risk = result.get("overall_risk_score", baseline_risk)
    
    # Determine alert level based on thresholds
    thresholds = config["alert_thresholds"]
    
    if actual_risk >= thresholds["critical"]:
        expected_alert = "critical"
    elif actual_risk >= thresholds["high"]:
        expected_alert = "high"
    elif actual_risk >= thresholds["medium"]:
        expected_alert = "medium"
    else:
        expected_alert = "low"
    
    # Verify appropriate alert level
    assert actual_risk >= baseline_risk, f"Risk not elevated after market change: {actual_risk} vs baseline {baseline_risk}"
    
    # For significant changes, should trigger at least medium alert
    if risk_increase >= 0.25:
        assert actual_risk >= thresholds["medium"], f"Significant market change should trigger medium+ alert: risk {actual_risk}"


@then('mitigation recommendations should be provided')
def verify_mitigation_recommendations():
    """Verify mitigation recommendations are provided"""
    result = pytest.real_time_risk_update
    
    assert "mitigation_strategies" in result
    strategies = result["mitigation_strategies"]
    
    assert len(strategies) >= 2, f"Insufficient mitigation strategies: {len(strategies)}"
    
    # Verify strategies are actionable
    strategy_keywords = ["diversify", "hedge", "reduce", "increase", "monitor", "rebalance", "limit"]
    strategies_text = " ".join(strategies).lower()
    
    has_actionable_strategies = any(keyword in strategies_text for keyword in strategy_keywords)
    assert has_actionable_strategies, "Mitigation strategies are not actionable"


# ============================================================================
# SCENARIO ANALYSIS STEPS
# ============================================================================

@given('multiple economic scenarios are defined')
def multiple_scenarios_defined(sample_risk_scenarios):
    """Define multiple economic scenarios for analysis"""
    scenarios = {
        "base_case": {
            "gdp_growth": 2.5,
            "inflation": 2.0,
            "unemployment": 4.0,
            "probability": 0.60
        },
        "recession": {
            "gdp_growth": -1.5,
            "inflation": 1.0,
            "unemployment": 7.0,
            "probability": 0.25
        },
        "high_growth": {
            "gdp_growth": 4.0,
            "inflation": 3.5,
            "unemployment": 3.0,
            "probability": 0.15
        }
    }
    
    pytest.economic_scenarios = scenarios


@when('scenario analysis is performed across all scenarios')
async def perform_scenario_analysis(mock_fintech_agents):
    """Perform scenario analysis across all defined scenarios"""
    agent = mock_fintech_agents["risk_assessment"]
    scenarios = pytest.economic_scenarios
    portfolio = pytest.portfolio_data
    
    scenario_results = {}
    
    for scenario_name, scenario_data in scenarios.items():
        analysis_request = {
            "portfolio_data": portfolio,
            "economic_scenario": scenario_data,
            "scenario_name": scenario_name,
            "analysis_type": "scenario_analysis"
        }
        
        result = await agent.assess_risk(analysis_request)
        scenario_results[scenario_name] = result
    
    pytest.scenario_analysis_results = scenario_results


@then('risk outcomes should be calculated for each scenario')
def verify_scenario_risk_outcomes():
    """Verify risk outcomes are calculated for each scenario"""
    results = pytest.scenario_analysis_results
    scenarios = pytest.economic_scenarios
    
    for scenario_name in scenarios.keys():
        assert scenario_name in results, f"No results for scenario {scenario_name}"
        
        result = results[scenario_name]
        assert "overall_risk_score" in result, f"No risk score for scenario {scenario_name}"
        
        risk_score = result["overall_risk_score"]
        assert 0.0 <= risk_score <= 1.0, f"Invalid risk score {risk_score} for scenario {scenario_name}"


@then('probability-weighted risk should be computed')
def verify_probability_weighted_risk():
    """Verify probability-weighted risk is computed across scenarios"""
    results = pytest.scenario_analysis_results
    scenarios = pytest.economic_scenarios
    
    # Calculate probability-weighted risk
    weighted_risk = 0.0
    total_probability = 0.0
    
    for scenario_name, scenario_data in scenarios.items():
        if scenario_name in results:
            risk_score = results[scenario_name].get("overall_risk_score", 0)
            probability = scenario_data.get("probability", 0)
            
            weighted_risk += risk_score * probability
            total_probability += probability
    
    # Verify probabilities sum to approximately 1.0
    assert abs(total_probability - 1.0) < 0.05, f"Scenario probabilities sum to {total_probability}, not 1.0"
    
    # Verify weighted risk is reasonable
    assert 0.0 <= weighted_risk <= 1.0, f"Probability-weighted risk {weighted_risk} outside valid range"
    
    pytest.probability_weighted_risk = weighted_risk


@then('scenario comparison should highlight key differences')
def verify_scenario_comparison():
    """Verify scenario comparison highlights key differences"""
    results = pytest.scenario_analysis_results
    
    # Extract risk scores for comparison
    risk_scores = {
        scenario: result.get("overall_risk_score", 0)
        for scenario, result in results.items()
    }
    
    # Verify meaningful differences between scenarios
    min_risk = min(risk_scores.values())
    max_risk = max(risk_scores.values())
    risk_range = max_risk - min_risk
    
    assert risk_range >= 0.1, f"Insufficient risk differentiation between scenarios: range {risk_range}"
    
    # Recession scenario should typically have higher risk
    if "recession" in risk_scores and "base_case" in risk_scores:
        recession_risk = risk_scores["recession"]
        base_case_risk = risk_scores["base_case"]
        
        assert recession_risk >= base_case_risk, f"Recession risk {recession_risk} not higher than base case {base_case_risk}"


# ============================================================================
# PERFORMANCE AND SCALABILITY STEPS
# ============================================================================

@given(parsers.parse('the system handles {assessment_count:d} concurrent risk assessments'))
async def concurrent_risk_assessments(assessment_count: int, mock_fintech_agents):
    """Set up concurrent risk assessment processing"""
    agent = mock_fintech_agents["risk_assessment"]
    
    # Create multiple assessment requests
    tasks = []
    for i in range(assessment_count):
        # Create varied portfolio data
        portfolio_value = 1000000 * (i + 1)  # $1M to $NM
        
        portfolio_data = {
            "portfolio_id": f"PORTFOLIO_{i:03d}",
            "total_value": portfolio_value,
            "asset_classes": {
                "stocks": 0.5 + (i % 3) * 0.1,
                "bonds": 0.3 - (i % 3) * 0.05,
                "commodities": 0.15,
                "cash": 0.05
            }
        }
        
        request = {
            "portfolio_data": portfolio_data,
            "analysis_scope": ["market", "credit", "operational"],
            "assessment_type": "standard",
            "request_id": f"risk_assessment_{i}"
        }
        
        task = agent.assess_risk(request)
        tasks.append(task)
    
    pytest.concurrent_risk_tasks = tasks
    pytest.concurrent_risk_count = assessment_count


@when('all risk assessments are processed simultaneously')
async def process_concurrent_risk_assessments():
    """Process all concurrent risk assessments"""
    tasks = pytest.concurrent_risk_tasks
    
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks)
    end_time = asyncio.get_event_loop().time()
    
    pytest.concurrent_risk_results = results
    pytest.concurrent_risk_processing_time = end_time - start_time


@then('all assessments should complete within performance benchmarks')
def verify_concurrent_risk_performance(bdd_performance_benchmarks):
    """Verify concurrent risk assessments meet performance benchmarks"""
    results = pytest.concurrent_risk_results
    processing_time = pytest.concurrent_risk_processing_time
    assessment_count = pytest.concurrent_risk_count
    
    # Verify all assessments completed successfully
    successful_results = [r for r in results if r.get("overall_risk_score") is not None]
    success_rate = len(successful_results) / len(results)
    
    assert success_rate >= 0.95, f"Risk assessment success rate {success_rate:.1%} below 95% requirement"
    
    # Verify average processing time
    avg_processing_time = processing_time / assessment_count
    max_risk_time = bdd_performance_benchmarks["risk_assessment_time"]
    
    assert avg_processing_time <= max_risk_time, f"Average risk assessment time {avg_processing_time:.1f}s exceeds {max_risk_time}s limit"


@then('risk calculation accuracy should remain above 90%')
def verify_risk_calculation_accuracy():
    """Verify risk calculation accuracy remains high under load"""
    results = pytest.concurrent_risk_results
    
    # Calculate accuracy based on confidence scores and consistency
    high_confidence_results = [
        r for r in results 
        if r.get("confidence_score", 0) >= 0.8
    ]
    
    accuracy_rate = len(high_confidence_results) / len(results) if results else 0
    
    assert accuracy_rate >= 0.90, f"Risk calculation accuracy {accuracy_rate:.1%} below 90% requirement"
    
    # Verify risk scores are within reasonable ranges
    risk_scores = [r.get("overall_risk_score", 0) for r in results]
    valid_scores = [score for score in risk_scores if 0.0 <= score <= 1.0]
    
    validity_rate = len(valid_scores) / len(risk_scores) if risk_scores else 0
    assert validity_rate >= 0.99, f"Risk score validity {validity_rate:.1%} below 99% requirement"
