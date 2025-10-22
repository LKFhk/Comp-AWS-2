"""
Integration Tests for Centralized API Structure
Tests the centralized API management, routing, middleware, and configuration.
"""

import pytest
import json
import time
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from riskintel360.api.main import create_app
from riskintel360.api.config import get_api_config, FeatureFlag, ServiceTier
from riskintel360.api.middleware import get_api_metrics
from riskintel360.api.models import APIVersion, ResponseStatus, ErrorCode


class TestCentralizedAPIStructure:
    """Test centralized API structure and management"""
    
    @pytest.fixture
    def client(self):
        """Create test client with centralized API"""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def api_config(self):
        """Get API configuration instance"""
        return get_api_config()
    
    def test_root_endpoint_standardized_response(self, client):
        """Test root endpoint returns standardized response format"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify standardized response structure
        assert "status" in data
        assert "data" in data
        assert "metadata" in data
        
        assert data["status"] == ResponseStatus.SUCCESS.value
        
        # Verify metadata structure
        metadata = data["metadata"]
        assert "request_id" in metadata
        assert "timestamp" in metadata
        assert "version" in metadata
        assert metadata["version"] == APIVersion.V1.value
        
        # Verify API information
        api_info = data["data"]
        assert api_info["name"] == "RiskIntel360 Platform API"
        assert "version" in api_info
        assert "environment" in api_info
        assert "endpoints" in api_info
        assert "features" in api_info
    
    def test_health_check_comprehensive(self, client):
        """Test comprehensive health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify health check structure
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
        assert "services" in data
        assert "uptime_seconds" in data
        
        # Verify services health
        services = data["services"]
        assert "api" in services
        assert "database" in services
        assert "cache" in services
        assert "external_apis" in services
        
        for service_name, service_info in services.items():
            assert "status" in service_info
            assert "response_time_ms" in service_info
    
    def test_simple_health_check(self, client):
        """Test simple health check for load balancers"""
        response = client.get("/health/simple")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "ok"
    
    def test_api_configuration_endpoint(self, client):
        """Test API configuration endpoint"""
        response = client.get("/config")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify standardized response
        assert data["status"] == ResponseStatus.SUCCESS.value
        assert "data" in data
        assert "metadata" in data
        
        # Verify configuration data
        config = data["data"]
        assert "version" in config
        assert "environment" in config
        assert "features" in config
        assert "rate_limits" in config
        assert "maintenance_mode" in config
        
        # Verify features list
        features = config["features"]
        expected_features = [
            "fintech_intelligence",
            "risk_assessment",
            "fraud_detection",
            "regulatory_compliance",
            "market_analysis",
            "cost_optimization",
            "performance_monitoring"
        ]
        for feature in expected_features:
            assert feature in features
    
    def test_api_metrics_endpoint(self, client):
        """Test API metrics endpoint"""
        # Make a few requests to generate metrics
        client.get("/")
        client.get("/health")
        client.get("/config")
        
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify standardized response
        assert data["status"] == ResponseStatus.SUCCESS.value
        assert "data" in data
        
        # Verify metrics data
        metrics = data["data"]
        assert "requests_total" in metrics
        assert "requests_by_method" in metrics
        assert "requests_by_status" in metrics
        assert "errors_total" in metrics
        assert "error_rate" in metrics
        assert "average_response_time_ms" in metrics
        assert "metrics_collected_at" in metrics
        
        # Verify we have some requests recorded
        assert metrics["requests_total"] > 0
        assert "GET" in metrics["requests_by_method"]
    
    def test_version_endpoint(self, client):
        """Test version information endpoint"""
        response = client.get("/version")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "version" in data
        assert "api_version" in data
        assert "environment" in data
        assert data["api_version"] == APIVersion.V1.value
    
    def test_documentation_endpoints(self, client):
        """Test documentation endpoints"""
        # Test endpoints list
        response = client.get("/docs/endpoints")
        assert response.status_code == 200
        data = response.json()
        
        assert "v1_endpoints" in data
        assert "v2_endpoints" in data
        
        v1_endpoints = data["v1_endpoints"]
        assert "fintech" in v1_endpoints
        assert "cost_optimization" in v1_endpoints
        assert "performance" in v1_endpoints
        
        # Test changelog
        response = client.get("/docs/changelog")
        assert response.status_code == 200
        data = response.json()
        
        assert "v1.0.0" in data
        assert "date" in data["v1.0.0"]
        assert "changes" in data["v1.0.0"]
    
    def test_request_context_middleware(self, client):
        """Test request context middleware adds request ID"""
        response = client.get("/")
        
        # Verify request ID header is present
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 0
        
        # Verify request ID is in response metadata
        data = response.json()
        metadata = data["metadata"]
        assert metadata["request_id"] == request_id
    
    def test_rate_limiting_middleware(self, client):
        """Test centralized rate limiting middleware"""
        # Make requests up to the limit
        responses = []
        for i in range(5):  # Stay well under default limit
            response = client.get("/")
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            
            # Verify rate limit headers
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
    
    def test_error_handling_middleware(self, client):
        """Test centralized error handling middleware"""
        # Test 404 error
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        
        # Verify standardized error response
        assert data["status"] == ResponseStatus.ERROR.value
        assert "errors" in data
        assert "metadata" in data
        
        errors = data["errors"]
        assert len(errors) > 0
        
        error = errors[0]
        assert "code" in error
        assert "message" in error
        assert "trace_id" in error
        assert error["code"] == ErrorCode.NOT_FOUND.value
    
    def test_api_versioning_structure(self, client):
        """Test API versioning structure"""
        # Test V1 endpoints are accessible
        v1_endpoints = [
            "/api/v1/auth/status",
            "/api/v1/fintech/health",
            "/api/v1/cost-optimization/summary"
        ]
        
        for endpoint in v1_endpoints:
            response = client.get(endpoint)
            # Should not be 404 (endpoint exists, may require auth)
            assert response.status_code != 404
    
    def test_cors_headers(self, client):
        """Test CORS headers are properly set"""
        response = client.options("/", headers={"Origin": "http://localhost:3000"})
        
        # CORS headers should be present
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers
    
    def test_security_headers(self, client):
        """Test security headers are added by middleware"""
        response = client.get("/")
        
        # Verify security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Content-Security-Policy" in response.headers
        
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
    
    def test_performance_headers(self, client):
        """Test performance monitoring headers"""
        response = client.get("/")
        
        # Verify performance headers
        assert "X-Response-Time" in response.headers
        
        response_time = response.headers["X-Response-Time"]
        assert response_time.endswith("ms")
        
        # Parse and verify response time is reasonable
        time_value = float(response_time[:-2])
        assert 0 < time_value < 10000  # Should be less than 10 seconds


class TestAPIConfiguration:
    """Test API configuration management"""
    
    @pytest.fixture
    def api_config(self):
        """Get API configuration instance"""
        return get_api_config()
    
    def test_feature_flag_management(self, api_config):
        """Test feature flag management"""
        # Test default features are enabled
        assert api_config.is_feature_enabled(FeatureFlag.FINTECH_INTELLIGENCE)
        assert api_config.is_feature_enabled(FeatureFlag.FRAUD_DETECTION)
        assert api_config.is_feature_enabled(FeatureFlag.REGULATORY_COMPLIANCE)
        
        # Test feature toggle
        api_config.disable_feature(FeatureFlag.BULK_OPERATIONS)
        assert not api_config.is_feature_enabled(FeatureFlag.BULK_OPERATIONS)
        
        api_config.enable_feature(FeatureFlag.BULK_OPERATIONS)
        assert api_config.is_feature_enabled(FeatureFlag.BULK_OPERATIONS)
    
    def test_endpoint_configuration(self, api_config):
        """Test endpoint configuration management"""
        # Test getting endpoint config
        config = api_config.get_endpoint_config("/api/v1/fintech/risk-analysis")
        assert config is not None
        assert config.enabled
        assert FeatureFlag.FINTECH_INTELLIGENCE in config.required_features
        assert config.min_service_tier == ServiceTier.BASIC
        
        # Test wildcard matching
        config = api_config.get_endpoint_config("/api/v1/cost-optimization/summary")
        assert config is not None
        assert config.enabled
    
    def test_service_tier_access(self, api_config):
        """Test service tier access control"""
        # Test free tier access
        assert api_config.is_endpoint_enabled("/api/v1/fintech/market-intelligence", ServiceTier.FREE)
        
        # Test professional tier requirement
        assert not api_config.is_endpoint_enabled("/api/v1/fintech/fraud-detection", ServiceTier.FREE)
        assert api_config.is_endpoint_enabled("/api/v1/fintech/fraud-detection", ServiceTier.PROFESSIONAL)
    
    def test_rate_limit_configuration(self, api_config):
        """Test rate limit configuration by service tier"""
        # Test different service tiers
        free_limits = api_config.get_rate_limit_config(ServiceTier.FREE)
        assert free_limits.requests_per_minute == 10
        assert free_limits.requests_per_day == 1000
        
        enterprise_limits = api_config.get_rate_limit_config(ServiceTier.ENTERPRISE)
        assert enterprise_limits.requests_per_minute == 1000
        assert enterprise_limits.requests_per_day == 200000
    
    def test_service_configuration(self, api_config):
        """Test service configuration management"""
        # Test getting service config
        bedrock_config = api_config.get_service_config("bedrock_client")
        assert bedrock_config is not None
        assert bedrock_config.enabled
        assert bedrock_config.timeout_seconds == 60
        assert bedrock_config.retry_attempts == 3
    
    def test_configuration_validation(self, api_config):
        """Test configuration validation"""
        assert api_config.validate_configuration()
    
    def test_configuration_export(self, api_config):
        """Test configuration export"""
        exported = api_config.export_config()
        
        assert "feature_flags" in exported
        assert "endpoint_configs" in exported
        assert "service_configs" in exported
        assert "rate_limits" in exported
        assert "exported_at" in exported
        
        # Verify structure
        assert isinstance(exported["feature_flags"], dict)
        assert isinstance(exported["endpoint_configs"], dict)
        assert isinstance(exported["service_configs"], dict)


class TestAPIMetrics:
    """Test API metrics collection"""
    
    def test_metrics_collection(self):
        """Test API metrics are collected properly"""
        metrics = get_api_metrics()
        
        assert "requests_total" in metrics
        assert "requests_by_method" in metrics
        assert "requests_by_status" in metrics
        assert "errors_total" in metrics
        assert "error_rate" in metrics
        assert "average_response_time_ms" in metrics
        assert "metrics_collected_at" in metrics
        
        # Verify data types
        assert isinstance(metrics["requests_total"], int)
        assert isinstance(metrics["requests_by_method"], dict)
        assert isinstance(metrics["error_rate"], float)
        assert isinstance(metrics["average_response_time_ms"], float)


@pytest.mark.integration
class TestEndToEndAPIWorkflow:
    """Test end-to-end API workflow with centralized structure"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        return TestClient(app)
    
    def test_complete_api_workflow(self, client):
        """Test complete API workflow from request to response"""
        # 1. Check API status
        response = client.get("/")
        assert response.status_code == 200
        
        # 2. Check health
        response = client.get("/health")
        assert response.status_code == 200
        
        # 3. Get configuration
        response = client.get("/config")
        assert response.status_code == 200
        
        # 4. Check metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # 5. Test API versioning
        response = client.get("/version")
        assert response.status_code == 200
        
        # All responses should have consistent structure
        for endpoint in ["/", "/config", "/metrics"]:
            response = client.get(endpoint)
            data = response.json()
            
            # Verify standardized response structure
            assert "status" in data
            assert "metadata" in data
            assert data["status"] == ResponseStatus.SUCCESS.value
            
            # Verify request tracking
            assert "X-Request-ID" in response.headers
            assert "X-Response-Time" in response.headers
    
    def test_error_handling_workflow(self, client):
        """Test error handling workflow"""
        # Test 404 error
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert data["status"] == ResponseStatus.ERROR.value
        assert "errors" in data
        assert len(data["errors"]) > 0
        
        error = data["errors"][0]
        assert error["code"] == ErrorCode.NOT_FOUND.value
        assert "trace_id" in error
    
    @patch('riskintel360.api.middleware.time.time')
    def test_rate_limiting_workflow(self, mock_time, client):
        """Test rate limiting workflow"""
        # Mock time to control rate limiting
        mock_time.return_value = 1000.0
        
        # Make requests within limit
        for i in range(5):
            response = client.get("/")
            assert response.status_code == 200
            
            # Verify rate limit headers
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
