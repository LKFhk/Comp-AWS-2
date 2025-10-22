"""
Authentication Dependencies for FastAPI
Provides dependency injection for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from .models import User, Role, RoleType, UserStatus, SecurityContext
from ..config.settings import get_settings

# Security scheme for JWT tokens
security = HTTPBearer()

# Mock user for development/testing
MOCK_USER = User(
    id="test-user-123",
    username="test_user",
    email="test@RiskIntel360.com",
    first_name="Test",
    last_name="User",
    tenant_id="default",
    roles=[
        Role(
            id="analyst-role",
            name="Analyst",
            role_type=RoleType.ANALYST,
            description="Business analyst role with validation access",
            permissions=[],
            is_active=True
        )
    ],
    status=UserStatus.ACTIVE
)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Get the current authenticated user from JWT token.
    For development/testing, returns a mock user.
    """
    settings = get_settings()
    
    # In development/testing mode, return mock user
    if settings.environment.value in ["development", "testing"]:
        return MOCK_USER
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.security.jwt_secret_key,
            algorithms=[settings.security.jwt_algorithm]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # In a real implementation, you would fetch the user from database
        # For now, return the mock user with the token's user_id
        user = MOCK_USER.model_copy()
        user.id = user_id
        user.email = payload.get("email", user.email)
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user (not suspended or inactive)."""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    return current_user


async def get_security_context(
    current_user: User = Depends(get_current_user)
) -> SecurityContext:
    """Get the security context for the current request."""
    return SecurityContext(
        user=current_user,
        tenant_id=current_user.tenant_id
    )


def require_role(required_role: RoleType):
    """Dependency factory to require specific role."""
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' required"
            )
        return current_user
    return role_checker


def require_admin():
    """Dependency to require admin role."""
    return require_role(RoleType.ADMIN)


def require_analyst():
    """Dependency to require analyst role."""
    return require_role(RoleType.ANALYST)


# Optional authentication (allows anonymous access)
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get the current user if authenticated, otherwise None."""
    try:
        if credentials:
            return await get_current_user(credentials)
    except HTTPException:
        pass
    return None
