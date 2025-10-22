"""
Unit Tests for Compliance Service
Tests regulatory compliance, audit trails, and GDPR compliance functionality.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from riskintel360.services.compliance_service import (
    ComplianceService, ComplianceStandard, DataClassification, ComplianceStatus,
    ComplianceViolation, DataRetentionPolicy, GDPRDataSubject, compliance_service
)
from riskintel360.auth.models import SecurityContext, ResourceType, User, Role, RoleType


class TestComplianceService:
    """Test compliance service functionality"""
    
    @pytest.fixture
    def compliance_service_instance(self):
        """Create compliance service instance for testing"""
        with patch('riskintel360.services.compliance_service.boto3'):
            service = ComplianceService()
            return service
    
    @pytest.fixture
    def mock_security_context(self):
        """Mock security context for testing"""
        mock_user = Mock(spec=User)
        mock_user.id = "test_user_123"
        mock_user.email = "test@example.com"
        
        mock_role = Mock(spec=Role)
        mock_role.role_type = RoleType.ANALYST
        mock_user.roles = [mock_role]
        
        context = Mock(spec=SecurityContext)
        context.user = mock_user
        context.tenant_id = "test_tenant"
        context.ip_address = "192.168.1.100"
        context.user_agent = "Test Agent"
        context.is_authenticated.return_value = True
        
        return context
    
    @pytest.fixture
    def sample_financial_data(self):
        """Sample financial data for testing"""
        return {
            "account_id": "ACC_123456",
            "balance": 50000.00,
            "transactions": [
                {
                    "id": "TXN_001",
                    "amount": 1000.00,
                    "date": "2024-01-15T10:30:00Z",
                    "type": "deposit",
                    "description": "Salary deposit"
                }
            ],
            "created_at": "2024-01-01T00:00:00Z",
            "user_id": "USER_789"
        }
    
    @pytest.fixture
    def sample_pii_data(self):
        """Sample PII data for testing"""
        return {
            "user_id": "USER_789",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "ssn": "123-45-6789",
            "date_of_birth": "1990-01-01",
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip": "10001"
            },
            "created_at": "2024-01-01T00:00:00Z"
        }
    
    @pytest.fixture
    def sample_payment_data(self):
        """Sample payment data for PCI DSS testing"""
        return {
            "payment_id": "PAY_123",
            "card_number": "4111111111111111",  # Test Visa number
            "cvv": "123",
            "expiry_date": "12/25",
            "amount": 100.00,
            "merchant": "Test Merchant"
        }
    
    @pytest.mark.asyncio
    async def test_validate_compliance_gdpr(self, compliance_service_instance, sample_pii_data, mock_security_context):
        """Test GDPR compliance validation"""
        result = await compliance_service_instance.validate_compliance(
            data=sample_pii_data,
            resource_type=ResourceType.CUSTOMER_DATA,
            standards=[ComplianceStandard.GDPR],
            security_context=mock_security_context
        )
        
        # Verify result structure
        assert "compliant" in result
        assert "violations" in result
        assert "warnings" in result
        assert "standards_checked" in result
        assert "timestamp" in result
        
        # Should check GDPR
        assert "gdpr" in result["standards_checked"]
        
        # Should detect PII fields without consent
        assert len(result["violations"]) > 0
        assert any("GDPR" in violation for violation in result["violations"])
        assert result["compliant"] is False
    
    @pytest.mark.asyncio
    async def test_validate_compliance_pci_dss(self, compliance_service_instance, sample_payment_data):
        """Test PCI DSS compliance validation"""
        result = await compliance_service_instance.validate_compliance(
            data=sample_payment_data,
            resource_type=ResourceType.FINANCIAL_DATA,
            standards=[ComplianceStandard.PCI_DSS]
        )
        
        # Should detect unencrypted card data
        assert result["compliant"] is False
        assert len(result["violations"]) > 0
        
        # Check for specific PCI DSS violations
        pci_violations = [v for v in result["violations"] if "PCI_DSS" in v]
        assert len(pci_violations) > 0
        
        # Should detect card number and CVV
        card_violations = [v for v in pci_violations if "card number" in v.lower()]
        cvv_violations = [v for v in pci_violations if "cvv" in v.lower()]
        
        assert len(card_violations) > 0 or len(cvv_violations) > 0
    
    @pytest.mark.asyncio
    async def test_validate_compliance_sox(self, compliance_service_instance, sample_financial_data):
        """Test SOX compliance validation"""
        # Test with missing required fields
        incomplete_data = {
            "balance": 50000.00,
            # Missing timestamp, user_id, approval_status
        }
        
        result = await compliance_service_instance.validate_compliance(
            data=incomplete_data,
            resource_type=ResourceType.FINANCIAL_DATA,
            standards=[ComplianceStandard.SOX]
        )
        
        # Should detect missing required fields
        assert result["compliant"] is False
        assert len(result["violations"]) > 0
        
        sox_violations = [v for v in result["violations"] if "SOX" in v]
        assert len(sox_violations) > 0
    
    @pytest.mark.asyncio
    async def test_validate_compliance_finra(self, compliance_service_instance):
        """Test FINRA compliance validation"""
        trade_data = {
            "trade_id": "TRADE_123",
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.00,
            "timestamp": "2024-01-15T10:30:00Z",
            "type": "buy"
        }
        
        result = await compliance_service_instance.validate_compliance(
            data=trade_data,
            resource_type=ResourceType.MARKET_DATA,
            standards=[ComplianceStandard.FINRA]
        )
        
        # FINRA validation should pass for complete trade data
        assert "finra" in result["standards_checked"]
        # May have warnings but should not have violations for complete data
        assert len(result["violations"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_compliance_multiple_standards(self, compliance_service_instance, sample_pii_data):
        """Test validation against multiple compliance standards"""
        result = await compliance_service_instance.validate_compliance(
            data=sample_pii_data,
            resource_type=ResourceType.CUSTOMER_DATA,
            standards=[ComplianceStandard.GDPR, ComplianceStandard.SOX, ComplianceStandard.FINRA]
        )
        
        # Should check all requested standards
        expected_standards = ["gdpr", "sox", "finra"]
        for standard in expected_standards:
            assert standard in result["standards_checked"]
        
        # Should have violations from GDPR (PII without consent)
        assert len(result["violations"]) > 0
        assert result["compliant"] is False
    
    @pytest.mark.asyncio
    async def test_record_compliance_violation(self, compliance_service_instance):
        """Test recording compliance violations"""
        violation_id = await compliance_service_instance.record_compliance_violation(
            standard=ComplianceStandard.GDPR,
            severity="HIGH",
            description="Personal data processed without consent",
            resource_type=ResourceType.CUSTOMER_DATA,
            resource_id="CUST_123",
            remediation_steps=["Obtain consent", "Update privacy policy"],
            remediation_deadline_days=30
        )
        
        # Verify violation was recorded
        assert violation_id is not None
        assert violation_id.startswith("viol_")
        
        # Check violation was added to internal list
        assert len(compliance_service_instance._violations) > 0
        
        violation = compliance_service_instance._violations[-1]
        assert violation.id == violation_id
        assert violation.standard == ComplianceStandard.GDPR
        assert violation.severity == "HIGH"
        assert violation.description == "Personal data processed without consent"
        assert violation.resource_type == ResourceType.CUSTOMER_DATA
        assert violation.resource_id == "CUST_123"
        assert violation.remediation_required is True  # HIGH severity
        assert len(violation.remediation_steps) == 2
    
    @pytest.mark.asyncio
    async def test_manage_gdpr_consent(self, compliance_service_instance):
        """Test GDPR consent management"""
        subject_id = "USER_123"
        email = "user@example.com"
        
        # Give consent
        await compliance_service_instance.manage_gdpr_consent(
            subject_id=subject_id,
            email=email,
            consent_given=True,
            data_categories=["personal", "financial"],
            processing_purposes=["service_provision", "analytics"]
        )
        
        # Verify consent was recorded
        assert subject_id in compliance_service_instance._gdpr_subjects
        
        subject = compliance_service_instance._gdpr_subjects[subject_id]
        assert subject.subject_id == subject_id
        assert subject.email == email
        assert subject.consent_given is True
        assert subject.consent_withdrawn is False
        assert subject.data_categories == ["personal", "financial"]
        assert subject.processing_purposes == ["service_provision", "analytics"]
        
        # Withdraw consent
        await compliance_service_instance.manage_gdpr_consent(
            subject_id=subject_id,
            consent_given=False
        )
        
        # Verify consent was withdrawn
        subject = compliance_service_instance._gdpr_subjects[subject_id]
        assert subject.consent_withdrawn is True
        assert subject.withdrawal_date is not None
    
    @pytest.mark.asyncio
    async def test_process_gdpr_data_access_request(self, compliance_service_instance, mock_security_context):
        """Test GDPR data access request processing"""
        subject_id = "USER_123"
        
        # First register the subject
        await compliance_service_instance.manage_gdpr_consent(
            subject_id=subject_id,
            email="user@example.com",
            consent_given=True
        )
        
        # Process access request
        result = await compliance_service_instance.process_gdpr_data_request(
            subject_id=subject_id,
            request_type="access",
            security_context=mock_security_context
        )
        
        # Verify result
        assert result["success"] is True
        assert result["request_type"] == "access"
        assert "data" in result
        assert "subject_info" in result["data"]
    
    @pytest.mark.asyncio
    async def test_process_gdpr_data_erasure_request(self, compliance_service_instance, mock_security_context):
        """Test GDPR data erasure request processing"""
        subject_id = "USER_123"
        
        # First register the subject
        await compliance_service_instance.manage_gdpr_consent(
            subject_id=subject_id,
            email="user@example.com",
            consent_given=True
        )
        
        # Process erasure request
        result = await compliance_service_instance.process_gdpr_data_request(
            subject_id=subject_id,
            request_type="erasure",
            security_context=mock_security_context
        )
        
        # Verify result
        assert result["success"] is True
        assert result["request_type"] == "erasure"
        
        # Verify consent was withdrawn
        subject = compliance_service_instance._gdpr_subjects[subject_id]
        assert subject.consent_withdrawn is True
    
    @pytest.mark.asyncio
    async def test_process_gdpr_unknown_subject(self, compliance_service_instance, mock_security_context):
        """Test GDPR request for unknown subject"""
        result = await compliance_service_instance.process_gdpr_data_request(
            subject_id="UNKNOWN_USER",
            request_type="access",
            security_context=mock_security_context
        )
        
        # Should return error for unknown subject
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_process_gdpr_invalid_request_type(self, compliance_service_instance, mock_security_context):
        """Test GDPR request with invalid request type"""
        subject_id = "USER_123"
        
        # Register subject
        await compliance_service_instance.manage_gdpr_consent(
            subject_id=subject_id,
            consent_given=True
        )
        
        # Process invalid request
        result = await compliance_service_instance.process_gdpr_data_request(
            subject_id=subject_id,
            request_type="invalid_type",
            security_context=mock_security_context
        )
        
        # Should return error for invalid request type
        assert result["success"] is False
        assert "unknown request type" in result["error"].lower()
    
    def test_default_retention_policies(self, compliance_service_instance):
        """Test default data retention policies"""
        policies = compliance_service_instance._retention_policies
        
        # Should have policies for key resource types
        assert ResourceType.FINANCIAL_DATA in policies
        assert ResourceType.CUSTOMER_DATA in policies
        assert ResourceType.AUDIT_LOG in policies
        assert ResourceType.MARKET_DATA in policies
        assert ResourceType.VALIDATION_REQUEST in policies
        
        # Check financial data policy (7 years for SOX/SEC)
        financial_policy = policies[ResourceType.FINANCIAL_DATA]
        assert financial_policy.retention_period_days == 7 * 365
        assert ComplianceStandard.SOX in financial_policy.compliance_standards
        assert ComplianceStandard.SEC in financial_policy.compliance_standards
        assert financial_policy.deletion_method == "SECURE_DELETE"
        
        # Check customer data policy (6 years for GDPR)
        customer_policy = policies[ResourceType.CUSTOMER_DATA]
        assert customer_policy.retention_period_days == 6 * 365
        assert ComplianceStandard.GDPR in customer_policy.compliance_standards
        assert customer_policy.deletion_method == "ANONYMIZE"
    
    @pytest.mark.asyncio
    async def test_gdpr_retention_validation(self, compliance_service_instance):
        """Test GDPR data retention validation"""
        # Create data that exceeds retention period
        old_data = {
            "user_id": "USER_123",
            "email": "user@example.com",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=7*365+1)).isoformat()  # Over 7 years old
        }
        
        result = await compliance_service_instance.validate_compliance(
            data=old_data,
            resource_type=ResourceType.CUSTOMER_DATA,
            standards=[ComplianceStandard.GDPR]
        )
        
        # Should detect retention period violation
        retention_violations = [v for v in result["violations"] if "retention period" in v.lower()]
        assert len(retention_violations) > 0
        assert result["compliant"] is False
    
    @pytest.mark.asyncio
    async def test_has_gdpr_consent_with_data(self, compliance_service_instance):
        """Test GDPR consent checking with consent data"""
        # Test data with consent information
        data_with_consent = {
            "user_id": "USER_123",
            "email": "user@example.com",
            "gdpr_consent": {
                "email": True,
                "phone": False,
                "all_fields": False
            }
        }
        
        # Should find consent for email field
        has_email_consent = compliance_service_instance._has_gdpr_consent(data_with_consent, "email")
        assert has_email_consent is True
        
        # Should not find consent for phone field
        has_phone_consent = compliance_service_instance._has_gdpr_consent(data_with_consent, "phone")
        assert has_phone_consent is False
    
    @pytest.mark.asyncio
    async def test_has_gdpr_consent_global(self, compliance_service_instance):
        """Test GDPR consent checking with global consent"""
        subject_id = "USER_123"
        
        # Register subject with consent
        await compliance_service_instance.manage_gdpr_consent(
            subject_id=subject_id,
            consent_given=True
        )
        
        data = {"user_id": subject_id, "email": "user@example.com"}
        
        # Should find global consent
        has_consent = compliance_service_instance._has_gdpr_consent(data, "email")
        assert has_consent is True
        
        # Withdraw consent
        await compliance_service_instance.manage_gdpr_consent(
            subject_id=subject_id,
            consent_given=False
        )
        
        # Should not find consent after withdrawal
        has_consent = compliance_service_instance._has_gdpr_consent(data, "email")
        assert has_consent is False
    
    @pytest.mark.asyncio
    async def test_get_compliance_report(self, compliance_service_instance):
        """Test compliance report generation"""
        # Record some test violations
        await compliance_service_instance.record_compliance_violation(
            standard=ComplianceStandard.GDPR,
            severity="HIGH",
            description="Test GDPR violation",
            resource_type=ResourceType.CUSTOMER_DATA
        )
        
        await compliance_service_instance.record_compliance_violation(
            standard=ComplianceStandard.PCI_DSS,
            severity="CRITICAL",
            description="Test PCI DSS violation",
            resource_type=ResourceType.FINANCIAL_DATA
        )
        
        # Generate report
        report = await compliance_service_instance.get_compliance_report(
            standards=[ComplianceStandard.GDPR, ComplianceStandard.PCI_DSS]
        )
        
        # Verify report structure
        assert "report_period" in report
        assert "standards_covered" in report
        assert "summary" in report
        assert "violations_by_standard" in report
        assert "generated_at" in report
        
        # Verify summary data
        summary = report["summary"]
        assert summary["total_violations"] == 2
        assert summary["critical_violations"] == 1
        assert "compliance_rate" in summary
        
        # Verify violations by standard
        violations_by_standard = report["violations_by_standard"]
        assert violations_by_standard["gdpr"] == 1
        assert violations_by_standard["pci_dss"] == 1
    
    @pytest.mark.asyncio
    async def test_compliance_validation_error_handling(self, compliance_service_instance):
        """Test compliance validation error handling"""
        # Test with invalid data that might cause errors
        invalid_data = {
            "created_at": "invalid_date_format"
        }
        
        result = await compliance_service_instance.validate_compliance(
            data=invalid_data,
            resource_type=ResourceType.CUSTOMER_DATA,
            standards=[ComplianceStandard.GDPR]
        )
        
        # Should handle errors gracefully
        assert "compliant" in result
        assert "violations" in result or "warnings" in result
    
    def test_compliance_standards_enum(self):
        """Test compliance standards enumeration"""
        # Verify all expected standards are available
        expected_standards = [
            "GDPR", "PCI_DSS", "SOX", "FINRA", "CFPB", "SEC", "BASEL_III", "MiFID_II"
        ]
        
        for standard_name in expected_standards:
            assert hasattr(ComplianceStandard, standard_name)
            standard = getattr(ComplianceStandard, standard_name)
            assert isinstance(standard, ComplianceStandard)
    
    def test_data_classification_enum(self):
        """Test data classification enumeration"""
        expected_classifications = [
            "PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED", "TOP_SECRET"
        ]
        
        for classification_name in expected_classifications:
            assert hasattr(DataClassification, classification_name)
    
    def test_compliance_status_enum(self):
        """Test compliance status enumeration"""
        expected_statuses = [
            "COMPLIANT", "NON_COMPLIANT", "PARTIALLY_COMPLIANT", 
            "UNDER_REVIEW", "REMEDIATION_REQUIRED"
        ]
        
        for status_name in expected_statuses:
            assert hasattr(ComplianceStatus, status_name)


class TestComplianceServiceAWSIntegration:
    """Test AWS integration functionality (mocked)"""
    
    @pytest.fixture
    def mock_dynamodb_client(self):
        """Mock DynamoDB client"""
        mock_client = Mock()
        mock_client.put_item.return_value = {}
        return mock_client
    
    @pytest.fixture
    def compliance_service_with_aws(self, mock_dynamodb_client):
        """Create compliance service with mocked AWS clients"""
        with patch('riskintel360.services.compliance_service.boto3') as mock_boto3:
            mock_boto3.client.return_value = mock_dynamodb_client
            
            service = ComplianceService()
            service._dynamodb_client = mock_dynamodb_client
            return service
    
    @pytest.mark.asyncio
    async def test_store_violation_in_dynamodb(self, compliance_service_with_aws, mock_dynamodb_client):
        """Test storing violations in DynamoDB"""
        violation_id = await compliance_service_with_aws.record_compliance_violation(
            standard=ComplianceStandard.GDPR,
            severity="HIGH",
            description="Test violation for DynamoDB storage",
            resource_type=ResourceType.CUSTOMER_DATA,
            resource_id="CUST_123"
        )
        
        # Verify DynamoDB put_item was called
        mock_dynamodb_client.put_item.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_dynamodb_client.put_item.call_args
        assert 'TableName' in call_args[1]
        assert 'Item' in call_args[1]
        
        item = call_args[1]['Item']
        assert item['id']['S'] == violation_id
        assert item['standard']['S'] == 'gdpr'
        assert item['severity']['S'] == 'HIGH'


@pytest.mark.asyncio
async def test_global_compliance_service_instance():
    """Test global compliance service instance"""
    # Test that global instance is accessible
    assert compliance_service is not None
    
    # Test basic functionality
    test_data = {"test": "data"}
    result = await compliance_service.validate_compliance(
        data=test_data,
        resource_type=ResourceType.VALIDATION_REQUEST,
        standards=[ComplianceStandard.GDPR]
    )
    
    assert "compliant" in result
    assert "violations" in result
    assert "warnings" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
