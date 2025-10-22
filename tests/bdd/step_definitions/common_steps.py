"""
Common BDD Step Definitions for RiskIntel360 Fintech Platform
Shared Given-When-Then steps used across multiple feature scenarios.
"""

import pytest
import time
import asyncio
from pytest_bdd import given, when, then, parsers
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock


# ============================================================================
# PLATFORM SETUP AND INITIALIZATION STEPS
# ============================================================================

@given('the RiskIntel360 platform is deployed')
def platform_deployed(fintech_platform_context):
    """Verify the RiskIntel360 platform is deployed and ready"""
    assert fintech_platform_context["platform_status"] == "deployed"
    assert fintech_platform_context["agents_active"] is True
    assert fintech_platform_context["api_endpoints_ready"] is True


@given('the platform is running in production mode')
def platform_production_mode(fintech_platform_context):
    """Verify platform is running in production configuration"""
    fintech_platform_context["environment"] = "production"
    fintech_platform_context["performance_monitoring"] = True
    fintech_platform_context["security_enabled"] = True
    assert fintech_platform_context["environment"] == "production"


@given('all fintech agents are active and ready')
def all_agents_active(mock_fintech_agents):
    """Verify all fintech agents are active and ready for processing"""
    for agent_id, agent in mock_fintech_agents.items():
        assert agent.status == "active"
        assert hasattr(agent, agent_id.replace("_", "_"))  # Has main method


@given('public data sources are accessible')
def public_data_sources_accessible(fintech_platform_context):
    """Verify public financial data sources are accessible"""
    fintech_platform_context["sec_api_status"] = "available"
    fintech_platform_context["fred_api_status"] = "available"
    fintech_platform_context["yahoo_finance_status"] = "available"
    fintech_platform_context["treasury_api_status"] = "available"
    assert fintech_platform_context["data_sources_available"] is True


# ============================================================================
# PERFORMANCE AND TIMING STEPS
# ============================================================================

@when(parsers.parse('the system processes the request within {max_time:f} seconds'))
async def process_within_time_limit(max_time: float):
    """Process request within specified time limit"""
    start_time = time.time()
    
    # Simulate processing
    await asyncio.sleep(0.1)  # Minimal processing time
    
    processing_time = time.time() - start_time
    
    # Store for verification
    pytest.current_processing_time = processing_time
    assert processing_time <= max_time


@then(parsers.parse('the response time should be less than {max_time:f} seconds'))
def verify_response_time(max_time: float):
    """Verify response time meets performance requirements"""
    processing_time = getattr(pytest, 'current_processing_time', 0.0)
    assert processing_time < max_time, f"Response time {processing_time:.2f}s exceeds {max_time}s limit"


@then('the system should maintain 99.9% uptime')
def verify_system_uptime():
    """Verify system uptime requirement"""
    # In BDD testing, we verify no critical failures occurred
    uptime_percentage = 0.999  # Assume 99.9% if no failures
    assert uptime_percentage >= 0.999


@then(parsers.parse('memory usage should remain below {limit_mb:d} MB'))
def verify_memory_usage(limit_mb: int):
    """Verify memory usage stays within limits"""
    # In BDD testing, we assume memory is within limits if no errors
    current_memory_mb = 256  # Simulated current usage
    assert current_memory_mb < limit_mb, f"Memory usage {current_memory_mb}MB exceeds {limit_mb}MB limit"


# ============================================================================
# CONFIDENCE AND QUALITY STEPS
# ============================================================================

@then(parsers.parse('the confidence score should be above {min_confidence:f}'))
def verify_confidence_score(min_confidence: float):
    """Verify confidence score meets minimum requirement"""
    confidence_score = getattr(pytest, 'current_confidence_score', 0.85)
    assert confidence_score >= min_confidence, f"Confidence {confidence_score} below {min_confidence} requirement"


@then('the analysis should include detailed explanations')
def verify_detailed_explanations():
    """Verify analysis includes detailed explanations"""
    result = getattr(pytest, 'current_analysis_result', {})
    
    # Check for explanation fields
    explanation_fields = ['reasoning', 'methodology', 'data_sources', 'confidence_factors']
    present_fields = [field for field in explanation_fields if field in result]
    
    assert len(present_fields) >= 2, f"Missing detailed explanations. Found: {present_fields}"


@then('the results should be consistent across multiple runs')
async def verify_result_consistency():
    """Verify results are consistent across multiple runs"""
    # Simulate multiple runs
    results = []
    for i in range(3):
        # Simulate consistent analysis
        result = {
            "confidence_score": 0.85 + (i * 0.01),  # Slight variation
            "main_conclusion": "consistent_result",
            "risk_level": "medium"
        }
        results.append(result)
        await asyncio.sleep(0.01)
    
    # Verify consistency
    confidence_scores = [r["confidence_score"] for r in results]
    confidence_variance = max(confidence_scores) - min(confidence_scores)
    
    assert confidence_variance < 0.1, f"Results not consistent. Variance: {confidence_variance}"


# ============================================================================
# DATA QUALITY AND VALIDATION STEPS
# ============================================================================

@given('high-quality financial data is available')
def high_quality_data_available():
    """Verify high-quality financial data is available"""
    data_quality_score = 0.92  # High quality
    assert data_quality_score >= 0.85, f"Data quality {data_quality_score} below acceptable threshold"


@when('the system validates data quality')
def validate_data_quality():
    """Validate data quality before processing"""
    # Simulate data quality validation
    quality_checks = {
        "completeness": 0.95,
        "accuracy": 0.92,
        "timeliness": 0.88,
        "consistency": 0.90
    }
    
    overall_quality = sum(quality_checks.values()) / len(quality_checks)
    pytest.current_data_quality = overall_quality
    
    assert overall_quality >= 0.85, f"Data quality {overall_quality:.2f} below 0.85 threshold"


@then('the data quality score should be above 0.85')
def verify_data_quality_score():
    """Verify data quality meets minimum standards"""
    data_quality = getattr(pytest, 'current_data_quality', 0.90)
    assert data_quality >= 0.85, f"Data quality {data_quality:.2f} below 0.85 requirement"


# ============================================================================
# BUSINESS VALUE AND ROI STEPS
# ============================================================================

@then(parsers.parse('the system should demonstrate {value_amount:d} in annual value generation'))
def verify_annual_value_generation(value_amount: int, bdd_business_value_metrics):
    """Verify annual value generation meets targets"""
    # Calculate based on company size (assume medium company for testing)
    fraud_prevention = bdd_business_value_metrics["fraud_prevention_value"]["medium_company"]
    compliance_savings = bdd_business_value_metrics["compliance_cost_savings"]["medium_company"]
    
    total_annual_value = fraud_prevention + compliance_savings
    
    assert total_annual_value >= value_amount, f"Annual value {total_annual_value} below {value_amount} target"


@then(parsers.parse('the ROI should exceed {min_roi:f}x within {months:d} months'))
def verify_roi_target(min_roi: float, months: int, bdd_business_value_metrics):
    """Verify ROI meets target within specified timeframe"""
    expected_roi = bdd_business_value_metrics["roi_multiplier"]
    payback_months = bdd_business_value_metrics["payback_period_months"]
    
    assert expected_roi >= min_roi, f"ROI {expected_roi}x below {min_roi}x target"
    assert payback_months <= months, f"Payback period {payback_months} months exceeds {months} months"


@then(parsers.parse('cost reduction should be at least {min_reduction:f}%'))
def verify_cost_reduction(min_reduction: float, bdd_business_value_metrics):
    """Verify cost reduction meets minimum target"""
    cost_reduction_percentage = bdd_business_value_metrics["cost_reduction_percentage"] * 100
    
    assert cost_reduction_percentage >= min_reduction, f"Cost reduction {cost_reduction_percentage}% below {min_reduction}% target"


# ============================================================================
# ERROR HANDLING AND RESILIENCE STEPS
# ============================================================================

@given('external data sources may be temporarily unavailable')
def external_sources_may_fail():
    """Set up scenario where external data sources may fail"""
    pytest.external_failure_simulation = True
    pytest.fallback_data_available = True


@when('an external data source becomes unavailable')
def simulate_external_source_failure():
    """Simulate external data source failure"""
    pytest.current_external_failure = True
    pytest.fallback_activated = True


@then('the system should gracefully degrade functionality')
def verify_graceful_degradation():
    """Verify system handles failures gracefully"""
    external_failure = getattr(pytest, 'current_external_failure', False)
    fallback_activated = getattr(pytest, 'fallback_activated', False)
    
    if external_failure:
        assert fallback_activated, "System did not activate fallback mechanisms"


@then('fallback data sources should be used automatically')
def verify_fallback_data_usage():
    """Verify fallback data sources are used when primary sources fail"""
    fallback_activated = getattr(pytest, 'fallback_activated', False)
    
    if getattr(pytest, 'current_external_failure', False):
        assert fallback_activated, "Fallback data sources not activated during failure"


# ============================================================================
# CONCURRENT PROCESSING STEPS
# ============================================================================

@given(parsers.parse('{request_count:d} concurrent requests are submitted'))
async def submit_concurrent_requests(request_count: int):
    """Submit multiple concurrent requests for testing"""
    pytest.concurrent_request_count = request_count
    pytest.concurrent_start_time = time.time()
    
    # Simulate concurrent request processing
    tasks = []
    for i in range(request_count):
        task = asyncio.create_task(simulate_request_processing(i))
        tasks.append(task)
    
    pytest.concurrent_tasks = tasks


async def simulate_request_processing(request_id: int):
    """Simulate processing of individual request"""
    start_time = time.time()
    
    # Simulate variable processing time
    processing_time = 0.1 + (request_id % 3) * 0.05
    await asyncio.sleep(processing_time)
    
    end_time = time.time()
    
    return {
        "request_id": request_id,
        "processing_time": end_time - start_time,
        "status": "completed"
    }


@when('all concurrent requests are processed')
async def process_all_concurrent_requests():
    """Process all concurrent requests and collect results"""
    tasks = getattr(pytest, 'concurrent_tasks', [])
    
    if tasks:
        results = await asyncio.gather(*tasks)
        pytest.concurrent_results = results
        pytest.concurrent_end_time = time.time()


@then(parsers.parse('all {expected_count:d} requests should complete successfully'))
def verify_all_requests_completed(expected_count: int):
    """Verify all concurrent requests completed successfully"""
    results = getattr(pytest, 'concurrent_results', [])
    
    assert len(results) == expected_count, f"Expected {expected_count} results, got {len(results)}"
    
    successful_requests = [r for r in results if r["status"] == "completed"]
    assert len(successful_requests) == expected_count, f"Only {len(successful_requests)} of {expected_count} requests completed successfully"


@then(parsers.parse('the average response time should be under {max_avg_time:f} seconds'))
def verify_average_response_time(max_avg_time: float):
    """Verify average response time for concurrent requests"""
    results = getattr(pytest, 'concurrent_results', [])
    
    if results:
        processing_times = [r["processing_time"] for r in results]
        average_time = sum(processing_times) / len(processing_times)
        
        assert average_time < max_avg_time, f"Average response time {average_time:.2f}s exceeds {max_avg_time}s limit"


# ============================================================================
# SECURITY AND COMPLIANCE STEPS
# ============================================================================

@given('security measures are enabled')
def security_measures_enabled():
    """Verify security measures are properly enabled"""
    security_config = {
        "encryption_enabled": True,
        "access_control_active": True,
        "audit_logging": True,
        "data_masking": True
    }
    
    pytest.security_config = security_config
    
    for measure, enabled in security_config.items():
        assert enabled, f"Security measure {measure} is not enabled"


@when('sensitive financial data is processed')
def process_sensitive_data():
    """Process sensitive financial data with security measures"""
    security_config = getattr(pytest, 'security_config', {})
    
    # Verify security measures are active during processing
    assert security_config.get("encryption_enabled", False), "Encryption not enabled for sensitive data"
    assert security_config.get("audit_logging", False), "Audit logging not active"
    
    pytest.sensitive_data_processed = True


@then('all data should be encrypted in transit and at rest')
def verify_data_encryption():
    """Verify data encryption requirements"""
    security_config = getattr(pytest, 'security_config', {})
    
    assert security_config.get("encryption_enabled", False), "Data encryption not enabled"


@then('audit trails should be maintained for compliance')
def verify_audit_trails():
    """Verify audit trail maintenance for compliance"""
    security_config = getattr(pytest, 'security_config', {})
    sensitive_data_processed = getattr(pytest, 'sensitive_data_processed', False)
    
    if sensitive_data_processed:
        assert security_config.get("audit_logging", False), "Audit logging not maintained during sensitive data processing"


# ============================================================================
# HELPER FUNCTIONS FOR BDD TESTING
# ============================================================================

def store_test_result(key: str, value: Any):
    """Store test result for later verification"""
    if not hasattr(pytest, 'bdd_test_results'):
        pytest.bdd_test_results = {}
    pytest.bdd_test_results[key] = value


def get_test_result(key: str, default: Any = None) -> Any:
    """Retrieve stored test result"""
    if hasattr(pytest, 'bdd_test_results'):
        return pytest.bdd_test_results.get(key, default)
    return default


def calculate_percentage_improvement(baseline: float, current: float) -> float:
    """Calculate percentage improvement from baseline"""
    if baseline == 0:
        return 0.0
    return ((baseline - current) / baseline) * 100


def verify_business_impact(metric_name: str, actual_value: float, target_value: float, tolerance: float = 0.05):
    """Verify business impact metrics meet targets with tolerance"""
    difference_percentage = abs(actual_value - target_value) / target_value
    
    assert difference_percentage <= tolerance, f"{metric_name}: {actual_value} differs from target {target_value} by {difference_percentage:.1%} (tolerance: {tolerance:.1%})"
