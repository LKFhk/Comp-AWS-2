"""
Security and Compliance Framework for RiskIntel360

This module provides security and compliance monitoring capabilities
for financial services applications.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    """Compliance status levels"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"
    UNKNOWN = "unknown"


class SecurityEventType(Enum):
    """Types of security events"""
    ACCESS_VIOLATION = "access_violation"
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    COMPLIANCE_VIOLATION = "compliance_violation"


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_id: str
    event_type: SecurityEventType
    timestamp: datetime
    severity: str  # "low", "medium", "high", "critical"
    description: str
    source: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditTrail:
    """Audit trail entry"""
    audit_id: str
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    result: str  # "success", "failure", "denied"
    details: Dict[str, Any] = field(default_factory=dict)


class EncryptionManager:
    """Manages encryption for sensitive data"""
    
    def __init__(self):
        self.encryption_enabled = True
        logger.info("EncryptionManager initialized")
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        # In a real implementation, this would use proper encryption
        # For testing purposes, we'll just return a mock encrypted value
        return f"encrypted_{hash(data)}"
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        # Mock decryption for testing
        if encrypted_data.startswith("encrypted_"):
            return "decrypted_data"
        return encrypted_data


class AccessControlManager:
    """Manages access control and permissions"""
    
    def __init__(self):
        self.permissions: Dict[str, List[str]] = {}
        logger.info("AccessControlManager initialized")
    
    def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """Check if user has permission for action on resource"""
        user_permissions = self.permissions.get(user_id, [])
        required_permission = f"{resource}:{action}"
        return required_permission in user_permissions or "admin:*" in user_permissions
    
    def grant_permission(self, user_id: str, resource: str, action: str):
        """Grant permission to user"""
        if user_id not in self.permissions:
            self.permissions[user_id] = []
        
        permission = f"{resource}:{action}"
        if permission not in self.permissions[user_id]:
            self.permissions[user_id].append(permission)


class SecurityComplianceFramework:
    """Main security and compliance framework"""
    
    def __init__(self):
        self.encryption_manager = EncryptionManager()
        self.access_control_manager = AccessControlManager()
        self.security_events: List[SecurityEvent] = []
        self.audit_trail: List[AuditTrail] = []
        self.compliance_rules: Dict[str, Any] = {}
        
        logger.info("SecurityComplianceFramework initialized")
    
    def record_security_event(self, event: SecurityEvent):
        """Record a security event"""
        self.security_events.append(event)
        logger.warning(f"Security event recorded: {event.event_type.value} - {event.description}")
    
    def add_audit_entry(self, entry: AuditTrail):
        """Add entry to audit trail"""
        self.audit_trail.append(entry)
        logger.info(f"Audit entry added: {entry.action} on {entry.resource} by {entry.user_id}")
    
    def check_compliance(self, rule_name: str, data: Dict[str, Any]) -> ComplianceStatus:
        """Check compliance against a specific rule"""
        # Mock compliance checking for testing
        if rule_name in self.compliance_rules:
            rule = self.compliance_rules[rule_name]
            # Simple mock logic
            if rule.get("always_compliant", False):
                return ComplianceStatus.COMPLIANT
            elif rule.get("always_non_compliant", False):
                return ComplianceStatus.NON_COMPLIANT
            else:
                return ComplianceStatus.REQUIRES_REVIEW
        
        return ComplianceStatus.UNKNOWN
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security and compliance summary"""
        return {
            "total_security_events": len(self.security_events),
            "recent_events": len([
                e for e in self.security_events 
                if (datetime.now(timezone.utc) - e.timestamp).days < 7
            ]),
            "audit_entries": len(self.audit_trail),
            "compliance_rules": len(self.compliance_rules),
            "encryption_enabled": self.encryption_manager.encryption_enabled
        }


# Global instance
_security_framework: Optional[SecurityComplianceFramework] = None


def get_security_compliance_framework() -> SecurityComplianceFramework:
    """Get the global security compliance framework instance"""
    global _security_framework
    
    if _security_framework is None:
        _security_framework = SecurityComplianceFramework()
    
    return _security_framework