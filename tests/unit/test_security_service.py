"""
Unit Tests for Security Service
Tests encryption, data protection, and security monitoring functionality.
"""

import pytest
import json
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from cryptography.fernet import Fernet

from riskintel360.services.security_service import (
    SecurityService, EncryptionResult, SecurityEvent, security_service
)


class TestSecurityService:
    """Test security service functionality"""
    
    @pytest.fixture
    def security_service_instance(self):
        """Create security service instance for testing"""
        with patch('riskintel360.services.security_service.boto3'):
            service = SecurityService()
            return service
    
    @pytest.fixture
    def sample_sensitive_data(self):
        """Sample sensitive fintech data for testing"""
        return {
            "customer_id": "CUST_12345",
            "account_number": "ACC_987654321",
            "balance": 150000.50,
            "transactions": [
                {"amount": 1000.00, "date": "2024-01-15", "type": "deposit"},
                {"amount": -250.00, "date": "2024-01-16", "type": "withdrawal"}
            ],
            "risk_score": 0.75,
            "compliance_flags": ["KYC_VERIFIED", "AML_CLEARED"]
        }
    
    @pytest.fixture
    def sample_pii_data(self):
        """Sample PII data for testing"""
        return {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "ssn": "123-45-6789",
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip": "10001"
            }
        }
    
    @pytest.mark.asyncio
    async def test_encrypt_sensitive_data_local(self, security_service_instance, sample_sensitive_data):
        """Test local encryption of sensitive data"""
        # Test encryption without AWS KMS
        result = await security_service_instance.encrypt_sensitive_data(
            data=sample_sensitive_data,
            data_classification="CONFIDENTIAL",
            use_aws_kms=False
        )
        
        # Verify encryption result
        assert isinstance(result, EncryptionResult)
        assert result.encrypted_data != json.dumps(sample_sensitive_data)
        assert result.algorithm == "FERNET_AES128"
        assert result.encryption_key_id == "local_fernet_key"
        assert len(result.checksum) == 64  # SHA256 hex digest
        assert isinstance(result.timestamp, datetime)
        
        # Verify encrypted data is not empty and different from original
        assert len(result.encrypted_data) > 0
        assert result.encrypted_data != str(sample_sensitive_data)
    
    @pytest.mark.asyncio
    async def test_decrypt_sensitive_data_local(self, security_service_instance, sample_sensitive_data):
        """Test local decryption of sensitive data"""
        # First encrypt the data
        encryption_result = await security_service_instance.encrypt_sensitive_data(
            data=sample_sensitive_data,
            use_aws_kms=False
        )
        
        # Then decrypt it
        decrypted_data = await security_service_instance.decrypt_sensitive_data(
            encryption_result=encryption_result,
            verify_integrity=True
        )
        
        # Verify decryption
        assert decrypted_data == sample_sensitive_data
    
    @pytest.mark.asyncio
    async def test_encrypt_decrypt_string_data(self, security_service_instance):
        """Test encryption/decryption of string data"""
        test_string = "This is sensitive financial information"
        
        # Encrypt string
        encryption_result = await security_service_instance.encrypt_sensitive_data(
            data=test_string,
            use_aws_kms=False
        )
        
        # Decrypt string
        decrypted_string = await security_service_instance.decrypt_sensitive_data(
            encryption_result=encryption_result
        )
        
        assert decrypted_string == test_string
    
    @pytest.mark.asyncio
    async def test_encryption_integrity_verification(self, security_service_instance, sample_sensitive_data):
        """Test encryption integrity verification"""
        # Encrypt data
        encryption_result = await security_service_instance.encrypt_sensitive_data(
            data=sample_sensitive_data,
            use_aws_kms=False
        )
        
        # Tamper with checksum
        tampered_result = EncryptionResult(
            encrypted_data=encryption_result.encrypted_data,
            encryption_key_id=encryption_result.encryption_key_id,
            algorithm=encryption_result.algorithm,
            timestamp=encryption_result.timestamp,
            checksum="tampered_checksum"
        )
        
        # Decryption should fail with integrity check
        with pytest.raises(ValueError, match="Data integrity check failed"):
            await security_service_instance.decrypt_sensitive_data(
                encryption_result=tampered_result,
                verify_integrity=True
            )
    
    @pytest.mark.asyncio
    async def test_hash_sensitive_data(self, security_service_instance):
        """Test hashing of sensitive data"""
        test_password = "SecurePassword123!"
        
        # Hash password
        hash_result = await security_service_instance.hash_sensitive_data(
            data=test_password,
            algorithm="SHA256"
        )
        
        # Verify hash result structure
        assert "hash" in hash_result
        assert "salt" in hash_result
        assert "algorithm" in hash_result
        assert "timestamp" in hash_result
        
        assert hash_result["algorithm"] == "SHA256"
        assert len(hash_result["hash"]) == 64  # SHA256 hex digest
        assert len(hash_result["salt"]) > 0
        
        # Hash should be different from original
        assert hash_result["hash"] != test_password
    
    @pytest.mark.asyncio
    async def test_verify_hash(self, security_service_instance):
        """Test hash verification"""
        test_password = "SecurePassword123!"
        
        # Hash password
        hash_result = await security_service_instance.hash_sensitive_data(
            data=test_password
        )
        
        # Verify correct password
        is_valid = await security_service_instance.verify_hash(
            data=test_password,
            hash_info=hash_result
        )
        assert is_valid is True
        
        # Verify incorrect password
        is_valid = await security_service_instance.verify_hash(
            data="WrongPassword",
            hash_info=hash_result
        )
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_sanitize_input_string(self, security_service_instance):
        """Test input sanitization for strings"""
        # Test XSS prevention
        xss_input = "<script>alert('xss')</script>"
        sanitized = await security_service_instance.sanitize_input(xss_input, strict_mode=True)
        assert "<script>" not in sanitized
        assert "alert(" not in sanitized
        
        # Test SQL injection prevention
        sql_input = "'; DROP TABLE users; --"
        sanitized = await security_service_instance.sanitize_input(sql_input, strict_mode=True)
        assert "DROP TABLE" not in sanitized
        assert "--" not in sanitized
        
        # Test command injection prevention
        cmd_input = "; rm -rf /"
        sanitized = await security_service_instance.sanitize_input(cmd_input, strict_mode=True)
        assert "rm -rf" not in sanitized
        
        # Test legitimate input preservation
        legitimate_input = "This is a legitimate business concept"
        sanitized = await security_service_instance.sanitize_input(legitimate_input, strict_mode=True)
        assert sanitized == legitimate_input
    
    @pytest.mark.asyncio
    async def test_sanitize_input_dict(self, security_service_instance):
        """Test input sanitization for dictionaries"""
        malicious_dict = {
            "business_concept": "<script>alert('xss')</script>",
            "target_market": "'; DROP TABLE users; --",
            "legitimate_field": "This is safe content",
            "nested": {
                "malicious": "javascript:alert('xss')",
                "safe": "Safe nested content"
            }
        }
        
        sanitized = await security_service_instance.sanitize_input(malicious_dict, strict_mode=True)
        
        # Check that malicious content is removed
        assert "<script>" not in sanitized["business_concept"]
        assert "DROP TABLE" not in sanitized["target_market"]
        assert "javascript:" not in sanitized["nested"]["malicious"]
        
        # Check that legitimate content is preserved
        assert sanitized["legitimate_field"] == "This is safe content"
        assert sanitized["nested"]["safe"] == "Safe nested content"
    
    @pytest.mark.asyncio
    async def test_validate_fintech_data_compliance(self, security_service_instance, sample_pii_data):
        """Test fintech data compliance validation"""
        # Test compliance validation
        result = await security_service_instance.validate_fintech_data_compliance(
            data=sample_pii_data,
            compliance_standards=["PCI_DSS", "GDPR", "SOX"]
        )
        
        # Verify result structure
        assert "compliant" in result
        assert "violations" in result
        assert "warnings" in result
        assert "standards_checked" in result
        
        assert isinstance(result["compliant"], bool)
        assert isinstance(result["violations"], list)
        assert isinstance(result["warnings"], list)
        assert result["standards_checked"] == ["PCI_DSS", "GDPR", "SOX"]
    
    @pytest.mark.asyncio
    async def test_pci_dss_validation(self, security_service_instance):
        """Test PCI DSS compliance validation"""
        # Test data with credit card number
        card_data = {
            "payment_info": {
                "card_number": "4111111111111111",  # Test Visa number
                "expiry": "12/25"
            }
        }
        
        result = await security_service_instance.validate_fintech_data_compliance(
            data=card_data,
            compliance_standards=["PCI_DSS"]
        )
        
        # Should detect unencrypted card data
        assert result["compliant"] is False
        assert any("PCI_DSS" in violation for violation in result["violations"])
    
    @pytest.mark.asyncio
    async def test_gdpr_validation(self, security_service_instance, sample_pii_data):
        """Test GDPR compliance validation"""
        result = await security_service_instance.validate_fintech_data_compliance(
            data=sample_pii_data,
            compliance_standards=["GDPR"]
        )
        
        # Should detect PII fields
        assert len(result["warnings"]) > 0
        assert any("GDPR" in warning for warning in result["warnings"])
    
    @pytest.mark.asyncio
    async def test_security_event_logging(self, security_service_instance):
        """Test security event logging"""
        # Log a security event
        await security_service_instance._log_security_event(
            event_type="TEST_EVENT",
            severity="MEDIUM",
            source="unit_test",
            details={"test": "data"},
            user_id="test_user",
            ip_address="192.168.1.100"
        )
        
        # Verify event was logged
        assert len(security_service_instance._security_events) > 0
        
        latest_event = security_service_instance._security_events[-1]
        assert latest_event.event_type == "TEST_EVENT"
        assert latest_event.severity == "MEDIUM"
        assert latest_event.source == "unit_test"
        assert latest_event.user_id == "test_user"
        assert latest_event.ip_address == "192.168.1.100"
        assert latest_event.details == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_threat_indicator_tracking(self, security_service_instance):
        """Test threat indicator tracking"""
        # Log multiple security events of same type
        for i in range(3):
            await security_service_instance._log_security_event(
                event_type="ENCRYPTION_FAILURE",
                severity="HIGH",
                source="unit_test",
                details={"attempt": i}
            )
        
        # Check threat indicators
        assert "ENCRYPTION_FAILURE" in security_service_instance._threat_indicators
        assert security_service_instance._threat_indicators["ENCRYPTION_FAILURE"] == 3
    
    @pytest.mark.asyncio
    async def test_get_security_summary(self, security_service_instance):
        """Test security summary generation"""
        # Log some test events
        await security_service_instance._log_security_event(
            event_type="DATA_ENCRYPTION",
            severity="LOW",
            source="unit_test",
            details={}
        )
        
        await security_service_instance._log_security_event(
            event_type="COMPLIANCE_CHECK",
            severity="MEDIUM",
            source="unit_test",
            details={}
        )
        
        # Get security summary
        summary = await security_service_instance.get_security_summary()
        
        # Verify summary structure
        assert "total_events_24h" in summary
        assert "severity_breakdown" in summary
        assert "event_type_breakdown" in summary
        assert "threat_indicators" in summary
        assert "encryption_status" in summary
        assert "compliance_checks" in summary
        assert "aws_integration" in summary
        
        # Verify data
        assert summary["encryption_status"] == "ACTIVE"
        assert summary["compliance_checks"] == "ENABLED"
        assert isinstance(summary["total_events_24h"], int)
        assert isinstance(summary["severity_breakdown"], dict)
        assert isinstance(summary["event_type_breakdown"], dict)
    
    @pytest.mark.asyncio
    async def test_encryption_error_handling(self, security_service_instance):
        """Test encryption error handling"""
        # Test with invalid data type that might cause issues
        with patch.object(security_service_instance._cipher_suite, 'encrypt', side_effect=Exception("Encryption failed")):
            with pytest.raises(Exception, match="Encryption failed"):
                await security_service_instance.encrypt_sensitive_data(
                    data="test data",
                    use_aws_kms=False
                )
        
        # Verify security event was logged
        events = security_service_instance._security_events
        encryption_failure_events = [e for e in events if e.event_type == "ENCRYPTION_FAILURE"]
        assert len(encryption_failure_events) > 0
    
    @pytest.mark.asyncio
    async def test_decryption_error_handling(self, security_service_instance):
        """Test decryption error handling"""
        # Create invalid encryption result
        invalid_result = EncryptionResult(
            encrypted_data="invalid_encrypted_data",
            encryption_key_id="test_key",
            algorithm="FERNET_AES128",
            timestamp=datetime.now(timezone.utc),
            checksum="test_checksum"
        )
        
        # Decryption should fail and log security event
        with pytest.raises(Exception):
            await security_service_instance.decrypt_sensitive_data(invalid_result)
        
        # Verify security event was logged
        events = security_service_instance._security_events
        decryption_failure_events = [e for e in events if e.event_type == "DECRYPTION_FAILURE"]
        assert len(decryption_failure_events) > 0
    
    def test_sanitize_string_length_limit(self, security_service_instance):
        """Test string sanitization length limit"""
        # Create very long string
        long_string = "A" * 15000  # Exceeds 10000 character limit
        
        sanitized = security_service_instance._sanitize_string(long_string, strict_mode=True)
        
        # Should be truncated to max length
        assert len(sanitized) <= 10000
    
    def test_sanitize_non_string_input(self, security_service_instance):
        """Test sanitization of non-string input"""
        # Test with number
        result = security_service_instance._sanitize_string(12345, strict_mode=True)
        assert result == "12345"
        
        # Test with None
        result = security_service_instance._sanitize_string(None, strict_mode=True)
        assert result == "None"
    
    @pytest.mark.asyncio
    async def test_hash_different_algorithms(self, security_service_instance):
        """Test hashing with different algorithms"""
        test_data = "test_password"
        
        # Test SHA256
        sha256_result = await security_service_instance.hash_sensitive_data(
            data=test_data,
            algorithm="SHA256"
        )
        assert sha256_result["algorithm"] == "SHA256"
        assert len(sha256_result["hash"]) == 64
        
        # Test SHA512
        sha512_result = await security_service_instance.hash_sensitive_data(
            data=test_data,
            algorithm="SHA512"
        )
        assert sha512_result["algorithm"] == "SHA512"
        assert len(sha512_result["hash"]) == 128
        
        # Hashes should be different
        assert sha256_result["hash"] != sha512_result["hash"]
    
    @pytest.mark.asyncio
    async def test_hash_unsupported_algorithm(self, security_service_instance):
        """Test hashing with unsupported algorithm"""
        with pytest.raises(ValueError, match="Unsupported hash algorithm"):
            await security_service_instance.hash_sensitive_data(
                data="test",
                algorithm="UNSUPPORTED"
            )
    
    @pytest.mark.asyncio
    async def test_sanitize_input_list(self, security_service_instance):
        """Test input sanitization for lists"""
        malicious_list = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "Legitimate content",
            {
                "nested_malicious": "javascript:alert('xss')",
                "nested_safe": "Safe content"
            }
        ]
        
        sanitized = await security_service_instance.sanitize_input(malicious_list, strict_mode=True)
        
        # Check that malicious content is removed
        assert "<script>" not in sanitized[0]
        assert "DROP TABLE" not in sanitized[1]
        assert "javascript:" not in sanitized[3]["nested_malicious"]
        
        # Check that legitimate content is preserved
        assert sanitized[2] == "Legitimate content"
        assert sanitized[3]["nested_safe"] == "Safe content"


class TestSecurityServiceAWSIntegration:
    """Test AWS integration functionality (mocked)"""
    
    @pytest.fixture
    def mock_kms_client(self):
        """Mock KMS client"""
        mock_client = Mock()
        mock_client.encrypt.return_value = {
            'CiphertextBlob': b'encrypted_data',
            'KeyId': 'test-key-id'
        }
        mock_client.decrypt.return_value = {
            'Plaintext': b'decrypted_data'
        }
        mock_client.describe_key.return_value = {
            'KeyMetadata': {'KeyId': 'existing-key-id'}
        }
        return mock_client
    
    @pytest.fixture
    def security_service_with_aws(self, mock_kms_client):
        """Create security service with mocked AWS clients"""
        with patch('riskintel360.services.security_service.boto3') as mock_boto3:
            mock_boto3.client.return_value = mock_kms_client
            
            service = SecurityService()
            service._kms_client = mock_kms_client
            return service
    
    @pytest.mark.asyncio
    async def test_encrypt_with_kms(self, security_service_with_aws, mock_kms_client):
        """Test encryption with AWS KMS"""
        test_data = "sensitive financial data"
        
        # Mock KMS encryption
        mock_kms_client.encrypt.return_value = {
            'CiphertextBlob': b'mock_encrypted_data',
            'KeyId': 'arn:aws:kms:us-east-1:123456789012:key/test-key-id'
        }
        
        result = await security_service_with_aws.encrypt_sensitive_data(
            data=test_data,
            data_classification="CONFIDENTIAL",
            use_aws_kms=True
        )
        
        # Verify KMS was called
        mock_kms_client.encrypt.assert_called_once()
        
        # Verify result
        assert result.algorithm == "AWS_KMS_AES256"
        assert result.encryption_key_id == 'arn:aws:kms:us-east-1:123456789012:key/test-key-id'
    
    @pytest.mark.asyncio
    async def test_decrypt_with_kms(self, security_service_with_aws, mock_kms_client):
        """Test decryption with AWS KMS"""
        # Create encryption result that would come from KMS
        encryption_result = EncryptionResult(
            encrypted_data="bW9ja19lbmNyeXB0ZWRfZGF0YQ==",  # base64 encoded
            encryption_key_id="test-key-id",
            algorithm="AWS_KMS_AES256",
            timestamp=datetime.now(timezone.utc),
            checksum="test_checksum"
        )
        
        # Mock KMS decryption
        mock_kms_client.decrypt.return_value = {
            'Plaintext': b'decrypted test data'
        }
        
        result = await security_service_with_aws.decrypt_sensitive_data(
            encryption_result=encryption_result,
            verify_integrity=False  # Skip integrity check for this test
        )
        
        # Verify KMS was called
        mock_kms_client.decrypt.assert_called_once()
        
        # Verify result
        assert result == "decrypted test data"


@pytest.mark.asyncio
async def test_global_security_service_instance():
    """Test global security service instance"""
    # Test that global instance is accessible
    assert security_service is not None
    
    # Test basic functionality
    test_data = "test encryption"
    result = await security_service.encrypt_sensitive_data(
        data=test_data,
        use_aws_kms=False
    )
    
    assert isinstance(result, EncryptionResult)
    assert result.encrypted_data != test_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
