# RiskIntel360 Authentication & Authorization System

A comprehensive OAuth 2.0 authentication and authorization system built for the RiskIntel360 Platform, featuring AWS Cognito integration, role-based access control (RBAC), multi-tenant data isolation, and complete audit trail logging.

## ?? Features

### OAuth 2.0 Enterprise Authentication
- **AWS Cognito Integration**: Full OAuth 2.0 flow with AWS Cognito User Pools
- **Token Management**: JWT access tokens, refresh tokens, and secure token validation
- **User Management**: User registration, authentication, and profile management
- **Group-Based Roles**: Cognito User Pool Groups mapped to application roles

### Role-Based Access Control (RBAC)
- **Hierarchical Roles**: Admin, Analyst, Viewer, and API User roles
- **Granular Permissions**: Resource-specific permissions (Read, Write, Delete, Admin)
- **Permission Inheritance**: Role hierarchy with permission inheritance
- **Custom Roles**: Support for creating custom roles with specific permissions

### Multi-Tenant Data Isolation
- **Strict Isolation**: Complete data separation between tenants
- **Configurable Isolation Levels**: Strict, Moderate, and Shared isolation modes
- **Resource Filtering**: Automatic filtering of resources by tenant
- **Tenant Management**: Create, update, and manage tenant configurations

### Comprehensive Audit Trail
- **Complete Logging**: All user actions logged for compliance
- **AWS CloudTrail Integration**: API-level audit logging
- **CloudWatch Metrics**: Real-time security and usage metrics
- **DynamoDB Storage**: Scalable audit log storage with TTL
- **Compliance Ready**: SOC 2, GDPR, and enterprise compliance support

## ??ï¸?Architecture

```
?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
??  FastAPI App   ??   ?? Cognito Client ??   ?? AWS Cognito    ??
??                ?‚â??€?€?ºâ?                 ?‚â??€?€?ºâ?   User Pool     ??
?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
         ??                      ??
         ??                      ??
?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
??     RBAC       ??   ??Multi-Tenant    ??   ?? Audit Logger   ??
??   System       ??   ??   Manager      ??   ??                ??
?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
         ??                      ??                      ??
         ??                      ??                      ??
?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
??  Permissions   ??   ??Tenant Isolation??   ??  DynamoDB      ??
??  & Roles       ??   ??  & Filtering   ??   ?? CloudWatch     ??
?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
```

## ?? Quick Start

### 1. Environment Setup

Create a `.env` file with your AWS Cognito configuration:

```bash
# AWS Configuration
AWS_REGION=us-east-1

# Cognito Configuration
COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
COGNITO_REGION=us-east-1

# Security Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
MULTI_TENANT_ENABLED=true
AUDIT_ENABLED=true
```

### 2. Deploy Infrastructure

Deploy the AWS infrastructure using CDK:

```bash
cd infrastructure
cdk deploy --context environment=development
```

This creates:
- Cognito User Pool with client
- User Pool Groups (admin, analyst, viewer, api_user)
- DynamoDB tables for audit logs
- CloudTrail for API logging
- CloudWatch dashboards

### 3. Set Up Test Users

Use the provided script to create test users:

```bash
python scripts/setup_cognito_users.py --user-pool-id us-east-1_xxxxxxxxx
```

This creates test users:
- `admin_user` (AdminPass123!) - Full admin access
- `analyst_user` (AnalystPass123!) - Business analyst access
- `viewer_user` (ViewerPass123!) - Read-only access
- `api_user` (ApiPass123!) - API programmatic access

### 4. Test the System

Run the comprehensive test:

```bash
python test_auth_system.py
```

## ?? Usage Examples

### Authentication

```python
from RiskIntel360_platform.auth.cognito_client import CognitoClient
from RiskIntel360_platform.auth.models import AuthenticationRequest

# Initialize client
cognito_client = CognitoClient()

# Authenticate user
auth_request = AuthenticationRequest(
    username="analyst_user",
    password="AnalystPass123!"
)

auth_response = await cognito_client.authenticate_user(auth_request)
print(f"Access token: {auth_response.access_token}")
print(f"User: {auth_response.user.username}")
print(f"Roles: {[role.name for role in auth_response.user.roles]}")
```

### Authorization (RBAC)

```python
from RiskIntel360_platform.auth.rbac import RoleBasedAccessControl
from RiskIntel360_platform.auth.models import ResourceType, PermissionType

rbac = RoleBasedAccessControl()

# Check permissions
has_permission = rbac.check_permission(
    user=auth_response.user,
    resource_type=ResourceType.VALIDATION_REQUEST,
    permission_type=PermissionType.READ
)

print(f"Can read validation requests: {has_permission}")
```

### Multi-Tenant Isolation

```python
from RiskIntel360_platform.auth.multi_tenant import MultiTenantManager
from RiskIntel360_platform.auth.models import SecurityContext

tenant_manager = MultiTenantManager()

# Create security context
security_context = SecurityContext(
    user=auth_response.user,
    tenant_id=auth_response.user.tenant_id,
    ip_address="192.168.1.1"
)

# Validate tenant access
can_access = tenant_manager.validate_tenant_access(
    security_context=security_context,
    resource_tenant_id="target-tenant-id",
    resource_type=ResourceType.VALIDATION_REQUEST
)

print(f"Can access tenant data: {can_access}")
```

### Audit Logging

```python
from RiskIntel360_platform.auth.audit_logger import AuditLogger
from RiskIntel360_platform.auth.models import AuditAction

audit_logger = AuditLogger()

# Log user action
await audit_logger.log_action(
    security_context=security_context,
    action=AuditAction.READ,
    resource_type=ResourceType.VALIDATION_REQUEST,
    resource_id="validation-123",
    success=True
)

# Log authentication event
await audit_logger.log_authentication(
    user_id="user-123",
    action=AuditAction.LOGIN,
    success=True,
    ip_address="192.168.1.1"
)
```

### FastAPI Integration

```python
from fastapi import Depends, HTTPException
from RiskIntel360_platform.auth.auth_decorators import (
    get_current_user, get_security_context,
    RequireAnalyst, RequireValidationRead
)

@app.get("/api/v1/validations")
async def get_validations(
    security_context = Depends(RequireValidationRead)
):
    # User is authenticated and has validation read permission
    return {"validations": []}

@app.post("/api/v1/validations")
async def create_validation(
    request: ValidationRequest,
    security_context = Depends(RequireAnalyst)
):
    # User is authenticated and has analyst role
    return {"validation_id": "123"}
```

## ?”§ Configuration

### Role Configuration

The system includes four default roles:

1. **Admin** - Full system access (36 permissions)
2. **Analyst** - Business data read/write (14 permissions)
3. **Viewer** - Read-only access (7 permissions)
4. **API User** - Programmatic access (6 permissions)

### Tenant Isolation Levels

- **Strict**: No cross-tenant access (default)
- **Moderate**: Limited cross-tenant access for specific resources
- **Shared**: Cross-tenant access with proper permissions

### Audit Configuration

- **Retention**: 30 days (configurable)
- **Storage**: DynamoDB with TTL
- **Metrics**: CloudWatch custom metrics
- **Compliance**: SOC 2, GDPR ready

## ?§ª Testing

### Unit Tests

```bash
# Run all authentication tests
python -m pytest tests/test_authentication.py -v

# Run integration tests
python -m pytest tests/test_authentication_integration.py -v

# Run specific test
python -m pytest tests/test_authentication.py::TestCognitoClient::test_authenticate_user_success -v
```

### Test Coverage

- **OAuth 2.0 Flow**: Authentication, token validation, refresh, logout
- **RBAC System**: Role assignment, permission checking, inheritance
- **Multi-Tenant**: Isolation, filtering, access validation
- **Audit Trail**: Action logging, authentication events, metrics
- **Error Handling**: Invalid credentials, expired tokens, access denied
- **Integration**: Complete end-to-end workflows

## ?? Security Features

### Authentication Security
- **Password Policy**: 8+ chars, mixed case, numbers, symbols
- **Token Security**: JWT with configurable expiration
- **Session Management**: Secure token storage and validation
- **Account Recovery**: Email-based password reset

### Authorization Security
- **Principle of Least Privilege**: Minimal required permissions
- **Role Hierarchy**: Structured permission inheritance
- **Resource-Level Control**: Granular access control
- **Tenant Isolation**: Complete data separation

### Audit Security
- **Immutable Logs**: Tamper-proof audit trail
- **Real-time Monitoring**: Immediate security alerts
- **Compliance Logging**: Complete action tracking
- **Retention Policies**: Configurable log retention

## ?? Monitoring & Observability

### CloudWatch Metrics
- Authentication success/failure rates
- Permission check counts
- Tenant access violations
- Audit log volume

### CloudWatch Dashboards
- Security overview dashboard
- User activity monitoring
- System health metrics
- Compliance reporting

### Alerts
- Failed authentication attempts
- Permission violations
- Unusual access patterns
- System errors

## ?? Deployment

### Local Development
```bash
# Start with Docker Compose
docker-compose --profile dev up

# Run API server
uvicorn RiskIntel360_platform.api.main:app --reload
```

### AWS Production
```bash
# Deploy infrastructure
cd infrastructure
cdk deploy --context environment=production

# Deploy application
# (ECS deployment handled by CDK)
```

## ?? API Documentation

The authentication system provides REST API endpoints:

- `POST /auth/login` - User authentication
- `POST /auth/refresh` - Token refresh
- `POST /auth/logout` - User logout
- `GET /auth/me` - Current user info
- `GET /auth/validate` - Token validation
- `GET /auth/permissions` - User permissions

See the FastAPI auto-generated docs at `/docs` when running the server.

## ?? Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation
4. Ensure all security tests pass
5. Follow the principle of least privilege

## ?? License

This authentication system is part of the RiskIntel360 Platform and follows the same licensing terms.
