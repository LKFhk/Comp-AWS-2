"""
Security Service for RiskIntel360 Platform
Handles encryption, data protection, and security monitoring for fintech data.
"""

import os
import json
import hashlib
import hmac
import base64
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import boto3
from botocore.exceptions import ClientError

from riskintel360.config.settings import get_settings
from riskintel360.auth.models import SecurityContext, AuditAction, ResourceType

logger = logging.getLogger(__name__)


@dataclass
class EncryptionResult:
    """Result of encryption operation"""
    encrypted_data: str
    encryption_key_id: str
    algorithm: str
    timestamp: datetime
    checksum: str


@dataclass
class SecurityEvent:
    """Security event for monitoring"""
    event_id: str
    event_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    source: str
    timestamp: datetime
    details: Dict[str, Any]
    user_id: Optional[str] = None
    ip_address: Optional[str] = None


class SecurityService:
    """Comprehensive security service for fintech data protection"""
    
    def __init__(self):
        self.settings = get_settings()
        self._kms_client = None
        self._cloudtrail_client = None
        self._cloudwatch_client = None
        self._secrets_manager_client = None
        
        # Initialize encryption
        self._master_key = self._get_master_key()
        self._cipher_suite = self._initialize_encryption()
        
        # Initialize AWS clients
        self._initialize_aws_clients()
        
        # Security monitoring
        self._security_events: List[SecurityEvent] = []
        self._threat_indicators: Dict[str, int] = {}
    
    def _get_master_key(self) -> str:
        """Get master encryption key from environment or AWS Secrets Manager"""
        # Try environment variable first (for development)
        master_key = os.getenv('RISKINTEL360_MASTER_KEY')
        if master_key:
            return master_key
        
        # Try AWS Secrets Manager (for production)
        try:
            if self._secrets_manager_client:
                response = self._secrets_manager_client.get_secret_value(
                    SecretId=f"riskintel360/{self.settings.environment.value}/master-key"
                )
                return response['SecretString']
        except Exception as e:
            logger.warning(f"Could not retrieve master key from Secrets Manager: {e}")
        
        # Fallback to default (development only)
        logger.warning("Using default master key - NOT SECURE FOR PRODUCTION")
        return "default-dev-key-change-in-production-immediately"
    
    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption cipher with PBKDF2 key derivation"""
        # Use PBKDF2 to derive encryption key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'riskintel360_fintech_salt_v1',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._master_key.encode()))
        return Fernet(key)
    
    def _initialize_aws_clients(self) -> None:
        """Initialize AWS clients for security services"""
        try:
            # KMS for key management
            self._kms_client = boto3.client('kms')
            
            # CloudTrail for audit logging
            self._cloudtrail_client = boto3.client('cloudtrail')
            
            # CloudWatch for security monitoring
            self._cloudwatch_client = boto3.client('cloudwatch')
            
            # Secrets Manager for secure credential storage
            self._secrets_manager_client = boto3.client('secretsmanager')
            
            logger.info("Security service AWS clients initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            # Continue without AWS clients for local development
    
    async def encrypt_sensitive_data(
        self,
        data: Union[str, Dict[str, Any]],
        data_classification: str = "CONFIDENTIAL",
        use_aws_kms: bool = True
    ) -> EncryptionResult:
        """Encrypt sensitive fintech data with multiple layers of protection"""
        try:
            # Convert data to string if needed
            if isinstance(data, dict):
                data_str = json.dumps(data, sort_keys=True)
            else:
                data_str = str(data)
            
            # Generate checksum for integrity verification
            checksum = hashlib.sha256(data_str.encode()).hexdigest()
            
            if use_aws_kms and self._kms_client:
                # Use AWS KMS for encryption (production)
                encrypted_data, key_id = await self._encrypt_with_kms(data_str, data_classification)
                algorithm = "AWS_KMS_AES256"
            else:
                # Use local encryption (development)
                encrypted_data = self._cipher_suite.encrypt(data_str.encode()).decode()
                key_id = "local_fernet_key"
                algorithm = "FERNET_AES128"
            
            result = EncryptionResult(
                encrypted_data=encrypted_data,
                encryption_key_id=key_id,
                algorithm=algorithm,
                timestamp=datetime.now(timezone.utc),
                checksum=checksum
            )
            
            # Log security event
            await self._log_security_event(
                event_type="DATA_ENCRYPTION",
                severity="LOW",
                source="security_service",
                details={
                    "data_classification": data_classification,
                    "algorithm": algorithm,
                    "data_size": len(data_str)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            await self._log_security_event(
                event_type="ENCRYPTION_FAILURE",
                severity="HIGH",
                source="security_service",
                details={"error": str(e)}
            )
            raise
    
    async def decrypt_sensitive_data(
        self,
        encryption_result: EncryptionResult,
        verify_integrity: bool = True
    ) -> Union[str, Dict[str, Any]]:
        """Decrypt sensitive fintech data with integrity verification"""
        try:
            if encryption_result.algorithm == "AWS_KMS_AES256":
                # Decrypt with AWS KMS
                decrypted_data = await self._decrypt_with_kms(
                    encryption_result.encrypted_data,
                    encryption_result.encryption_key_id
                )
            else:
                # Decrypt with local cipher
                decrypted_data = self._cipher_suite.decrypt(
                    encryption_result.encrypted_data.encode()
                ).decode()
            
            # Verify integrity if requested
            if verify_integrity:
                current_checksum = hashlib.sha256(decrypted_data.encode()).hexdigest()
                if current_checksum != encryption_result.checksum:
                    raise ValueError("Data integrity check failed - possible tampering")
            
            # Try to parse as JSON, return as string if not valid JSON
            try:
                return json.loads(decrypted_data)
            except json.JSONDecodeError:
                return decrypted_data
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            await self._log_security_event(
                event_type="DECRYPTION_FAILURE",
                severity="HIGH",
                source="security_service",
                details={"error": str(e)}
            )
            raise
    
    async def _encrypt_with_kms(self, data: str, data_classification: str) -> tuple[str, str]:
        """Encrypt data using AWS KMS"""
        try:
            # Get or create KMS key for data classification
            key_id = await self._get_kms_key_for_classification(data_classification)
            
            # Encrypt with KMS
            response = self._kms_client.encrypt(
                KeyId=key_id,
                Plaintext=data.encode(),
                EncryptionContext={
                    'service': 'riskintel360',
                    'classification': data_classification,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Return base64 encoded ciphertext and key ID
            encrypted_data = base64.b64encode(response['CiphertextBlob']).decode()
            return encrypted_data, response['KeyId']
            
        except ClientError as e:
            logger.error(f"KMS encryption failed: {e}")
            raise
    
    async def _decrypt_with_kms(self, encrypted_data: str, key_id: str) -> str:
        """Decrypt data using AWS KMS"""
        try:
            # Decode base64 ciphertext
            ciphertext_blob = base64.b64decode(encrypted_data.encode())
            
            # Decrypt with KMS
            response = self._kms_client.decrypt(
                CiphertextBlob=ciphertext_blob
            )
            
            return response['Plaintext'].decode()
            
        except ClientError as e:
            logger.error(f"KMS decryption failed: {e}")
            raise
    
    async def _get_kms_key_for_classification(self, data_classification: str) -> str:
        """Get or create KMS key for data classification"""
        key_alias = f"alias/riskintel360-{data_classification.lower()}-{self.settings.environment.value}"
        
        try:
            # Try to describe the key (check if it exists)
            response = self._kms_client.describe_key(KeyId=key_alias)
            return response['KeyMetadata']['KeyId']
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NotFoundException':
                # Create new key
                return await self._create_kms_key(data_classification)
            else:
                raise
    
    async def _create_kms_key(self, data_classification: str) -> str:
        """Create new KMS key for data classification"""
        try:
            # Create KMS key
            response = self._kms_client.create_key(
                Description=f"RiskIntel360 {data_classification} data encryption key",
                Usage='ENCRYPT_DECRYPT',
                KeySpec='SYMMETRIC_DEFAULT',
                Tags=[
                    {'TagKey': 'Service', 'TagValue': 'RiskIntel360'},
                    {'TagKey': 'Classification', 'TagValue': data_classification},
                    {'TagKey': 'Environment', 'TagValue': self.settings.environment.value}
                ]
            )
            
            key_id = response['KeyMetadata']['KeyId']
            
            # Create alias
            key_alias = f"alias/riskintel360-{data_classification.lower()}-{self.settings.environment.value}"
            self._kms_client.create_alias(
                AliasName=key_alias,
                TargetKeyId=key_id
            )
            
            logger.info(f"Created KMS key for {data_classification}: {key_id}")
            return key_id
            
        except ClientError as e:
            logger.error(f"Failed to create KMS key: {e}")
            raise
    
    async def hash_sensitive_data(
        self,
        data: str,
        salt: Optional[str] = None,
        algorithm: str = "SHA256"
    ) -> Dict[str, str]:
        """Hash sensitive data for secure storage (passwords, PII)"""
        try:
            # Generate salt if not provided
            if not salt:
                salt = base64.b64encode(os.urandom(32)).decode()
            
            # Create hash based on algorithm
            if algorithm == "SHA256":
                hash_obj = hashlib.sha256()
            elif algorithm == "SHA512":
                hash_obj = hashlib.sha512()
            else:
                raise ValueError(f"Unsupported hash algorithm: {algorithm}")
            
            # Hash data with salt
            hash_obj.update(salt.encode())
            hash_obj.update(data.encode())
            hashed_data = hash_obj.hexdigest()
            
            return {
                "hash": hashed_data,
                "salt": salt,
                "algorithm": algorithm,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Hashing failed: {e}")
            raise
    
    async def verify_hash(
        self,
        data: str,
        hash_info: Dict[str, str]
    ) -> bool:
        """Verify hashed data"""
        try:
            # Recreate hash with same parameters
            new_hash_info = await self.hash_sensitive_data(
                data=data,
                salt=hash_info["salt"],
                algorithm=hash_info["algorithm"]
            )
            
            # Compare hashes using constant-time comparison
            return hmac.compare_digest(hash_info["hash"], new_hash_info["hash"])
            
        except Exception as e:
            logger.error(f"Hash verification failed: {e}")
            return False
    
    async def sanitize_input(
        self,
        input_data: Union[str, Dict[str, Any]],
        strict_mode: bool = True
    ) -> Union[str, Dict[str, Any]]:
        """Sanitize input data to prevent injection attacks"""
        try:
            if isinstance(input_data, str):
                return self._sanitize_string(input_data, strict_mode)
            elif isinstance(input_data, dict):
                return {
                    key: await self.sanitize_input(value, strict_mode)
                    for key, value in input_data.items()
                }
            elif isinstance(input_data, list):
                return [
                    await self.sanitize_input(item, strict_mode)
                    for item in input_data
                ]
            else:
                return input_data
                
        except Exception as e:
            logger.error(f"Input sanitization failed: {e}")
            # Return empty string/dict on sanitization failure for security
            return "" if isinstance(input_data, str) else {}
    
    def _sanitize_string(self, input_str: str, strict_mode: bool = True) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            return str(input_str)
        
        # Remove null bytes
        sanitized = input_str.replace('\x00', '')
        
        if strict_mode:
            # Remove potentially dangerous characters
            dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')', '{', '}']
            for char in dangerous_chars:
                sanitized = sanitized.replace(char, '')
            
            # Remove SQL injection patterns
            sql_patterns = [
                'DROP TABLE', 'DELETE FROM', 'INSERT INTO', 'UPDATE SET',
                'UNION SELECT', 'OR 1=1', 'AND 1=1', '--', '/*', '*/',
                'xp_cmdshell', 'sp_executesql'
            ]
            
            for pattern in sql_patterns:
                sanitized = sanitized.replace(pattern.upper(), '')
                sanitized = sanitized.replace(pattern.lower(), '')
            
            # Remove XSS patterns
            xss_patterns = [
                'javascript:', 'vbscript:', 'onload=', 'onerror=', 'onclick=',
                'onmouseover=', 'onfocus=', 'onblur=', 'onchange=', 'onsubmit='
            ]
            
            for pattern in xss_patterns:
                sanitized = sanitized.replace(pattern.upper(), '')
                sanitized = sanitized.replace(pattern.lower(), '')
            
            # Remove command injection patterns
            cmd_patterns = [
                'rm -rf', 'del /f', 'format c:', 'shutdown', 'reboot',
                'wget', 'curl', 'nc -l', 'netcat', 'ping -c', 'ps aux',
                'kill -9', 'chmod 777', 'sudo', 'su -'
            ]
            
            for pattern in cmd_patterns:
                sanitized = sanitized.replace(pattern.upper(), '')
                sanitized = sanitized.replace(pattern.lower(), '')
        
        # Limit length to prevent DoS
        max_length = 10000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            logger.warning(f"Input truncated to {max_length} characters")
        
        return sanitized.strip()
    
    async def validate_fintech_data_compliance(
        self,
        data: Dict[str, Any],
        compliance_standards: List[str] = None
    ) -> Dict[str, Any]:
        """Validate fintech data for compliance with regulations"""
        if compliance_standards is None:
            compliance_standards = ["PCI_DSS", "GDPR", "SOX", "FINRA"]
        
        validation_results = {
            "compliant": True,
            "violations": [],
            "warnings": [],
            "standards_checked": compliance_standards
        }
        
        try:
            for standard in compliance_standards:
                if standard == "PCI_DSS":
                    await self._validate_pci_dss_compliance(data, validation_results)
                elif standard == "GDPR":
                    await self._validate_gdpr_compliance(data, validation_results)
                elif standard == "SOX":
                    await self._validate_sox_compliance(data, validation_results)
                elif standard == "FINRA":
                    await self._validate_finra_compliance(data, validation_results)
            
            # Log compliance check
            await self._log_security_event(
                event_type="COMPLIANCE_CHECK",
                severity="LOW" if validation_results["compliant"] else "MEDIUM",
                source="security_service",
                details={
                    "standards": compliance_standards,
                    "compliant": validation_results["compliant"],
                    "violations_count": len(validation_results["violations"])
                }
            )
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Compliance validation failed: {e}")
            validation_results["compliant"] = False
            validation_results["violations"].append(f"Validation error: {str(e)}")
            return validation_results
    
    async def _validate_pci_dss_compliance(
        self,
        data: Dict[str, Any],
        results: Dict[str, Any]
    ) -> None:
        """Validate PCI DSS compliance for payment card data"""
        # Check for credit card numbers (basic pattern matching)
        card_patterns = [
            r'\b4[0-9]{12}(?:[0-9]{3})?\b',  # Visa
            r'\b5[1-5][0-9]{14}\b',          # MasterCard
            r'\b3[47][0-9]{13}\b',           # American Express
            r'\b6(?:011|5[0-9]{2})[0-9]{12}\b'  # Discover
        ]
        
        import re
        data_str = json.dumps(data)
        
        for pattern in card_patterns:
            if re.search(pattern, data_str):
                results["compliant"] = False
                results["violations"].append("PCI_DSS: Unencrypted payment card data detected")
                break
    
    async def _validate_gdpr_compliance(
        self,
        data: Dict[str, Any],
        results: Dict[str, Any]
    ) -> None:
        """Validate GDPR compliance for personal data"""
        # Check for PII fields
        pii_fields = [
            'email', 'phone', 'address', 'ssn', 'passport', 'license',
            'first_name', 'last_name', 'full_name', 'date_of_birth'
        ]
        
        def check_dict(d, path=""):
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, dict):
                    check_dict(value, current_path)
                elif any(pii_field in key.lower() for pii_field in pii_fields):
                    results["warnings"].append(f"GDPR: PII field detected at {current_path}")
        
        check_dict(data)
    
    async def _validate_sox_compliance(
        self,
        data: Dict[str, Any],
        results: Dict[str, Any]
    ) -> None:
        """Validate SOX compliance for financial data"""
        # Check for financial data that requires SOX controls
        financial_fields = [
            'revenue', 'profit', 'loss', 'assets', 'liabilities', 'equity',
            'financial_statement', 'balance_sheet', 'income_statement'
        ]
        
        data_str = json.dumps(data).lower()
        
        for field in financial_fields:
            if field in data_str:
                results["warnings"].append(f"SOX: Financial data detected - ensure proper controls")
                break
    
    async def _validate_finra_compliance(
        self,
        data: Dict[str, Any],
        results: Dict[str, Any]
    ) -> None:
        """Validate FINRA compliance for securities data"""
        # Check for securities-related data
        securities_fields = [
            'stock', 'bond', 'security', 'trade', 'portfolio', 'investment',
            'broker', 'dealer', 'commission', 'markup'
        ]
        
        data_str = json.dumps(data).lower()
        
        for field in securities_fields:
            if field in data_str:
                results["warnings"].append(f"FINRA: Securities data detected - ensure compliance")
                break
    
    async def _log_security_event(
        self,
        event_type: str,
        severity: str,
        source: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Log security event for monitoring"""
        try:
            event = SecurityEvent(
                event_id=f"sec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}",
                event_type=event_type,
                severity=severity,
                source=source,
                timestamp=datetime.now(timezone.utc),
                details=details,
                user_id=user_id,
                ip_address=ip_address
            )
            
            # Store event
            self._security_events.append(event)
            
            # Log to application logger
            logger.info(f"SECURITY_EVENT: {event.event_type} - {event.severity} - {json.dumps(event.details)}")
            
            # Send to CloudWatch if available
            if self._cloudwatch_client:
                await self._send_security_metrics(event)
            
            # Update threat indicators
            self._update_threat_indicators(event)
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    async def _send_security_metrics(self, event: SecurityEvent) -> None:
        """Send security metrics to CloudWatch"""
        try:
            metrics = [
                {
                    'MetricName': 'SecurityEvents',
                    'Dimensions': [
                        {'Name': 'EventType', 'Value': event.event_type},
                        {'Name': 'Severity', 'Value': event.severity},
                        {'Name': 'Source', 'Value': event.source}
                    ],
                    'Value': 1.0,
                    'Unit': 'Count',
                    'Timestamp': event.timestamp
                }
            ]
            
            self._cloudwatch_client.put_metric_data(
                Namespace='RiskIntel360/Security',
                MetricData=metrics
            )
            
        except Exception as e:
            logger.error(f"Failed to send security metrics: {e}")
    
    def _update_threat_indicators(self, event: SecurityEvent) -> None:
        """Update threat indicators based on security events"""
        # Increment threat indicator for event type
        self._threat_indicators[event.event_type] = self._threat_indicators.get(event.event_type, 0) + 1
        
        # Check for threat patterns
        if event.event_type in ["ENCRYPTION_FAILURE", "DECRYPTION_FAILURE"]:
            if self._threat_indicators.get(event.event_type, 0) > 5:
                logger.warning(f"High number of {event.event_type} events detected - possible attack")
    
    async def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary and metrics"""
        try:
            # Calculate metrics from recent events (last 24 hours)
            recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_events = [e for e in self._security_events if e.timestamp > recent_cutoff]
            
            # Group by severity
            severity_counts = {}
            event_type_counts = {}
            
            for event in recent_events:
                severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1
                event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
            
            return {
                "total_events_24h": len(recent_events),
                "severity_breakdown": severity_counts,
                "event_type_breakdown": event_type_counts,
                "threat_indicators": self._threat_indicators.copy(),
                "encryption_status": "ACTIVE",
                "compliance_checks": "ENABLED",
                "aws_integration": {
                    "kms": self._kms_client is not None,
                    "cloudtrail": self._cloudtrail_client is not None,
                    "cloudwatch": self._cloudwatch_client is not None,
                    "secrets_manager": self._secrets_manager_client is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate security summary: {e}")
            return {"error": str(e)}


# Global security service instance
security_service = SecurityService()