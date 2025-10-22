"""
Authentication API Endpoints
Provides OAuth 2.0 authentication endpoints for the platform.
"""

import logging
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from riskintel360.auth.cognito_client import (
    CognitoClient,
    CognitoAuthenticationError,
)
from riskintel360.auth.models import (
    AuthenticationRequest,
    AuthenticationResponse,
    User,
    AuditAction,
)
from riskintel360.auth.auth_decorators import get_current_user
from riskintel360.auth.audit_logger import AuditLogger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request model - accepts both username and email"""

    username: Optional[str] = None
    email: Optional[str] = None
    password: str
    tenant_id: Optional[str] = None
    
    def get_username(self) -> str:
        """Get username from either username or email field"""
        return self.username or self.email or ""


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request model"""

    access_token: str


@router.post("/login")
async def login(request: Request, login_request: LoginRequest) -> dict:
    """Authenticate user with username and password"""
    from riskintel360.config.settings import get_settings
    
    settings = get_settings()
    
    # Development mode: Support demo and test credentials
    if settings.environment.value == "development":
        username = login_request.get_username()
        logger.info(f"Development mode: Authenticating user {username}")
        
        # Demo credentials - Full featured user with AWS integration
        if username == "demo@riskintel360.com" and login_request.password == "demo123":
            user_data = {
                "id": "demo-user-001",
                "email": "demo@riskintel360.com",
                "name": "Demo User",
                "role": "admin",
                "permissions": ["read", "write", "admin"],
                "preferences": {
                    "theme": "light",
                    "notifications": {
                        "email": True,
                        "push": True,
                        "fraudAlerts": True,
                        "complianceAlerts": True
                    },
                    "defaultDashboard": "risk-intel"
                }
            }
            logger.info("Demo user authenticated successfully")
        
        # Test credentials - Simple test user for basic functionality
        elif username == "test" and login_request.password == "test":
            user_data = {
                "id": "test-user-001",
                "email": "test@test.com",
                "name": "Test User",
                "role": "analyst",
                "permissions": ["read"],
                "preferences": {
                    "theme": "light",
                    "notifications": {
                        "email": False,
                        "push": False
                    }
                }
            }
            logger.info("Test user authenticated successfully")
        
        # Any other credentials - Auto-accept as basic user
        else:
            user_data = {
                "id": "dev-user-123",
                "email": username,
                "name": "Development User",
                "role": "admin",
                "permissions": ["read", "write", "admin"],
                "preferences": {
                    "theme": "light",
                    "notifications": {
                        "email": True,
                        "push": True
                    }
                }
            }
            logger.info(f"Auto-authenticated user: {username}")
        
        # Create mock token
        from riskintel360.auth.middleware import create_mock_jwt_token
        token = create_mock_jwt_token(user_data["id"], user_data["email"])
        
        return {
            "user": user_data,
            "token": token,
            "token_type": "bearer",
            "expires_in": 3600
        }
    
    # Production mode: Use Cognito
    try:
        username = login_request.get_username()
        
        # Create authentication request
        auth_request = AuthenticationRequest(
            username=username,
            password=login_request.password,
            tenant_id=login_request.tenant_id,
        )

        # Authenticate with Cognito
        cognito_client = CognitoClient()
        auth_response = await cognito_client.authenticate_user(auth_request)

        # Log successful authentication
        audit_logger = AuditLogger()
        await audit_logger.log_authentication(
            user_id=auth_response.user.id,
            action=AuditAction.LOGIN,
            success=True,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        logger.info(f"User {auth_response.user.username} authenticated successfully")
        return auth_response.model_dump() if hasattr(auth_response, 'model_dump') else auth_response

    except CognitoAuthenticationError as e:
        # Log failed authentication
        username = login_request.get_username()
        audit_logger = AuditLogger()
        await audit_logger.log_authentication(
            user_id=username,
            action=AuditAction.LOGIN,
            success=False,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_message=str(e),
        )

        logger.warning(f"Authentication failed for user {username}: {e}")
        raise HTTPException(status_code=401, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}")
        raise HTTPException(
            status_code=500, detail="Authentication service unavailable"
        )


@router.post("/refresh", response_model=AuthenticationResponse)
async def refresh_token(
    request: Request, refresh_request: RefreshTokenRequest
) -> AuthenticationResponse:
    """Refresh access token using refresh token"""
    try:
        cognito_client = CognitoClient()
        auth_response = await cognito_client.refresh_token(
            refresh_request.refresh_token
        )

        if not auth_response:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        logger.info(f"Token refreshed for user {auth_response.user.username}")
        return auth_response

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail="Token refresh failed")


@router.post("/logout")
async def logout(
    request: Request,
    logout_request: LogoutRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Logout user and invalidate tokens"""
    try:
        cognito_client = CognitoClient()
        success = await cognito_client.logout_user(logout_request.access_token)

        # Log logout
        audit_logger = AuditLogger()
        await audit_logger.log_authentication(
            user_id=current_user.id,
            action=AuditAction.LOGOUT,
            success=success,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        if success:
            logger.info(f"User {current_user.username} logged out successfully")
            return {"message": "Logged out successfully"}
        else:
            logger.warning(f"Logout failed for user {current_user.username}")
            return {"message": "Logout completed (token may have been already invalid)"}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout service unavailable")


@router.get("/me")
async def get_current_user_info(request: Request) -> dict:
    """Get current authenticated user information"""
    from riskintel360.config.settings import get_settings
    
    settings = get_settings()
    
    # Development mode: Extract user from token or return demo user
    if settings.environment.value == "development":
        # Try to get user from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                import jwt
                # Decode without verification in dev mode
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get("sub", "demo-user-001")
                email = payload.get("email", "demo@riskintel360.com")
                
                # Return user matching the token
                if user_id == "demo-user-001":
                    return {
                        "id": "demo-user-001",
                        "email": "demo@riskintel360.com",
                        "name": "Demo User",
                        "role": "admin",
                        "permissions": ["read", "write", "admin"],
                        "preferences": {
                            "theme": "light",
                            "notifications": {
                                "email": True,
                                "push": True,
                                "fraudAlerts": True,
                                "complianceAlerts": True
                            },
                            "defaultDashboard": "risk-intel"
                        }
                    }
                elif user_id == "test-user-001":
                    return {
                        "id": "test-user-001",
                        "email": "test@test.com",
                        "name": "Test User",
                        "role": "analyst",
                        "permissions": ["read"],
                        "preferences": {
                            "theme": "light",
                            "notifications": {
                                "email": False,
                                "push": False
                            }
                        }
                    }
            except Exception as e:
                logger.warning(f"Could not decode token: {e}")
        
        # Default dev user if no valid token
        return {
            "id": "demo-user-001",
            "email": "demo@riskintel360.com",
            "name": "Demo User",
            "role": "admin",
            "permissions": ["read", "write", "admin"],
            "preferences": {
                "theme": "light",
                "notifications": {
                    "email": True,
                    "push": True,
                    "fraudAlerts": True,
                    "complianceAlerts": True
                },
                "defaultDashboard": "risk-intel"
            }
        }
    
    # Check if user is authenticated via middleware
    if not hasattr(request.state, "current_user"):
        raise HTTPException(status_code=401, detail="Authentication required")

    current_user = request.state.current_user
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "tenant_id": current_user["tenant_id"],
        "roles": current_user["roles"],
        "authenticated": True,
    }


@router.get("/validate")
async def validate_token(current_user: User = Depends(get_current_user)) -> dict:
    """Validate current access token"""
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "tenant_id": current_user.tenant_id,
        "roles": [role.name for role in current_user.roles if role.is_active],
    }


@router.get("/permissions")
async def get_user_permissions(current_user: User = Depends(get_current_user)) -> dict:
    """Get current user's permissions"""
    from riskintel360.auth.rbac import RoleBasedAccessControl

    rbac = RoleBasedAccessControl()
    permissions = rbac.get_user_permissions(current_user)

    return {
        "user_id": current_user.id,
        "tenant_id": current_user.tenant_id,
        "roles": [
            {
                "id": role.id,
                "name": role.name,
                "type": role.role_type.value,
                "is_active": role.is_active,
            }
            for role in current_user.roles
        ],
        "permissions": [
            {
                "id": perm.id,
                "name": perm.name,
                "resource_type": perm.resource_type.value,
                "permission_type": perm.permission_type.value,
            }
            for perm in permissions
        ],
    }


# Health check endpoint for authentication service
@router.get("/test-token")
async def generate_test_token(
    user_id: str = "test-user", email: str = "test@example.com"
) -> dict:
    """Generate a test JWT token for development purposes"""
    from riskintel360.auth.middleware import create_mock_jwt_token
    from riskintel360.config.settings import get_settings

    settings = get_settings()

    # Only allow in development environment
    if settings.environment.value != "development":
        raise HTTPException(
            status_code=403,
            detail="Test token generation only available in development environment",
        )

    token = create_mock_jwt_token(user_id, email)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "email": email,
        "expires_in": 3600,
        "message": "Test token generated for development use only",
    }


@router.get("/health")
async def auth_health_check() -> dict:
    """Health check for authentication service"""
    try:
        # Test Cognito client initialization
        cognito_client = CognitoClient()

        return {
            "status": "healthy",
            "service": "authentication",
            "cognito_configured": cognito_client._client_id is not None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Authentication health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "authentication",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
