"""
Tests for RiskIntel360 Platform API endpoints
Tests validation endpoints, WebSocket connections, and API functionality.
"""

import json
import pytest
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from riskintel360.api.main import app
from riskintel360.models import ValidationRequest, ValidationResult, Priority, WorkflowStatus
from riskintel360.models.core import MarketAnalysisResult, CompetitiveAnalysisResult


class TestValidationEndpoints:
    """Test validation API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_auth_user(self):
        """Mock authenticated user"""
        return {
            "user_id": "test-user-123",
            "email": "test@example.com",
            "tenant_id": "test-tenant",
            "roles": ["API_USER"]
        }
    
    @pytest.fixture
    def sample_validation_request(self):
        """Sample validation request data"""
        return {
            "business_concept": "AI-powered customer service chatbot for e-commerce",
            "target_market": "Small to medium e-commerce businesses in North America",
            "analysis_scope": ["market", "competitive", "financial", "risk", "customer"],
            "priority": "medium",
            "custom_parameters": {
                "budget_range": "50000-100000",
                "timeline": "6-months"
            }
        }
    
    @pytest.fixture
    def sample_validation_result(self):
        """Sample validation result"""
        return ValidationResult(
            request_id="test-validation-123",
            overall_score=75.5,
            confidence_level=0.85,
            market_analysis=MarketAnalysisResult(
                confidence_score=0.8
            ),
            competitive_analysis=CompetitiveAnalysisResult(
                confidence_score=0.75
            ),
            strategic_recommendations=[],
            supporting_data={},
            data_quality_score=0.9,
            analysis_completeness=0.95,
            generated_at=datetime.now(timezone.utc)
        )
    
    @patch('riskintel360.api.validations.data_manager')
    def test_create_validation_success(self, mock_data_manager, client, mock_auth_user, sample_validation_request):
        """Test successful validation creation"""
        from riskintel360.auth.auth_decorators import require_auth
        
        # Setup mocks
        mock_data_manager.store_validation_request = AsyncMock(return_value="test-validation-123")
        mock_data_manager.store_validation_result = AsyncMock(return_value="test-result-123")
        mock_data_manager.update_validation_request = AsyncMock(return_value=True)
        
        # Override the dependency on the app
        def mock_auth_dependency():
            return mock_auth_user
        
        client.app.dependency_overrides[require_auth] = mock_auth_dependency
        
        try:
            # Make request
            response = client.post(
                "/api/v1/validations/",
                json=sample_validation_request,
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Assertions
            assert response.status_code == 201
            data = response.json()
            assert data["user_id"] == mock_auth_user["user_id"]
            assert data["business_concept"] == sample_validation_request["business_concept"]
            assert data["status"] == "pending"
            assert "progress_url" in data
        finally:
            # Clean up
            client.app.dependency_overrides.clear()
    
    def test_create_validation_invalid_data(self, client, mock_auth_user):
        """Test validation creation with invalid data"""
        from riskintel360.auth.auth_decorators import require_auth
        
        # Override the dependency on the app
        def mock_auth_dependency():
            return mock_auth_user
        
        client.app.dependency_overrides[require_auth] = mock_auth_dependency
        
        try:
            # Invalid request - missing required fields
            invalid_request = {
                "business_concept": "Too short",  # Too short
                "target_market": ""  # Empty
            }
            
            response = client.post(
                "/api/v1/validations/",
                json=invalid_request,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 422  # Validation error
        finally:
            # Clean up
            client.app.dependency_overrides.clear()
    
    @patch('riskintel360.api.validations.data_manager')
    def test_list_validations(self, mock_data_manager, client, mock_auth_user):
        """Test listing validations"""
        from riskintel360.auth.auth_decorators import require_auth
        
        # Setup mocks
        sample_validation = ValidationRequest(
            id="test-validation-123",
            user_id=mock_auth_user["user_id"],
            business_concept="Test concept",
            target_market="Test market",
            analysis_scope=["market"],
            priority=Priority.MEDIUM,
            custom_parameters={},
            created_at=datetime.now(timezone.utc)
        )
        
        mock_data_manager.list_validation_requests = AsyncMock(
            return_value=([sample_validation], 1)
        )
        
        # Override the dependency on the app
        def mock_auth_dependency():
            return mock_auth_user
        
        client.app.dependency_overrides[require_auth] = mock_auth_dependency
        
        try:
            # Make request
            response = client.get(
                "/api/v1/validations/",
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["validations"]) == 1
            assert data["validations"][0]["id"] == "test-validation-123"
        finally:
            # Clean up
            client.app.dependency_overrides.clear()
    
    @patch('riskintel360.api.validations.data_manager')
    def test_get_validation(self, mock_data_manager, client, mock_auth_user):
        """Test getting a specific validation"""
        from riskintel360.auth.auth_decorators import require_auth
        
        # Setup mocks
        sample_validation = ValidationRequest(
            id="test-validation-123",
            user_id=mock_auth_user["user_id"],
            business_concept="Test concept",
            target_market="Test market",
            analysis_scope=["market"],
            priority=Priority.MEDIUM,
            custom_parameters={},
            created_at=datetime.now(timezone.utc)
        )
        
        mock_data_manager.get_validation_request = AsyncMock(return_value=sample_validation)
        
        # Override the dependency on the app
        def mock_auth_dependency():
            return mock_auth_user
        
        client.app.dependency_overrides[require_auth] = mock_auth_dependency
        
        try:
            # Make request
            response = client.get(
                "/api/v1/validations/test-validation-123",
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "test-validation-123"
            assert data["user_id"] == mock_auth_user["user_id"]
        finally:
            # Clean up
            client.app.dependency_overrides.clear()
    
    @patch('riskintel360.api.validations.data_manager')
    def test_get_validation_not_found(self, mock_data_manager, client, mock_auth_user):
        """Test getting non-existent validation"""
        from riskintel360.auth.auth_decorators import require_auth
        
        mock_data_manager.get_validation_request = AsyncMock(return_value=None)
        
        # Override the dependency on the app
        def mock_auth_dependency():
            return mock_auth_user
        
        client.app.dependency_overrides[require_auth] = mock_auth_dependency
        
        try:
            response = client.get(
                "/api/v1/validations/non-existent",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 404
        finally:
            # Clean up
            client.app.dependency_overrides.clear()
    
    @patch('riskintel360.api.validations.data_manager')
    def test_get_validation_access_denied(self, mock_data_manager, client, mock_auth_user):
        """Test getting validation with access denied"""
        from riskintel360.auth.auth_decorators import require_auth
        
        # Validation belongs to different user
        other_user_validation = ValidationRequest(
            id="test-validation-123",
            user_id="other-user-456",
            business_concept="Test concept",
            target_market="Test market",
            analysis_scope=["market"],
            priority=Priority.MEDIUM,
            custom_parameters={},
            created_at=datetime.now(timezone.utc)
        )
        
        mock_data_manager.get_validation_request = AsyncMock(return_value=other_user_validation)
        
        # Override the dependency on the app
        def mock_auth_dependency():
            return mock_auth_user
        
        client.app.dependency_overrides[require_auth] = mock_auth_dependency
        
        try:
            response = client.get(
                "/api/v1/validations/test-validation-123",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 403
        finally:
            # Clean up
            client.app.dependency_overrides.clear()
    
    @patch('riskintel360.api.validations.data_manager')
    def test_get_validation_result(self, mock_data_manager, client, mock_auth_user, sample_validation_result):
        """Test getting validation result"""
        from riskintel360.auth.auth_decorators import require_auth
        
        # Setup mocks
        sample_validation = ValidationRequest(
            id="test-validation-123",
            user_id=mock_auth_user["user_id"],
            business_concept="Test concept",
            target_market="Test market",
            analysis_scope=["market"],
            priority=Priority.MEDIUM,
            custom_parameters={},
            created_at=datetime.now(timezone.utc),
            status=WorkflowStatus.COMPLETED
        )
        
        mock_data_manager.get_validation_request = AsyncMock(return_value=sample_validation)
        mock_data_manager.get_validation_result = AsyncMock(return_value=sample_validation_result)
        
        # Override the dependency on the app
        def mock_auth_dependency():
            return mock_auth_user
        
        client.app.dependency_overrides[require_auth] = mock_auth_dependency
        
        try:
            # Make request
            response = client.get(
                "/api/v1/validations/test-validation-123/result",
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["request_id"] == "test-validation-123"
            assert data["overall_score"] == 75.5
            assert data["confidence_level"] == 0.85
        finally:
            # Clean up
            client.app.dependency_overrides.clear()
    
    @patch('riskintel360.api.validations.data_manager')
    def test_cancel_validation(self, mock_data_manager, client, mock_auth_user):
        """Test cancelling a validation"""
        from riskintel360.auth.auth_decorators import require_auth
        
        # Setup mocks
        sample_validation = ValidationRequest(
            id="test-validation-123",
            user_id=mock_auth_user["user_id"],
            business_concept="Test concept",
            target_market="Test market",
            analysis_scope=["market"],
            priority=Priority.MEDIUM,
            custom_parameters={},
            created_at=datetime.now(timezone.utc),
            status=WorkflowStatus.IN_PROGRESS
        )
        
        mock_data_manager.get_validation_request = AsyncMock(return_value=sample_validation)
        mock_data_manager.update_validation_request = AsyncMock(return_value=True)
        
        # Override the dependency on the app
        def mock_auth_dependency():
            return mock_auth_user
        
        client.app.dependency_overrides[require_auth] = mock_auth_dependency
        
        try:
            with patch('riskintel360.api.validations.get_session_manager') as mock_session_manager:
                mock_session_manager.return_value.cancel_session = AsyncMock()
                
                # Make request
                response = client.delete(
                    "/api/v1/validations/test-validation-123",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                # Assertions
                assert response.status_code == 204
        finally:
            # Clean up
            client.app.dependency_overrides.clear()


class TestProgressEndpoints:
    """Test progress tracking endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_auth_user(self):
        """Mock authenticated user"""
        return {
            "user_id": "test-user-123",
            "email": "test@example.com",
            "tenant_id": "test-tenant",
            "roles": ["API_USER"]
        }
    
    @patch('riskintel360.api.progress.data_manager')
    @patch('riskintel360.api.progress.get_session_manager')
    def test_get_validation_progress(self, mock_session_manager, mock_data_manager, client, mock_auth_user):
        """Test getting validation progress"""
        from riskintel360.auth.auth_decorators import require_auth
        
        # Setup mocks
        sample_validation = ValidationRequest(
            id="test-validation-123",
            user_id=mock_auth_user["user_id"],
            business_concept="Test concept",
            target_market="Test market",
            analysis_scope=["market"],
            priority=Priority.MEDIUM,
            custom_parameters={},
            created_at=datetime.now(timezone.utc),
            status=WorkflowStatus.IN_PROGRESS
        )
        
        mock_data_manager.get_validation_request = AsyncMock(return_value=sample_validation)
        
        mock_session_manager.return_value.get_session_info = AsyncMock(return_value={
            "progress": 45.0,
            "current_agent": "market_analysis",
            "message": "Analyzing market trends"
        })
        
        # Override the dependency on the app
        def mock_auth_dependency():
            return mock_auth_user
        
        client.app.dependency_overrides[require_auth] = mock_auth_dependency
        
        try:
            # Make request
            response = client.get(
                "/api/v1/validations/test-validation-123/progress",
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["validation_id"] == "test-validation-123"
            assert data["progress_percentage"] == 45.0
            assert data["current_agent"] == "market_analysis"
            assert data["message"] == "Analyzing market trends"
        finally:
            # Clean up
            client.app.dependency_overrides.clear()
    
    @patch('riskintel360.api.progress.data_manager')
    def test_get_validation_progress_not_found(self, mock_data_manager, client, mock_auth_user):
        """Test getting progress for non-existent validation"""
        from riskintel360.auth.auth_decorators import require_auth
        
        mock_data_manager.get_validation_request = AsyncMock(return_value=None)
        
        # Override the dependency on the app
        def mock_auth_dependency():
            return mock_auth_user
        
        client.app.dependency_overrides[require_auth] = mock_auth_dependency
        
        try:
            response = client.get(
                "/api/v1/validations/non-existent/progress",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 404
        finally:
            # Clean up
            client.app.dependency_overrides.clear()


class TestWebSocketEndpoints:
    """Test WebSocket endpoints"""
    
    @pytest.fixture
    def mock_auth_user(self):
        """Mock authenticated user"""
        return {
            "user_id": "test-user-123",
            "email": "test@example.com",
            "tenant_id": "test-tenant",
            "roles": ["API_USER"]
        }
    
    @patch('riskintel360.api.websockets.get_current_user_from_token')
    @patch('riskintel360.api.websockets.data_manager')
    def test_validation_progress_websocket_connection(self, mock_data_manager, mock_auth, mock_auth_user):
        """Test WebSocket connection for validation progress"""
        # Setup mocks
        mock_auth.return_value = mock_auth_user
        
        sample_validation = ValidationRequest(
            id="test-validation-123",
            user_id=mock_auth_user["user_id"],
            business_concept="Test concept",
            target_market="Test market",
            analysis_scope=["market"],
            priority=Priority.MEDIUM,
            custom_parameters={},
            created_at=datetime.now(timezone.utc)
        )
        
        mock_data_manager.get_validation_request = AsyncMock(return_value=sample_validation)
        
        # Test WebSocket connection
        with TestClient(app) as client:
            with client.websocket_connect("/ws/validations/test-validation-123/progress?token=test-token") as websocket:
                # Should receive connection established message
                data = websocket.receive_json()
                assert data["type"] == "connection_established"
                assert data["data"]["validation_id"] == "test-validation-123"
    
    @patch('riskintel360.api.websockets.get_current_user_from_token')
    def test_websocket_authentication_failure(self, mock_auth):
        """Test WebSocket authentication failure"""
        mock_auth.side_effect = ValueError("Invalid token")
        
        with TestClient(app) as client:
            with pytest.raises(Exception):  # WebSocket should close with error
                with client.websocket_connect("/ws/validations/test-validation-123/progress?token=invalid-token"):
                    pass


class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_api_health_check(self, client):
        """Test API health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data
        assert "version" in data
    
    def test_api_root_endpoint(self, client):
        """Test API root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "RiskIntel360 Platform API"
        assert "version" in data
        assert "status" in data
    
    def test_api_docs_available(self, client):
        """Test API documentation is available"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_api_openapi_spec(self, client):
        """Test OpenAPI specification is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        spec = response.json()
        assert spec["info"]["title"] == "RiskIntel360 Platform API"
        assert "paths" in spec
        assert "/api/v1/validations/" in spec["paths"]


@pytest.mark.asyncio
class TestAsyncAPIFunctionality:
    """Test async API functionality"""
    
    async def test_background_task_execution(self):
        """Test background task execution for validation workflow"""
        from riskintel360.api.validations import start_validation_workflow
        
        sample_request = ValidationRequest(
            id="test-validation-123",
            user_id="test-user-123",
            business_concept="Test concept",
            target_market="Test market",
            analysis_scope=["market"],
            priority=Priority.MEDIUM,
            custom_parameters={},
            created_at=datetime.now(timezone.utc)
        )
        
        with patch('riskintel360.api.validations.WorkflowOrchestrator') as mock_orchestrator:
            with patch('riskintel360.api.validations.data_manager') as mock_data_manager:
                mock_orchestrator.return_value.execute_validation_workflow = AsyncMock()
                mock_data_manager.store_validation_result = AsyncMock()
                mock_data_manager.update_validation_request = AsyncMock()
                
                # Should not raise exception
                await start_validation_workflow(sample_request)
    
    async def test_websocket_message_handling(self):
        """Test WebSocket message handling"""
        from riskintel360.api.websockets import handle_client_message
        from unittest.mock import AsyncMock
        
        mock_websocket = AsyncMock()
        
        # Test ping message
        ping_message = {"type": "ping"}
        await handle_client_message(mock_websocket, "test-validation-123", ping_message)
        
        # Should send pong response
        mock_websocket.send_text.assert_called_once()
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data["type"] == "pong"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
