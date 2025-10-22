"""
Role-Based Access Control (RBAC) System
Manages roles, permissions, and access control policies.
"""

import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timezone
import json

from .models import (
    User, Role, Permission, RoleType, PermissionType, ResourceType,
    SecurityContext
)

logger = logging.getLogger(__name__)


class RoleBasedAccessControl:
    """Role-based access control system for managing permissions"""
    
    def __init__(self):
        self._roles: Dict[str, Role] = {}
        self._permissions: Dict[str, Permission] = {}
        self._role_hierarchy: Dict[RoleType, Set[RoleType]] = {}
        
        # Initialize default roles and permissions
        self._initialize_default_permissions()
        self._initialize_default_roles()
        self._initialize_role_hierarchy()
    
    def _initialize_default_permissions(self) -> None:
        """Initialize default system permissions"""
        permissions = []
        
        # Create permissions for each resource type and permission type combination
        for resource_type in ResourceType:
            for permission_type in PermissionType:
                permission_id = f"{resource_type.value}_{permission_type.value}"
                permission = Permission(
                    id=permission_id,
                    name=f"{permission_type.value.title()} {resource_type.value.replace('_', ' ').title()}",
                    resource_type=resource_type,
                    permission_type=permission_type,
                    description=f"{permission_type.value.title()} access to {resource_type.value.replace('_', ' ')}"
                )
                permissions.append(permission)
                self._permissions[permission_id] = permission
        
        logger.info(f"Initialized {len(permissions)} default permissions")
    
    def _initialize_default_roles(self) -> None:
        """Initialize default system roles"""
        # Admin role - full access (all permissions)
        admin_permissions = list(self._permissions.values())
        admin_role = Role(
            id="admin",
            name="Administrator",
            role_type=RoleType.ADMIN,
            description="Full system administrator with all permissions",
            permissions=admin_permissions,
            is_active=True
        )
        self._roles["admin"] = admin_role
        
        # Analyst role - business data access
        analyst_permissions = []
        business_resources = [
            ResourceType.VALIDATION_REQUEST,
            ResourceType.MARKET_DATA,
            ResourceType.COMPETITIVE_INTEL,
            ResourceType.FINANCIAL_DATA,
            ResourceType.RISK_ASSESSMENT,
            ResourceType.CUSTOMER_DATA,
            ResourceType.REPORTS,
        ]
        
        for resource_type in business_resources:
            for permission_type in [PermissionType.READ, PermissionType.WRITE]:
                permission_id = f"{resource_type.value}_{permission_type.value}"
                if permission_id in self._permissions:
                    analyst_permissions.append(self._permissions[permission_id])
        
        analyst_role = Role(
            id="analyst",
            name="Business Analyst",
            role_type=RoleType.ANALYST,
            description="Business analyst with read/write access to business data",
            permissions=analyst_permissions,
            is_active=True
        )
        self._roles["analyst"] = analyst_role
        
        # API User role - programmatic access
        api_permissions = []
        api_resources = [
            ResourceType.VALIDATION_REQUEST,
            ResourceType.MARKET_DATA,
            ResourceType.REPORTS,
        ]
        
        for resource_type in api_resources:
            for permission_type in [PermissionType.READ, PermissionType.WRITE]:
                permission_id = f"{resource_type.value}_{permission_type.value}"
                if permission_id in self._permissions:
                    api_permissions.append(self._permissions[permission_id])
        
        api_role = Role(
            id="api_user",
            name="API User",
            role_type=RoleType.API_USER,
            description="API user with programmatic access to core resources",
            permissions=api_permissions,
            is_active=True
        )
        self._roles["api_user"] = api_role
        
        # Viewer role - read-only access
        viewer_permissions = []
        viewer_resources = [
            ResourceType.VALIDATION_REQUEST,
            ResourceType.MARKET_DATA,
            ResourceType.COMPETITIVE_INTEL,
            ResourceType.FINANCIAL_DATA,
            ResourceType.RISK_ASSESSMENT,
            ResourceType.CUSTOMER_DATA,
            ResourceType.REPORTS,
        ]
        
        for resource_type in viewer_resources:
            permission_id = f"{resource_type.value}_{PermissionType.READ.value}"
            if permission_id in self._permissions:
                viewer_permissions.append(self._permissions[permission_id])
        
        viewer_role = Role(
            id="viewer",
            name="Viewer",
            role_type=RoleType.VIEWER,
            description="Read-only access to business data",
            permissions=viewer_permissions,
            is_active=True
        )
        self._roles["viewer"] = viewer_role
        
        logger.info(f"Initialized {len(self._roles)} default roles")
    
    def _initialize_role_hierarchy(self) -> None:
        """Initialize role hierarchy for inheritance"""
        # Admin inherits all other roles
        self._role_hierarchy[RoleType.ADMIN] = {
            RoleType.ANALYST, RoleType.API_USER, RoleType.VIEWER
        }
        
        # Analyst inherits viewer permissions
        self._role_hierarchy[RoleType.ANALYST] = {RoleType.VIEWER}
        
        # API User is standalone
        self._role_hierarchy[RoleType.API_USER] = set()
        
        # Viewer is base role
        self._role_hierarchy[RoleType.VIEWER] = set()
    
    def get_role(self, role_id: str) -> Optional[Role]:
        """Get role by ID"""
        return self._roles.get(role_id)
    
    def get_role_by_type(self, role_type: RoleType) -> Optional[Role]:
        """Get role by type"""
        for role in self._roles.values():
            if role.role_type == role_type:
                return role
        return None
    
    def get_permission(self, permission_id: str) -> Optional[Permission]:
        """Get permission by ID"""
        return self._permissions.get(permission_id)
    
    def get_permissions_for_resource(
        self,
        resource_type: ResourceType,
        permission_type: Optional[PermissionType] = None
    ) -> List[Permission]:
        """Get permissions for a specific resource type"""
        permissions = []
        for permission in self._permissions.values():
            if permission.resource_type == resource_type:
                if permission_type is None or permission.permission_type == permission_type:
                    permissions.append(permission)
        return permissions
    
    def check_permission(
        self,
        user: User,
        resource_type: ResourceType,
        permission_type: PermissionType
    ) -> bool:
        """Check if user has specific permission"""
        # Check direct permissions
        if user.has_permission(resource_type, permission_type):
            return True
        
        # Check inherited permissions through role hierarchy
        for role in user.roles:
            if not role.is_active:
                continue
            
            # Check if role type has inherited permissions
            inherited_roles = self._role_hierarchy.get(role.role_type, set())
            for inherited_role_type in inherited_roles:
                inherited_role = self.get_role_by_type(inherited_role_type)
                if inherited_role:
                    for permission in inherited_role.permissions:
                        if (permission.resource_type == resource_type and 
                            permission.permission_type == permission_type):
                            return True
                        # Admin permission grants all access
                        if permission.permission_type == PermissionType.ADMIN:
                            return True
        
        return False
    
    def get_user_permissions(self, user: User) -> List[Permission]:
        """Get all permissions for a user"""
        permissions = set()
        
        # Add direct permissions from user roles
        for role in user.roles:
            if role.is_active:
                permissions.update(role.permissions)
        
        # Add inherited permissions
        for role in user.roles:
            if not role.is_active:
                continue
            
            inherited_roles = self._role_hierarchy.get(role.role_type, set())
            for inherited_role_type in inherited_roles:
                inherited_role = self.get_role_by_type(inherited_role_type)
                if inherited_role:
                    permissions.update(inherited_role.permissions)
        
        return list(permissions)
    
    def create_custom_role(
        self,
        role_id: str,
        name: str,
        description: str,
        permission_ids: List[str]
    ) -> Role:
        """Create a custom role with specified permissions"""
        # Validate permissions exist
        permissions = []
        for permission_id in permission_ids:
            permission = self.get_permission(permission_id)
            if permission:
                permissions.append(permission)
            else:
                logger.warning(f"Permission not found: {permission_id}")
        
        # Create custom role
        custom_role = Role(
            id=role_id,
            name=name,
            role_type=RoleType.VIEWER,  # Default to viewer type for custom roles
            description=description,
            permissions=permissions,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self._roles[role_id] = custom_role
        logger.info(f"Created custom role: {role_id}")
        
        return custom_role
    
    def update_role_permissions(
        self,
        role_id: str,
        permission_ids: List[str]
    ) -> Optional[Role]:
        """Update permissions for an existing role"""
        role = self.get_role(role_id)
        if not role:
            return None
        
        # Validate permissions exist
        permissions = []
        for permission_id in permission_ids:
            permission = self.get_permission(permission_id)
            if permission:
                permissions.append(permission)
            else:
                logger.warning(f"Permission not found: {permission_id}")
        
        # Update role permissions
        role.permissions = permissions
        role.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Updated permissions for role: {role_id}")
        return role
    
    def assign_role_to_user(self, user: User, role_id: str) -> bool:
        """Assign role to user"""
        role = self.get_role(role_id)
        if not role:
            logger.error(f"Role not found: {role_id}")
            return False
        
        # Check if user already has this role
        for existing_role in user.roles:
            if existing_role.id == role_id:
                logger.info(f"User {user.id} already has role {role_id}")
                return True
        
        # Add role to user
        user.roles.append(role)
        user.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Assigned role {role_id} to user {user.id}")
        return True
    
    def remove_role_from_user(self, user: User, role_id: str) -> bool:
        """Remove role from user"""
        # Find and remove role
        for i, role in enumerate(user.roles):
            if role.id == role_id:
                user.roles.pop(i)
                user.updated_at = datetime.now(timezone.utc)
                logger.info(f"Removed role {role_id} from user {user.id}")
                return True
        
        logger.warning(f"Role {role_id} not found for user {user.id}")
        return False
    
    def get_role_summary(self) -> Dict[str, Dict[str, any]]:
        """Get summary of all roles and their permissions"""
        summary = {}
        
        for role_id, role in self._roles.items():
            summary[role_id] = {
                "name": role.name,
                "type": role.role_type.value,
                "description": role.description,
                "is_active": role.is_active,
                "permission_count": len(role.permissions),
                "permissions": [
                    {
                        "resource": p.resource_type.value,
                        "type": p.permission_type.value,
                        "name": p.name
                    }
                    for p in role.permissions
                ]
            }
        
        return summary
    
    def validate_security_context(self, security_context: SecurityContext) -> bool:
        """Validate security context and user permissions"""
        if not security_context.is_authenticated():
            return False
        
        # Validate user has at least one active role
        active_roles = [role for role in security_context.user.roles if role.is_active]
        if not active_roles:
            logger.warning(f"User {security_context.user.id} has no active roles")
            return False
        
        # Validate roles exist in RBAC system
        for role in active_roles:
            if role.id not in self._roles:
                logger.warning(f"Role {role.id} not found in RBAC system")
                return False
        
        return True
