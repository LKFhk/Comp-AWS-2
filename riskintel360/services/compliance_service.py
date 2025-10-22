"""
Compliance Service for RiskIntel360 Platform
Handles regulatory compliance, audit trails, and GDPR compliance for fintech operations.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import boto3
from botocore.exceptions import ClientError

from riskintel360.config.settings import get_settings
from riskintel360.auth.models import SecurityContext, AuditAction, ResourceType
from riskintel360.auth.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class ComplianceStandard(Enum):
    """Supported compliance standards"""
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    SOX = "sox"
    FINRA = "finra"
    CFPB = "cfpb"
    SEC = "sec"
    BASEL_III = "basel_iii"
    MiFID_II = "mifid_ii"


class DataClassification(Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class ComplianceStatus(Enum):
    """Compliance status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNDER_REVIEW = "under_review"
    REMEDIATION_REQUIRED = "remediation_required"


@dataclass
class ComplianceViolation:
    """Compliance violation record"""
    id: str
    standard: ComplianceStandard
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    resource_type: ResourceType
    resource_id: Optional[str]
    detected_at: datetime
    remediation_required: bool
    remediation_deadline: Optional[datetime]
    remediation_steps: List[str]
    status: ComplianceStatus
    metadata: Dict[str, Any]


@dataclass
class DataRetentionPolicy:
    """Data retention policy"""
    resource_type: ResourceType
    retention_period_days: int
    deletion_method: str  # SECURE_DELETE, ANONYMIZE, ARCHIVE
    compliance_standards: List[ComplianceStandard]
    auto_delete: bool
    notification_before_deletion_days: int


@dataclass
class GDPRDataSubject:
    """GDPR data subject information"""
    subject_id: str
    email: Optional[str]
    consent_given: bool
    consent_date: Optional[datetime]
    consent_withdrawn: bool
    withdrawal_date: Optional[datetime]
    data_categories: List[str]
    processing_purposes: List[str]
    retention_period: Optional[int]


class ComplianceService:
    """Comprehensive compliance service for fintech regulations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.audit_logger = AuditLogger()
        
        # AWS clients
        self._s3_client = None
        self._dynamodb_client = None
        self._cloudtrail_client = None
        
        # Compliance data
        self._violations: List[ComplianceViolation] = []
        self._retention_policies: Dict[ResourceType, DataRetentionPolicy] = {}
        self._gdpr_subjects: Dict[str, GDPRDataSubject] = {}
        
        # Initialize AWS clients and policies
        self._initialize_aws_clients()
        self._initialize_default_retention_policies()
    
    def _initialize_aws_clients(self) -> None:
        """Initialize AWS clients for compliance services"""
        try:
            self._s3_client = boto3.client('s3')
            self._dynamodb_client = boto3.client('dynamodb')
            self._cloudtrail_client = boto3.client('cloudtrail')
            
            logger.info("Compliance service AWS clients initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
    
    def _initialize_default_retention_policies(self) -> None:
        """Initialize default data retention policies"""
        policies = [
            # Financial data - 7 years (SOX, SEC requirements)
            DataRetentionPolicy(
                resource_type=ResourceType.FINANCIAL_DATA,
                retention_period_days=7 * 365,  # 7 years
                deletion_method="SECURE_DELETE",
                compliance_standards=[ComplianceStandard.SOX, ComplianceStandard.SEC],
                auto_delete=False,  # Manual review required
                notification_before_deletion_days=90
            ),
            
            # Customer data - 6 years (GDPR allows longer for financial services)
            DataRetentionPolicy(
                resource_type=ResourceType.CUSTOMER_DATA,
                retention_period_days=6 * 365,
                deletion_method="ANONYMIZE",
                compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.FINRA],
                auto_delete=True,
                notification_before_deletion_days=30
            ),
            
            # Audit logs - 10 years (regulatory requirements)
            DataRetentionPolicy(
                resource_type=ResourceType.AUDIT_LOG,
                retention_period_days=10 * 365,
                deletion_method="ARCHIVE",
                compliance_standards=[ComplianceStandard.SOX, ComplianceStandard.FINRA],
                auto_delete=False,
                notification_before_deletion_days=180
            ),
            
            # Market data - 5 years (FINRA requirements)
            DataRetentionPolicy(
                resource_type=ResourceType.MARKET_DATA,
                retention_period_days=5 * 365,
                deletion_method="SECURE_DELETE",
                compliance_standards=[ComplianceStandard.FINRA, ComplianceStandard.SEC],
                auto_delete=True,
                notification_before_deletion_days=60
            ),
            
            # Validation requests - 3 years (business requirement)
            DataRetentionPolicy(
                resource_type=ResourceType.VALIDATION_REQUEST,
                retention_period_days=3 * 365,
                deletion_method="SECURE_DELETE",
                compliance_standards=[ComplianceStandard.GDPR],
                auto_delete=True,
                notification_before_deletion_days=30
            )
        ]
        
        for policy in policies:
            self._retention_policies[policy.resource_type] = policy
        
        logger.info(f"Initialized {len(policies)} default retention policies")
    
    async def validate_compliance(
        self,
        data: Dict[str, Any],
        resource_type: ResourceType,
        standards: List[ComplianceStandard] = None,
        security_context: Optional[SecurityContext] = None
    ) -> Dict[str, Any]:
        """Validate data compliance against specified standards"""
        if standards is None:
            standards = [ComplianceStandard.GDPR, ComplianceStandard.FINRA, ComplianceStandard.SOX]
        
        validation_result = {
            "compliant": True,
            "violations": [],
            "warnings": [],
            "standards_checked": [s.value for s in standards],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            for standard in standards:
                if standard == ComplianceStandard.GDPR:
                    await self._validate_gdpr_compliance(data, resource_type, validation_result)
                elif standard == ComplianceStandard.PCI_DSS:
                    await self._validate_pci_dss_compliance(data, validation_result)
                elif standard == ComplianceStandard.SOX:
                    await self._validate_sox_compliance(data, resource_type, validation_result)
                elif standard == ComplianceStandard.FINRA:
                    await self._validate_finra_compliance(data, resource_type, validation_result)
                elif standard == ComplianceStandard.SEC:
                    await self._validate_sec_compliance(data, resource_type, validation_result)
            
            # Log compliance validation
            if security_context:
                await self.audit_logger.log_action(
                    security_context=security_context,
                    action=AuditAction.COMPLIANCE_CHECK,
                    resource_type=resource_type,
                    success=validation_result["compliant"],
                    metadata={
                        "standards": [s.value for s in standards],
                        "violations_count": len(validation_result["violations"])
                    }
                )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Compliance validation failed: {e}")
            validation_result["compliant"] = False
            validation_result["violations"].append(f"Validation error: {str(e)}")
            return validation_result
    
    async def _validate_gdpr_compliance(
        self,
        data: Dict[str, Any],
        resource_type: ResourceType,
        result: Dict[str, Any]
    ) -> None:
        """Validate GDPR compliance"""
        # Check for personal data without proper consent
        personal_data_fields = [
            'email', 'phone', 'address', 'name', 'first_name', 'last_name',
            'date_of_birth', 'ssn', 'passport', 'license', 'ip_address'
        ]
        
        def check_personal_data(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check if field contains personal data
                    if any(pd_field in key.lower() for pd_field in personal_data_fields):
                        # Check if consent is documented
                        if not self._has_gdpr_consent(data, key):
                            result["violations"].append(
                                f"GDPR: Personal data field '{current_path}' without documented consent"
                            )
                            result["compliant"] = False
                    
                    if isinstance(value, (dict, list)):
                        check_personal_data(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_personal_data(item, f"{path}[{i}]")
        
        check_personal_data(data)
        
        # Check data retention compliance
        retention_policy = self._retention_policies.get(resource_type)
        if retention_policy and ComplianceStandard.GDPR in retention_policy.compliance_standards:
            # Check if data is within retention period
            if 'created_at' in data:
                try:
                    created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
                    retention_deadline = created_at + timedelta(days=retention_policy.retention_period_days)
                    
                    if datetime.now(timezone.utc) > retention_deadline:
                        result["violations"].append(
                            f"GDPR: Data exceeds retention period of {retention_policy.retention_period_days} days"
                        )
                        result["compliant"] = False
                except Exception as e:
                    result["warnings"].append(f"GDPR: Could not validate retention period: {e}")
    
    def _has_gdpr_consent(self, data: Dict[str, Any], field: str) -> bool:
        """Check if GDPR consent exists for personal data field"""
        # Check if consent is documented in the data
        consent_fields = ['consent', 'gdpr_consent', 'data_consent', 'privacy_consent']
        
        for consent_field in consent_fields:
            if consent_field in data:
                consent_data = data[consent_field]
                if isinstance(consent_data, dict):
                    return consent_data.get(field, False) or consent_data.get('all_fields', False)
                elif isinstance(consent_data, bool):
                    return consent_data
        
        # Check if user has global consent
        user_id = data.get('user_id')
        if user_id and user_id in self._gdpr_subjects:
            subject = self._gdpr_subjects[user_id]
            return subject.consent_given and not subject.consent_withdrawn
        
        return False
    
    async def _validate_pci_dss_compliance(
        self,
        data: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """Validate PCI DSS compliance for payment card data"""
        import re
        
        # Credit card number patterns
        card_patterns = {
            'visa': r'\b4[0-9]{12}(?:[0-9]{3})?\b',
            'mastercard': r'\b5[1-5][0-9]{14}\b',
            'amex': r'\b3[47][0-9]{13}\b',
            'discover': r'\b6(?:011|5[0-9]{2})[0-9]{12}\b'
        }
        
        data_str = json.dumps(data)
        
        for card_type, pattern in card_patterns.items():
            if re.search(pattern, data_str):
                result["violations"].append(
                    f"PCI_DSS: Unencrypted {card_type} card number detected"
                )
                result["compliant"] = False
        
        # Check for CVV codes
        cvv_pattern = r'\b[0-9]{3,4}\b'
        if 'cvv' in data_str.lower() and re.search(cvv_pattern, data_str):
            result["violations"].append("PCI_DSS: CVV code detected - must not be stored")
            result["compliant"] = False
    
    async def _validate_sox_compliance(
        self,
        data: Dict[str, Any],
        resource_type: ResourceType,
        result: Dict[str, Any]
    ) -> None:
        """Validate SOX compliance for financial data"""
        # Check for financial data that requires SOX controls
        if resource_type == ResourceType.FINANCIAL_DATA:
            required_fields = ['timestamp', 'user_id', 'approval_status']
            
            for field in required_fields:
                if field not in data:
                    result["violations"].append(
                        f"SOX: Required field '{field}' missing for financial data"
                    )
                    result["compliant"] = False
            
            # Check for proper approval workflow
            if 'approval_status' in data and data['approval_status'] not in ['approved', 'pending', 'rejected']:
                result["violations"].append("SOX: Invalid approval status for financial data")
                result["compliant"] = False
    
    async def _validate_finra_compliance(
        self,
        data: Dict[str, Any],
        resource_type: ResourceType,
        result: Dict[str, Any]
    ) -> None:
        """Validate FINRA compliance for securities data"""
        if resource_type in [ResourceType.MARKET_DATA, ResourceType.COMPETITIVE_INTEL]:
            # Check for required trade reporting fields
            if 'trade' in json.dumps(data).lower():
                required_fields = ['timestamp', 'symbol', 'quantity', 'price']
                
                for field in required_fields:
                    if field not in data:
                        result["warnings"].append(
                            f"FINRA: Recommended field '{field}' missing for trade data"
                        )
    
    async def _validate_sec_compliance(
        self,
        data: Dict[str, Any],
        resource_type: ResourceType,
        result: Dict[str, Any]
    ) -> None:
        """Validate SEC compliance for securities filings"""
        if resource_type == ResourceType.FINANCIAL_DATA:
            # Check for material information disclosure requirements
            material_keywords = ['earnings', 'revenue', 'profit', 'loss', 'merger', 'acquisition']
            data_str = json.dumps(data).lower()
            
            for keyword in material_keywords:
                if keyword in data_str:
                    if 'disclosure_date' not in data:
                        result["warnings"].append(
                            f"SEC: Material information '{keyword}' may require disclosure date"
                        )
    
    async def record_compliance_violation(
        self,
        standard: ComplianceStandard,
        severity: str,
        description: str,
        resource_type: ResourceType,
        resource_id: Optional[str] = None,
        remediation_steps: List[str] = None,
        remediation_deadline_days: int = 30
    ) -> str:
        """Record a compliance violation"""
        violation_id = f"viol_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._violations)}"
        
        violation = ComplianceViolation(
            id=violation_id,
            standard=standard,
            severity=severity,
            description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            detected_at=datetime.now(timezone.utc),
            remediation_required=severity in ['HIGH', 'CRITICAL'],
            remediation_deadline=datetime.now(timezone.utc) + timedelta(days=remediation_deadline_days),
            remediation_steps=remediation_steps or [],
            status=ComplianceStatus.REMEDIATION_REQUIRED,
            metadata={}
        )
        
        self._violations.append(violation)
        
        # Log violation
        logger.warning(f"Compliance violation recorded: {violation_id} - {description}")
        
        # Store in persistent storage if available
        await self._store_violation(violation)
        
        return violation_id
    
    async def _store_violation(self, violation: ComplianceViolation) -> None:
        """Store violation in persistent storage"""
        if not self._dynamodb_client:
            return
        
        try:
            table_name = f"riskintel360-compliance-violations-{self.settings.environment.value}"
            
            item = {
                'id': {'S': violation.id},
                'standard': {'S': violation.standard.value},
                'severity': {'S': violation.severity},
                'description': {'S': violation.description},
                'resource_type': {'S': violation.resource_type.value},
                'detected_at': {'S': violation.detected_at.isoformat()},
                'status': {'S': violation.status.value},
                'remediation_required': {'BOOL': violation.remediation_required}
            }
            
            if violation.resource_id:
                item['resource_id'] = {'S': violation.resource_id}
            
            if violation.remediation_deadline:
                item['remediation_deadline'] = {'S': violation.remediation_deadline.isoformat()}
            
            if violation.remediation_steps:
                item['remediation_steps'] = {'SS': violation.remediation_steps}
            
            self._dynamodb_client.put_item(
                TableName=table_name,
                Item=item
            )
            
        except Exception as e:
            logger.error(f"Failed to store violation: {e}")
    
    async def manage_gdpr_consent(
        self,
        subject_id: str,
        email: Optional[str] = None,
        consent_given: bool = True,
        data_categories: List[str] = None,
        processing_purposes: List[str] = None
    ) -> None:
        """Manage GDPR consent for data subjects"""
        if subject_id in self._gdpr_subjects:
            subject = self._gdpr_subjects[subject_id]
            
            if consent_given and subject.consent_withdrawn:
                # Re-consent after withdrawal
                subject.consent_given = True
                subject.consent_date = datetime.now(timezone.utc)
                subject.consent_withdrawn = False
                subject.withdrawal_date = None
            elif not consent_given and subject.consent_given:
                # Withdraw consent
                subject.consent_withdrawn = True
                subject.withdrawal_date = datetime.now(timezone.utc)
        else:
            # New subject
            subject = GDPRDataSubject(
                subject_id=subject_id,
                email=email,
                consent_given=consent_given,
                consent_date=datetime.now(timezone.utc) if consent_given else None,
                consent_withdrawn=False,
                withdrawal_date=None,
                data_categories=data_categories or [],
                processing_purposes=processing_purposes or [],
                retention_period=None
            )
            
            self._gdpr_subjects[subject_id] = subject
        
        logger.info(f"GDPR consent updated for subject {subject_id}: {consent_given}")
    
    async def process_gdpr_data_request(
        self,
        subject_id: str,
        request_type: str,  # 'access', 'rectification', 'erasure', 'portability'
        security_context: SecurityContext
    ) -> Dict[str, Any]:
        """Process GDPR data subject requests"""
        try:
            if subject_id not in self._gdpr_subjects:
                return {
                    "success": False,
                    "error": "Data subject not found",
                    "request_type": request_type
                }
            
            subject = self._gdpr_subjects[subject_id]
            
            if request_type == 'access':
                # Right to access - provide all data
                result = await self._process_data_access_request(subject)
            elif request_type == 'rectification':
                # Right to rectification - allow data correction
                result = await self._process_data_rectification_request(subject)
            elif request_type == 'erasure':
                # Right to erasure (right to be forgotten)
                result = await self._process_data_erasure_request(subject)
            elif request_type == 'portability':
                # Right to data portability
                result = await self._process_data_portability_request(subject)
            else:
                return {
                    "success": False,
                    "error": f"Unknown request type: {request_type}",
                    "request_type": request_type
                }
            
            # Log GDPR request
            await self.audit_logger.log_action(
                security_context=security_context,
                action=AuditAction.GDPR_REQUEST,
                resource_type=ResourceType.CUSTOMER_DATA,
                resource_id=subject_id,
                success=result["success"],
                metadata={
                    "request_type": request_type,
                    "subject_email": subject.email
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"GDPR request processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "request_type": request_type
            }
    
    async def _process_data_access_request(self, subject: GDPRDataSubject) -> Dict[str, Any]:
        """Process data access request"""
        # In a real implementation, this would query all systems for the subject's data
        return {
            "success": True,
            "request_type": "access",
            "data": {
                "subject_info": asdict(subject),
                "note": "Complete data export would be generated from all systems"
            }
        }
    
    async def _process_data_rectification_request(self, subject: GDPRDataSubject) -> Dict[str, Any]:
        """Process data rectification request"""
        return {
            "success": True,
            "request_type": "rectification",
            "message": "Data rectification process initiated - manual review required"
        }
    
    async def _process_data_erasure_request(self, subject: GDPRDataSubject) -> Dict[str, Any]:
        """Process data erasure request (right to be forgotten)"""
        # Mark for deletion
        subject.consent_withdrawn = True
        subject.withdrawal_date = datetime.now(timezone.utc)
        
        return {
            "success": True,
            "request_type": "erasure",
            "message": "Data erasure process initiated - will be completed within 30 days"
        }
    
    async def _process_data_portability_request(self, subject: GDPRDataSubject) -> Dict[str, Any]:
        """Process data portability request"""
        return {
            "success": True,
            "request_type": "portability",
            "data_format": "JSON",
            "message": "Portable data export will be provided within 30 days"
        }
    
    async def get_compliance_report(
        self,
        standards: List[ComplianceStandard] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        if standards is None:
            standards = list(ComplianceStandard)
        
        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        
        # Filter violations by date range
        filtered_violations = [
            v for v in self._violations
            if start_date <= v.detected_at <= end_date
        ]
        
        # Group violations by standard
        violations_by_standard = {}
        for standard in standards:
            violations_by_standard[standard.value] = [
                v for v in filtered_violations if v.standard == standard
            ]
        
        # Calculate compliance metrics
        total_violations = len(filtered_violations)
        critical_violations = len([v for v in filtered_violations if v.severity == 'CRITICAL'])
        resolved_violations = len([v for v in filtered_violations if v.status == ComplianceStatus.COMPLIANT])
        
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "standards_covered": [s.value for s in standards],
            "summary": {
                "total_violations": total_violations,
                "critical_violations": critical_violations,
                "resolved_violations": resolved_violations,
                "compliance_rate": (1 - (total_violations - resolved_violations) / max(total_violations, 1)) * 100
            },
            "violations_by_standard": {
                standard: len(violations) for standard, violations in violations_by_standard.items()
            },
            "gdpr_subjects": len(self._gdpr_subjects),
            "retention_policies": len(self._retention_policies),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }


# Global compliance service instance
compliance_service = ComplianceService()