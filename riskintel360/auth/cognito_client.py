"""
AWS Cognito Client for OAuth 2.0 Authentication
Handles user authentication, token management, and user pool operations.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from riskintel360.config.settings import get_settings
from .models import (
    User, Role, Permission, TokenClaims, AuthenticationRequest, 
    AuthenticationResponse, UserStatus, RoleType, PermissionType
)

logger = logging.getLogger(__name__)


class CognitoAuthenticationError(Exception):
    """Cognito authentication specific error"""
    pass


class CognitoClient:
    """AWS Cognito client for user authentication and management"""
    
    def __init__(self):
        self.settings = get_settings()
        self._cognito_client = None
        self._user_pool_id = None
        self._client_id = None
        self._client_secret = None
        self._region = None
        
        # Initialize Cognito client
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize AWS Cognito client and configuration"""
        try:
            # Get AWS region from environment or default
            self._region = self.settings.security.oauth_region if hasattr(self.settings.security, 'oauth_region') else 'us-east-1'
            
            # Initialize boto3 client
            self._cognito_client = boto3.client('cognito-idp', region_name=self._region)
            
            # Get configuration from environment variables
            self._user_pool_id = self.settings.security.cognito_user_pool_id if hasattr(self.settings.security, 'cognito_user_pool_id') else None
            self._client_id = self.settings.security.oauth_client_id
            self._client_secret = self.settings.security.oauth_client_secret
            
            if not self._user_pool_id:
                logger.warning("Cognito User Pool ID not configured - authentication will be limited")
            
            if not self._client_id:
                logger.warning("OAuth Client ID not configured - authentication will be limited")
                
            logger.info("Cognito client initialized successfully")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found - Cognito authentication unavailable")
            raise CognitoAuthenticationError("AWS credentials not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Cognito client: {e}")
            raise CognitoAuthenticationError(f"Cognito initialization failed: {e}")
    
    async def authenticate_user(self, request: AuthenticationRequest) -> AuthenticationResponse:
        """Authenticate user with username/password"""
        try:
            if not self._cognito_client or not self._client_id:
                raise CognitoAuthenticationError("Cognito client not properly configured")
            
            # Prepare authentication parameters
            auth_params = {
                'USERNAME': request.username,
                'PASSWORD': request.password,
            }
            
            # Add client secret if configured
            if self._client_secret:
                import hmac
                import hashlib
                import base64
                
                message = request.username + self._client_id
                dig = hmac.new(
                    self._client_secret.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256
                ).digest()
                auth_params['SECRET_HASH'] = base64.b64encode(dig).decode()
            
            # Initiate authentication
            response = self._cognito_client.initiate_auth(
                ClientId=self._client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters=auth_params
            )
            
            # Extract tokens
            auth_result = response['AuthenticationResult']
            access_token = auth_result['AccessToken']
            refresh_token = auth_result.get('RefreshToken')
            expires_in = auth_result.get('ExpiresIn', 3600)
            
            # Get user information from token
            user = await self._get_user_from_token(access_token)
            
            return AuthenticationResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                user=user
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'NotAuthorizedException':
                raise CognitoAuthenticationError("Invalid username or password")
            elif error_code == 'UserNotConfirmedException':
                raise CognitoAuthenticationError("User account not confirmed")
            elif error_code == 'UserNotFoundException':
                raise CognitoAuthenticationError("User not found")
            else:
                logger.error(f"Cognito authentication error: {error_code} - {error_message}")
                raise CognitoAuthenticationError(f"Authentication failed: {error_message}")
        
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            raise CognitoAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def _get_user_from_token(self, access_token: str) -> User:
        """Extract user information from access token"""
        try:
            # Get user attributes from Cognito
            response = self._cognito_client.get_user(AccessToken=access_token)
            
            # Extract user attributes
            attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
            
            # Create user object
            user = User(
                id=response['Username'],
                username=response['Username'],
                email=attributes.get('email', ''),
                first_name=attributes.get('given_name', ''),
                last_name=attributes.get('family_name', ''),
                tenant_id=attributes.get('custom:tenant_id', 'default'),
                status=UserStatus.ACTIVE,
                last_login=datetime.now(timezone.utc),
                roles=await self._get_user_roles(response['Username'])
            )
            
            return user
            
        except ClientError as e:
            logger.error(f"Failed to get user from token: {e}")
            raise CognitoAuthenticationError("Invalid access token")
    
    async def _get_user_roles(self, username: str) -> List[Role]:
        """Get user roles from Cognito groups"""
        try:
            if not self._user_pool_id:
                # Return default roles if user pool not configured
                return [self._get_default_role()]
            
            # Get user groups (roles)
            response = self._cognito_client.admin_list_groups_for_user(
                UserPoolId=self._user_pool_id,
                Username=username
            )
            
            roles = []
            for group in response['Groups']:
                role_type = self._map_group_to_role_type(group['GroupName'])
                permissions = self._get_role_permissions(role_type)
                
                role = Role(
                    id=group['GroupName'],
                    name=group['GroupName'],
                    role_type=role_type,
                    description=group.get('Description', ''),
                    permissions=permissions,
                    is_active=True
                )
                roles.append(role)
            
            # If no roles found, assign default viewer role
            if not roles:
                roles.append(self._get_default_role())
            
            return roles
            
        except ClientError as e:
            logger.warning(f"Failed to get user roles: {e}")
            # Return default role on error
            return [self._get_default_role()]
    
    def _map_group_to_role_type(self, group_name: str) -> RoleType:
        """Map Cognito group name to role type"""
        group_mapping = {
            'admin': RoleType.ADMIN,
            'analyst': RoleType.ANALYST,
            'viewer': RoleType.VIEWER,
            'api_user': RoleType.API_USER,
        }
        return group_mapping.get(group_name.lower(), RoleType.VIEWER)
    
    def _get_role_permissions(self, role_type: RoleType) -> List[Permission]:
        """Get permissions for a role type"""
        if role_type == RoleType.ADMIN:
            return self._get_admin_permissions()
        elif role_type == RoleType.ANALYST:
            return self._get_analyst_permissions()
        elif role_type == RoleType.API_USER:
            return self._get_api_user_permissions()
        else:  # VIEWER
            return self._get_viewer_permissions()
    
    def _get_admin_permissions(self) -> List[Permission]:
        """Get admin permissions (full access)"""
        from .models import ResourceType
        permissions = []
        
        # Admin gets all permission types for all resources
        for resource_type in ResourceType:
            for permission_type in PermissionType:
                permissions.append(Permission(
                    id=f"{resource_type.value}_{permission_type.value}",
                    name=f"{permission_type.value.title()} {resource_type.value.replace('_', ' ').title()}",
                    resource_type=resource_type,
                    permission_type=permission_type,
                    description=f"{permission_type.value.title()} access to {resource_type.value.replace('_', ' ')}"
                ))
        
        return permissions
    
    def _get_analyst_permissions(self) -> List[Permission]:
        """Get analyst permissions (read/write for business data)"""
        from .models import ResourceType
        permissions = []
        
        # Read/write access to business data
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
            for perm_type in [PermissionType.READ, PermissionType.WRITE]:
                permissions.append(Permission(
                    id=f"analyst_{resource_type.value}_{perm_type.value}",
                    name=f"Analyst {perm_type.value} access to {resource_type.value}",
                    resource_type=resource_type,
                    permission_type=perm_type,
                    description=f"Analyst {perm_type.value} access to {resource_type.value}"
                ))
        
        return permissions
    
    def _get_api_user_permissions(self) -> List[Permission]:
        """Get API user permissions (programmatic access)"""
        from .models import ResourceType
        permissions = []
        
        # API access to core resources
        api_resources = [
            ResourceType.VALIDATION_REQUEST,
            ResourceType.MARKET_DATA,
            ResourceType.REPORTS,
        ]
        
        for resource_type in api_resources:
            for perm_type in [PermissionType.READ, PermissionType.WRITE]:
                permissions.append(Permission(
                    id=f"api_{resource_type.value}_{perm_type.value}",
                    name=f"API {perm_type.value} access to {resource_type.value}",
                    resource_type=resource_type,
                    permission_type=perm_type,
                    description=f"API {perm_type.value} access to {resource_type.value}"
                ))
        
        return permissions
    
    def _get_viewer_permissions(self) -> List[Permission]:
        """Get viewer permissions (read-only access)"""
        from .models import ResourceType
        permissions = []
        
        # Read-only access to business data
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
            permissions.append(Permission(
                id=f"viewer_{resource_type.value}_read",
                name=f"Viewer read access to {resource_type.value}",
                resource_type=resource_type,
                permission_type=PermissionType.READ,
                description=f"Read-only access to {resource_type.value}"
            ))
        
        return permissions
    
    def _get_default_role(self) -> Role:
        """Get default viewer role"""
        return Role(
            id="default_viewer",
            name="Viewer",
            role_type=RoleType.VIEWER,
            description="Default viewer role with read-only access",
            permissions=self._get_viewer_permissions(),
            is_active=True
        )
    
    async def validate_token(self, token: str) -> Optional[User]:
        """Validate JWT token and return user"""
        try:
            if not self._cognito_client:
                logger.warning("Cognito client not configured - token validation limited")
                return None
            
            # Get user from token
            user = await self._get_user_from_token(token)
            return user
            
        except CognitoAuthenticationError:
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[AuthenticationResponse]:
        """Refresh access token using refresh token"""
        try:
            if not self._cognito_client or not self._client_id:
                raise CognitoAuthenticationError("Cognito client not properly configured")
            
            # Prepare refresh parameters
            auth_params = {
                'REFRESH_TOKEN': refresh_token,
            }
            
            # Add client secret if configured
            if self._client_secret:
                # Note: For refresh token, we don't include username in secret hash
                import hmac
                import hashlib
                import base64
                
                dig = hmac.new(
                    self._client_secret.encode('utf-8'),
                    self._client_id.encode('utf-8'),
                    hashlib.sha256
                ).digest()
                auth_params['SECRET_HASH'] = base64.b64encode(dig).decode()
            
            # Refresh token
            response = self._cognito_client.initiate_auth(
                ClientId=self._client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters=auth_params
            )
            
            # Extract new tokens
            auth_result = response['AuthenticationResult']
            access_token = auth_result['AccessToken']
            expires_in = auth_result.get('ExpiresIn', 3600)
            
            # Get user information
            user = await self._get_user_from_token(access_token)
            
            return AuthenticationResponse(
                access_token=access_token,
                refresh_token=refresh_token,  # Refresh token usually stays the same
                expires_in=expires_in,
                user=user
            )
            
        except ClientError as e:
            logger.error(f"Token refresh error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected token refresh error: {e}")
            return None
    
    async def logout_user(self, access_token: str) -> bool:
        """Logout user and invalidate token"""
        try:
            if not self._cognito_client:
                return False
            
            # Global sign out (invalidates all tokens)
            self._cognito_client.global_sign_out(AccessToken=access_token)
            return True
            
        except ClientError as e:
            logger.error(f"Logout error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected logout error: {e}")
            return False
