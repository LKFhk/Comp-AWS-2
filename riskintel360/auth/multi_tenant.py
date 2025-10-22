"""
Multi-Tenant Data Isolation System
Manages tenant isolation and data access policies.
"""

import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timezone
import uuid

from .models import User, SecurityContext, ResourceType

logger = logging.getLogger(__name__)


class TenantInfo:
    """Tenant information and configuration"""
    
    def __init__(
        self,
        tenant_id: str,
        name: str,
        description: str = "",
        is_active: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.tenant_id = tenant_id
        self.name = name
        self.description = description
        self.is_active = is_active
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
        # Data isolation settings
        self.data_isolation_level = "strict"  # strict, moderate, shared
        self.allowed_cross_tenant_resources: Set[ResourceType] = set()
        
        # Resource limits
        self.max_users = 1000
        self.max_validation_requests_per_month = 10000
        self.max_storage_gb = 100


class MultiTenantManager:
    """Multi-tenant data isolation and access management"""
    
    def __init__(self):
        self._tenants: Dict[str, TenantInfo] = {}
        self._tenant_users: Dict[str, Set[str]] = {}  # tenant_id -> set of user_ids
        self._user_tenants: Dict[str, str] = {}  # user_id -> tenant_id
        
        # Initialize default tenant
        self._initialize_default_tenant()
    
    def _initialize_default_tenant(self) -> None:
        """Initialize default tenant for single-tenant deployments"""
        default_tenant = TenantInfo(
            tenant_id="default",
            name="Default Tenant",
            description="Default tenant for single-tenant deployments",
            is_active=True
        )
        
        self._tenants["default"] = default_tenant
        self._tenant_users["default"] = set()
        
        logger.info("Initialized default tenant")
    
    def create_tenant(
        self,
        name: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> TenantInfo:
        """Create a new tenant"""
        tenant_id = str(uuid.uuid4())
        
        tenant = TenantInfo(
            tenant_id=tenant_id,
            name=name,
            description=description,
            metadata=metadata
        )
        
        self._tenants[tenant_id] = tenant
        self._tenant_users[tenant_id] = set()
        
        logger.info(f"Created tenant: {tenant_id} ({name})")
        return tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[TenantInfo]:
        """Get tenant by ID"""
        return self._tenants.get(tenant_id)
    
    def get_tenant_by_name(self, name: str) -> Optional[TenantInfo]:
        """Get tenant by name"""
        for tenant in self._tenants.values():
            if tenant.name == name:
                return tenant
        return None
    
    def list_tenants(self, active_only: bool = True) -> List[TenantInfo]:
        """List all tenants"""
        tenants = list(self._tenants.values())
        if active_only:
            tenants = [t for t in tenants if t.is_active]
        return tenants
    
    def update_tenant(
        self,
        tenant_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[TenantInfo]:
        """Update tenant information"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        if name is not None:
            tenant.name = name
        if description is not None:
            tenant.description = description
        if is_active is not None:
            tenant.is_active = is_active
        if metadata is not None:
            tenant.metadata.update(metadata)
        
        tenant.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Updated tenant: {tenant_id}")
        return tenant
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant (soft delete by deactivating)"""
        if tenant_id == "default":
            logger.error("Cannot delete default tenant")
            return False
        
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        # Deactivate tenant instead of deleting
        tenant.is_active = False
        tenant.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Deactivated tenant: {tenant_id}")
        return True
    
    def assign_user_to_tenant(self, user_id: str, tenant_id: str) -> bool:
        """Assign user to tenant"""
        tenant = self.get_tenant(tenant_id)
        if not tenant or not tenant.is_active:
            logger.error(f"Tenant not found or inactive: {tenant_id}")
            return False
        
        # Remove user from previous tenant if exists
        previous_tenant_id = self._user_tenants.get(user_id)
        if previous_tenant_id and previous_tenant_id in self._tenant_users:
            self._tenant_users[previous_tenant_id].discard(user_id)
        
        # Assign to new tenant
        self._user_tenants[user_id] = tenant_id
        self._tenant_users[tenant_id].add(user_id)
        
        logger.info(f"Assigned user {user_id} to tenant {tenant_id}")
        return True
    
    def remove_user_from_tenant(self, user_id: str) -> bool:
        """Remove user from their current tenant"""
        tenant_id = self._user_tenants.get(user_id)
        if not tenant_id:
            return False
        
        # Remove from tenant
        if tenant_id in self._tenant_users:
            self._tenant_users[tenant_id].discard(user_id)
        
        del self._user_tenants[user_id]
        
        logger.info(f"Removed user {user_id} from tenant {tenant_id}")
        return True
    
    def get_user_tenant(self, user_id: str) -> Optional[str]:
        """Get tenant ID for user"""
        return self._user_tenants.get(user_id)
    
    def get_tenant_users(self, tenant_id: str) -> Set[str]:
        """Get all users for a tenant"""
        return self._tenant_users.get(tenant_id, set()).copy()
    
    def validate_tenant_access(
        self,
        security_context: SecurityContext,
        resource_tenant_id: str,
        resource_type: ResourceType
    ) -> bool:
        """Validate if user can access resource from another tenant"""
        if not security_context.is_authenticated():
            return False
        
        user_tenant_id = security_context.tenant_id
        
        # Same tenant access is always allowed
        if user_tenant_id == resource_tenant_id:
            return True
        
        # Check if cross-tenant access is allowed for this resource type
        user_tenant = self.get_tenant(user_tenant_id)
        if not user_tenant:
            return False
        
        # Check tenant isolation level
        if user_tenant.data_isolation_level == "strict":
            # Strict isolation - no cross-tenant access
            return False
        elif user_tenant.data_isolation_level == "moderate":
            # Moderate isolation - only allowed resources
            return resource_type in user_tenant.allowed_cross_tenant_resources
        elif user_tenant.data_isolation_level == "shared":
            # Shared isolation - access allowed with proper permissions
            return True
        
        return False
    
    def filter_resources_by_tenant(
        self,
        security_context: SecurityContext,
        resources: List[Dict[str, Any]],
        tenant_id_field: str = "tenant_id"
    ) -> List[Dict[str, Any]]:
        """Filter resources to only include those accessible by user's tenant"""
        if not security_context.is_authenticated():
            return []
        
        user_tenant_id = security_context.tenant_id
        filtered_resources = []
        
        for resource in resources:
            resource_tenant_id = resource.get(tenant_id_field)
            
            # Include resource if it belongs to user's tenant
            if resource_tenant_id == user_tenant_id:
                filtered_resources.append(resource)
            # Or if cross-tenant access is allowed
            elif self.validate_tenant_access(
                security_context,
                resource_tenant_id,
                ResourceType.VALIDATION_REQUEST  # Default resource type
            ):
                filtered_resources.append(resource)
        
        return filtered_resources
    
    def get_tenant_resource_prefix(self, tenant_id: str, resource_type: str) -> str:
        """Get resource prefix for tenant isolation in storage"""
        return f"tenant_{tenant_id}_{resource_type}"
    
    def get_tenant_database_schema(self, tenant_id: str) -> str:
        """Get database schema name for tenant"""
        if tenant_id == "default":
            return "public"
        return f"tenant_{tenant_id}"
    
    def get_tenant_s3_prefix(self, tenant_id: str) -> str:
        """Get S3 prefix for tenant data isolation"""
        return f"tenants/{tenant_id}/"
    
    def validate_tenant_limits(self, tenant_id: str) -> Dict[str, Any]:
        """Validate tenant resource limits"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return {"valid": False, "error": "Tenant not found"}
        
        # Get current usage (this would typically query the database)
        current_users = len(self.get_tenant_users(tenant_id))
        
        # Check limits
        limits_status = {
            "valid": True,
            "limits": {
                "users": {
                    "current": current_users,
                    "max": tenant.max_users,
                    "exceeded": current_users >= tenant.max_users
                },
                "validation_requests": {
                    "current": 0,  # Would be queried from database
                    "max": tenant.max_validation_requests_per_month,
                    "exceeded": False
                },
                "storage": {
                    "current_gb": 0,  # Would be queried from storage
                    "max_gb": tenant.max_storage_gb,
                    "exceeded": False
                }
            }
        }
        
        # Check if any limits are exceeded
        for limit_type, limit_info in limits_status["limits"].items():
            if limit_info["exceeded"]:
                limits_status["valid"] = False
        
        return limits_status
    
    def configure_tenant_isolation(
        self,
        tenant_id: str,
        isolation_level: str,
        allowed_cross_tenant_resources: Optional[List[ResourceType]] = None
    ) -> bool:
        """Configure tenant data isolation settings"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        if isolation_level not in ["strict", "moderate", "shared"]:
            logger.error(f"Invalid isolation level: {isolation_level}")
            return False
        
        tenant.data_isolation_level = isolation_level
        
        if allowed_cross_tenant_resources:
            tenant.allowed_cross_tenant_resources = set(allowed_cross_tenant_resources)
        
        tenant.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Updated isolation settings for tenant {tenant_id}: {isolation_level}")
        return True
    
    def get_tenant_summary(self) -> Dict[str, Any]:
        """Get summary of all tenants and their status"""
        summary = {
            "total_tenants": len(self._tenants),
            "active_tenants": len([t for t in self._tenants.values() if t.is_active]),
            "total_users": len(self._user_tenants),
            "tenants": {}
        }
        
        for tenant_id, tenant in self._tenants.items():
            user_count = len(self.get_tenant_users(tenant_id))
            limits_status = self.validate_tenant_limits(tenant_id)
            
            summary["tenants"][tenant_id] = {
                "name": tenant.name,
                "is_active": tenant.is_active,
                "user_count": user_count,
                "isolation_level": tenant.data_isolation_level,
                "limits_valid": limits_status["valid"],
                "created_at": tenant.created_at.isoformat(),
                "updated_at": tenant.updated_at.isoformat()
            }
        
        return summary
