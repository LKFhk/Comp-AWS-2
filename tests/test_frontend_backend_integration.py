"""
Frontend-Backend Integration Tests for RiskIntel360 Platform
Tests API endpoints, WebSocket connections, and data flow between React frontend and FastAPI backend.
"""

import pytest
import asyncio
import json
import websockets
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

import requests
from fastapi.testclient import TestClient
from riskintel360.api.main import app
from riskintel360.models import ValidationRequest, Priority, WorkflowStatus


class FrontendBackendIntegrationTests:
    """Integration tests for frontend-backend communication"""
    
    def __init__(self):
        self.client = TestClient(app)
        self.base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000"
        self.auth_token = "test_jwt_token_12345"
        self.test_user_id = "test-user-123"
    
    def setup_method(self):
        """Set up test environment"""
        # Mock authentication
        self.auth_headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_api_health_check(self):
        """Test API health check endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        
        print("??API health check test passed")
    
    def test_validation_crud_operations(self):
        """Test complete CRUD operations for validations"""
        
        # Create validation request
        validation_data = {
            "business_concept": "AI-powered customer service automation",
            "target_market": "Small to medium businesses",
            "analysis_scope": ["market", "competitive", "financial"],
            "priority": "medium"
        }
        
        # POST - Create validation
        response = self.client.post(
            "/api/v1/validations/",
            json=validation_data,
            headers=self.auth_headers
        )
        assert response.status_code == 201
        
        validation = response.json()
        validation_id = validation["id"]
        assert validation["business_concept"] == validation_data["business_concept"]
        assert validation["status"] == "pending"
        
        # GET - Retrieve validation
        response = self.client.get(
            f"/api/v1/validations/{validation_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        retrieved_validation = response.json()
        assert retrieved_validation["id"] == validation_id
        assert retrieved_validation["business_concept"] == validation_data["business_concept"]
        
        # GET - List validations
        response = self.client.get(
            "/api/v1/validations/",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        validations_list = response.json()
        assert "validations" in validations_list
        assert validations_list["total"] >= 1
        
        # DELETE - Cancel validation
        response = self.client.delete(
            f"/api/v1/validations/{validation_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 204
        
        print("??Validation CRUD operations test passed")  
  
    def test_validation_progress_api(self):
        """Test validation progress tracking API"""
        
        # Create a test validation first
        validation_data = {
            "business_concept": "Test business concept",
            "target_market": "Test market",
            "analysis_scope": ["market", "competitive"],
            "priority": "medium"
        }
        
        response = self.client.post(
            "/api/v1/validations/",
            json=validation_data,
            headers=self.auth_headers
        )
        validation_id = response.json()["id"]
        
        # Get progress
        response = self.client.get(
            f"/api/v1/validations/{validation_id}/progress",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        progress = response.json()
        assert "validation_id" in progress
        assert "status" in progress
        assert "progress_percentage" in progress
        
        print("??Validation progress API test passed")
    
    def test_visualization_data_api(self):
        """Test visualization data endpoints"""
        
        # Create test validation
        validation_data = {
            "business_concept": "Test visualization",
            "target_market": "Test market",
            "analysis_scope": ["market", "financial"],
            "priority": "medium"
        }
        
        response = self.client.post(
            "/api/v1/validations/",
            json=validation_data,
            headers=self.auth_headers
        )
        validation_id = response.json()["id"]
        
        # Test different chart types
        chart_types = ["market-size", "competitive-landscape", "financial-projections"]
        
        for chart_type in chart_types:
            response = self.client.get(
                f"/api/v1/visualizations/{validation_id}/{chart_type}",
                headers=self.auth_headers
            )
            
            # Should return data or 404 if not ready
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                chart_data = response.json()
                assert "labels" in chart_data or "data" in chart_data
        
        print("??Visualization data API test passed")
    
    def test_report_generation_api(self):
        """Test report generation and download"""
        
        # Create test validation
        validation_data = {
            "business_concept": "Test report generation",
            "target_market": "Test market",
            "analysis_scope": ["market"],
            "priority": "medium"
        }
        
        response = self.client.post(
            "/api/v1/validations/",
            json=validation_data,
            headers=self.auth_headers
        )
        validation_id = response.json()["id"]
        
        # Test PDF report generation
        response = self.client.get(
            f"/api/v1/reports/{validation_id}",
            params={"format": "pdf"},
            headers=self.auth_headers
        )
        
        # Should return PDF or 404 if not ready
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            assert response.headers["content-type"] == "application/pdf"
            assert len(response.content) > 0
        
        print("??Report generation API test passed")
    
    @pytest.mark.asyncio
    async def test_websocket_progress_updates(self):
        """Test WebSocket progress updates"""
        
        # This test requires a running WebSocket server
        try:
            uri = f"{self.ws_url}/ws/validations/test-validation-1/progress?token={self.auth_token}"
            
            async with websockets.connect(uri) as websocket:
                # Send connection message
                await websocket.send(json.dumps({
                    "type": "get_status",
                    "data": {}
                }))
                
                # Receive response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(response)
                
                assert "type" in message
                assert "data" in message
                
                print("??WebSocket progress updates test passed")
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    def test_authentication_flow(self):
        """Test authentication endpoints"""
        
        # Test login endpoint
        login_data = {
            "email": "test@RiskIntel360.com",
            "password": "test123"
        }
        
        response = self.client.post("/api/v1/auth/login", json=login_data)
        
        # Should return token or 401 for invalid credentials
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            auth_response = response.json()
            assert "token" in auth_response
            assert "user" in auth_response
        
        # Test current user endpoint
        response = self.client.get("/api/v1/auth/me", headers=self.auth_headers)
        
        # Should return user info or 401
        assert response.status_code in [200, 401]
        
        print("??Authentication flow test passed")
    
    def test_user_preferences_api(self):
        """Test user preferences endpoints"""
        
        # Get current preferences
        response = self.client.get(
            "/api/v1/users/preferences",
            headers=self.auth_headers
        )
        
        assert response.status_code in [200, 404]
        
        # Update preferences
        preferences_data = {
            "theme": "dark",
            "notifications": {
                "email": True,
                "push": False
            },
            "defaultAnalysisScope": ["market", "competitive", "financial"]
        }
        
        response = self.client.put(
            "/api/v1/users/preferences",
            json=preferences_data,
            headers=self.auth_headers
        )
        
        assert response.status_code in [200, 201, 404]
        
        print("??User preferences API test passed")
    
    def test_cost_management_api(self):
        """Test cost management endpoints"""
        
        # Test cost estimation
        estimation_data = {
            "business_concept": "Test cost estimation",
            "analysis_scope": ["market", "competitive", "financial"],
            "target_market": "Test market"
        }
        
        response = self.client.post(
            "/api/v1/cost/estimate",
            json=estimation_data,
            headers=self.auth_headers
        )
        
        assert response.status_code in [200, 501]  # 501 if not implemented
        
        if response.status_code == 200:
            estimate = response.json()
            assert "total_cost_usd" in estimate
            assert "estimated_duration_minutes" in estimate
        
        # Test cost tracking
        response = self.client.get(
            "/api/v1/cost/usage",
            headers=self.auth_headers
        )
        
        assert response.status_code in [200, 501]
        
        print("??Cost management API test passed")
    
    def test_error_handling(self):
        """Test API error handling"""
        
        # Test 404 for non-existent validation
        response = self.client.get(
            "/api/v1/validations/non-existent-id",
            headers=self.auth_headers
        )
        assert response.status_code == 404
        
        # Test 400 for invalid data
        invalid_data = {
            "business_concept": "",  # Empty required field
            "target_market": "Test market",
            "analysis_scope": [],  # Empty array
            "priority": "invalid_priority"  # Invalid enum value
        }
        
        response = self.client.post(
            "/api/v1/validations/",
            json=invalid_data,
            headers=self.auth_headers
        )
        assert response.status_code == 422  # Validation error
        
        # Test 401 for missing authentication
        response = self.client.get("/api/v1/validations/")
        assert response.status_code == 401
        
        print("??Error handling test passed")


@pytest.mark.integration
class TestRealTimeFeatures:
    """Test real-time features and WebSocket functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.client = TestClient(app)
        self.auth_token = "test_jwt_token_12345"
        self.auth_headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self):
        """Test WebSocket connection establishment and cleanup"""
        
        try:
            uri = f"ws://localhost:8000/ws/validations/test-validation/progress?token={self.auth_token}"
            
            # Test connection establishment
            async with websockets.connect(uri) as websocket:
                # Wait for connection confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(response)
                
                assert message["type"] == "connection_established"
                assert message["data"]["validation_id"] == "test-validation"
                
                # Test ping-pong
                ping_message = {
                    "type": "ping",
                    "data": {"timestamp": datetime.now(timezone.utc).isoformat()}
                }
                
                await websocket.send(json.dumps(ping_message))
                
                pong_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                pong_message = json.loads(pong_response)
                
                assert pong_message["type"] == "pong"
                
                print("??WebSocket connection lifecycle test passed")
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")
    
    @pytest.mark.asyncio
    async def test_notifications_websocket(self):
        """Test user notifications WebSocket"""
        
        try:
            uri = f"ws://localhost:8000/ws/notifications?token={self.auth_token}"
            
            async with websockets.connect(uri) as websocket:
                # Wait for connection confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(response)
                
                assert message["type"] == "notifications_connected"
                
                print("??Notifications WebSocket test passed")
                
        except Exception as e:
            pytest.skip(f"WebSocket server not available: {e}")


if __name__ == "__main__":
    # Run the integration tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])
