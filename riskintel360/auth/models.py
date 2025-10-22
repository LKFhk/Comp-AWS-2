"""
Authentication and Authorization Data Models
Defines user, role, permission, and audit models for the platform.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from dataclasses import dataclass


class UserStatus(str, Enum):
    """User account status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class RoleType(str, Enum):
    """Role type enumeration"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_USER = "api_user"


class PermissionType(str, Enum):
    """Permission type enumeration"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class ResourceType(str, Enum):
    """Resource type enumeration"""
    VALIDATION_REQUEST = "validation_request"
    MARKET_DATA = "market_data"
    COMPETITIVE_INTEL = "competitive_intel"
    FINANCIAL_DATA = "financial_data"
    RISK_ASSESSMENT = "risk_assessment"
    CUSTOMER_DATA = "customer_data"
    REPORTS = "reports"
    USER_MANAGEMENT = "user_management"
    SYSTEM_CONFIG = "system_config"
    AUDIT_LOG = "audit_log"


class AuditAction(str, Enum):
    """Audit action enumeration"""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    SHARE = "share"
    ACCESS_DENIED = "access_denied"
    COMPLIANCE_CHECK = "compliance_check"
    GDPR_REQUEST = "gdpr_request"
    SECURITY_INCIDENT = "security_incident"


class Permission(BaseModel):
    """Permission model for role-based access control"""
    id: str = Field(..., description="Unique permission identifier")
    name: str = Field(..., description="Permission name")
    resource_type: ResourceType = Field(..., description="Resource type this permission applies to")
    permission_type: PermissionType = Field(..., description="Type of permission")
    description: Optional[str] = Field(None, description="Permission description")
    
    model_config = ConfigDict(use_enum_values=True)
    
    def __hash__(self):
        return hash((self.id, self.resource_type, self.permission_type))
    
    def __eq__(self, other):
        if not isinstance(other, Permission):
            return False
        return (self.id == other.id and 
                self.resource_type == other.resource_type and 
                self.permission_type == other.permission_type)


class Role(BaseModel):
    """Role model for role-based access control"""
    id: str = Field(..., description="Unique role identifier")
    name: str = Field(..., description="Role name")
    role_type: RoleType = Field(..., description="Role type")
    description: Optional[str] = Field(None, description="Role description")
    permissions: List[Permission] = Field(default_factory=list, description="Role permissions")
    is_active: bool = Field(True, description="Whether role is active")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    
    model_config = ConfigDict(use_enum_values=True)


class User(BaseModel):
    """User model for authentication and authorization"""
    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    tenant_id: str = Field(..., description="Tenant identifier for multi-tenancy")
    roles: List[Role] = Field(default_factory=list, description="User roles")
    status: UserStatus = Field(UserStatus.ACTIVE, description="User account status")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional user metadata")
    
    model_config = ConfigDict(use_enum_values=True)
    
    def has_permission(self, resource_type: ResourceType, permission_type: PermissionType) -> bool:
        """Check if user has specific permission"""
        for role in self.roles:
            if not role.is_active:
                continue
            for permission in role.permissions:
                if (permission.resource_type == resource_type and 
                    permission.permission_type == permission_type):
                    return True
                # Admin permission grants all access
                if permission.permission_type == PermissionType.ADMIN:
                    return True
        return False
    
    def has_role(self, role_type: RoleType) -> bool:
        """Check if user has specific role"""
        return any(role.role_type == role_type and role.is_active for role in self.roles)


class AuditLogEntry(BaseModel):
    """Audit log entry model for compliance tracking"""
    id: str = Field(..., description="Unique audit log entry identifier")
    user_id: str = Field(..., description="User who performed the action")
    tenant_id: str = Field(..., description="Tenant identifier")
    action: AuditAction = Field(..., description="Action performed")
    resource_type: ResourceType = Field(..., description="Resource type affected")
    resource_id: Optional[str] = Field(None, description="Specific resource identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Action timestamp")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    success: bool = Field(True, description="Whether action was successful")
    error_message: Optional[str] = Field(None, description="Error message if action failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional audit metadata")
    
    model_config = ConfigDict(use_enum_values=True)


class TokenClaims(BaseModel):
    """JWT token claims model"""
    sub: str = Field(..., description="Subject (user ID)")
    email: str = Field(..., description="User email")
    tenant_id: str = Field(..., description="Tenant identifier")
    roles: List[str] = Field(default_factory=list, description="User role names")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    iss: str = Field(..., description="Token issuer")


class AuthenticationRequest(BaseModel):
    """Authentication request model"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")


class AuthenticationResponse(BaseModel):
    """Authentication response model"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: User = Field(..., description="Authenticated user information")


@dataclass
class SecurityContext:
    """Security context for request processing"""
    user: Optional[User] = None
    tenant_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    
    def is_authenticated(self) -> bool:
        """Check if context has authenticated user"""
        return self.user is not None and self.user.status == UserStatus.ACTIVE
    
    def has_permission(self, resource_type: ResourceType, permission_type: PermissionType) -> bool:
        """Check if context user has specific permission"""
        if not self.is_authenticated():
            return False
        return self.user.has_permission(resource_type, permission_type)
    
    def has_role(self, role_type: RoleType) -> bool:
        """Check if context user has specific role"""
        if not self.is_authenticated():
            return False
        return self.user.has_role(role_type)
