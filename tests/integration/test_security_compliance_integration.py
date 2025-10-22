"""
Integration tests for security and compliance framework.
Tests AWS security services integration, compliance monitoring, and audit trails.
"""

import pytest
import pytest_asyncio
import asyncio
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from riskintel360.services.security_compliance_framework import (
    SecurityComplianceFramework, ComplianceStatus, SecurityEvent,
    AuditTrail, EncryptionManager, AccessControlManager
)
from riskintel360.services.aws_security_integration import (
    AWSSecurityManager, IAMRoleManager, KMSEncryptionService,
    CloudTrailMonitor, SecurityGroupManager
)


class TestAWSSecurityIntegration:
    """Integration tests for AWS security services"""
    
    @pytest.fixture
    def aws_security_manager(self):
        """Create AWS security manager for testing"""
        return AWSSecurityManager()
    
    @pytest.fixture
    def mock_aws_clients(self):
        """Mock AWS service clients"""
        return {
            "iam": Mock(),
            "kms": Mock(),
            "cloudtrail": Mock(),
            "ec2": Mock(),
            "sts": Mock()
        }
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_iam_role_management_integration(self, aws_security_manager, mock_aws_clients):
        """Test IAM role management for fintech security"""
        with patch.object(aws_security_manager, '_get_aws_client') as mock_get_client:
            mock_get_client.return_value = mock_aws_clients["iam"]
            
            # Mock IAM responses
            mock_aws_clients["iam"].create_role.return_value = {
                "Role": {
                    "RoleName": "RiskIntel360-Agent-Role",
                    "Arn": "arn:aws:iam::123456789012:role/RiskIntel360-Agent-Role",
                    "CreateDate": datetime.now(timezone.utc)
                }
            }
            
            mock_aws_clients["iam"].attach_role_policy.return_value = {}
            
            # Test fintech agent role creation
            fintech_roles = [
                {
                    "role_name": "RiskIntel360-RegulatoryCompliance-Role",
                    "permissions": [
                        "bedrock:InvokeModel",
                        "s3:GetObject",
                        "s3:PutObject",
                        "secretsmanager:GetSecretValue"
                    ],
                    "trust_policy": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                                "Action": "sts:AssumeRole"
                            }
                        ]
                    }
                },
                {
                    "role_name": "RiskIntel360-FraudDetection-Role",
                    "permissions": [
                        "bedrock:InvokeModel",
                        "s3:GetObject",
                        "s3:PutObject",
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "kms:Decrypt",
                        "kms:Encrypt"
                    ],
                    "trust_policy": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                                "Action": "sts:AssumeRole"
                            }
                        ]
                    }
                }
            ]
            
            # Create fintech security roles
            created_roles = []
            for role_config in fintech_roles:
                role_result = await aws_security_manager.create_fintech_role(
                    role_name=role_config["role_name"],
                    permissions=role_config["permissions"],
                    trust_policy=role_config["trust_policy"]
                )
                
                created_roles.append(role_result)
                
                # Verify role creation
                assert role_result["success"] is True
                assert role_result["role_arn"] is not None
                assert "RiskIntel360" in role_result["role_name"]
            
            # Verify IAM calls were made
            assert mock_aws_clients["iam"].create_role.call_count == len(fintech_roles)
            assert mock_aws_clients["iam"].attach_role_policy.call_count >= len(fintech_roles)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_kms_encryption_integration(self, aws_security_manager, mock_aws_clients):
        """Test KMS encryption for fintech data protection"""
        with patch.object(aws_security_manager, '_get_aws_client') as mock_get_client:
            mock_get_client.return_value = mock_aws_clients["kms"]
            
            # Mock KMS responses
            mock_aws_clients["kms"].create_key.return_value = {
                "KeyMetadata": {
                    "KeyId": "12345678-1234-1234-1234-123456789012",
                    "Arn": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
                    "Description": "RiskIntel360 FinTech Data Encryption Key"
                }
            }
            
            mock_aws_clients["kms"].encrypt.return_value = {
                "CiphertextBlob": b"encrypted_data_blob",
                "KeyId": "12345678-1234-1234-1234-123456789012"
            }
            
            mock_aws_clients["kms"].decrypt.return_value = {
                "Plaintext": b"sensitive_fintech_data",
                "KeyId": "12345678-1234-1234-1234-123456789012"
            }
            
            # Test fintech data encryption keys
            fintech_encryption_keys = [
                {
                    "key_usage": "fraud_detection_data",
                    "description": "Encryption key for fraud detection ML models and transaction data"
                },
                {
                    "key_usage": "compliance_documents",
                    "description": "Encryption key for regulatory compliance documents and reports"
                },
                {
                    "key_usage": "customer_pii",
                    "description": "Encryption key for customer PII and KYC verification data"
                }
            ]
            
            # Create encryption keys
            created_keys = []
            for key_config in fintech_encryption_keys:
                key_result = await aws_security_manager.create_fintech_encryption_key(
                    key_usage=key_config["key_usage"],
                    description=key_config["description"]
                )
                
                created_keys.append(key_result)
                
                # Verify key creation
                assert key_result["success"] is True
                assert key_result["key_id"] is not None
                assert key_result["key_arn"] is not None
            
            # Test data encryption/decryption
            sensitive_data = "customer_ssn:123-45-6789,account_number:9876543210"
            
            # Encrypt sensitive fintech data
            encryption_result = await aws_security_manager.encrypt_fintech_data(
                plaintext_data=sensitive_data,
                key_id=created_keys[2]["key_id"],  # Use customer PII key
                encryption_context={
                    "data_type": "customer_pii",
                    "compliance_requirement": "PCI_DSS"
                }
            )
            
            assert encryption_result["success"] is True
            assert encryption_result["encrypted_data"] is not None
            
            # Decrypt sensitive fintech data
            decryption_result = await aws_security_manager.decrypt_fintech_data(
                encrypted_data=encryption_result["encrypted_data"],
                encryption_context={
                    "data_type": "customer_pii",
                    "compliance_requirement": "PCI_DSS"
                }
            )
            
            assert decryption_result["success"] is True
            assert decryption_result["plaintext_data"] == sensitive_data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cloudtrail_audit_integration(self, aws_security_manager, mock_aws_clients):
        """Test CloudTrail integration for compliance audit trails"""
        with patch.object(aws_security_manager, '_get_aws_client') as mock_get_client:
            mock_get_client.return_value = mock_aws_clients["cloudtrail"]
            
            # Mock CloudTrail responses
            mock_aws_clients["cloudtrail"].create_trail.return_value = {
                "TrailARN": "arn:aws:cloudtrail:us-east-1:123456789012:trail/RiskIntel360-AuditTrail",
                "Name": "RiskIntel360-AuditTrail"
            }
            
            mock_aws_clients["cloudtrail"].lookup_events.return_value = {
                "Events": [
                    {
                        "EventId": "event-123",
                        "EventName": "InvokeModel",
                        "EventSource": "bedrock.amazonaws.com",
                        "EventTime": datetime.now(timezone.utc),
                        "Username": "RiskIntel360-Agent",
                        "Resources": [
                            {
                                "ResourceType": "AWS::Bedrock::Model",
                                "ResourceName": "anthropic.claude-3-sonnet"
                            }
                        ]
                    },
                    {
                        "EventId": "event-124",
                        "EventName": "GetSecretValue",
                        "EventSource": "secretsmanager.amazonaws.com",
                        "EventTime": datetime.now(timezone.utc),
                        "Username": "RiskIntel360-Agent",
                        "Resources": [
                            {
                                "ResourceType": "AWS::SecretsManager::Secret",
                                "ResourceName": "RiskIntel360/API/Keys"
                            }
                        ]
                    }
                ]
            }
            
            # Create audit trail for fintech compliance
            audit_trail_result = await aws_security_manager.create_fintech_audit_trail(
                trail_name="RiskIntel360-FinTech-AuditTrail",
                s3_bucket="riskintel360-audit-logs",
                include_global_events=True,
                enable_log_file_validation=True
            )
            
            assert audit_trail_result["success"] is True
            assert audit_trail_result["trail_arn"] is not None
            
            # Query audit events for compliance reporting
            audit_events = await aws_security_manager.get_fintech_audit_events(
                start_time=datetime.now(timezone.utc) - timedelta(hours=24),
                end_time=datetime.now(timezone.utc),
                event_sources=["bedrock.amazonaws.com", "secretsmanager.amazonaws.com"]
            )
            
            assert len(audit_events) > 0
            
            # Verify audit event structure for compliance
            for event in audit_events:
                assert "event_id" in event
                assert "event_name" in event
                assert "event_source" in event
                assert "event_time" in event
                assert "username" in event
                assert "resources" in event


class TestComplianceFrameworkIntegration:
    """Integration tests for compliance framework"""
    
    @pytest.fixture
    def compliance_framework(self):
        """Create compliance framework for testing"""
        return SecurityComplianceFramework()
    
    @pytest.fixture
    def mock_regulatory_requirements(self):
        """Mock regulatory requirements for fintech"""
        return {
            "PCI_DSS": {
                "version": "4.0",
                "requirements": [
                    "secure_cardholder_data",
                    "encrypt_transmission",
                    "maintain_vulnerability_management",
                    "implement_access_controls",
                    "monitor_networks",
                    "maintain_security_policy"
                ],
                "compliance_deadline": "2024-12-31"
            },
            "SOX": {
                "version": "2002",
                "requirements": [
                    "financial_reporting_controls",
                    "audit_trail_maintenance",
                    "data_integrity_assurance",
                    "access_control_documentation"
                ],
                "compliance_deadline": "ongoing"
            },
            "GDPR": {
                "version": "2018",
                "requirements": [
                    "data_protection_by_design",
                    "consent_management",
                    "data_breach_notification",
                    "data_portability",
                    "right_to_erasure"
                ],
                "compliance_deadline": "ongoing"
            },
            "BSA_AML": {
                "version": "2021",
                "requirements": [
                    "customer_identification_program",
                    "suspicious_activity_reporting",
                    "record_keeping",
                    "compliance_program_maintenance"
                ],
                "compliance_deadline": "ongoing"
            }
        }
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_comprehensive_compliance_assessment(
        self, 
        compliance_framework, 
        mock_regulatory_requirements
    ):
        """Test comprehensive compliance assessment for fintech regulations"""
        
        # Mock current system compliance status
        current_compliance_status = {
            "PCI_DSS": {
                "secure_cardholder_data": {"status": "compliant", "evidence": "encryption_implemented"},
                "encrypt_transmission": {"status": "compliant", "evidence": "tls_1_3_enabled"},
                "maintain_vulnerability_management": {"status": "partial", "evidence": "quarterly_scans"},
                "implement_access_controls": {"status": "compliant", "evidence": "rbac_implemented"},
                "monitor_networks": {"status": "compliant", "evidence": "cloudwatch_monitoring"},
                "maintain_security_policy": {"status": "non_compliant", "evidence": "policy_outdated"}
            },
            "SOX": {
                "financial_reporting_controls": {"status": "compliant", "evidence": "automated_controls"},
                "audit_trail_maintenance": {"status": "compliant", "evidence": "cloudtrail_enabled"},
                "data_integrity_assurance": {"status": "compliant", "evidence": "checksums_verified"},
                "access_control_documentation": {"status": "partial", "evidence": "documentation_incomplete"}
            },
            "GDPR": {
                "data_protection_by_design": {"status": "compliant", "evidence": "privacy_by_design"},
                "consent_management": {"status": "compliant", "evidence": "consent_system_implemented"},
                "data_breach_notification": {"status": "compliant", "evidence": "notification_procedures"},
                "data_portability": {"status": "partial", "evidence": "export_functionality_limited"},
                "right_to_erasure": {"status": "compliant", "evidence": "deletion_procedures"}
            },
            "BSA_AML": {
                "customer_identification_program": {"status": "compliant", "evidence": "kyc_system_active"},
                "suspicious_activity_reporting": {"status": "compliant", "evidence": "automated_sar_generation"},
                "record_keeping": {"status": "compliant", "evidence": "retention_policies"},
                "compliance_program_maintenance": {"status": "compliant", "evidence": "regular_updates"}
            }
        }
        
        # Perform comprehensive compliance assessment
        compliance_assessment = await compliance_framework.assess_comprehensive_compliance(
            regulatory_requirements=mock_regulatory_requirements,
            current_status=current_compliance_status
        )
        
        # Verify assessment structure
        assert "overall_compliance_score" in compliance_assessment
        assert "regulation_scores" in compliance_assessment
        assert "compliance_gaps" in compliance_assessment
        assert "remediation_plan" in compliance_assessment
        assert "risk_assessment" in compliance_assessment
        
        # Verify overall compliance score
        overall_score = compliance_assessment["overall_compliance_score"]
        assert 0.0 <= overall_score <= 1.0
        
        # Verify regulation-specific scores
        regulation_scores = compliance_assessment["regulation_scores"]
        for regulation in mock_regulatory_requirements.keys():
            assert regulation in regulation_scores
            assert 0.0 <= regulation_scores[regulation] <= 1.0
        
        # Verify compliance gaps identification
        compliance_gaps = compliance_assessment["compliance_gaps"]
        assert len(compliance_gaps) > 0  # Should identify some gaps
        
        # Verify remediation plan
        remediation_plan = compliance_assessment["remediation_plan"]
        assert "immediate_actions" in remediation_plan
        assert "short_term_actions" in remediation_plan
        assert "long_term_actions" in remediation_plan
        
        # Verify high-priority gaps are identified
        high_priority_gaps = [gap for gap in compliance_gaps if gap["priority"] == "high"]
        assert len(high_priority_gaps) > 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_time_compliance_monitoring(self, compliance_framework):
        """Test real-time compliance monitoring for fintech operations"""
        
        # Start compliance monitoring
        await compliance_framework.start_compliance_monitoring()
        
        try:
            # Simulate fintech operational events
            operational_events = [
                {
                    "event_type": "data_access",
                    "user_id": "analyst_001",
                    "resource": "customer_pii_database",
                    "action": "read",
                    "timestamp": datetime.now(timezone.utc),
                    "compliance_context": ["GDPR", "PCI_DSS"]
                },
                {
                    "event_type": "transaction_processing",
                    "transaction_id": "txn_12345",
                    "amount": 50000,
                    "currency": "USD",
                    "timestamp": datetime.now(timezone.utc),
                    "compliance_context": ["BSA_AML", "PCI_DSS"]
                },
                {
                    "event_type": "model_inference",
                    "model_id": "fraud_detection_v2",
                    "data_processed": "transaction_batch_001",
                    "timestamp": datetime.now(timezone.utc),
                    "compliance_context": ["SOX", "GDPR"]
                },
                {
                    "event_type": "regulatory_report_generation",
                    "report_type": "SAR",
                    "generated_by": "compliance_agent_001",
                    "timestamp": datetime.now(timezone.utc),
                    "compliance_context": ["BSA_AML"]
                }
            ]
            
            # Process operational events for compliance
            compliance_violations = []
            for event in operational_events:
                violation_check = await compliance_framework.check_event_compliance(event)
                if violation_check["violations"]:
                    compliance_violations.extend(violation_check["violations"])
            
            # Verify compliance monitoring
            monitoring_status = await compliance_framework.get_monitoring_status()
            
            assert monitoring_status["is_active"] is True
            assert monitoring_status["events_processed"] == len(operational_events)
            assert "compliance_score" in monitoring_status
            
            # Verify violation detection (if any)
            if compliance_violations:
                for violation in compliance_violations:
                    assert "violation_type" in violation
                    assert "severity" in violation
                    assert "regulation" in violation
                    assert "remediation_required" in violation
            
        finally:
            await compliance_framework.stop_compliance_monitoring()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_audit_trail_generation(self, compliance_framework):
        """Test audit trail generation for compliance reporting"""
        
        # Mock fintech business activities requiring audit trails
        business_activities = [
            {
                "activity_id": "fraud_analysis_001",
                "activity_type": "fraud_detection",
                "user_id": "fraud_analyst_001",
                "timestamp": datetime.now(timezone.utc) - timedelta(hours=2),
                "details": {
                    "transactions_analyzed": 1000,
                    "fraud_alerts_generated": 5,
                    "ml_model_used": "isolation_forest_v2",
                    "confidence_threshold": 0.85
                },
                "compliance_requirements": ["SOX", "BSA_AML"]
            },
            {
                "activity_id": "compliance_check_001",
                "activity_type": "regulatory_compliance",
                "user_id": "compliance_officer_001",
                "timestamp": datetime.now(timezone.utc) - timedelta(hours=1),
                "details": {
                    "regulations_checked": ["SEC", "FINRA", "CFPB"],
                    "violations_found": 2,
                    "remediation_actions": ["update_policy", "staff_training"],
                    "completion_deadline": "2024-02-15"
                },
                "compliance_requirements": ["SOX", "PCI_DSS"]
            },
            {
                "activity_id": "kyc_verification_001",
                "activity_type": "customer_verification",
                "user_id": "kyc_specialist_001",
                "timestamp": datetime.now(timezone.utc) - timedelta(minutes=30),
                "details": {
                    "customer_id": "cust_12345",
                    "verification_level": "enhanced",
                    "documents_verified": ["identity", "address", "income"],
                    "risk_score": 0.25,
                    "approval_status": "approved"
                },
                "compliance_requirements": ["BSA_AML", "GDPR"]
            }
        ]
        
        # Generate audit trails
        audit_trails = []
        for activity in business_activities:
            audit_trail = await compliance_framework.generate_audit_trail(
                activity=activity,
                include_data_lineage=True,
                include_compliance_mapping=True
            )
            audit_trails.append(audit_trail)
        
        # Verify audit trail structure
        for audit_trail in audit_trails:
            assert "audit_id" in audit_trail
            assert "activity_summary" in audit_trail
            assert "compliance_mapping" in audit_trail
            assert "data_lineage" in audit_trail
            assert "integrity_hash" in audit_trail
            assert "timestamp" in audit_trail
            
            # Verify compliance mapping
            compliance_mapping = audit_trail["compliance_mapping"]
            assert len(compliance_mapping) > 0
            
            for regulation in compliance_mapping:
                assert "regulation_name" in regulation
                assert "requirements_met" in regulation
                assert "evidence_references" in regulation
            
            # Verify data lineage
            data_lineage = audit_trail["data_lineage"]
            assert "data_sources" in data_lineage
            assert "processing_steps" in data_lineage
            assert "output_destinations" in data_lineage
        
        # Test audit trail integrity verification
        for audit_trail in audit_trails:
            integrity_check = await compliance_framework.verify_audit_trail_integrity(
                audit_trail=audit_trail
            )
            
            assert integrity_check["is_valid"] is True
            assert integrity_check["hash_verified"] is True
            assert integrity_check["tampering_detected"] is False
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compliance_reporting_generation(self, compliance_framework):
        """Test compliance reporting for regulatory submissions"""
        
        # Mock compliance data for reporting period
        reporting_period = {
            "start_date": datetime.now(timezone.utc) - timedelta(days=90),
            "end_date": datetime.now(timezone.utc),
            "period_type": "quarterly"
        }
        
        compliance_data = {
            "fraud_detection_activities": {
                "total_transactions_monitored": 10_000_000,
                "fraud_alerts_generated": 1250,
                "false_positive_rate": 0.015,  # 1.5% (90% reduction achieved)
                "suspicious_activity_reports_filed": 45,
                "average_detection_time": 2.3  # seconds
            },
            "regulatory_compliance_activities": {
                "compliance_checks_performed": 500,
                "violations_identified": 12,
                "violations_remediated": 10,
                "policy_updates": 8,
                "staff_training_sessions": 15
            },
            "data_protection_activities": {
                "data_access_requests": 150,
                "data_portability_requests": 25,
                "data_erasure_requests": 18,
                "data_breach_incidents": 0,
                "privacy_impact_assessments": 5
            },
            "audit_activities": {
                "audit_trails_generated": 2500,
                "integrity_checks_performed": 2500,
                "integrity_failures": 0,
                "compliance_audits_completed": 3,
                "audit_findings": 8
            }
        }
        
        # Generate compliance reports for different regulations
        compliance_reports = {}
        
        regulations_to_report = ["PCI_DSS", "SOX", "GDPR", "BSA_AML"]
        
        for regulation in regulations_to_report:
            report = await compliance_framework.generate_compliance_report(
                regulation=regulation,
                reporting_period=reporting_period,
                compliance_data=compliance_data,
                include_executive_summary=True,
                include_detailed_findings=True,
                include_remediation_status=True
            )
            
            compliance_reports[regulation] = report
        
        # Verify compliance report structure
        for regulation, report in compliance_reports.items():
            assert "report_id" in report
            assert "regulation" in report
            assert "reporting_period" in report
            assert "executive_summary" in report
            assert "compliance_status" in report
            assert "detailed_findings" in report
            assert "remediation_status" in report
            assert "recommendations" in report
            
            # Verify executive summary
            executive_summary = report["executive_summary"]
            assert "overall_compliance_score" in executive_summary
            assert "key_achievements" in executive_summary
            assert "areas_for_improvement" in executive_summary
            
            # Verify compliance status
            compliance_status = report["compliance_status"]
            assert "current_status" in compliance_status
            assert "status_trend" in compliance_status
            assert "risk_level" in compliance_status
            
            # Verify detailed findings
            detailed_findings = report["detailed_findings"]
            assert "compliant_areas" in detailed_findings
            assert "non_compliant_areas" in detailed_findings
            assert "partially_compliant_areas" in detailed_findings
        
        # Test consolidated compliance dashboard report
        consolidated_report = await compliance_framework.generate_consolidated_compliance_report(
            reporting_period=reporting_period,
            regulations=regulations_to_report,
            compliance_data=compliance_data
        )
        
        # Verify consolidated report
        assert "overall_compliance_score" in consolidated_report
        assert "regulation_scores" in consolidated_report
        assert "compliance_trends" in consolidated_report
        assert "risk_assessment" in consolidated_report
        assert "strategic_recommendations" in consolidated_report
        
        # Verify overall compliance meets requirements
        overall_score = consolidated_report["overall_compliance_score"]
        assert overall_score >= 0.80, f"Overall compliance score {overall_score:.2f} should be >= 0.80"


class TestSecurityIncidentResponse:
    """Integration tests for security incident response"""
    
    @pytest.fixture
    def compliance_framework(self):
        """Create compliance framework for testing"""
        return SecurityComplianceFramework()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_incident_detection_and_response(self, compliance_framework):
        """Test security incident detection and automated response"""
        
        # Start security monitoring
        await compliance_framework.start_security_monitoring()
        
        try:
            # Simulate security incidents
            security_incidents = [
                {
                    "incident_type": "unauthorized_access_attempt",
                    "severity": "high",
                    "source_ip": "192.168.1.100",
                    "target_resource": "fraud_detection_model",
                    "user_id": "unknown",
                    "timestamp": datetime.now(timezone.utc),
                    "details": {
                        "failed_authentication_attempts": 5,
                        "access_method": "api_key",
                        "blocked_by_firewall": True
                    }
                },
                {
                    "incident_type": "data_exfiltration_attempt",
                    "severity": "critical",
                    "source_ip": "10.0.1.50",
                    "target_resource": "customer_pii_database",
                    "user_id": "compromised_analyst_002",
                    "timestamp": datetime.now(timezone.utc),
                    "details": {
                        "data_volume_attempted": "10GB",
                        "data_types": ["customer_ssn", "account_numbers"],
                        "blocked_by_dlp": True
                    }
                },
                {
                    "incident_type": "suspicious_model_behavior",
                    "severity": "medium",
                    "source_ip": "internal",
                    "target_resource": "risk_assessment_agent",
                    "user_id": "system",
                    "timestamp": datetime.now(timezone.utc),
                    "details": {
                        "anomalous_predictions": 150,
                        "confidence_score_drop": 0.25,
                        "potential_model_poisoning": True
                    }
                }
            ]
            
            # Process security incidents
            incident_responses = []
            for incident in security_incidents:
                response = await compliance_framework.process_security_incident(incident)
                incident_responses.append(response)
            
            # Verify incident response
            for i, response in enumerate(incident_responses):
                incident = security_incidents[i]
                
                assert "incident_id" in response
                assert "response_actions" in response
                assert "containment_status" in response
                assert "notification_sent" in response
                assert "escalation_required" in response
                
                # Verify appropriate response based on severity
                if incident["severity"] == "critical":
                    assert response["escalation_required"] is True
                    assert "immediate_containment" in response["response_actions"]
                    assert response["notification_sent"] is True
                
                elif incident["severity"] == "high":
                    assert "access_restriction" in response["response_actions"]
                    assert response["containment_status"] == "contained"
                
                elif incident["severity"] == "medium":
                    assert "monitoring_increased" in response["response_actions"]
            
            # Verify security monitoring status
            monitoring_status = await compliance_framework.get_security_monitoring_status()
            
            assert monitoring_status["incidents_processed"] == len(security_incidents)
            assert monitoring_status["critical_incidents"] == 1
            assert monitoring_status["high_severity_incidents"] == 1
            assert monitoring_status["medium_severity_incidents"] == 1
            
        finally:
            await compliance_framework.stop_security_monitoring()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
