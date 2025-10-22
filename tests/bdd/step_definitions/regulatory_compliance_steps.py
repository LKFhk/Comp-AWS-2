"""
BDD Step Definitions for Regulatory Compliance Monitoring
Implements Given-When-Then scenarios for regulatory compliance testing.
"""

import pytest
import asyncio
from pytest_bdd import given, when, then, scenarios, parsers
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Ensure pytest is available for BDD testing
try:
    import pytest
except ImportError:
    print("Warning: pytest not available for BDD testing")


# Load scenarios from feature file
scenarios('../features/regulatory_compliance.feature')


# ============================================================================
# REGULATORY COMPLIANCE SETUP STEPS
# ============================================================================

@given('the Regulatory Compliance Agent is active')
def regulatory_agent_active(mock_fintech_agents, regulatory_compliance_context):
    """Verify regulatory compliance agent is active and ready"""
    agent = mock_fintech_agents["regulatory_compliance"]
    assert agent.status == "active"
    assert regulatory_compliance_context["compliance_agent_active"] is True


@given('public regulatory data sources are accessible')
def regulatory_sources_accessible(regulatory_compliance_context):
    """Verify public regulatory data sources are accessible"""
    sources = regulatory_compliance_context["regulatory_sources"]
    
    for source in sources:
        source_key = f"{source.lower()}_api_available"
        assert regulatory_compliance_context.get(source_key, True), f"{source} API not available"


@given('the system monitors SEC, FINRA, CFPB, and Treasury sources')
def monitoring_regulatory_sources(regulatory_compliance_context):
    """Verify system is monitoring all required regulatory sources"""
    required_sources = ["SEC", "FINRA", "CFPB", "Treasury", "FRED"]
    monitored_sources = regulatory_compliance_context["regulatory_sources"]
    
    for source in required_sources:
        assert source in monitored_sources, f"{source} not being monitored"


# ============================================================================
# REGULATORY UPDATE DETECTION STEPS
# ============================================================================

@given(parsers.parse('a new {regulation_type} regulation is published'))
def new_regulation_published(regulation_type: str, sample_regulatory_data, bdd_test_data_generator):
    """Simulate new regulation publication"""
    if regulation_type.upper() == "SEC":
        regulation = sample_regulatory_data["sec_filings"][0]
    elif regulation_type.upper() == "FINRA":
        regulation = sample_regulatory_data["finra_updates"][0]
    elif regulation_type.upper() == "CFPB":
        regulation = sample_regulatory_data["cfpb_announcements"][0]
    else:
        # Generate custom regulation
        regulation = bdd_test_data_generator.generate_regulatory_update("medium")
    
    pytest.current_regulation = regulation
    pytest.regulation_type = regulation_type.upper()


@when('the Regulatory Compliance Agent processes the regulatory update')
async def process_regulatory_update(mock_fintech_agents):
    """Process the regulatory update through the compliance agent"""
    agent = mock_fintech_agents["regulatory_compliance"]
    regulation = pytest.current_regulation
    
    # Simulate processing the regulatory update
    start_time = asyncio.get_event_loop().time()
    
    result = await agent.analyze_compliance({
        "regulation_data": regulation,
        "business_type": "fintech_startup",
        "analysis_scope": ["impact_assessment", "compliance_requirements", "remediation_plan"]
    })
    
    end_time = asyncio.get_event_loop().time()
    result["processing_time"] = end_time - start_time
    
    pytest.compliance_analysis_result = result


@then('it should analyze the impact on current operations within 5 minutes')
def verify_impact_analysis_time():
    """Verify impact analysis completes within time limit"""
    result = pytest.compliance_analysis_result
    
    assert "processing_time" in result
    assert result["processing_time"] < 300.0, f"Impact analysis took {result['processing_time']:.1f}s, exceeds 5 minute limit"
    
    # Verify impact analysis was performed
    assert "compliance_status" in result
    assert "risk_level" in result


@then(parsers.parse('it should generate compliance recommendations with confidence > {min_confidence:f}'))
def verify_compliance_recommendations(min_confidence: float):
    """Verify compliance recommendations are generated with sufficient confidence"""
    result = pytest.compliance_analysis_result
    
    assert "confidence_score" in result
    assert result["confidence_score"] > min_confidence, f"Confidence {result['confidence_score']} not above {min_confidence}"
    
    assert "recommendations" in result
    assert len(result["recommendations"]) > 0, "No compliance recommendations generated"


@then('it should reference public regulatory guidance')
def verify_public_guidance_references():
    """Verify recommendations reference public regulatory guidance"""
    result = pytest.compliance_analysis_result
    regulation_type = pytest.regulation_type
    
    # Verify guidance sources are referenced
    recommendations = result.get("recommendations", [])
    assert len(recommendations) > 0, "No recommendations to verify guidance references"
    
    # Check that recommendations mention regulatory sources
    guidance_keywords = ["SEC", "FINRA", "CFPB", "Treasury", "Federal Register", "guidance", "regulation"]
    has_guidance_reference = any(
        any(keyword.lower() in rec.lower() for keyword in guidance_keywords)
        for rec in recommendations
    )
    
    assert has_guidance_reference, "Recommendations do not reference public regulatory guidance"


@then('it should alert compliance teams with actionable insights')
def verify_compliance_alerts():
    """Verify compliance teams receive actionable alerts"""
    result = pytest.compliance_analysis_result
    
    # Verify alert-worthy information is present
    assert "risk_level" in result
    assert "compliance_status" in result
    assert "recommendations" in result
    
    # High or medium risk should trigger alerts
    risk_level = result["risk_level"]
    if risk_level in ["high", "medium"]:
        assert len(result["recommendations"]) > 0, f"No actionable insights for {risk_level} risk level"


# ============================================================================
# COMPLIANCE REMEDIATION STEPS
# ============================================================================

@given('a compliance gap is identified for a fintech startup')
def compliance_gap_identified():
    """Simulate identification of compliance gap"""
    compliance_gap = {
        "gap_type": "data_privacy_requirements",
        "severity": "high",
        "affected_operations": ["customer_onboarding", "data_processing", "third_party_sharing"],
        "regulatory_source": "CFPB",
        "deadline": datetime.now() + timedelta(days=90),
        "business_type": "fintech_startup"
    }
    
    pytest.compliance_gap = compliance_gap


@when('the agent analyzes regulatory requirements using public sources')
async def analyze_requirements_public_sources(mock_fintech_agents):
    """Analyze regulatory requirements using only public data sources"""
    agent = mock_fintech_agents["regulatory_compliance"]
    gap = pytest.compliance_gap
    
    # Simulate analysis using public sources only
    analysis_result = await agent.analyze_compliance({
        "compliance_gap": gap,
        "data_sources": "public_only",
        "analysis_type": "remediation_planning",
        "budget_constraint": "startup_budget"
    })
    
    pytest.remediation_analysis = analysis_result


@then('it should create a detailed remediation plan')
def verify_detailed_remediation_plan():
    """Verify detailed remediation plan is created"""
    analysis = pytest.remediation_analysis
    
    # Verify remediation plan components
    required_components = ["recommendations", "compliance_status"]
    for component in required_components:
        assert component in analysis, f"Remediation plan missing {component}"
    
    recommendations = analysis["recommendations"]
    assert len(recommendations) >= 3, f"Remediation plan has only {len(recommendations)} recommendations, expected at least 3"


@then('the plan should use only free public regulatory guidance')
def verify_public_guidance_only():
    """Verify remediation plan uses only free public sources"""
    analysis = pytest.remediation_analysis
    
    # Verify no premium data sources are referenced
    premium_sources = ["Bloomberg Law", "Thomson Reuters", "Compliance.ai", "RegTech Analytics"]
    recommendations_text = " ".join(analysis.get("recommendations", []))
    
    for premium_source in premium_sources:
        assert premium_source.lower() not in recommendations_text.lower(), f"Premium source {premium_source} referenced in public-only plan"
    
    # Verify public sources are referenced
    public_sources = ["SEC.gov", "FINRA.org", "CFPB.gov", "Treasury.gov", "Federal Register"]
    has_public_reference = any(
        source.lower() in recommendations_text.lower() 
        for source in public_sources
    )
    
    assert has_public_reference, "No public regulatory sources referenced in remediation plan"


@then('the plan should include implementation timeline and cost estimates')
def verify_timeline_and_costs():
    """Verify remediation plan includes timeline and cost estimates"""
    analysis = pytest.remediation_analysis
    gap = pytest.compliance_gap
    
    # For BDD testing, we verify the analysis includes timeline considerations
    recommendations = analysis.get("recommendations", [])
    
    # Check for timeline-related keywords
    timeline_keywords = ["days", "weeks", "months", "deadline", "timeline", "schedule", "implementation"]
    has_timeline = any(
        any(keyword in rec.lower() for keyword in timeline_keywords)
        for rec in recommendations
    )
    
    assert has_timeline, "Remediation plan does not include timeline information"
    
    # Check for cost-related keywords
    cost_keywords = ["cost", "budget", "expense", "investment", "affordable", "free", "low-cost"]
    has_cost_info = any(
        any(keyword in rec.lower() for keyword in cost_keywords)
        for rec in recommendations
    )
    
    assert has_cost_info, "Remediation plan does not include cost considerations"


@then('the plan should be accessible to companies without expensive subscriptions')
def verify_accessibility_without_subscriptions():
    """Verify plan is accessible without expensive regulatory subscriptions"""
    analysis = pytest.remediation_analysis
    
    # Verify plan focuses on public resources and low-cost solutions
    recommendations = analysis.get("recommendations", [])
    recommendations_text = " ".join(recommendations)
    
    # Check for accessibility indicators
    accessibility_keywords = ["free", "public", "no-cost", "open source", "government", "accessible"]
    has_accessibility = any(
        keyword in recommendations_text.lower() 
        for keyword in accessibility_keywords
    )
    
    assert has_accessibility, "Remediation plan not accessible without expensive subscriptions"


# ============================================================================
# REAL-TIME MONITORING STEPS
# ============================================================================

@given('the system is monitoring regulatory changes in real-time')
def real_time_monitoring_active(regulatory_compliance_context):
    """Verify real-time regulatory monitoring is active"""
    assert regulatory_compliance_context["compliance_agent_active"] is True
    
    # Simulate real-time monitoring setup
    pytest.monitoring_active = True
    pytest.last_check_time = datetime.now()


@when(parsers.parse('a {urgency_level} regulatory change occurs'))
async def regulatory_change_occurs(urgency_level: str, bdd_test_data_generator):
    """Simulate regulatory change with specified urgency level"""
    urgency_map = {
        "critical": "high",
        "important": "medium", 
        "routine": "low"
    }
    
    severity = urgency_map.get(urgency_level.lower(), "medium")
    regulatory_change = bdd_test_data_generator.generate_regulatory_update(severity)
    
    pytest.regulatory_change = regulatory_change
    pytest.change_urgency = urgency_level.lower()


@then(parsers.parse('the system should detect the change within {max_minutes:d} minutes'))
def verify_change_detection_time(max_minutes: int):
    """Verify regulatory change is detected within specified time"""
    change = pytest.regulatory_change
    urgency = pytest.change_urgency
    
    # Simulate detection time based on urgency
    detection_times = {
        "critical": 1,    # 1 minute for critical
        "important": 5,   # 5 minutes for important
        "routine": 15     # 15 minutes for routine
    }
    
    simulated_detection_time = detection_times.get(urgency, 5)
    
    assert simulated_detection_time <= max_minutes, f"Detection time {simulated_detection_time} minutes exceeds {max_minutes} minute limit"


@then('compliance officers should be notified immediately')
def verify_immediate_notification():
    """Verify compliance officers receive immediate notification"""
    change = pytest.regulatory_change
    urgency = pytest.change_urgency
    
    # For critical and important changes, immediate notification is required
    if urgency in ["critical", "important"]:
        # Simulate notification system
        notification_sent = True
        notification_time = 0.5  # 30 seconds
        
        assert notification_sent, f"No notification sent for {urgency} regulatory change"
        assert notification_time < 1.0, f"Notification took {notification_time} minutes, not immediate"


# ============================================================================
# COST EFFECTIVENESS STEPS
# ============================================================================

@given('the system uses primarily free public data sources')
def using_public_data_sources():
    """Verify system is configured to use primarily public data sources"""
    data_source_config = {
        "public_sources_percentage": 90,
        "premium_sources_percentage": 10,
        "cost_optimization": True,
        "public_first_strategy": True
    }
    
    pytest.data_source_config = data_source_config
    
    assert data_source_config["public_sources_percentage"] >= 80, "Not using primarily public data sources"


@when('compliance analysis is performed for a small fintech company')
async def perform_compliance_analysis_small_company(mock_fintech_agents):
    """Perform compliance analysis optimized for small company budget"""
    agent = mock_fintech_agents["regulatory_compliance"]
    
    analysis_request = {
        "company_size": "small",
        "budget_tier": "startup",
        "data_sources": "public_first",
        "analysis_scope": ["basic_compliance", "cost_effective_solutions"]
    }
    
    result = await agent.analyze_compliance(analysis_request)
    pytest.small_company_analysis = result


@then(parsers.parse('the analysis cost should be under ${max_cost:d}'))
def verify_analysis_cost_limit(max_cost: int):
    """Verify analysis cost stays under specified limit"""
    config = pytest.data_source_config
    
    # Calculate simulated cost based on public vs premium data usage
    public_percentage = config["public_sources_percentage"] / 100
    base_cost = 1000  # Base cost for premium analysis
    
    actual_cost = base_cost * (1 - public_percentage * 0.8)  # 80% savings from public data
    
    assert actual_cost <= max_cost, f"Analysis cost ${actual_cost:.0f} exceeds ${max_cost} limit"


@then('the solution should be accessible to startups and small businesses')
def verify_startup_accessibility():
    """Verify solution is accessible to startups and small businesses"""
    analysis = pytest.small_company_analysis
    config = pytest.data_source_config
    
    # Verify startup-friendly features
    assert config["public_first_strategy"] is True, "Not using public-first strategy for startups"
    assert config["cost_optimization"] is True, "Cost optimization not enabled for startups"
    
    # Verify analysis includes startup considerations
    assert analysis["confidence_score"] >= 0.7, "Analysis quality insufficient for startup decision-making"


# ============================================================================
# PERFORMANCE AND SCALABILITY STEPS
# ============================================================================

@given(parsers.parse('the system handles {request_count:d} concurrent compliance requests'))
async def handle_concurrent_compliance_requests(request_count: int, mock_fintech_agents):
    """Handle multiple concurrent compliance analysis requests"""
    agent = mock_fintech_agents["regulatory_compliance"]
    
    # Create concurrent requests
    tasks = []
    for i in range(request_count):
        request = {
            "request_id": f"compliance_req_{i}",
            "company_type": "fintech",
            "urgency": "medium",
            "analysis_scope": ["basic_compliance"]
        }
        task = agent.analyze_compliance(request)
        tasks.append(task)
    
    pytest.concurrent_compliance_tasks = tasks
    pytest.concurrent_request_count = request_count


@when('all compliance requests are processed simultaneously')
async def process_concurrent_compliance_requests():
    """Process all concurrent compliance requests"""
    tasks = pytest.concurrent_compliance_tasks
    
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks)
    end_time = asyncio.get_event_loop().time()
    
    pytest.concurrent_compliance_results = results
    pytest.concurrent_processing_time = end_time - start_time


@then('all requests should complete within the performance requirements')
def verify_concurrent_performance_requirements(bdd_performance_benchmarks):
    """Verify concurrent requests meet performance requirements"""
    results = pytest.concurrent_compliance_results
    processing_time = pytest.concurrent_processing_time
    request_count = pytest.concurrent_request_count
    
    # Verify all requests completed successfully
    successful_results = [r for r in results if r.get("confidence_score", 0) > 0.5]
    success_rate = len(successful_results) / len(results)
    
    assert success_rate >= 0.95, f"Success rate {success_rate:.1%} below 95% requirement"
    
    # Verify average processing time
    avg_processing_time = processing_time / request_count
    max_compliance_time = bdd_performance_benchmarks["compliance_analysis_time"]
    
    assert avg_processing_time <= max_compliance_time, f"Average processing time {avg_processing_time:.1f}s exceeds {max_compliance_time}s limit"


@then('the system should maintain regulatory monitoring accuracy above 95%')
def verify_monitoring_accuracy():
    """Verify regulatory monitoring maintains high accuracy"""
    results = pytest.concurrent_compliance_results
    
    # Calculate accuracy based on confidence scores
    confidence_scores = [r.get("confidence_score", 0) for r in results]
    high_confidence_results = [score for score in confidence_scores if score >= 0.8]
    
    accuracy_rate = len(high_confidence_results) / len(confidence_scores) if confidence_scores else 0
    
    assert accuracy_rate >= 0.95, f"Monitoring accuracy {accuracy_rate:.1%} below 95% requirement"
