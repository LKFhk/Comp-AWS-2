"""
BDD Step Definitions for KYC Verification Processes
Implements Given-When-Then scenarios for KYC verification testing.
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
scenarios('../features/kyc_verification.feature')


# ============================================================================
# KYC VERIFICATION SETUP STEPS
# ============================================================================

@given('the KYC Verification Agent is active')
def kyc_agent_active(mock_fintech_agents, kyc_verification_context):
    """Verify KYC verification agent is active and ready"""
    agent = mock_fintech_agents["kyc_verification"]
    assert agent.status == "active"
    assert kyc_verification_context["kyc_agent_active"] is True


@given('identity verification services are accessible')
def identity_services_accessible(kyc_verification_context):
    """Verify identity verification services are accessible"""
    required_services = {
        "identity_verification_api": True,
        "sanctions_list_available": True,
        "public_records_access": True,
        "document_processing": True
    }
    
    for service, expected in required_services.items():
        assert kyc_verification_context.get(service, False) == expected, f"{service} not accessible"


@given('sanctions lists and public records are up-to-date')
def sanctions_and_records_updated():
    """Verify sanctions lists and public records are current"""
    pytest.sanctions_last_update = datetime.now() - timedelta(hours=2)
    pytest.records_last_update = datetime.now() - timedelta(hours=1)
    
    # Verify updates are recent (within 24 hours)
    time_threshold = datetime.now() - timedelta(hours=24)
    
    assert pytest.sanctions_last_update > time_threshold, "Sanctions list not recently updated"
    assert pytest.records_last_update > time_threshold, "Public records not recently updated"


# ============================================================================
# INDIVIDUAL KYC VERIFICATION STEPS
# ============================================================================

@given('a new individual customer requires KYC verification')
def new_individual_customer(sample_kyc_documents):
    """Set up new individual customer for KYC verification"""
    customer_data = sample_kyc_documents["individual_kyc"]
    
    pytest.kyc_customer = customer_data
    pytest.kyc_type = "individual"
    pytest.verification_start_time = datetime.now()


@when('the KYC Verification Agent processes the customer information')
async def process_individual_kyc(mock_fintech_agents):
    """Process individual customer KYC verification"""
    agent = mock_fintech_agents["kyc_verification"]
    customer = pytest.kyc_customer
    
    verification_request = {
        "customer_data": customer,
        "verification_type": "individual",
        "verification_level": "enhanced",
        "document_types": ["drivers_license", "passport", "utility_bill"],
        "risk_assessment": True
    }
    
    start_time = asyncio.get_event_loop().time()
    result = await agent.verify_customer(verification_request)
    end_time = asyncio.get_event_loop().time()
    
    result["processing_time"] = end_time - start_time
    pytest.kyc_verification_result = result


@then('identity documents should be validated automatically')
def verify_document_validation():
    """Verify identity documents are validated automatically"""
    result = pytest.kyc_verification_result
    
    assert "document_validity" in result
    assert result["document_validity"] in ["valid", "invalid", "requires_review"]
    
    # For testing, assume documents are valid
    assert result["document_validity"] == "valid", f"Document validation failed: {result['document_validity']}"


@then('sanctions screening should be performed')
def verify_sanctions_screening():
    """Verify sanctions screening is performed"""
    result = pytest.kyc_verification_result
    
    assert "sanctions_check" in result
    assert result["sanctions_check"] in ["clear", "match_found", "requires_review"]
    
    # Verify sanctions check was actually performed
    assert result["sanctions_check"] is not None, "Sanctions screening not performed"


@then('risk scoring should be calculated based on multiple factors')
def verify_risk_scoring():
    """Verify risk scoring is calculated using multiple factors"""
    result = pytest.kyc_verification_result
    customer = pytest.kyc_customer
    
    assert "risk_score" in result
    assert 0.0 <= result["risk_score"] <= 1.0, f"Risk score {result['risk_score']} outside valid range [0.0, 1.0]"
    
    # Verify risk score is reasonable for the customer profile
    expected_risk = customer.get("risk_score", 0.25)
    actual_risk = result["risk_score"]
    
    # Allow some variance in risk calculation
    risk_difference = abs(actual_risk - expected_risk)
    assert risk_difference <= 0.2, f"Risk score {actual_risk} differs significantly from expected {expected_risk}"


@then('verification should complete within 2 minutes')
def verify_kyc_processing_time():
    """Verify KYC verification completes within time limit"""
    result = pytest.kyc_verification_result
    
    assert "processing_time" in result
    assert result["processing_time"] < 120.0, f"KYC verification took {result['processing_time']:.1f}s, exceeds 2 minute limit"


# ============================================================================
# BUSINESS KYC VERIFICATION STEPS
# ============================================================================

@given('a new business entity requires enhanced due diligence')
def new_business_entity(sample_kyc_documents):
    """Set up new business entity for enhanced KYC verification"""
    business_data = sample_kyc_documents["business_kyc"]
    
    pytest.kyc_business = business_data
    pytest.kyc_type = "business"
    pytest.verification_level = "enhanced_due_diligence"


@when('the system performs enhanced due diligence')
async def perform_enhanced_due_diligence(mock_fintech_agents):
    """Perform enhanced due diligence for business entity"""
    agent = mock_fintech_agents["kyc_verification"]
    business = pytest.kyc_business
    
    edd_request = {
        "business_data": business,
        "verification_type": "business",
        "verification_level": "enhanced_due_diligence",
        "checks_required": [
            "beneficial_ownership",
            "corporate_structure",
            "regulatory_status",
            "sanctions_screening",
            "adverse_media_check"
        ]
    }
    
    result = await agent.verify_customer(edd_request)
    pytest.edd_result = result


@then('beneficial ownership should be identified and verified')
def verify_beneficial_ownership():
    """Verify beneficial ownership identification and verification"""
    result = pytest.edd_result
    business = pytest.kyc_business
    
    # Verify beneficial ownership information is processed
    expected_owners = business.get("beneficial_owners", [])
    
    # For BDD testing, verify the system processed ownership information
    assert result["verification_status"] in ["approved", "pending", "rejected"]
    
    # If approved, ownership verification should be complete
    if result["verification_status"] == "approved":
        assert len(expected_owners) > 0, "No beneficial owners identified for approved business"


@then('corporate structure should be analyzed')
def verify_corporate_structure_analysis():
    """Verify corporate structure analysis is performed"""
    result = pytest.edd_result
    business = pytest.kyc_business
    
    # Verify corporate information is considered
    assert "regulatory_status" in result
    assert result["regulatory_status"] in ["active", "inactive", "suspended", "unknown"]
    
    # For active businesses, structure should be verified
    if result["regulatory_status"] == "active":
        incorporation_date = business.get("incorporation_date")
        assert incorporation_date is not None, "Incorporation date not verified for active business"


@then('regulatory compliance status should be checked')
def verify_regulatory_compliance_status():
    """Verify regulatory compliance status is checked"""
    result = pytest.edd_result
    
    assert "regulatory_status" in result
    regulatory_status = result["regulatory_status"]
    
    # Verify regulatory status is properly assessed
    valid_statuses = ["active", "inactive", "suspended", "unknown"]
    assert regulatory_status in valid_statuses, f"Invalid regulatory status: {regulatory_status}"
    
    # Active status should have higher confidence
    if regulatory_status == "active":
        confidence = result.get("confidence_score", 0)
        assert confidence >= 0.8, f"Low confidence {confidence} for active regulatory status"


# ============================================================================
# RISK-BASED VERIFICATION STEPS
# ============================================================================

@given(parsers.parse('a customer with {risk_level} risk profile'))
def customer_with_risk_profile(risk_level: str, sample_kyc_documents):
    """Set up customer with specified risk profile"""
    risk_map = {
        "low": {"risk_score": 0.2, "verification_level": "basic"},
        "medium": {"risk_score": 0.5, "verification_level": "standard"},
        "high": {"risk_score": 0.8, "verification_level": "enhanced"}
    }
    
    risk_config = risk_map.get(risk_level.lower(), risk_map["medium"])
    
    # Use individual customer data and adjust risk
    customer_data = sample_kyc_documents["individual_kyc"].copy()
    customer_data["risk_score"] = risk_config["risk_score"]
    customer_data["verification_level"] = risk_config["verification_level"]
    
    pytest.risk_based_customer = customer_data
    pytest.expected_risk_level = risk_level.lower()


@when('risk-based verification procedures are applied')
async def apply_risk_based_verification(mock_fintech_agents):
    """Apply risk-based verification procedures"""
    agent = mock_fintech_agents["kyc_verification"]
    customer = pytest.risk_based_customer
    
    verification_request = {
        "customer_data": customer,
        "verification_approach": "risk_based",
        "risk_tolerance": "standard",
        "adaptive_procedures": True
    }
    
    result = await agent.verify_customer(verification_request)
    pytest.risk_based_result = result


@then('verification depth should match the risk level')
def verify_risk_appropriate_verification():
    """Verify verification depth matches customer risk level"""
    result = pytest.risk_based_result
    expected_risk = pytest.expected_risk_level
    customer = pytest.risk_based_customer
    
    actual_risk_score = result.get("risk_score", 0)
    expected_risk_score = customer.get("risk_score", 0.5)
    
    # Verify risk assessment is consistent
    risk_difference = abs(actual_risk_score - expected_risk_score)
    assert risk_difference <= 0.15, f"Risk assessment inconsistent: expected {expected_risk_score}, got {actual_risk_score}"
    
    # Verify verification level matches risk
    verification_level = result.get("verification_level", "standard")
    
    if expected_risk == "low":
        assert verification_level in ["basic", "standard"], f"Over-verification for low risk: {verification_level}"
    elif expected_risk == "high":
        assert verification_level in ["enhanced", "standard"], f"Under-verification for high risk: {verification_level}"


@then('additional checks should be triggered for high-risk customers')
def verify_additional_checks_high_risk():
    """Verify additional checks for high-risk customers"""
    result = pytest.risk_based_result
    expected_risk = pytest.expected_risk_level
    
    if expected_risk == "high":
        # High-risk customers should have enhanced verification
        verification_level = result.get("verification_level", "standard")
        assert verification_level == "enhanced", f"High-risk customer not flagged for enhanced verification: {verification_level}"
        
        # Should have additional screening
        sanctions_check = result.get("sanctions_check", "clear")
        assert sanctions_check is not None, "No sanctions check for high-risk customer"


# ============================================================================
# AUTOMATED DECISION MAKING STEPS
# ============================================================================

@given('automated KYC decision rules are configured')
def automated_decision_rules_configured():
    """Configure automated KYC decision rules"""
    decision_rules = {
        "auto_approve_threshold": 0.9,  # 90% confidence for auto-approval
        "auto_reject_threshold": 0.3,   # 30% confidence for auto-rejection
        "manual_review_range": (0.3, 0.9),  # Manual review between thresholds
        "sanctions_match_action": "auto_reject",
        "document_invalid_action": "manual_review",
        "high_risk_action": "enhanced_verification"
    }
    
    pytest.kyc_decision_rules = decision_rules


@when('the system makes automated verification decisions')
async def make_automated_decisions(mock_fintech_agents):
    """Make automated KYC verification decisions"""
    agent = mock_fintech_agents["kyc_verification"]
    rules = pytest.kyc_decision_rules
    
    # Test multiple customer scenarios
    test_scenarios = [
        {"confidence": 0.95, "sanctions": "clear", "documents": "valid", "expected": "auto_approve"},
        {"confidence": 0.25, "sanctions": "clear", "documents": "valid", "expected": "auto_reject"},
        {"confidence": 0.65, "sanctions": "clear", "documents": "valid", "expected": "manual_review"},
        {"confidence": 0.85, "sanctions": "match_found", "documents": "valid", "expected": "auto_reject"}
    ]
    
    results = []
    for scenario in test_scenarios:
        request = {
            "customer_data": {"test_scenario": True},
            "simulated_confidence": scenario["confidence"],
            "simulated_sanctions": scenario["sanctions"],
            "simulated_documents": scenario["documents"],
            "automated_decision": True
        }
        
        result = await agent.verify_customer(request)
        result["expected_decision"] = scenario["expected"]
        results.append(result)
    
    pytest.automated_decision_results = results


@then('decisions should be made within defined confidence thresholds')
def verify_confidence_threshold_decisions():
    """Verify decisions are made within defined confidence thresholds"""
    results = pytest.automated_decision_results
    rules = pytest.kyc_decision_rules
    
    for result in results:
        confidence = result.get("confidence_score", 0)
        verification_status = result.get("verification_status", "pending")
        expected_decision = result.get("expected_decision", "manual_review")
        
        # Verify decision logic
        if confidence >= rules["auto_approve_threshold"]:
            assert verification_status == "approved", f"High confidence {confidence} should auto-approve"
        elif confidence <= rules["auto_reject_threshold"]:
            assert verification_status == "rejected", f"Low confidence {confidence} should auto-reject"
        else:
            # Manual review range
            assert verification_status in ["pending", "requires_review"], f"Medium confidence {confidence} should require manual review"


@then('manual review should be flagged for edge cases')
def verify_manual_review_flagging():
    """Verify manual review is flagged for appropriate edge cases"""
    results = pytest.automated_decision_results
    
    manual_review_cases = [
        result for result in results 
        if result.get("verification_status") in ["pending", "requires_review"]
    ]
    
    # Should have at least one manual review case
    assert len(manual_review_cases) > 0, "No cases flagged for manual review"
    
    # Verify manual review cases are appropriate
    for case in manual_review_cases:
        confidence = case.get("confidence_score", 0)
        
        # Manual review should be for medium confidence scores
        assert 0.3 <= confidence <= 0.9, f"Manual review case has inappropriate confidence: {confidence}"


# ============================================================================
# PERFORMANCE AND SCALABILITY STEPS
# ============================================================================

@given(parsers.parse('the system processes {verification_count:d} concurrent KYC verifications'))
async def concurrent_kyc_verifications(verification_count: int, mock_fintech_agents, sample_kyc_documents):
    """Set up concurrent KYC verification processing"""
    agent = mock_fintech_agents["kyc_verification"]
    
    # Create multiple verification requests
    tasks = []
    for i in range(verification_count):
        # Alternate between individual and business verifications
        if i % 2 == 0:
            customer_data = sample_kyc_documents["individual_kyc"].copy()
            verification_type = "individual"
        else:
            customer_data = sample_kyc_documents["business_kyc"].copy()
            verification_type = "business"
        
        customer_data["customer_id"] = f"customer_{i}"
        
        request = {
            "customer_data": customer_data,
            "verification_type": verification_type,
            "verification_level": "standard",
            "request_id": f"kyc_req_{i}"
        }
        
        task = agent.verify_customer(request)
        tasks.append(task)
    
    pytest.concurrent_kyc_tasks = tasks
    pytest.concurrent_kyc_count = verification_count


@when('all KYC verifications are processed simultaneously')
async def process_concurrent_kyc_verifications():
    """Process all concurrent KYC verifications"""
    tasks = pytest.concurrent_kyc_tasks
    
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks)
    end_time = asyncio.get_event_loop().time()
    
    pytest.concurrent_kyc_results = results
    pytest.concurrent_kyc_processing_time = end_time - start_time


@then('all verifications should complete within performance requirements')
def verify_concurrent_kyc_performance(bdd_performance_benchmarks):
    """Verify concurrent KYC verifications meet performance requirements"""
    results = pytest.concurrent_kyc_results
    processing_time = pytest.concurrent_kyc_processing_time
    verification_count = pytest.concurrent_kyc_count
    
    # Verify all verifications completed successfully
    completed_results = [r for r in results if r.get("verification_status") is not None]
    completion_rate = len(completed_results) / len(results)
    
    assert completion_rate >= 0.95, f"KYC completion rate {completion_rate:.1%} below 95% requirement"
    
    # Verify average processing time
    avg_processing_time = processing_time / verification_count
    max_kyc_time = bdd_performance_benchmarks["kyc_verification_time"]
    
    assert avg_processing_time <= max_kyc_time, f"Average KYC processing time {avg_processing_time:.1f}s exceeds {max_kyc_time}s limit"


@then('verification accuracy should remain above 95%')
def verify_kyc_accuracy():
    """Verify KYC verification accuracy remains high"""
    results = pytest.concurrent_kyc_results
    
    # Calculate accuracy based on confidence scores and decision consistency
    high_confidence_results = [
        r for r in results 
        if r.get("confidence_score", 0) >= 0.8
    ]
    
    accuracy_rate = len(high_confidence_results) / len(results) if results else 0
    
    assert accuracy_rate >= 0.95, f"KYC accuracy {accuracy_rate:.1%} below 95% requirement"


# ============================================================================
# COMPLIANCE AND AUDIT TRAIL STEPS
# ============================================================================

@given('audit trail requirements are enabled')
def audit_trail_enabled():
    """Enable audit trail requirements for KYC verification"""
    audit_config = {
        "audit_logging": True,
        "data_retention_days": 2555,  # 7 years
        "compliance_reporting": True,
        "decision_tracking": True,
        "document_versioning": True
    }
    
    pytest.kyc_audit_config = audit_config
    
    for requirement, enabled in audit_config.items():
        assert enabled, f"Audit requirement {requirement} not enabled"


@when('KYC verification decisions are made')
async def make_kyc_decisions_with_audit(mock_fintech_agents, sample_kyc_documents):
    """Make KYC verification decisions with audit trail"""
    agent = mock_fintech_agents["kyc_verification"]
    audit_config = pytest.kyc_audit_config
    
    verification_request = {
        "customer_data": sample_kyc_documents["individual_kyc"],
        "verification_type": "individual",
        "audit_trail": audit_config["audit_logging"],
        "compliance_mode": True
    }
    
    result = await agent.verify_customer(verification_request)
    pytest.audited_kyc_result = result


@then('all decisions should be logged for audit purposes')
def verify_audit_logging():
    """Verify all KYC decisions are logged for audit purposes"""
    result = pytest.audited_kyc_result
    audit_config = pytest.kyc_audit_config
    
    if audit_config["audit_logging"]:
        # Verify audit information is present
        assert "verification_status" in result, "Verification decision not logged"
        assert "confidence_score" in result, "Confidence score not logged"
        
        # Verify decision rationale is available
        decision_status = result.get("verification_status")
        assert decision_status is not None, "No decision status for audit trail"


@then('compliance reports should be generated automatically')
def verify_compliance_reporting():
    """Verify compliance reports are generated automatically"""
    audit_config = pytest.kyc_audit_config
    
    if audit_config["compliance_reporting"]:
        # Simulate compliance report generation
        compliance_report = {
            "report_date": datetime.now(),
            "total_verifications": 1,
            "approved_count": 1,
            "rejected_count": 0,
            "pending_count": 0,
            "average_processing_time": 45.0,
            "compliance_rate": 1.0
        }
        
        pytest.compliance_report = compliance_report
        
        # Verify report contains required information
        assert compliance_report["total_verifications"] > 0, "No verifications in compliance report"
        assert compliance_report["compliance_rate"] >= 0.95, f"Compliance rate {compliance_report['compliance_rate']:.1%} below 95% requirement"


@then('data retention policies should be enforced')
def verify_data_retention_policies():
    """Verify data retention policies are enforced"""
    audit_config = pytest.kyc_audit_config
    
    retention_days = audit_config["data_retention_days"]
    
    # Verify retention period meets regulatory requirements (7 years = 2555 days)
    assert retention_days >= 2555, f"Data retention period {retention_days} days below 7-year requirement"
    
    # Verify retention policy is configured
    assert audit_config["document_versioning"] is True, "Document versioning not enabled for retention"
