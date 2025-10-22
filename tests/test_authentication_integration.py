"""
Integration Tests for Authentication System
Tests the complete authentication flow with real AWS services (when available).
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch
from typing import Dict, Any

from riskintel360.auth.cognito_client import CognitoClient, CognitoAuthenticationError
from riskintel360.auth.rbac import RoleBasedAccessControl
from riskintel360.auth.multi_tenant import MultiTenantManager
from riskintel360.auth.audit_logger import AuditLogger
from riskintel360.auth.models import (
    AuthenticationRequest, RoleType, ResourceType, PermissionType,
    AuditAction, SecurityContext
)


class TestAuthenticationIntegration:
    """Integration tests for authentication system"""
    
    @pytest.fixture
    def mock_aws_services(self):
        """Mock AWS services for integration testing"""
        with patch('boto3.client') as mock_boto_client:
            # Mock Cognito client
            mock_cognito = Mock()
            mock_dynamodb = Mock()
            mock_cloudwatch = Mock()
            
            def client_factory(service_name, **kwargs):
                if service_name == 'cognito-idp':
                    return mock_cognito
                elif service_name == 'dynamodb':
                    return mock_dynamodb
                elif service_name == 'cloudwatch':
                    return mock_cloudwatch
                else:
                    return Mock()
            
            mock_boto_client.side_effect = client_factory
            
            yield {
                'cognito': mock_cognito,
                'dynamodb': mock_dynamodb,
                'cloudwatch': mock_cloudwatch
            }
    
    @pytest.mark.asyncio
    async def test_complete_authentication_workflow(self, mock_aws_services):
        """Test complete authentication workflow from login to resource access"""
        
        # 1. Set up mock responses
        mock_cognito = mock_aws_services['cognito']
        mock_dynamodb = mock_aws_services['dynamodb']
        mock_cloudwatch = mock_aws_services['cloudwatch']
        
        # Mock successful authentication
        mock_cognito.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'test-access-token',
                'RefreshToken': 'test-refresh-token',
                'ExpiresIn': 3600
            }
        }
        
        # Mock user details
        mock_cognito.get_user.return_value = {
            'Username': 'test_analyst',
            'UserAttributes': [
                {'Name': 'email', 'Value': 'analyst@RiskIntel360.com'},
                {'Name': 'given_name', 'Value': 'Test'},
                {'Name': 'family_name', 'Value': 'Analyst'},
                {'Name': 'custom:tenant_id', 'Value': 'test-company'}
            ]
        }
        
        # Mock user groups
        mock_cognito.admin_list_groups_for_user.return_value = {
            'Groups': [
                {'GroupName': 'analyst', 'Description': 'Business Analyst'}
            ]
        }
        
        # Mock DynamoDB and CloudWatch
        mock_dynamodb.put_item.return_value = {}
        mock_cloudwatch.put_metric_data.return_value = {}
        
        # 2. Initialize authentication components
        cognito_client = CognitoClient()
        # Set up the mock client properly
        cognito_client._cognito_client = mock_cognito
        cognito_client._client_id = "test-client-id"
        cognito_client._user_pool_id = "test-user-pool-id"
        
        rbac = RoleBasedAccessControl()
        tenant_manager = MultiTenantManager()
        audit_logger = AuditLogger()
        
        # 3. Test authentication
        auth_request = AuthenticationRequest(
            username="test_analyst",
            password="TestPass123!"
        )
        
        auth_response = await cognito_client.authenticate_user(auth_request)
        
        # Verify authentication response
        assert auth_response.access_token == "test-access-token"
        assert auth_response.refresh_token == "test-refresh-token"
        assert auth_response.expires_in == 3600
        assert auth_response.user.username == "test_analyst"
        assert auth_response.user.email == "analyst@RiskIntel360.com"
        assert auth_response.user.tenant_id == "test-company"
        assert len(auth_response.user.roles) == 1
        assert auth_response.user.roles[0].role_type == RoleType.ANALYST
        
        # 4. Test authorization (RBAC)
        user = auth_response.user
        
        # Test analyst permissions
        has_read_permission = rbac.check_permission(
            user, ResourceType.VALIDATION_REQUEST, PermissionType.READ
        )
        assert has_read_permission is True
        
        has_write_permission = rbac.check_permission(
            user, ResourceType.VALIDATION_REQUEST, PermissionType.WRITE
        )
        assert has_write_permission is True
        
        has_admin_permission = rbac.check_permission(
            user, ResourceType.USER_MANAGEMENT, PermissionType.ADMIN
        )
        assert has_admin_permission is False
        
        # 5. Test multi-tenant isolation
        security_context = SecurityContext(
            user=user,
            tenant_id=user.tenant_id,
            ip_address="192.168.1.100",
            user_agent="Test Client"
        )
        
        # Same tenant access should be allowed
        same_tenant_access = tenant_manager.validate_tenant_access(
            security_context,
            user.tenant_id,
            ResourceType.VALIDATION_REQUEST
        )
        assert same_tenant_access is True
        
        # Different tenant access should be denied (strict isolation)
        different_tenant_access = tenant_manager.validate_tenant_access(
            security_context,
            "other-company",
            ResourceType.VALIDATION_REQUEST
        )
        assert different_tenant_access is False
        
        # 6. Test audit logging
        await audit_logger.log_action(
            security_context=security_context,
            action=AuditAction.READ,
            resource_type=ResourceType.VALIDATION_REQUEST,
            resource_id="test-validation-123",
            success=True
        )
        
        # Verify audit log was called
        mock_dynamodb.put_item.assert_called()
        mock_cloudwatch.put_metric_data.assert_called()
        
        # 7. Test token validation
        validated_user = await cognito_client.validate_token("test-access-token")
        assert validated_user is not None
        assert validated_user.username == "test_analyst"
        
        # 8. Test token refresh
        refresh_response = await cognito_client.refresh_token("test-refresh-token")
        assert refresh_response is not None
        assert refresh_response.access_token is not None
        
        # 9. Test logout
        mock_cognito.global_sign_out.return_value = {}
        logout_success = await cognito_client.logout_user("test-access-token")
        assert logout_success is True
        
        print("??Complete authentication workflow test passed!")
    
    @pytest.mark.asyncio
    async def test_authentication_failure_scenarios(self, mock_aws_services):
        """Test authentication failure scenarios"""
        
        mock_cognito = mock_aws_services['cognito']
        
        # Test invalid credentials
        from botocore.exceptions import ClientError
        mock_cognito.initiate_auth.side_effect = ClientError(
            {'Error': {'Code': 'NotAuthorizedException', 'Message': 'Incorrect username or password.'}},
            'InitiateAuth'
        )
        
        cognito_client = CognitoClient()
        # Set up the mock client properly
        cognito_client._cognito_client = mock_cognito
        cognito_client._client_id = "test-client-id"
        cognito_client._user_pool_id = "test-user-pool-id"
        
        auth_request = AuthenticationRequest(
            username="invalid_user",
            password="wrongpassword"
        )
        
        with pytest.raises(CognitoAuthenticationError, match="Invalid username or password"):
            await cognito_client.authenticate_user(auth_request)
        
        print("??Authentication failure scenarios test passed!")
    
    @pytest.mark.asyncio
    async def test_role_based_access_control_scenarios(self):
        """Test various RBAC scenarios"""
        
        rbac = RoleBasedAccessControl()
        
        # Test admin role has all permissions
        admin_role = rbac.get_role("admin")
        assert admin_role is not None
        
        # Admin should have more permissions than other roles
        analyst_role = rbac.get_role("analyst")
        viewer_role = rbac.get_role("viewer")
        api_role = rbac.get_role("api_user")
        
        assert len(admin_role.permissions) > len(analyst_role.permissions)
        assert len(analyst_role.permissions) > len(viewer_role.permissions)
        
        # Test permission inheritance
        from riskintel360.auth.models import User, UserStatus
        
        admin_user = User(
            id="admin-1",
            username="admin",
            email="admin@test.com",
            tenant_id="test",
            roles=[admin_role],
            status=UserStatus.ACTIVE
        )
        
        # Admin should have all permissions
        assert rbac.check_permission(admin_user, ResourceType.USER_MANAGEMENT, PermissionType.ADMIN)
        assert rbac.check_permission(admin_user, ResourceType.VALIDATION_REQUEST, PermissionType.READ)
        assert rbac.check_permission(admin_user, ResourceType.VALIDATION_REQUEST, PermissionType.WRITE)
        assert rbac.check_permission(admin_user, ResourceType.VALIDATION_REQUEST, PermissionType.DELETE)
        
        print("??RBAC scenarios test passed!")
    
    @pytest.mark.asyncio
    async def test_multi_tenant_isolation_scenarios(self):
        """Test multi-tenant isolation scenarios"""
        
        tenant_manager = MultiTenantManager()
        
        # Create test tenants
        tenant_a = tenant_manager.create_tenant("Company A", "Test company A")
        tenant_b = tenant_manager.create_tenant("Company B", "Test company B")
        
        # Assign users to tenants
        tenant_manager.assign_user_to_tenant("user-a", tenant_a.tenant_id)
        tenant_manager.assign_user_to_tenant("user-b", tenant_b.tenant_id)
        
        # Test tenant isolation
        from riskintel360.auth.models import User, UserStatus
        
        user_a = User(
            id="user-a",
            username="usera",
            email="usera@companya.com",
            tenant_id=tenant_a.tenant_id,
            status=UserStatus.ACTIVE
        )
        
        security_context_a = SecurityContext(
            user=user_a,
            tenant_id=tenant_a.tenant_id
        )
        
        # User A should access their own tenant
        assert tenant_manager.validate_tenant_access(
            security_context_a, tenant_a.tenant_id, ResourceType.VALIDATION_REQUEST
        ) is True
        
        # User A should NOT access tenant B (strict isolation)
        assert tenant_manager.validate_tenant_access(
            security_context_a, tenant_b.tenant_id, ResourceType.VALIDATION_REQUEST
        ) is False
        
        # Test resource filtering
        resources = [
            {"id": "res-1", "tenant_id": tenant_a.tenant_id, "name": "Resource A1"},
            {"id": "res-2", "tenant_id": tenant_b.tenant_id, "name": "Resource B1"},
            {"id": "res-3", "tenant_id": tenant_a.tenant_id, "name": "Resource A2"},
        ]
        
        filtered = tenant_manager.filter_resources_by_tenant(security_context_a, resources)
        assert len(filtered) == 2
        assert all(r["tenant_id"] == tenant_a.tenant_id for r in filtered)
        
        print("??Multi-tenant isolation scenarios test passed!")
    
    @pytest.mark.asyncio
    async def test_audit_trail_scenarios(self, mock_aws_services):
        """Test audit trail scenarios"""
        
        mock_dynamodb = mock_aws_services['dynamodb']
        mock_cloudwatch = mock_aws_services['cloudwatch']
        
        mock_dynamodb.put_item.return_value = {}
        mock_cloudwatch.put_metric_data.return_value = {}
        
        audit_logger = AuditLogger()
        
        from riskintel360.auth.models import User, UserStatus
        
        user = User(
            id="test-user",
            username="testuser",
            email="test@example.com",
            tenant_id="test-tenant",
            status=UserStatus.ACTIVE
        )
        
        security_context = SecurityContext(
            user=user,
            tenant_id="test-tenant",
            ip_address="192.168.1.1",
            user_agent="Test Browser"
        )
        
        # Test successful action logging
        await audit_logger.log_action(
            security_context=security_context,
            action=AuditAction.CREATE,
            resource_type=ResourceType.VALIDATION_REQUEST,
            resource_id="validation-123",
            success=True
        )
        
        # Test failed action logging
        await audit_logger.log_action(
            security_context=security_context,
            action=AuditAction.DELETE,
            resource_type=ResourceType.VALIDATION_REQUEST,
            resource_id="validation-456",
            success=False,
            error_message="Permission denied"
        )
        
        # Test authentication logging
        await audit_logger.log_authentication(
            user_id="test-user",
            action=AuditAction.LOGIN,
            success=True,
            ip_address="192.168.1.1"
        )
        
        # Test access denied logging
        await audit_logger.log_access_denied(
            security_context,
            "Insufficient permissions for admin access"
        )
        
        # Verify all audit calls were made
        assert mock_dynamodb.put_item.call_count >= 4
        assert mock_cloudwatch.put_metric_data.call_count >= 4
        
        print("??Audit trail scenarios test passed!")


@pytest.mark.skipif(
    not os.getenv("COGNITO_USER_POOL_ID"),
    reason="Requires real Cognito User Pool ID for live testing"
)
class TestLiveAuthenticationIntegration:
    """Live integration tests with real AWS Cognito (optional)"""
    
    @pytest.mark.asyncio
    async def test_live_cognito_authentication(self):
        """Test with real Cognito User Pool (requires setup)"""
        
        # This test requires:
        # - COGNITO_USER_POOL_ID environment variable
        # - OAUTH_CLIENT_ID environment variable
        # - OAUTH_CLIENT_SECRET environment variable (optional)
        # - Test user created in the User Pool
        
        user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
        client_id = os.getenv("OAUTH_CLIENT_ID")
        
        if not user_pool_id or not client_id:
            pytest.skip("Live Cognito testing requires COGNITO_USER_POOL_ID and OAUTH_CLIENT_ID")
        
        # Set up environment for testing
        os.environ["COGNITO_USER_POOL_ID"] = user_pool_id
        os.environ["OAUTH_CLIENT_ID"] = client_id
        
        cognito_client = CognitoClient()
        
        # Test with a known test user (you need to create this manually)
        test_username = "test_user"  # Change to your test user
        test_password = "TestPass123!"  # Change to your test password
        
        try:
            auth_request = AuthenticationRequest(
                username=test_username,
                password=test_password
            )
            
            auth_response = await cognito_client.authenticate_user(auth_request)
            
            assert auth_response.access_token is not None
            assert auth_response.user.username == test_username
            
            # Test token validation
            validated_user = await cognito_client.validate_token(auth_response.access_token)
            assert validated_user is not None
            assert validated_user.username == test_username
            
            print("??Live Cognito authentication test passed!")
            
        except CognitoAuthenticationError as e:
            pytest.skip(f"Live authentication failed (expected if test user not set up): {e}")
