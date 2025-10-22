"""
WebSocket Integration Tests for RiskIntel360 Platform
Tests real-time communication between frontend and backend via WebSockets.
"""

import pytest
import asyncio
import json
import websockets
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from riskintel360.api.websockets import connection_manager, send_progress_update, ProgressUpdate
from riskintel360.models import WorkflowStatus


@pytest.mark.asyncio
class TestWebSocketIntegration:
    """WebSocket integration tests"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_validation_id = "test-validation-123"
        self.test_user_id = "test-user-456"
        self.auth_token = "test_jwt_token_12345"
        self.ws_base_url = "ws://localhost:8000"
    
    async def test_validation_progress_websocket_connection(self):
        """Test WebSocket connection for validation progress"""
        
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.receive_text = AsyncMock(side_effect=asyncio.TimeoutError())
        
        # Test connection establishment
        await connection_manager.connect(mock_websocket, self.test_validation_id, self.test_user_id)
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()
        
        # Test sending progress update
        progress_update = ProgressUpdate(
            validation_id=self.test_validation_id,
            status=WorkflowStatus.IN_PROGRESS,
            progress_percentage=50.0,
            current_agent="market_analysis",
            message="Analyzing market data..."
        )
        
        await send_progress_update(self.test_validation_id, progress_update)
        
        # Verify message was sent
        assert mock_websocket.send_text.called
        
        # Test disconnection
        await connection_manager.disconnect(mock_websocket, self.test_validation_id, self.test_user_id)
        
        print("??WebSocket connection test passed")
    
    async def test_websocket_message_handling(self):
        """Test WebSocket message handling"""
        
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        # Connect to WebSocket
        await connection_manager.connect(mock_websocket, self.test_validation_id, self.test_user_id)
        
        # Test different message types
        test_messages = [
            {
                "type": "progress_update",
                "data": {
                    "validation_id": self.test_validation_id,
                    "status": "running",
                    "progress_percentage": 75.0,
                    "current_agent": "fraud_detection",
                    "message": "Calculating financial projections..."
                }
            },
            {
                "type": "validation_completed",
                "data": {
                    "validation_id": self.test_validation_id,
                    "overall_score": 85.5,
                    "confidence_level": 0.92,
                    "completion_time": 3600
                }
            },
            {
                "type": "validation_failed",
                "data": {
                    "validation_id": self.test_validation_id,
                    "error": "External API timeout"
                }
            }
        ]
        
        for message in test_messages:
            # Send message through connection manager
            from riskintel360.api.websockets import WebSocketMessage
            ws_message = WebSocketMessage(
                type=message["type"],
                data=message["data"]
            )
            
            await connection_manager.send_to_validation(self.test_validation_id, ws_message)
            
            # Verify message was sent
            assert mock_websocket.send_text.called
            
            # Verify message format
            sent_data = mock_websocket.send_text.call_args[0][0]
            parsed_message = json.loads(sent_data)
            
            assert parsed_message["type"] == message["type"]
            assert parsed_message["data"] == message["data"]
            assert "timestamp" in parsed_message
        
        print("??WebSocket message handling test passed")
    
    async def test_websocket_error_handling(self):
        """Test WebSocket error handling"""
        
        # Test connection with invalid token
        mock_websocket = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        # This would normally be handled by the WebSocket endpoint
        # We're testing the connection manager's error handling
        
        # Test sending message to non-existent validation
        from riskintel360.api.websockets import WebSocketMessage
        test_message = WebSocketMessage(
            type="test_message",
            data={"test": "data"}
        )
        
        # Should not raise exception for non-existent validation
        await connection_manager.send_to_validation("non-existent-validation", test_message)
        
        print("??WebSocket error handling test passed")
    
    async def test_websocket_ping_pong(self):
        """Test WebSocket ping-pong mechanism"""
        
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        # Connect to WebSocket
        await connection_manager.connect(mock_websocket, self.test_validation_id, self.test_user_id)
        
        # Send ping message
        ping_message = {
            "type": "ping",
            "data": {"timestamp": datetime.now(timezone.utc).isoformat()}
        }
        
        from riskintel360.api.websockets import WebSocketMessage
        ws_ping = WebSocketMessage(
            type="ping",
            data=ping_message["data"]
        )
        
        await connection_manager.send_to_validation(self.test_validation_id, ws_ping)
        
        # Verify ping was sent
        assert mock_websocket.send_text.called
        
        print("??WebSocket ping-pong test passed")
    
    async def test_multiple_client_connections(self):
        """Test multiple clients connected to same validation"""
        
        # Create multiple mock WebSocket connections
        mock_websockets = [AsyncMock() for _ in range(3)]
        
        for i, mock_ws in enumerate(mock_websockets):
            mock_ws.accept = AsyncMock()
            mock_ws.send_text = AsyncMock()
            
            # Connect each WebSocket
            await connection_manager.connect(mock_ws, self.test_validation_id, f"user-{i}")
        
        # Send broadcast message
        from riskintel360.api.websockets import WebSocketMessage
        broadcast_message = WebSocketMessage(
            type="broadcast_test",
            data={"message": "Test broadcast to all clients"}
        )
        
        await connection_manager.send_to_validation(self.test_validation_id, broadcast_message)
        
        # Verify all clients received the message
        for mock_ws in mock_websockets:
            assert mock_ws.send_text.called
        
        # Disconnect all clients
        for i, mock_ws in enumerate(mock_websockets):
            await connection_manager.disconnect(mock_ws, self.test_validation_id, f"user-{i}")
        
        print("??Multiple client connections test passed")
    
    async def test_user_notifications_websocket(self):
        """Test user-specific notifications WebSocket"""
        
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        # Connect to user notifications
        user_validation_id = f"user_{self.test_user_id}"
        await connection_manager.connect(mock_websocket, user_validation_id, self.test_user_id)
        
        # Send user notification
        from riskintel360.api.websockets import send_user_notification
        notification_data = {
            "message": "Your validation has been completed",
            "type": "success",
            "validation_id": self.test_validation_id
        }
        
        await send_user_notification(self.test_user_id, notification_data)
        
        # Verify notification was sent
        assert mock_websocket.send_text.called
        
        # Verify notification format
        sent_data = mock_websocket.send_text.call_args[0][0]
        parsed_message = json.loads(sent_data)
        
        assert parsed_message["type"] == "user_notification"
        assert parsed_message["data"] == notification_data
        
        print("??User notifications WebSocket test passed")
    
    async def test_websocket_connection_cleanup(self):
        """Test WebSocket connection cleanup"""
        
        # Use a unique validation ID for this test to avoid conflicts
        test_validation_id = f"cleanup-test-{id(self)}"
        
        mock_websockets = [AsyncMock() for _ in range(2)]
        
        for i, mock_ws in enumerate(mock_websockets):
            mock_ws.accept = AsyncMock()
            mock_ws.send_text = AsyncMock()
            await connection_manager.connect(mock_ws, test_validation_id, f"cleanup-user-{i}")
        
        # Verify connections are tracked
        assert test_validation_id in connection_manager.active_connections
        assert len(connection_manager.active_connections[test_validation_id]) == 2
        
        # Disconnect one client
        await connection_manager.disconnect(mock_websockets[0], test_validation_id, "cleanup-user-0")
        
        # Verify partial cleanup
        assert len(connection_manager.active_connections[test_validation_id]) == 1
        
        # Disconnect remaining client
        await connection_manager.disconnect(mock_websockets[1], test_validation_id, "cleanup-user-1")
        
        # Verify complete cleanup
        assert test_validation_id not in connection_manager.active_connections
        
        print("??WebSocket connection cleanup test passed")


@pytest.mark.asyncio
class TestWebSocketRealTimeFeatures:
    """Test real-time features via WebSocket"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_validation_id = "realtime-test-123"
        self.test_user_id = "realtime-user-456"
    
    async def test_real_time_progress_updates(self):
        """Test real-time progress updates during validation"""
        
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        # Connect WebSocket
        await connection_manager.connect(mock_websocket, self.test_validation_id, self.test_user_id)
        
        # Simulate validation progress updates
        progress_stages = [
            {"agent": "market_analysis", "progress": 16.7, "message": "Analyzing market data..."},
            {"agent": "regulatory_compliance", "progress": 33.3, "message": "Checking regulatory requirements..."},
            {"agent": "fraud_detection", "progress": 50.0, "message": "Detecting fraud patterns..."},
            {"agent": "risk_assessment", "progress": 66.7, "message": "Evaluating business risks..."},
            {"agent": "customer_behavior_intelligence", "progress": 83.3, "message": "Analyzing customer behavior..."},
            {"agent": "synthesis", "progress": 100.0, "message": "Generating recommendations..."}
        ]
        
        for stage in progress_stages:
            progress_update = ProgressUpdate(
                validation_id=self.test_validation_id,
                status=WorkflowStatus.IN_PROGRESS,
                progress_percentage=stage["progress"],
                current_agent=stage["agent"],
                message=stage["message"]
            )
            
            await send_progress_update(self.test_validation_id, progress_update)
            
            # Verify update was sent
            assert mock_websocket.send_text.called
            
            # Small delay to simulate real-time updates
            await asyncio.sleep(0.1)
        
        # Send completion notification
        from riskintel360.api.websockets import send_validation_completed
        result_summary = {
            "overall_score": 78.5,
            "confidence_level": 0.85,
            "completion_time": 3600
        }
        
        await send_validation_completed(self.test_validation_id, result_summary)
        
        # Verify completion was sent
        assert mock_websocket.send_text.called
        
        print("??Real-time progress updates test passed")
    
    async def test_real_time_error_notifications(self):
        """Test real-time error notifications"""
        
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        # Connect WebSocket
        await connection_manager.connect(mock_websocket, self.test_validation_id, self.test_user_id)
        
        # Send error notification
        from riskintel360.api.websockets import send_validation_failed
        error_message = "External API rate limit exceeded"
        
        await send_validation_failed(self.test_validation_id, error_message)
        
        # Verify error notification was sent
        assert mock_websocket.send_text.called
        
        # Verify error message format
        sent_data = mock_websocket.send_text.call_args[0][0]
        parsed_message = json.loads(sent_data)
        
        assert parsed_message["type"] == "validation_failed"
        assert parsed_message["data"]["validation_id"] == self.test_validation_id
        assert parsed_message["data"]["error"] == error_message
        
        print("??Real-time error notifications test passed")


if __name__ == "__main__":
    # Run WebSocket integration tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])
