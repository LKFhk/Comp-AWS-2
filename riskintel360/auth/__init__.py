"""
Authentication and Authorization Module for RiskIntel360 Platform
Provides OAuth 2.0, role-based access control, and audit trail functionality.
"""

from .cognito_client import CognitoClient
from .auth_decorators import require_auth, require_role, audit_trail
from .models import User, Role, Permission, AuditLogEntry
from .rbac import RoleBasedAccessControl
from .multi_tenant import MultiTenantManager

__all__ = [
    "CognitoClient",
    "require_auth",
    "require_role", 
    "audit_trail",
    "User",
    "Role",
    "Permission",
    "AuditLogEntry",
    "RoleBasedAccessControl",
    "MultiTenantManager",
]
