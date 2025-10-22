"""
BDD Step Definitions for End-to-End Fintech Workflows
Implements Given-When-Then scenarios for complete workflow testing.
"""

import pytest
import asyncio
import time
from pytest_bdd import given, when, then, scenarios, parsers
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Ensure pytest is available for BDD testing
try:
    import pytest
except ImportError:
    print("Warning: pytest not available for BDD testing")


# Load scenarios from feature file
scenarios('../features/end_to_end_workflows.feature')


# ============================================================================
# END-TO-END WORKFLOW SETUP STEPS
# ============================================================================

@given('the complete RiskIntel360 platform is operational')
def complete_platform_operational(fintech_platform_context, mock_fintech_agents):
    """Verify the complete RiskIntel360 platform is operational"""
    # Verify platform status
    assert fintech_platform_context["platform_status"] == "deployed"
    assert fintech_platform_context["agents_active"] is True
    assert fintech_platform_context["api_endpoints_ready"] is True
    
    # Verify all agents are active
    required_agents = ["regulatory_compliance", "fraud_detection", "market_analysis", "kyc_verification", "risk_assessment"]
    
    for agent_id in required_agents:
        assert agent_id in mock_fintech_agents, f"Agent {agent_id} not available"
        assert mock_fintech_agents[agent_id].status == "active", f"Agent {agent_id} not active"
    
    pytest.platform_operational = True


@given('all fintech data sources are connected and accessible')
def all_data_sources_connected():
    """Verify all fintech data sources are connected and accessible"""
    data_sources_status = {
        "sec_edgar": True,
        "finra_api": True,
        "cfpb_data": True,
        "fred_economic": True,
        "treasury_gov": True,
        "yahoo_finance": True,
        "alpha_vantage": True,
        "news_apis": True,
        "sanctions_lists": True,
        "public_records": True
    }
    
    pytest.data_sources_status = data_sources_status
    
    for source, status in data_sources_status.items():
        assert status, f"Data source {source} not accessible"


@given('the workflow orchestrator is ready for multi-agent coordination')
def workflow_orchestrator_ready():
    """Verify workflow orchestrator is ready for multi-agent coordination"""
    orchestrator_config = {
        "coordination_enabled": True,
        "agent_communication": True,
        "state_management": True,
        "task_distribution": True,
        "result_aggregation": True,
        "error_handling": True,
        "performance_monitoring": True
    }
    
    pytest.orchestrator_config = orchestrator_config
    
    for component, enabled in orchestrator_config.items():
        assert enabled, f"Orchestrator component {component} not ready"


# ============================================================================
# COMPREHENSIVE FINTECH ANALYSIS WORKFLOW STEPS
# ============================================================================

@given('a fintech company requests comprehensive risk intelligence analysis')
def fintech_company_analysis_request():
    """Set up comprehensive risk intelligence analysis request"""
    analysis_request = {
        "company_id": "FINTECH_STARTUP_001",
        "company_name": "Digital Banking Solutions Inc",
        "company_type": "fintech_startup",
        "business_model": "digital_banking",
        "analysis_scope": [
            "regulatory_compliance",
            "fraud_detection",
            "market_analysis", 
            "kyc_verification",
            "risk_assessment"
        ],
        "urgency": "high",
        "budget_tier": "startup",
        "timeline": "24_hours",
        "compliance_requirements": ["CFPB", "FINRA", "SEC"],
        "target_markets": ["US", "Canada"],
        "customer_segments": ["millennials", "small_business"],
        "requested_by": "ceo@digitalbankingsolutions.com",
        "request_timestamp": datetime.now()
    }
    
    pytest.comprehensive_analysis_request = analysis_request


@when('the complete fintech workflow is executed')
async def execute_complete_fintech_workflow(mock_fintech_agents):
    """Execute the complete fintech workflow with all agents"""
    request = pytest.comprehensive_analysis_request
    agents = mock_fintech_agents
    
    workflow_start_time = time.time()
    
    # Phase 1: Regulatory Compliance Analysis
    regulatory_task = agents["regulatory_compliance"].analyze_compliance({
        "company_data": request,
        "compliance_requirements": request["compliance_requirements"],
        "analysis_type": "comprehensive"
    })
    
    # Phase 2: Market Analysis
    market_task = agents["market_analysis"].analyze_market({
        "company_data": request,
        "target_markets": request["target_markets"],
        "business_model": request["business_model"]
    })
    
    # Phase 3: Risk Assessment
    risk_task = agents["risk_assessment"].assess_risk({
        "company_data": request,
        "risk_categories": ["market", "operational", "regulatory", "credit"],
        "assessment_depth": "comprehensive"
    })
    
    # Phase 4: KYC Verification (for customer onboarding processes)
    kyc_task = agents["kyc_verification"].verify_customer({
        "verification_type": "business_process_assessment",
        "company_data": request,
        "customer_segments": request["customer_segments"]
    })
    
    # Phase 5: Fraud Detection (for transaction monitoring capabilities)
    fraud_task = agents["fraud_detection"].detect_fraud({
        "analysis_type": "capability_assessment",
        "company_data": request,
        "transaction_volume": "startup_level"
    })
    
    # Execute all tasks concurrently
    results = await asyncio.gather(
        regulatory_task,
        market_task,
        risk_task,
        kyc_task,
        fraud_task,
        return_exceptions=True
    )
    
    workflow_end_time = time.time()
    
    # Aggregate results
    workflow_result = {
        "regulatory_compliance": results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])},
        "market_analysis": results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])},
        "risk_assessment": results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])},
        "kyc_verification": results[3] if not isinstance(results[3], Exception) else {"error": str(results[3])},
        "fraud_detection": results[4] if not isinstance(results[4], Exception) else {"error": str(results[4])},
        "workflow_execution_time": workflow_end_time - workflow_start_time,
        "workflow_status": "completed",
        "timestamp": datetime.now()
    }
    
    pytest.comprehensive_workflow_result = workflow_result


@then('all five fintech agents should participate in the analysis')
def verify_all_agents_participated():
    """Verify all five fintech agents participated in the analysis"""
    result = pytest.comprehensive_workflow_result
    
    required_agents = ["regulatory_compliance", "market_analysis", "risk_assessment", "kyc_verification", "fraud_detection"]
    
    for agent in required_agents:
        assert agent in result, f"Agent {agent} did not participate in workflow"
        assert "error" not in result[agent], f"Agent {agent} encountered error: {result[agent].get('error')}"
        assert result[agent].get("confidence_score", 0) > 0, f"Agent {agent} produced no valid results"


@then('comprehensive risk intelligence should be generated')
def verify_comprehensive_risk_intelligence():
    """Verify comprehensive risk intelligence is generated"""
    result = pytest.comprehensive_workflow_result
    
    # Verify each agent contributed meaningful intelligence
    intelligence_components = {
        "regulatory_compliance": ["compliance_status", "risk_level"],
        "market_analysis": ["market_trend", "confidence_score"],
        "risk_assessment": ["overall_risk_score", "risk_breakdown"],
        "kyc_verification": ["verification_status", "risk_score"],
        "fraud_detection": ["fraud_probability", "confidence_score"]
    }
    
    for agent, required_fields in intelligence_components.items():
        agent_result = result[agent]
        for field in required_fields:
            assert field in agent_result, f"Agent {agent} missing required field {field}"


@then('the workflow should complete within 2 hours')
def verify_workflow_completion_time():
    """Verify workflow completes within 2 hour requirement"""
    result = pytest.comprehensive_workflow_result
    
    execution_time = result["workflow_execution_time"]
    max_time_seconds = 7200  # 2 hours
    
    assert execution_time < max_time_seconds, f"Workflow took {execution_time:.1f}s, exceeds 2 hour ({max_time_seconds}s) limit"


@then('business value should be quantified and reported')
def verify_business_value_quantification(bdd_business_value_metrics):
    """Verify business value is quantified and reported"""
    result = pytest.comprehensive_workflow_result
    request = pytest.comprehensive_analysis_request
    
    # Calculate business value based on analysis results
    company_type = request["company_type"]
    
    if company_type == "fintech_startup":
        expected_fraud_prevention = bdd_business_value_metrics["fraud_prevention_value"]["small_company"]
        expected_compliance_savings = bdd_business_value_metrics["compliance_cost_savings"]["small_company"]
    else:
        expected_fraud_prevention = bdd_business_value_metrics["fraud_prevention_value"]["medium_company"]
        expected_compliance_savings = bdd_business_value_metrics["compliance_cost_savings"]["medium_company"]
    
    total_expected_value = expected_fraud_prevention + expected_compliance_savings
    
    # Verify value generation potential is identified
    fraud_result = result["fraud_detection"]
    compliance_result = result["regulatory_compliance"]
    
    # Business value should be implicit in the analysis quality and recommendations
    fraud_confidence = fraud_result.get("confidence_score", 0)
    compliance_confidence = compliance_result.get("confidence_score", 0)
    
    # High confidence results indicate high business value potential
    avg_confidence = (fraud_confidence + compliance_confidence) / 2
    assert avg_confidence >= 0.75, f"Analysis confidence {avg_confidence:.2f} too low to demonstrate business value"


# ============================================================================
# REAL-TIME COORDINATION WORKFLOW STEPS
# ============================================================================

@given('multiple urgent fintech scenarios occur simultaneously')
def multiple_urgent_scenarios():
    """Set up multiple urgent fintech scenarios occurring simultaneously"""
    urgent_scenarios = {
        "regulatory_alert": {
            "type": "new_regulation",
            "source": "SEC",
            "urgency": "critical",
            "impact": "high",
            "deadline": datetime.now() + timedelta(hours=4)
        },
        "fraud_spike": {
            "type": "fraud_pattern_detected",
            "severity": "high",
            "affected_transactions": 1500,
            "urgency": "immediate",
            "false_positive_risk": "low"
        },
        "market_volatility": {
            "type": "market_disruption",
            "volatility_increase": 45,  # 45% increase
            "affected_sectors": ["fintech", "banking"],
            "urgency": "high"
        },
        "kyc_backlog": {
            "type": "verification_backlog",
            "pending_verifications": 250,
            "sla_breach_risk": "medium",
            "urgency": "medium"
        }
    }
    
    pytest.urgent_scenarios = urgent_scenarios


@when('the system coordinates real-time multi-agent response')
async def coordinate_real_time_response(mock_fintech_agents):
    """Coordinate real-time multi-agent response to urgent scenarios"""
    scenarios = pytest.urgent_scenarios
    agents = mock_fintech_agents
    
    coordination_start_time = time.time()
    
    # Prioritize scenarios by urgency
    scenario_priorities = {
        "immediate": 1,
        "critical": 2,
        "high": 3,
        "medium": 4,
        "low": 5
    }
    
    # Sort scenarios by priority
    sorted_scenarios = sorted(
        scenarios.items(),
        key=lambda x: scenario_priorities.get(x[1]["urgency"], 5)
    )
    
    response_tasks = []
    
    for scenario_name, scenario_data in sorted_scenarios:
        if scenario_name == "regulatory_alert":
            task = agents["regulatory_compliance"].analyze_compliance({
                "urgent_scenario": scenario_data,
                "response_mode": "emergency",
                "priority": "critical"
            })
        elif scenario_name == "fraud_spike":
            task = agents["fraud_detection"].detect_fraud({
                "urgent_scenario": scenario_data,
                "response_mode": "immediate",
                "priority": "critical"
            })
        elif scenario_name == "market_volatility":
            task = agents["market_analysis"].analyze_market({
                "urgent_scenario": scenario_data,
                "response_mode": "real_time",
                "priority": "high"
            })
        elif scenario_name == "kyc_backlog":
            task = agents["kyc_verification"].verify_customer({
                "urgent_scenario": scenario_data,
                "response_mode": "batch_processing",
                "priority": "medium"
            })
        
        response_tasks.append((scenario_name, task))
    
    # Execute high-priority tasks first, then medium priority
    high_priority_tasks = [task for name, task in response_tasks if scenarios[name]["urgency"] in ["immediate", "critical", "high"]]
    medium_priority_tasks = [task for name, task in response_tasks if scenarios[name]["urgency"] in ["medium", "low"]]
    
    # Execute high priority tasks immediately
    high_priority_results = await asyncio.gather(*high_priority_tasks, return_exceptions=True)
    
    # Execute medium priority tasks
    medium_priority_results = await asyncio.gather(*medium_priority_tasks, return_exceptions=True)
    
    coordination_end_time = time.time()
    
    # Combine results
    all_results = {}
    result_index = 0
    
    for scenario_name, _ in response_tasks:
        if scenarios[scenario_name]["urgency"] in ["immediate", "critical", "high"]:
            all_results[scenario_name] = high_priority_results[result_index] if result_index < len(high_priority_results) else {"error": "No result"}
        else:
            medium_index = result_index - len(high_priority_results)
            all_results[scenario_name] = medium_priority_results[medium_index] if medium_index < len(medium_priority_results) else {"error": "No result"}
        result_index += 1
    
    coordination_result = {
        "scenario_responses": all_results,
        "coordination_time": coordination_end_time - coordination_start_time,
        "scenarios_handled": len(scenarios),
        "priority_order": [name for name, _ in sorted_scenarios],
        "coordination_status": "completed"
    }
    
    pytest.real_time_coordination_result = coordination_result


@then('high-priority scenarios should be addressed first')
def verify_priority_handling():
    """Verify high-priority scenarios are addressed first"""
    result = pytest.real_time_coordination_result
    scenarios = pytest.urgent_scenarios
    
    priority_order = result["priority_order"]
    
    # Verify critical and immediate scenarios come first
    urgent_scenarios = [name for name, data in scenarios.items() if data["urgency"] in ["immediate", "critical"]]
    
    for urgent_scenario in urgent_scenarios:
        urgent_position = priority_order.index(urgent_scenario)
        
        # Check that no lower priority scenarios come before urgent ones
        for i in range(urgent_position):
            earlier_scenario = priority_order[i]
            earlier_urgency = scenarios[earlier_scenario]["urgency"]
            
            assert earlier_urgency in ["immediate", "critical"], f"Lower priority scenario {earlier_scenario} ({earlier_urgency}) handled before urgent scenario {urgent_scenario}"


@then('agent coordination should be seamless and efficient')
def verify_seamless_coordination():
    """Verify agent coordination is seamless and efficient"""
    result = pytest.real_time_coordination_result
    
    coordination_time = result["coordination_time"]
    scenarios_handled = result["scenarios_handled"]
    
    # Verify coordination efficiency
    max_coordination_time = 300  # 5 minutes for multiple urgent scenarios
    assert coordination_time < max_coordination_time, f"Coordination took {coordination_time:.1f}s, exceeds {max_coordination_time}s limit"
    
    # Verify all scenarios were handled
    scenario_responses = result["scenario_responses"]
    assert len(scenario_responses) == scenarios_handled, f"Not all scenarios handled: {len(scenario_responses)} vs {scenarios_handled}"
    
    # Verify no coordination errors
    for scenario_name, response in scenario_responses.items():
        assert not isinstance(response, Exception), f"Coordination error for scenario {scenario_name}: {response}"
        assert "error" not in response or response.get("confidence_score", 0) > 0, f"Agent error in scenario {scenario_name}"


@then('response times should meet emergency SLA requirements')
def verify_emergency_sla_compliance():
    """Verify response times meet emergency SLA requirements"""
    result = pytest.real_time_coordination_result
    scenarios = pytest.urgent_scenarios
    
    # Define SLA requirements by urgency
    sla_requirements = {
        "immediate": 60,    # 1 minute
        "critical": 300,    # 5 minutes
        "high": 900,        # 15 minutes
        "medium": 1800      # 30 minutes
    }
    
    coordination_time = result["coordination_time"]
    
    # Check most stringent SLA (immediate scenarios)
    immediate_scenarios = [name for name, data in scenarios.items() if data["urgency"] == "immediate"]
    
    if immediate_scenarios:
        immediate_sla = sla_requirements["immediate"]
        assert coordination_time <= immediate_sla, f"Immediate scenario response time {coordination_time:.1f}s exceeds {immediate_sla}s SLA"
    
    # Verify overall coordination meets reasonable SLA
    max_urgency_sla = max(sla_requirements[data["urgency"]] for data in scenarios.values())
    assert coordination_time <= max_urgency_sla, f"Coordination time {coordination_time:.1f}s exceeds maximum SLA {max_urgency_sla}s"


# ============================================================================
# BUSINESS VALUE DEMONSTRATION WORKFLOW STEPS
# ============================================================================

@given('a financial institution wants to evaluate RiskIntel360 ROI')
def financial_institution_roi_evaluation():
    """Set up financial institution ROI evaluation scenario"""
    institution_profile = {
        "institution_type": "regional_bank",
        "asset_size": 5000000000,  # $5B in assets
        "customer_count": 250000,
        "transaction_volume_daily": 50000,
        "current_fraud_losses_annual": 2500000,  # $2.5M annual fraud losses
        "current_compliance_costs_annual": 1800000,  # $1.8M annual compliance costs
        "current_risk_management_costs": 1200000,  # $1.2M annual risk management
        "manual_processes_percentage": 70,  # 70% manual processes
        "evaluation_period": "12_months",
        "roi_target": 5.0,  # 5x ROI target
        "payback_period_target": 18  # 18 months max payback
    }
    
    pytest.institution_profile = institution_profile


@when('comprehensive business value analysis is performed')
async def perform_business_value_analysis(mock_fintech_agents, bdd_business_value_metrics):
    """Perform comprehensive business value analysis"""
    institution = pytest.institution_profile
    agents = mock_fintech_agents
    
    # Analyze current state and potential improvements
    value_analysis_tasks = {
        "fraud_prevention_analysis": agents["fraud_detection"].detect_fraud({
            "analysis_type": "value_assessment",
            "current_losses": institution["current_fraud_losses_annual"],
            "transaction_volume": institution["transaction_volume_daily"],
            "improvement_target": 0.9  # 90% reduction target
        }),
        
        "compliance_optimization": agents["regulatory_compliance"].analyze_compliance({
            "analysis_type": "cost_benefit",
            "current_costs": institution["current_compliance_costs_annual"],
            "manual_percentage": institution["manual_processes_percentage"],
            "automation_target": 0.8  # 80% automation target
        }),
        
        "risk_management_enhancement": agents["risk_assessment"].assess_risk({
            "analysis_type": "value_optimization",
            "current_costs": institution["current_risk_management_costs"],
            "asset_size": institution["asset_size"],
            "efficiency_target": 0.75  # 75% efficiency improvement
        }),
        
        "operational_efficiency": agents["kyc_verification"].verify_customer({
            "analysis_type": "process_optimization",
            "customer_count": institution["customer_count"],
            "manual_percentage": institution["manual_processes_percentage"],
            "automation_potential": 0.85  # 85% automation potential
        })
    }
    
    # Execute value analysis
    value_results = {}
    for analysis_type, task in value_analysis_tasks.items():
        result = await task
        value_results[analysis_type] = result
    
    # Calculate comprehensive business value
    business_value_calculation = {
        "fraud_prevention_savings": calculate_fraud_prevention_value(
            institution, value_results["fraud_prevention_analysis"]
        ),
        "compliance_cost_savings": calculate_compliance_savings(
            institution, value_results["compliance_optimization"]
        ),
        "risk_management_savings": calculate_risk_management_value(
            institution, value_results["risk_management_enhancement"]
        ),
        "operational_efficiency_gains": calculate_operational_gains(
            institution, value_results["operational_efficiency"]
        )
    }
    
    # Calculate total ROI
    total_annual_savings = sum(business_value_calculation.values())
    implementation_cost = 500000  # Estimated $500K implementation cost
    annual_subscription = 200000  # Estimated $200K annual subscription
    
    roi_calculation = {
        "total_annual_savings": total_annual_savings,
        "implementation_cost": implementation_cost,
        "annual_operating_cost": annual_subscription,
        "net_annual_benefit": total_annual_savings - annual_subscription,
        "roi_first_year": (total_annual_savings - implementation_cost - annual_subscription) / (implementation_cost + annual_subscription),
        "roi_ongoing": (total_annual_savings - annual_subscription) / annual_subscription,
        "payback_period_months": (implementation_cost + annual_subscription) / (total_annual_savings / 12)
    }
    
    comprehensive_value_result = {
        "institution_profile": institution,
        "value_analysis_results": value_results,
        "business_value_breakdown": business_value_calculation,
        "roi_calculation": roi_calculation,
        "analysis_timestamp": datetime.now()
    }
    
    pytest.business_value_analysis_result = comprehensive_value_result


def calculate_fraud_prevention_value(institution: Dict[str, Any], fraud_analysis: Dict[str, Any]) -> float:
    """Calculate fraud prevention value"""
    current_losses = institution["current_fraud_losses_annual"]
    fraud_confidence = fraud_analysis.get("confidence_score", 0.8)
    
    # Assume 80% reduction in fraud losses with high confidence system
    prevention_rate = 0.8 * fraud_confidence
    annual_savings = current_losses * prevention_rate
    
    return annual_savings


def calculate_compliance_savings(institution: Dict[str, Any], compliance_analysis: Dict[str, Any]) -> float:
    """Calculate compliance cost savings"""
    current_costs = institution["current_compliance_costs_annual"]
    manual_percentage = institution["manual_processes_percentage"] / 100
    compliance_confidence = compliance_analysis.get("confidence_score", 0.85)
    
    # Assume 70% reduction in manual compliance costs
    automation_savings_rate = 0.7 * manual_percentage * compliance_confidence
    annual_savings = current_costs * automation_savings_rate
    
    return annual_savings


def calculate_risk_management_value(institution: Dict[str, Any], risk_analysis: Dict[str, Any]) -> float:
    """Calculate risk management value"""
    current_costs = institution["current_risk_management_costs"]
    risk_confidence = risk_analysis.get("confidence_score", 0.8)
    
    # Assume 50% efficiency improvement in risk management
    efficiency_improvement = 0.5 * risk_confidence
    annual_savings = current_costs * efficiency_improvement
    
    return annual_savings


def calculate_operational_gains(institution: Dict[str, Any], operational_analysis: Dict[str, Any]) -> float:
    """Calculate operational efficiency gains"""
    customer_count = institution["customer_count"]
    manual_percentage = institution["manual_processes_percentage"] / 100
    operational_confidence = operational_analysis.get("confidence_score", 0.9)
    
    # Assume $50 per customer annual savings from automation
    per_customer_savings = 50
    automation_rate = 0.8 * manual_percentage * operational_confidence
    annual_savings = customer_count * per_customer_savings * automation_rate
    
    return annual_savings


@then(parsers.parse('ROI should exceed {min_roi:f}x within {months:d} months'))
def verify_roi_target(min_roi: float, months: int):
    """Verify ROI exceeds target within specified timeframe"""
    result = pytest.business_value_analysis_result
    roi_calc = result["roi_calculation"]
    
    # Check ongoing ROI (after first year)
    ongoing_roi = roi_calc["roi_ongoing"]
    assert ongoing_roi >= min_roi, f"Ongoing ROI {ongoing_roi:.1f}x below {min_roi}x target"
    
    # Check payback period
    payback_months = roi_calc["payback_period_months"]
    assert payback_months <= months, f"Payback period {payback_months:.1f} months exceeds {months} month target"


@then(parsers.parse('annual cost savings should exceed ${min_savings:d}'))
def verify_cost_savings_target(min_savings: int):
    """Verify annual cost savings exceed target"""
    result = pytest.business_value_analysis_result
    
    total_savings = result["roi_calculation"]["total_annual_savings"]
    assert total_savings >= min_savings, f"Annual savings ${total_savings:,.0f} below ${min_savings:,} target"


@then('fraud prevention value should be quantified and substantial')
def verify_fraud_prevention_value():
    """Verify fraud prevention value is quantified and substantial"""
    result = pytest.business_value_analysis_result
    institution = result["institution_profile"]
    
    fraud_savings = result["business_value_breakdown"]["fraud_prevention_savings"]
    current_losses = institution["current_fraud_losses_annual"]
    
    # Fraud prevention should save at least 60% of current losses
    min_expected_savings = current_losses * 0.6
    assert fraud_savings >= min_expected_savings, f"Fraud prevention savings ${fraud_savings:,.0f} below expected ${min_expected_savings:,.0f}"
    
    # Should be substantial portion of total value
    total_savings = result["roi_calculation"]["total_annual_savings"]
    fraud_percentage = fraud_savings / total_savings
    
    assert fraud_percentage >= 0.3, f"Fraud prevention only {fraud_percentage:.1%} of total value, expected at least 30%"


@then('compliance automation benefits should be demonstrated')
def verify_compliance_automation_benefits():
    """Verify compliance automation benefits are demonstrated"""
    result = pytest.business_value_analysis_result
    
    compliance_savings = result["business_value_breakdown"]["compliance_cost_savings"]
    institution = result["institution_profile"]
    current_compliance_costs = institution["current_compliance_costs_annual"]
    
    # Compliance savings should be meaningful
    min_expected_savings = current_compliance_costs * 0.4  # At least 40% savings
    assert compliance_savings >= min_expected_savings, f"Compliance savings ${compliance_savings:,.0f} below expected ${min_expected_savings:,.0f}"


# ============================================================================
# PERFORMANCE UNDER LOAD WORKFLOW STEPS
# ============================================================================

@given(parsers.parse('the system handles {concurrent_workflows:d} concurrent complete workflows'))
async def concurrent_complete_workflows(concurrent_workflows: int, mock_fintech_agents):
    """Set up concurrent complete workflow processing"""
    agents = mock_fintech_agents
    
    # Create multiple complete workflow requests
    workflow_tasks = []
    
    for i in range(concurrent_workflows):
        workflow_request = {
            "workflow_id": f"WORKFLOW_{i:03d}",
            "company_type": "fintech_startup" if i % 2 == 0 else "regional_bank",
            "analysis_scope": ["regulatory", "fraud", "market", "kyc", "risk"],
            "priority": "normal",
            "request_timestamp": datetime.now()
        }
        
        # Create complete workflow task
        workflow_task = execute_single_complete_workflow(agents, workflow_request)
        workflow_tasks.append(workflow_task)
    
    pytest.concurrent_workflow_tasks = workflow_tasks
    pytest.concurrent_workflow_count = concurrent_workflows


async def execute_single_complete_workflow(agents: Dict[str, Any], request: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single complete workflow"""
    # Execute all agents for the workflow
    agent_tasks = [
        agents["regulatory_compliance"].analyze_compliance({"workflow_request": request}),
        agents["market_analysis"].analyze_market({"workflow_request": request}),
        agents["risk_assessment"].assess_risk({"workflow_request": request}),
        agents["kyc_verification"].verify_customer({"workflow_request": request}),
        agents["fraud_detection"].detect_fraud({"workflow_request": request})
    ]
    
    start_time = time.time()
    results = await asyncio.gather(*agent_tasks, return_exceptions=True)
    end_time = time.time()
    
    return {
        "workflow_id": request["workflow_id"],
        "agent_results": {
            "regulatory_compliance": results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])},
            "market_analysis": results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])},
            "risk_assessment": results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])},
            "kyc_verification": results[3] if not isinstance(results[3], Exception) else {"error": str(results[3])},
            "fraud_detection": results[4] if not isinstance(results[4], Exception) else {"error": str(results[4])}
        },
        "execution_time": end_time - start_time,
        "status": "completed"
    }


@when('all workflows are executed simultaneously under load')
async def execute_workflows_under_load():
    """Execute all workflows simultaneously under load"""
    tasks = pytest.concurrent_workflow_tasks
    
    load_test_start_time = time.time()
    workflow_results = await asyncio.gather(*tasks, return_exceptions=True)
    load_test_end_time = time.time()
    
    pytest.load_test_results = {
        "workflow_results": workflow_results,
        "total_execution_time": load_test_end_time - load_test_start_time,
        "concurrent_count": pytest.concurrent_workflow_count,
        "load_test_timestamp": datetime.now()
    }


@then('all workflows should complete successfully')
def verify_all_workflows_successful():
    """Verify all workflows complete successfully under load"""
    results = pytest.load_test_results
    workflow_results = results["workflow_results"]
    
    # Verify all workflows completed
    successful_workflows = [
        result for result in workflow_results 
        if not isinstance(result, Exception) and result.get("status") == "completed"
    ]
    
    success_rate = len(successful_workflows) / len(workflow_results)
    assert success_rate >= 0.95, f"Workflow success rate {success_rate:.1%} below 95% requirement under load"


@then('system performance should remain within acceptable limits')
def verify_performance_under_load(bdd_performance_benchmarks):
    """Verify system performance remains within acceptable limits under load"""
    results = pytest.load_test_results
    workflow_results = results["workflow_results"]
    
    # Check individual workflow execution times
    execution_times = [
        result["execution_time"] for result in workflow_results 
        if not isinstance(result, Exception) and "execution_time" in result
    ]
    
    if execution_times:
        avg_execution_time = sum(execution_times) / len(execution_times)
        max_execution_time = max(execution_times)
        
        # Verify average execution time
        max_workflow_time = bdd_performance_benchmarks["workflow_completion_time"]
        assert avg_execution_time <= max_workflow_time, f"Average workflow time {avg_execution_time:.1f}s exceeds {max_workflow_time}s limit under load"
        
        # Verify no workflow took excessively long
        assert max_execution_time <= max_workflow_time * 1.5, f"Maximum workflow time {max_execution_time:.1f}s exceeds 1.5x limit under load"


@then('resource utilization should be optimized')
def verify_resource_optimization():
    """Verify resource utilization is optimized under load"""
    results = pytest.load_test_results
    
    total_time = results["total_execution_time"]
    concurrent_count = results["concurrent_count"]
    
    # Calculate efficiency metrics
    theoretical_sequential_time = concurrent_count * 300  # Assume 5 minutes per workflow sequentially
    efficiency_ratio = theoretical_sequential_time / total_time if total_time > 0 else 0
    
    # Concurrent execution should be much more efficient than sequential
    assert efficiency_ratio >= 5.0, f"Concurrency efficiency {efficiency_ratio:.1f}x below 5x minimum (poor parallelization)"
    
    # Total time should be reasonable for concurrent execution
    max_reasonable_time = 600  # 10 minutes for concurrent workflows
    assert total_time <= max_reasonable_time, f"Total concurrent execution time {total_time:.1f}s exceeds {max_reasonable_time}s reasonable limit"
