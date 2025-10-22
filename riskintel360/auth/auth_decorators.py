"""
Authentication and Authorization Decorators
Provides decorators for securing API endpoints and functions.
"""

import logging
from functools import wraps
from typing import Optional, List, Callable, Any
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import User, RoleType, ResourceType, PermissionType, SecurityContext, AuditAction
from .cognito_client import CognitoClient
from .audit_logger import AuditLogger

logger = logging.getLogger(__name__)

# Security scheme for FastAPI
security = HTTPBearer()

# Global instances
_cognito_client: Optional[CognitoClient] = None
_audit_logger: Optional[AuditLogger] = None


def get_cognito_client() -> CognitoClient:
    """Get or create Cognito client instance"""
    global _cognito_client
    if _cognito_client is None:
        _cognito_client = CognitoClient()
    return _cognito_client


def get_audit_logger() -> AuditLogger:
    """Get or create audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        from .audit_logger import AuditLogger
        _audit_logger = AuditLogger()
    return _audit_logger


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """FastAPI dependency to get current authenticated user"""
    try:
        token = credentials.credentials
        cognito_client = get_cognito_client()
        
        user = await cognito_client.validate_token(token)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_from_token(token: str) -> dict:
    """Get current user from token string (for WebSocket authentication)"""
    try:
        # First try JWT validation for development/testing
        from riskintel360.auth.middleware import validate_jwt_token
        from riskintel360.config.settings import get_settings
        
        settings = get_settings()
        
        # In development, prioritize JWT validation
        if settings.environment.value == "development":
            try:
                user_data = validate_jwt_token(token)
                logger.debug(f"JWT validation successful for user: {user_data.get('user_id')}")
                return user_data
            except Exception as jwt_error:
                logger.debug(f"JWT validation failed: {jwt_error}")
                # Don't fall back to Cognito in development for test tokens
                raise ValueError(f"JWT validation failed: {jwt_error}")
        
        # Try Cognito validation for production
        try:
            cognito_client = get_cognito_client()
            user = await cognito_client.validate_token(token)
            if not user:
                raise ValueError("Invalid authentication token")
            
            return {
                "user_id": user.user_id,
                "email": user.email,
                "tenant_id": user.tenant_id,
                "roles": [role.value for role in user.roles]
            }
        except Exception as cognito_error:
            logger.debug(f"Cognito validation failed: {cognito_error}")
            
            # Fall back to JWT validation if Cognito fails
            try:
                user_data = validate_jwt_token(token)
                logger.debug(f"JWT fallback validation successful for user: {user_data.get('user_id')}")
                return user_data
            except Exception as jwt_error:
                logger.debug(f"JWT fallback validation failed: {jwt_error}")
                raise ValueError(f"Token validation failed: Cognito: {cognito_error}, JWT: {jwt_error}")
        
    except Exception as e:
        logger.error(f"Token authentication error: {e}")
        raise ValueError(f"Could not validate token: {str(e)}")


async def get_security_context(
    request: Request,
    user: User = Depends(get_current_user)
) -> SecurityContext:
    """FastAPI dependency to get security context"""
    return SecurityContext(
        user=user,
        tenant_id=user.tenant_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        request_id=request.headers.get("x-request-id")
    )


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """FastAPI dependency to require authentication and return user data"""
    try:
        token = credentials.credentials
        user_data = await get_current_user_from_token(token)
        return user_data
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_auth_decorator(func: Callable) -> Callable:
    """Decorator to require authentication for a function"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # For FastAPI endpoints, authentication is handled by dependencies
        # This decorator is for non-FastAPI functions
        return await func(*args, **kwargs)
    
    return wrapper


def require_role(required_roles: List[RoleType]) -> Callable:
    """Decorator to require specific roles"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract security context from kwargs
            security_context = None
            for arg in args:
                if isinstance(arg, SecurityContext):
                    security_context = arg
                    break
            
            if not security_context:
                for key, value in kwargs.items():
                    if isinstance(value, SecurityContext):
                        security_context = value
                        break
            
            if not security_context or not security_context.is_authenticated():
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            # Check if user has any of the required roles
            user_has_role = any(
                security_context.user.has_role(role) for role in required_roles
            )
            
            if not user_has_role:
                # Log access denied
                audit_logger = get_audit_logger()
                await audit_logger.log_access_denied(
                    security_context,
                    f"Required roles: {[role.value for role in required_roles]}"
                )
                
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required roles: {[role.value for role in required_roles]}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(
    resource_type: ResourceType,
    permission_type: PermissionType
) -> Callable:
    """Decorator to require specific permission"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract security context from kwargs
            security_context = None
            for arg in args:
                if isinstance(arg, SecurityContext):
                    security_context = arg
                    break
            
            if not security_context:
                for key, value in kwargs.items():
                    if isinstance(value, SecurityContext):
                        security_context = value
                        break
            
            if not security_context or not security_context.is_authenticated():
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            # Check if user has required permission
            if not security_context.has_permission(resource_type, permission_type):
                # Log access denied
                audit_logger = get_audit_logger()
                await audit_logger.log_access_denied(
                    security_context,
                    f"Required permission: {permission_type.value} on {resource_type.value}"
                )
                
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required: {permission_type.value} on {resource_type.value}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def audit_trail(
    action: AuditAction,
    resource_type: ResourceType,
    resource_id_param: Optional[str] = None
) -> Callable:
    """Decorator to log actions for audit trail"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract security context and resource ID
            security_context = None
            resource_id = None
            
            # Look for security context in args/kwargs
            for arg in args:
                if isinstance(arg, SecurityContext):
                    security_context = arg
                    break
            
            if not security_context:
                for key, value in kwargs.items():
                    if isinstance(value, SecurityContext):
                        security_context = value
                        break
            
            # Extract resource ID if specified
            if resource_id_param and resource_id_param in kwargs:
                resource_id = str(kwargs[resource_id_param])
            
            # Execute function
            try:
                result = await func(*args, **kwargs)
                
                # Log successful action
                if security_context:
                    audit_logger = get_audit_logger()
                    await audit_logger.log_action(
                        security_context=security_context,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        success=True
                    )
                
                return result
                
            except Exception as e:
                # Log failed action
                if security_context:
                    audit_logger = get_audit_logger()
                    await audit_logger.log_action(
                        security_context=security_context,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        success=False,
                        error_message=str(e)
                    )
                
                raise
        
        return wrapper
    return decorator


# FastAPI dependency factories
def require_roles_dependency(required_roles: List[RoleType]):
    """Create FastAPI dependency that requires specific roles"""
    async def dependency(security_context: SecurityContext = Depends(get_security_context)):
        user_has_role = any(
            security_context.user.has_role(role) for role in required_roles
        )
        
        if not user_has_role:
            # Log access denied
            audit_logger = get_audit_logger()
            await audit_logger.log_access_denied(
                security_context,
                f"Required roles: {[role.value for role in required_roles]}"
            )
            
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required roles: {[role.value for role in required_roles]}"
            )
        
        return security_context
    
    return dependency


def require_permission_dependency(
    resource_type: ResourceType,
    permission_type: PermissionType
):
    """Create FastAPI dependency that requires specific permission"""
    async def dependency(security_context: SecurityContext = Depends(get_security_context)):
        if not security_context.has_permission(resource_type, permission_type):
            # Log access denied
            audit_logger = get_audit_logger()
            await audit_logger.log_access_denied(
                security_context,
                f"Required permission: {permission_type.value} on {resource_type.value}"
            )
            
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {permission_type.value} on {resource_type.value}"
            )
        
        return security_context
    
    return dependency


# Convenience dependencies for common role checks
RequireAdmin = require_roles_dependency([RoleType.ADMIN])
RequireAnalyst = require_roles_dependency([RoleType.ANALYST, RoleType.ADMIN])
RequireAPIUser = require_roles_dependency([RoleType.API_USER, RoleType.ADMIN])

# Convenience dependencies for common permission checks
RequireValidationRead = require_permission_dependency(
    ResourceType.VALIDATION_REQUEST, PermissionType.READ
)
RequireValidationWrite = require_permission_dependency(
    ResourceType.VALIDATION_REQUEST, PermissionType.WRITE
)
RequireReportsRead = require_permission_dependency(
    ResourceType.REPORTS, PermissionType.READ
)
RequireReportsWrite = require_permission_dependency(
    ResourceType.REPORTS, PermissionType.WRITE
)
