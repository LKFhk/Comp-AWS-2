"""
Comprehensive Authentication and Authorization Tests
Tests OAuth 2.0, RBAC, multi-tenant isolation, and audit trail functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from riskintel360.auth.models import (
    User, Role, Permission, RoleType, PermissionType, ResourceType,
    UserStatus, AuditAction, SecurityContext, AuthenticationRequest,
    AuthenticationResponse
)
from riskintel360.auth.cognito_client import CognitoClient, CognitoAuthenticationError
from riskintel360.auth.rbac import RoleBasedAccessControl
from riskintel360.auth.multi_tenant import MultiTenantManager, TenantInfo
from riskintel360.auth.audit_logger import AuditLogger
from riskintel360.auth.auth_decorators import (
    require_role, require_permission, audit_trail, get_current_user
)


class TestCognitoClient:
    """Test AWS Cognito OAuth 2.0 integration"""
    
    @pytest.fixture
    def cognito_client(self):
        """Create Cognito client for testing"""
        with patch('boto3.client'):
            client = CognitoClient()
            client._cognito_client = Mock()
            client._client_id = "test-client-id"
            client._client_secret = "test-client-secret"
            client._user_pool_id = "test-user-pool-id"
            return client
    
    @pytest.fixture
    def mock_cognito_response(self):
        """Mock Cognito authentication response"""
        return {
            'AuthenticationResult': {
                'AccessToken': 'mock-access-token',
                'RefreshToken': 'mock-refresh-token',
                'ExpiresIn': 3600
            }
        }
    
    @pytest.fixture
    def mock_user_response(self):
        """Mock Cognito get user response"""
        return {
            'Username': 'testuser',
            'UserAttributes': [
                {'Name': 'email', 'Value': 'test@example.com'},
                {'Name': 'given_name', 'Value': 'Test'},
                {'Name': 'family_name', 'Value': 'User'},
                {'Name': 'custom:tenant_id', 'Value': 'test-tenant'}
            ]
        }
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, cognito_client, mock_cognito_response, mock_user_response):
        """Test successful user authentication"""
        # Setup mocks
        cognito_client._cognito_client.initiate_auth.return_value = mock_cognito_response
        cognito_client._cognito_client.get_user.return_value = mock_user_response
        cognito_client._cognito_client.admin_list_groups_for_user.return_value = {
            'Groups': [{'GroupName': 'analyst', 'Description': 'Business Analyst'}]
        }
        
        # Test authentication
        request = AuthenticationRequest(
            username="testuser",
            password="testpass123"
        )
        
        response = await cognito_client.authenticate_user(request)
        
        # Verify response
        assert isinstance(response, AuthenticationResponse)
        assert response.access_token == "mock-access-token"
        assert response.refresh_token == "mock-refresh-token"
        assert response.expires_in == 3600
        assert response.user.username == "testuser"
        assert response.user.email == "test@example.com"
        assert response.user.tenant_id == "test-tenant"
        assert len(response.user.roles) > 0
        
        # Verify Cognito calls
        cognito_client._cognito_client.initiate_auth.assert_called_once()
        cognito_client._cognito_client.get_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self, cognito_client):
        """Test authentication with invalid credentials"""
        from botocore.exceptions import ClientError
        
        # Setup mock to raise authentication error
        error_response = {
            'Error': {
                'Code': 'NotAuthorizedException',
                'Message': 'Incorrect username or password.'
            }
        }
        cognito_client._cognito_client.initiate_auth.side_effect = ClientError(
            error_response, 'InitiateAuth'
        )
        
        # Test authentication failure
        request = AuthenticationRequest(
            username="testuser",
            password="wrongpass"
        )
        
        with pytest.raises(CognitoAuthenticationError, match="Invalid username or password"):
            await cognito_client.authenticate_user(request)
    
    @pytest.mark.asyncio
    async def test_validate_token_success(self, cognito_client, mock_user_response):
        """Test successful token validation"""
        # Setup mock
        cognito_client._cognito_client.get_user.return_value = mock_user_response
        cognito_client._cognito_client.admin_list_groups_for_user.return_value = {
            'Groups': []
        }
        
        # Test token validation
        user = await cognito_client.validate_token("valid-token")
        
        # Verify user
        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.status == UserStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, cognito_client):
        """Test token validation with invalid token"""
        from botocore.exceptions import ClientError
        
        # Setup mock to raise error
        error_response = {
            'Error': {
                'Code': 'NotAuthorizedException',
                'Message': 'Invalid Access Token'
            }
        }
        cognito_client._cognito_client.get_user.side_effect = ClientError(
            error_response, 'GetUser'
        )
        
        # Test token validation failure
        user = await cognito_client.validate_token("invalid-token")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, cognito_client, mock_user_response):
        """Test successful token refresh"""
        # Setup mocks
        refresh_response = {
            'AuthenticationResult': {
                'AccessToken': 'new-access-token',
                'ExpiresIn': 3600
            }
        }
        cognito_client._cognito_client.initiate_auth.return_value = refresh_response
        cognito_client._cognito_client.get_user.return_value = mock_user_response
        cognito_client._cognito_client.admin_list_groups_for_user.return_value = {
            'Groups': []
        }
        
        # Test token refresh
        response = await cognito_client.refresh_token("valid-refresh-token")
        
        # Verify response
        assert response is not None
        assert response.access_token == "new-access-token"
        assert response.expires_in == 3600
    
    @pytest.mark.asyncio
    async def test_logout_user_success(self, cognito_client):
        """Test successful user logout"""
        # Setup mock
        cognito_client._cognito_client.global_sign_out.return_value = {}
        
        # Test logout
        success = await cognito_client.logout_user("valid-token")
        
        # Verify logout
        assert success is True
        cognito_client._cognito_client.global_sign_out.assert_called_once_with(
            AccessToken="valid-token"
        )


class TestRoleBasedAccessControl:
    """Test Role-Based Access Control system"""
    
    @pytest.fixture
    def rbac(self):
        """Create RBAC instance for testing"""
        return RoleBasedAccessControl()
    
    @pytest.fixture
    def test_user(self):
        """Create test user with analyst role"""
        analyst_role = Role(
            id="analyst",
            name="Business Analyst",
            role_type=RoleType.ANALYST,
            permissions=[
                Permission(
                    id="validation_request_read",
                    name="Read Validation Requests",
                    resource_type=ResourceType.VALIDATION_REQUEST,
                    permission_type=PermissionType.READ
                ),
                Permission(
                    id="validation_request_write",
                    name="Write Validation Requests",
                    resource_type=ResourceType.VALIDATION_REQUEST,
                    permission_type=PermissionType.WRITE
                )
            ],
            is_active=True
        )
        
        return User(
            id="test-user-1",
            username="testuser",
            email="test@example.com",
            tenant_id="test-tenant",
            roles=[analyst_role],
            status=UserStatus.ACTIVE
        )
    
    def test_initialize_default_roles(self, rbac):
        """Test default roles initialization"""
        # Verify default roles exist
        admin_role = rbac.get_role("admin")
        analyst_role = rbac.get_role("analyst")
        viewer_role = rbac.get_role("viewer")
        api_role = rbac.get_role("api_user")
        
        assert admin_role is not None
        assert analyst_role is not None
        assert viewer_role is not None
        assert api_role is not None
        
        # Verify role types
        assert admin_role.role_type == RoleType.ADMIN
        assert analyst_role.role_type == RoleType.ANALYST
        assert viewer_role.role_type == RoleType.VIEWER
        assert api_role.role_type == RoleType.API_USER
        
        # Verify admin has most permissions
        assert len(admin_role.permissions) > len(analyst_role.permissions)
        assert len(analyst_role.permissions) > len(viewer_role.permissions)
    
    def test_check_permission_direct(self, rbac, test_user):
        """Test direct permission checking"""
        # Test user has read permission
        has_read = rbac.check_permission(
            test_user,
            ResourceType.VALIDATION_REQUEST,
            PermissionType.READ
        )
        assert has_read is True
        
        # Test user has write permission
        has_write = rbac.check_permission(
            test_user,
            ResourceType.VALIDATION_REQUEST,
            PermissionType.WRITE
        )
        assert has_write is True
        
        # Test user doesn't have delete permission
        has_delete = rbac.check_permission(
            test_user,
            ResourceType.VALIDATION_REQUEST,
            PermissionType.DELETE
        )
        assert has_delete is False
    
    def test_check_permission_inherited(self, rbac):
        """Test inherited permission checking through role hierarchy"""
        # Get admin user
        admin_role = rbac.get_role("admin")
        admin_user = User(
            id="admin-user",
            username="admin",
            email="admin@example.com",
            tenant_id="test-tenant",
            roles=[admin_role],
            status=UserStatus.ACTIVE
        )
        
        # Admin should have all permissions
        has_read = rbac.check_permission(
            admin_user,
            ResourceType.VALIDATION_REQUEST,
            PermissionType.READ
        )
        assert has_read is True
        
        has_admin = rbac.check_permission(
            admin_user,
            ResourceType.USER_MANAGEMENT,
            PermissionType.ADMIN
        )
        assert has_admin is True
    
    def test_create_custom_role(self, rbac):
        """Test custom role creation"""
        # Create custom role
        custom_role = rbac.create_custom_role(
            role_id="custom_analyst",
            name="Custom Analyst",
            description="Custom analyst role for testing",
            permission_ids=["validation_request_read", "market_data_read"]
        )
        
        # Verify role creation
        assert custom_role.id == "custom_analyst"
        assert custom_role.name == "Custom Analyst"
        assert len(custom_role.permissions) == 2
        
        # Verify role is stored
        stored_role = rbac.get_role("custom_analyst")
        assert stored_role is not None
        assert stored_role.id == "custom_analyst"
    
    def test_assign_role_to_user(self, rbac, test_user):
        """Test role assignment to user"""
        # Get viewer role
        viewer_role = rbac.get_role("viewer")
        
        # Assign role to user
        success = rbac.assign_role_to_user(test_user, "viewer")
        assert success is True
        
        # Verify role assignment
        assert len(test_user.roles) == 2  # Original analyst + new viewer
        role_ids = [role.id for role in test_user.roles]
        assert "viewer" in role_ids
    
    def test_remove_role_from_user(self, rbac, test_user):
        """Test role removal from user"""
        # Remove analyst role
        success = rbac.remove_role_from_user(test_user, "analyst")
        assert success is True
        
        # Verify role removal
        role_ids = [role.id for role in test_user.roles]
        assert "analyst" not in role_ids
    
    def test_get_user_permissions(self, rbac, test_user):
        """Test getting all user permissions"""
        permissions = rbac.get_user_permissions(test_user)
        
        # Verify permissions returned
        assert len(permissions) > 0
        
        # Check for expected permissions
        permission_ids = [p.id for p in permissions]
        assert "validation_request_read" in permission_ids
        assert "validation_request_write" in permission_ids


class TestMultiTenantManager:
    """Test Multi-Tenant data isolation system"""
    
    @pytest.fixture
    def tenant_manager(self):
        """Create tenant manager for testing"""
        return MultiTenantManager()
    
    @pytest.fixture
    def test_tenant(self, tenant_manager):
        """Create test tenant"""
        return tenant_manager.create_tenant(
            name="Test Company",
            description="Test tenant for unit tests"
        )
    
    def test_initialize_default_tenant(self, tenant_manager):
        """Test default tenant initialization"""
        default_tenant = tenant_manager.get_tenant("default")
        
        assert default_tenant is not None
        assert default_tenant.tenant_id == "default"
        assert default_tenant.name == "Default Tenant"
        assert default_tenant.is_active is True
    
    def test_create_tenant(self, tenant_manager):
        """Test tenant creation"""
        tenant = tenant_manager.create_tenant(
            name="New Company",
            description="New test tenant",
            metadata={"industry": "technology"}
        )
        
        # Verify tenant creation
        assert tenant.tenant_id is not None
        assert tenant.name == "New Company"
        assert tenant.description == "New test tenant"
        assert tenant.metadata["industry"] == "technology"
        assert tenant.is_active is True
        
        # Verify tenant is stored
        stored_tenant = tenant_manager.get_tenant(tenant.tenant_id)
        assert stored_tenant is not None
        assert stored_tenant.name == "New Company"
    
    def test_assign_user_to_tenant(self, tenant_manager, test_tenant):
        """Test user assignment to tenant"""
        user_id = "test-user-1"
        
        # Assign user to tenant
        success = tenant_manager.assign_user_to_tenant(user_id, test_tenant.tenant_id)
        assert success is True
        
        # Verify assignment
        user_tenant_id = tenant_manager.get_user_tenant(user_id)
        assert user_tenant_id == test_tenant.tenant_id
        
        # Verify user in tenant users list
        tenant_users = tenant_manager.get_tenant_users(test_tenant.tenant_id)
        assert user_id in tenant_users
    
    def test_validate_tenant_access_same_tenant(self, tenant_manager, test_tenant):
        """Test tenant access validation for same tenant"""
        # Create security context
        user = User(
            id="test-user",
            username="testuser",
            email="test@example.com",
            tenant_id=test_tenant.tenant_id,
            status=UserStatus.ACTIVE
        )
        
        security_context = SecurityContext(
            user=user,
            tenant_id=test_tenant.tenant_id
        )
        
        # Test same tenant access
        has_access = tenant_manager.validate_tenant_access(
            security_context,
            test_tenant.tenant_id,
            ResourceType.VALIDATION_REQUEST
        )
        assert has_access is True
    
    def test_validate_tenant_access_cross_tenant_strict(self, tenant_manager):
        """Test cross-tenant access with strict isolation"""
        # Create two tenants
        tenant1 = tenant_manager.create_tenant("Tenant 1")
        tenant2 = tenant_manager.create_tenant("Tenant 2")
        
        # Configure strict isolation
        tenant_manager.configure_tenant_isolation(tenant1.tenant_id, "strict")
        
        # Create security context for tenant1 user
        user = User(
            id="test-user",
            username="testuser",
            email="test@example.com",
            tenant_id=tenant1.tenant_id,
            status=UserStatus.ACTIVE
        )
        
        security_context = SecurityContext(
            user=user,
            tenant_id=tenant1.tenant_id
        )
        
        # Test cross-tenant access (should be denied)
        has_access = tenant_manager.validate_tenant_access(
            security_context,
            tenant2.tenant_id,
            ResourceType.VALIDATION_REQUEST
        )
        assert has_access is False
    
    def test_filter_resources_by_tenant(self, tenant_manager, test_tenant):
        """Test resource filtering by tenant"""
        # Create security context
        user = User(
            id="test-user",
            username="testuser",
            email="test@example.com",
            tenant_id=test_tenant.tenant_id,
            status=UserStatus.ACTIVE
        )
        
        security_context = SecurityContext(
            user=user,
            tenant_id=test_tenant.tenant_id
        )
        
        # Create test resources
        resources = [
            {"id": "resource1", "tenant_id": test_tenant.tenant_id, "name": "Resource 1"},
            {"id": "resource2", "tenant_id": "other-tenant", "name": "Resource 2"},
            {"id": "resource3", "tenant_id": test_tenant.tenant_id, "name": "Resource 3"},
        ]
        
        # Filter resources
        filtered = tenant_manager.filter_resources_by_tenant(
            security_context,
            resources
        )
        
        # Verify filtering
        assert len(filtered) == 2
        resource_ids = [r["id"] for r in filtered]
        assert "resource1" in resource_ids
        assert "resource3" in resource_ids
        assert "resource2" not in resource_ids
    
    def test_validate_tenant_limits(self, tenant_manager, test_tenant):
        """Test tenant resource limits validation"""
        # Assign users to test limits
        for i in range(3):
            tenant_manager.assign_user_to_tenant(f"user-{i}", test_tenant.tenant_id)
        
        # Validate limits
        limits_status = tenant_manager.validate_tenant_limits(test_tenant.tenant_id)
        
        # Verify limits validation
        assert limits_status["valid"] is True
        assert limits_status["limits"]["users"]["current"] == 3
        assert limits_status["limits"]["users"]["max"] == 1000
        assert limits_status["limits"]["users"]["exceeded"] is False


class TestAuditLogger:
    """Test Audit Trail logging system"""
    
    @pytest.fixture
    def audit_logger(self):
        """Create audit logger for testing"""
        with patch('boto3.client'):
            logger = AuditLogger()
            logger._dynamodb_client = Mock()
            logger._cloudwatch_client = Mock()
            logger._cloudtrail_client = Mock()
            logger._audit_table_name = "test-audit-table"
            return logger
    
    @pytest.fixture
    def security_context(self):
        """Create security context for testing"""
        user = User(
            id="test-user",
            username="testuser",
            email="test@example.com",
            tenant_id="test-tenant",
            status=UserStatus.ACTIVE
        )
        
        return SecurityContext(
            user=user,
            tenant_id="test-tenant",
            ip_address="192.168.1.1",
            user_agent="Test User Agent"
        )
    
    @pytest.mark.asyncio
    async def test_log_action_success(self, audit_logger, security_context):
        """Test successful action logging"""
        # Mock DynamoDB put_item
        audit_logger._dynamodb_client.put_item.return_value = {}
        audit_logger._cloudwatch_client.put_metric_data.return_value = {}
        
        # Log action
        await audit_logger.log_action(
            security_context=security_context,
            action=AuditAction.CREATE,
            resource_type=ResourceType.VALIDATION_REQUEST,
            resource_id="test-resource-1",
            success=True
        )
        
        # Verify DynamoDB call
        audit_logger._dynamodb_client.put_item.assert_called_once()
        call_args = audit_logger._dynamodb_client.put_item.call_args
        
        # Verify audit entry data
        item = call_args[1]['Item']
        assert item['user_id']['S'] == "test-user"
        assert item['tenant_id']['S'] == "test-tenant"
        assert item['action']['S'] == "create"
        assert item['resource_type']['S'] == "validation_request"
        assert item['resource_id']['S'] == "test-resource-1"
        assert item['success']['BOOL'] is True
        assert item['ip_address']['S'] == "192.168.1.1"
        
        # Verify CloudWatch metrics call
        audit_logger._cloudwatch_client.put_metric_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_authentication_success(self, audit_logger):
        """Test authentication event logging"""
        # Mock DynamoDB and CloudWatch
        audit_logger._dynamodb_client.put_item.return_value = {}
        audit_logger._cloudwatch_client.put_metric_data.return_value = {}
        
        # Log authentication
        await audit_logger.log_authentication(
            user_id="test-user",
            action=AuditAction.LOGIN,
            success=True,
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )
        
        # Verify logging
        audit_logger._dynamodb_client.put_item.assert_called_once()
        call_args = audit_logger._dynamodb_client.put_item.call_args
        item = call_args[1]['Item']
        
        assert item['action']['S'] == "login"
        assert item['success']['BOOL'] is True
        assert item['ip_address']['S'] == "192.168.1.1"
    
    @pytest.mark.asyncio
    async def test_log_access_denied(self, audit_logger, security_context):
        """Test access denied logging"""
        # Mock DynamoDB and CloudWatch
        audit_logger._dynamodb_client.put_item.return_value = {}
        audit_logger._cloudwatch_client.put_metric_data.return_value = {}
        
        # Log access denied
        await audit_logger.log_access_denied(
            security_context,
            "Insufficient permissions for admin access"
        )
        
        # Verify logging
        audit_logger._dynamodb_client.put_item.assert_called_once()
        call_args = audit_logger._dynamodb_client.put_item.call_args
        item = call_args[1]['Item']
        
        assert item['action']['S'] == "access_denied"
        assert item['success']['BOOL'] is False
        assert "Insufficient permissions" in item['error_message']['S']


class TestAuthenticationDecorators:
    """Test authentication and authorization decorators"""
    
    @pytest.fixture
    def mock_security_context(self):
        """Create mock security context"""
        user = User(
            id="test-user",
            username="testuser",
            email="test@example.com",
            tenant_id="test-tenant",
            roles=[
                Role(
                    id="analyst",
                    name="Analyst",
                    role_type=RoleType.ANALYST,
                    permissions=[
                        Permission(
                            id="validation_read",
                            name="Read Validations",
                            resource_type=ResourceType.VALIDATION_REQUEST,
                            permission_type=PermissionType.READ
                        )
                    ],
                    is_active=True
                )
            ],
            status=UserStatus.ACTIVE
        )
        
        return SecurityContext(
            user=user,
            tenant_id="test-tenant"
        )
    
    @pytest.mark.asyncio
    async def test_require_role_decorator_success(self, mock_security_context):
        """Test require_role decorator with valid role"""
        @require_role([RoleType.ANALYST])
        async def test_function(security_context: SecurityContext):
            return "success"
        
        # Test with valid role
        result = await test_function(mock_security_context)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_require_role_decorator_failure(self, mock_security_context):
        """Test require_role decorator with invalid role"""
        from fastapi import HTTPException
        
        @require_role([RoleType.ADMIN])
        async def test_function(security_context: SecurityContext):
            return "success"
        
        # Test with invalid role
        with pytest.raises(HTTPException) as exc_info:
            await test_function(mock_security_context)
        
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_require_permission_decorator_success(self, mock_security_context):
        """Test require_permission decorator with valid permission"""
        @require_permission(ResourceType.VALIDATION_REQUEST, PermissionType.READ)
        async def test_function(security_context: SecurityContext):
            return "success"
        
        # Test with valid permission
        result = await test_function(mock_security_context)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_require_permission_decorator_failure(self, mock_security_context):
        """Test require_permission decorator with invalid permission"""
        from fastapi import HTTPException
        
        @require_permission(ResourceType.VALIDATION_REQUEST, PermissionType.DELETE)
        async def test_function(security_context: SecurityContext):
            return "success"
        
        # Test with invalid permission
        with pytest.raises(HTTPException) as exc_info:
            await test_function(mock_security_context)
        
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_audit_trail_decorator_success(self, mock_security_context):
        """Test audit_trail decorator for successful action"""
        with patch('riskintel360.auth.auth_decorators.get_audit_logger') as mock_get_logger:
            mock_audit_logger = Mock()
            mock_audit_logger.log_action = AsyncMock()
            mock_get_logger.return_value = mock_audit_logger
            
            @audit_trail(AuditAction.READ, ResourceType.VALIDATION_REQUEST, "resource_id")
            async def test_function(security_context: SecurityContext, resource_id: str):
                return "success"
            
            # Test successful action
            result = await test_function(mock_security_context, resource_id="test-resource")
            assert result == "success"
            
            # Verify audit logging
            mock_audit_logger.log_action.assert_called_once()
            call_args = mock_audit_logger.log_action.call_args
            assert call_args[1]['action'] == AuditAction.READ
            assert call_args[1]['resource_type'] == ResourceType.VALIDATION_REQUEST
            assert call_args[1]['resource_id'] == "test-resource"
            assert call_args[1]['success'] is True
    
    @pytest.mark.asyncio
    async def test_audit_trail_decorator_failure(self, mock_security_context):
        """Test audit_trail decorator for failed action"""
        with patch('riskintel360.auth.auth_decorators.get_audit_logger') as mock_get_logger:
            mock_audit_logger = Mock()
            mock_audit_logger.log_action = AsyncMock()
            mock_get_logger.return_value = mock_audit_logger
            
            @audit_trail(AuditAction.CREATE, ResourceType.VALIDATION_REQUEST)
            async def test_function(security_context: SecurityContext):
                raise ValueError("Test error")
            
            # Test failed action
            with pytest.raises(ValueError):
                await test_function(mock_security_context)
            
            # Verify audit logging
            mock_audit_logger.log_action.assert_called_once()
            call_args = mock_audit_logger.log_action.call_args
            assert call_args[1]['success'] is False
            assert call_args[1]['error_message'] == "Test error"


class TestIntegrationScenarios:
    """Test end-to-end authentication and authorization scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_authentication_flow(self):
        """Test complete authentication flow from login to resource access"""
        # This would be an integration test that combines all components
        # For now, we'll test the key integration points
        
        # 1. Initialize components
        with patch('boto3.client'):
            cognito_client = CognitoClient()
            cognito_client._cognito_client = Mock()
            cognito_client._client_id = "test-client"
            
            rbac = RoleBasedAccessControl()
            tenant_manager = MultiTenantManager()
            audit_logger = AuditLogger()
            audit_logger._dynamodb_client = Mock()
            audit_logger._cloudwatch_client = Mock()
        
        # 2. Mock successful authentication
        mock_auth_response = {
            'AuthenticationResult': {
                'AccessToken': 'test-token',
                'RefreshToken': 'refresh-token',
                'ExpiresIn': 3600
            }
        }
        
        mock_user_response = {
            'Username': 'testuser',
            'UserAttributes': [
                {'Name': 'email', 'Value': 'test@example.com'},
                {'Name': 'custom:tenant_id', 'Value': 'test-tenant'}
            ]
        }
        
        cognito_client._cognito_client.initiate_auth.return_value = mock_auth_response
        cognito_client._cognito_client.get_user.return_value = mock_user_response
        cognito_client._cognito_client.admin_list_groups_for_user.return_value = {
            'Groups': [{'GroupName': 'analyst', 'Description': 'Analyst'}]
        }
        
        # 3. Authenticate user
        auth_request = AuthenticationRequest(username="testuser", password="password")
        auth_response = await cognito_client.authenticate_user(auth_request)
        
        # 4. Verify authentication
        assert auth_response.access_token == "test-token"
        assert auth_response.user.username == "testuser"
        assert len(auth_response.user.roles) > 0
        
        # 5. Test authorization
        user = auth_response.user
        has_permission = rbac.check_permission(
            user,
            ResourceType.VALIDATION_REQUEST,
            PermissionType.READ
        )
        assert has_permission is True
        
        # 6. Test tenant isolation
        security_context = SecurityContext(
            user=user,
            tenant_id=user.tenant_id
        )
        
        tenant_access = tenant_manager.validate_tenant_access(
            security_context,
            user.tenant_id,
            ResourceType.VALIDATION_REQUEST
        )
        assert tenant_access is True
        
        # 7. Test audit logging
        audit_logger._dynamodb_client.put_item.return_value = {}
        audit_logger._cloudwatch_client.put_metric_data.return_value = {}
        
        await audit_logger.log_action(
            security_context=security_context,
            action=AuditAction.READ,
            resource_type=ResourceType.VALIDATION_REQUEST,
            success=True
        )
        
        # Verify audit log was called
        audit_logger._dynamodb_client.put_item.assert_called_once()
    
    def test_security_configuration_validation(self):
        """Test security configuration validation"""
        # Test that all security components can be initialized
        # and have proper configuration
        
        with patch('boto3.client'):
            # Test Cognito client initialization
            cognito_client = CognitoClient()
            assert cognito_client is not None
            
            # Test RBAC initialization
            rbac = RoleBasedAccessControl()
            assert len(rbac._roles) > 0
            assert len(rbac._permissions) > 0
            
            # Test tenant manager initialization
            tenant_manager = MultiTenantManager()
            default_tenant = tenant_manager.get_tenant("default")
            assert default_tenant is not None
            
            # Test audit logger initialization
            audit_logger = AuditLogger()
            assert audit_logger is not None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
