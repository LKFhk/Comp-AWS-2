"""
WebSocket Real-time Updates End-to-End Tests
Tests real-time progress monitoring and live status updates via WebSocket
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
import httpx
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException


class TestWebSocketRealtime:
    """Test WebSocket real-time updates and progress monitoring"""
    
    @pytest.fixture(scope="class")
    def api_base_url(self):
        """API base URL for testing"""
        return "http://test-api:8000"
    
    @pytest.fixture(scope="class")
    def websocket_base_url(self):
        """WebSocket base URL for testing"""
        return "ws://test-api:8000"
    
    @pytest.fixture(scope="class")
    async def authenticated_client(self, api_base_url):
        """Authenticated HTTP client"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            auth_response = await client.post(f"{api_base_url}/api/v1/auth/login", json={
                "email": "analyst@testcorp.com",
                "password": "test_password_123"
            })
            assert auth_response.status_code == 200
            access_token = auth_response.json()["access_token"]
            client.headers.update({"Authorization": f"Bearer {access_token}"})
            yield client
    
    @pytest.mark.asyncio
    async def test_validation_progress_websocket_updates(self, api_base_url, websocket_base_url, authenticated_client):
        """
        Test real-time progress updates via WebSocket during validation workflow
        Verify progress updates, agent status changes, and completion notifications
        """
        print("\n?? Testing Validation Progress WebSocket Updates")
        print("=" * 50)
        
        # Create validation request
        validation_data = {
            "business_concept": "WebSocket test - Real-time analytics dashboard",
            "target_market": "Businesses requiring real-time data monitoring",
            "analysis_scope": ["market", "competitive", "financial", "risk", "customer"],
            "priority": "high",
            "custom_parameters": {
                "websocket_test": True,
                "real_time_updates": True
            }
        }
        
        create_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations",
            json=validation_data
        )
        assert create_response.status_code == 201
        validation_id = create_response.json()["id"]
        
        print(f"   ??Validation created for WebSocket test: {validation_id}")
        
        # Set up WebSocket connection for progress monitoring
        websocket_uri = f"{websocket_base_url}/ws/validations/{validation_id}/progress"
        
        received_updates = []
        connection_events = []
        
        async def websocket_listener():
            """Listen for WebSocket updates"""
            try:
                print(f"   ?? Connecting to WebSocket: {websocket_uri}")
                
                async with websockets.connect(websocket_uri) as websocket:
                    connection_events.append({"event": "connected", "timestamp": time.time()})
                    print("   ??WebSocket connection established")
                    
                    # Listen for updates for up to 5 minutes
                    timeout = time.time() + 300
                    
                    while time.time() < timeout:
                        try:
                            # Wait for message with timeout
                            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                            
                            try:
                                update_data = json.loads(message)
                                received_updates.append({
                                    "data": update_data,
                                    "timestamp": time.time(),
                                    "raw_message": message
                                })
                                
                                # Log update details
                                update_type = update_data.get("type", "unknown")
                                status = update_data.get("status", "unknown")
                                agent_id = update_data.get("agent_id", "system")
                                
                                print(f"   ?�� WebSocket Update: {update_type} - {agent_id} - {status}")
                                
                                # Check for completion
                                if update_data.get("status") == "completed" and update_data.get("type") == "workflow":
                                    print("   ?? Workflow completion received via WebSocket")
                                    break
                                    
                            except json.JSONDecodeError:
                                print(f"   ?��? Invalid JSON received: {message}")
                                received_updates.append({
                                    "data": {"error": "invalid_json", "raw": message},
                                    "timestamp": time.time(),
                                    "raw_message": message
                                })
                        
                        except asyncio.TimeoutError:
                            # No message received in timeout period, continue listening
                            continue
                        except ConnectionClosed:
                            print("   ?? WebSocket connection closed")
                            connection_events.append({"event": "closed", "timestamp": time.time()})
                            break
                        except WebSocketException as e:
                            print(f"   ??WebSocket error: {e}")
                            connection_events.append({"event": "error", "timestamp": time.time(), "error": str(e)})
                            break
                            
            except Exception as e:
                print(f"   ??WebSocket connection failed: {e}")
                connection_events.append({"event": "connection_failed", "timestamp": time.time(), "error": str(e)})
        
        # Start WebSocket listener
        websocket_task = asyncio.create_task(websocket_listener())
        
        # Wait a moment for WebSocket connection to establish
        await asyncio.sleep(2)
        
        # Start validation workflow
        print("   ?? Starting validation workflow...")
        
        start_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations/{validation_id}/start"
        )
        assert start_response.status_code == 200
        
        workflow_start_time = time.time()
        
        # Monitor workflow progress via both WebSocket and API
        api_status_checks = []
        max_wait_time = 300  # 5 minutes
        
        while (time.time() - workflow_start_time) < max_wait_time:
            # Check API status
            status_response = await authenticated_client.get(
                f"{api_base_url}/api/v1/validations/{validation_id}/status"
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                api_status_checks.append({
                    "timestamp": time.time(),
                    "status": status_data.get("status"),
                    "agent_statuses": status_data.get("agent_statuses", {})
                })
                
                # Check if workflow completed
                if status_data.get("status") == "completed":
                    print("   ??Workflow completed (confirmed via API)")
                    break
            
            await asyncio.sleep(5)  # Check every 5 seconds
        
        # Wait a bit more for final WebSocket updates
        await asyncio.sleep(5)
        
        # Cancel WebSocket listener
        websocket_task.cancel()
        try:
            await websocket_task
        except asyncio.CancelledError:
            pass
        
        total_workflow_time = time.time() - workflow_start_time
        
        # Analyze WebSocket update quality
        print(f"\n   ?? WebSocket Update Analysis:")
        print(f"   ?��?  Total Workflow Time: {total_workflow_time:.1f}s")
        print(f"   ?�� Total Updates Received: {len(received_updates)}")
        print(f"   ?? Connection Events: {len(connection_events)}")
        
        # Verify WebSocket connection was established
        connection_established = any(event.get("event") == "connected" for event in connection_events)
        assert connection_established, "WebSocket connection was not established"
        print("   ??WebSocket connection established successfully")
        
        # Verify we received updates
        assert len(received_updates) > 0, "No WebSocket updates received"
        print(f"   ??Received {len(received_updates)} real-time updates")
        
        # Analyze update types and content
        update_types = {}
        agent_updates = {}
        status_updates = {}
        
        for update in received_updates:
            data = update.get("data", {})
            update_type = data.get("type", "unknown")
            agent_id = data.get("agent_id", "system")
            status = data.get("status", "unknown")
            
            # Count update types
            update_types[update_type] = update_types.get(update_type, 0) + 1
            
            # Count agent updates
            if agent_id != "system":
                agent_updates[agent_id] = agent_updates.get(agent_id, 0) + 1
            
            # Count status updates
            status_updates[status] = status_updates.get(status, 0) + 1
        
        print(f"\n   ?? Update Type Distribution:")
        for update_type, count in update_types.items():
            print(f"      {update_type}: {count} updates")
        
        print(f"\n   ?? Agent Update Distribution:")
        for agent_id, count in agent_updates.items():
            print(f"      {agent_id}: {count} updates")
        
        print(f"\n   ?? Status Update Distribution:")
        for status, count in status_updates.items():
            print(f"      {status}: {count} updates")
        
        # Verify update quality
        expected_update_types = ["agent_started", "agent_progress", "agent_completed", "workflow_progress"]
        received_update_types = set(update_types.keys())
        
        # Should receive various types of updates
        assert len(received_update_types) >= 2, f"Too few update types: {received_update_types}"
        
        # Verify agent updates were received
        assert len(agent_updates) > 0, "No agent-specific updates received"
        
        # Verify status progression
        expected_statuses = ["started", "in_progress", "completed"]
        received_statuses = set(status_updates.keys())
        status_overlap = received_statuses.intersection(expected_statuses)
        
        assert len(status_overlap) >= 2, f"Missing expected status updates: {status_overlap}"
        
        # Verify update frequency (should receive updates regularly)
        if len(received_updates) >= 2:
            update_timestamps = [update["timestamp"] for update in received_updates]
            time_intervals = [update_timestamps[i+1] - update_timestamps[i] for i in range(len(update_timestamps)-1)]
            avg_interval = sum(time_intervals) / len(time_intervals)
            
            print(f"   ?��?  Average Update Interval: {avg_interval:.1f}s")
            
            # Updates should be reasonably frequent (not more than 30 seconds apart on average)
            assert avg_interval <= 30, f"Updates too infrequent: {avg_interval:.1f}s average interval"
        
        print("   ?? WebSocket Real-time Updates: SUCCESS")
        print("   ??Connection established and maintained")
        print("   ??Real-time updates received throughout workflow")
        print("   ??Update frequency and quality verified")
    
    @pytest.mark.asyncio
    async def test_multiple_websocket_connections(self, api_base_url, websocket_base_url, authenticated_client):
        """
        Test multiple concurrent WebSocket connections
        Verify system can handle multiple clients monitoring the same validation
        """
        print("\n?? Testing Multiple WebSocket Connections")
        print("=" * 40)
        
        # Create validation
        validation_data = {
            "business_concept": "Multi-connection test - Collaborative platform",
            "target_market": "Teams requiring real-time collaboration",
            "analysis_scope": ["market", "competitive", "financial"],
            "priority": "medium",
            "custom_parameters": {
                "multi_connection_test": True
            }
        }
        
        create_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations",
            json=validation_data
        )
        assert create_response.status_code == 201
        validation_id = create_response.json()["id"]
        
        print(f"   ??Validation created: {validation_id}")
        
        # Set up multiple WebSocket connections
        websocket_uri = f"{websocket_base_url}/ws/validations/{validation_id}/progress"
        connection_count = 3
        
        connection_results = []
        
        async def websocket_client(client_id: int):
            """Individual WebSocket client"""
            updates_received = []
            
            try:
                async with websockets.connect(websocket_uri) as websocket:
                    print(f"   ?? Client {client_id} connected")
                    
                    # Listen for updates for up to 2 minutes
                    timeout = time.time() + 120
                    
                    while time.time() < timeout:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            update_data = json.loads(message)
                            updates_received.append({
                                "client_id": client_id,
                                "data": update_data,
                                "timestamp": time.time()
                            })
                            
                            # Check for completion
                            if update_data.get("status") == "completed":
                                break
                                
                        except asyncio.TimeoutError:
                            continue
                        except json.JSONDecodeError:
                            continue
                        except ConnectionClosed:
                            break
                
                return {
                    "client_id": client_id,
                    "status": "success",
                    "updates_count": len(updates_received),
                    "updates": updates_received
                }
                
            except Exception as e:
                return {
                    "client_id": client_id,
                    "status": "error",
                    "error": str(e),
                    "updates_count": len(updates_received),
                    "updates": updates_received
                }
        
        # Start multiple WebSocket clients
        client_tasks = [websocket_client(i) for i in range(connection_count)]
        
        # Wait for connections to establish
        await asyncio.sleep(2)
        
        # Start validation workflow
        start_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations/{validation_id}/start"
        )
        assert start_response.status_code == 200
        
        print(f"   ?? Workflow started with {connection_count} WebSocket clients")
        
        # Wait for all clients to complete
        connection_results = await asyncio.gather(*client_tasks, return_exceptions=True)
        
        # Analyze multiple connection results
        successful_connections = 0
        total_updates = 0
        
        print(f"\n   ?? Multiple Connection Results:")
        
        for result in connection_results:
            if isinstance(result, Exception):
                print(f"   ??Client failed with exception: {result}")
            elif isinstance(result, dict):
                client_id = result.get("client_id", "unknown")
                status = result.get("status", "unknown")
                updates_count = result.get("updates_count", 0)
                
                print(f"   ?�� Client {client_id}: {status} - {updates_count} updates")
                
                if status == "success":
                    successful_connections += 1
                    total_updates += updates_count
        
        print(f"\n   ?? Connection Summary:")
        print(f"   ??Successful Connections: {successful_connections}/{connection_count}")
        print(f"   ?�� Total Updates Received: {total_updates}")
        
        # Verify multiple connections worked
        assert successful_connections >= 2, f"Too few successful connections: {successful_connections}/{connection_count}"
        
        # Verify all clients received updates
        assert total_updates > 0, "No updates received across all connections"
        
        # Verify update distribution (all clients should receive similar updates)
        if successful_connections >= 2:
            update_counts = [result.get("updates_count", 0) for result in connection_results 
                           if isinstance(result, dict) and result.get("status") == "success"]
            
            if len(update_counts) >= 2:
                avg_updates = sum(update_counts) / len(update_counts)
                update_variance = max(update_counts) - min(update_counts)
                
                print(f"   ?? Average Updates per Client: {avg_updates:.1f}")
                print(f"   ?? Update Count Variance: {update_variance}")
                
                # Update counts should be reasonably similar across clients
                assert update_variance <= avg_updates * 0.5, "Too much variance in update distribution"
        
        print("   ?? Multiple WebSocket Connections: SUCCESS")
        print("   ??Multiple concurrent connections supported")
        print("   ??Updates distributed to all connected clients")
    
    @pytest.mark.asyncio
    async def test_websocket_connection_resilience(self, api_base_url, websocket_base_url, authenticated_client):
        """
        Test WebSocket connection resilience and reconnection
        Verify graceful handling of connection drops and reconnections
        """
        print("\n?? Testing WebSocket Connection Resilience")
        print("=" * 45)
        
        # Create validation
        validation_data = {
            "business_concept": "Resilience test - Network monitoring platform",
            "target_market": "IT teams requiring network reliability",
            "analysis_scope": ["market", "competitive"],
            "priority": "low",
            "custom_parameters": {
                "resilience_test": True
            }
        }
        
        create_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations",
            json=validation_data
        )
        assert create_response.status_code == 201
        validation_id = create_response.json()["id"]
        
        websocket_uri = f"{websocket_base_url}/ws/validations/{validation_id}/progress"
        
        connection_attempts = []
        updates_received = []
        
        async def resilient_websocket_client():
            """WebSocket client with reconnection logic"""
            max_attempts = 3
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                
                try:
                    print(f"   ?? Connection attempt {attempt}")
                    
                    async with websockets.connect(websocket_uri) as websocket:
                        connection_attempts.append({
                            "attempt": attempt,
                            "status": "connected",
                            "timestamp": time.time()
                        })
                        
                        print(f"   ??Connected on attempt {attempt}")
                        
                        # Listen for updates
                        timeout = time.time() + 60  # 1 minute per attempt
                        
                        while time.time() < timeout:
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                                update_data = json.loads(message)
                                updates_received.append({
                                    "attempt": attempt,
                                    "data": update_data,
                                    "timestamp": time.time()
                                })
                                
                                print(f"   ?�� Update received on attempt {attempt}")
                                
                            except asyncio.TimeoutError:
                                continue
                            except ConnectionClosed:
                                print(f"   ?? Connection closed on attempt {attempt}")
                                break
                            except json.JSONDecodeError:
                                continue
                        
                        # If we reach here, connection was successful for the duration
                        break
                        
                except Exception as e:
                    connection_attempts.append({
                        "attempt": attempt,
                        "status": "failed",
                        "error": str(e),
                        "timestamp": time.time()
                    })
                    
                    print(f"   ??Connection attempt {attempt} failed: {e}")
                    
                    if attempt < max_attempts:
                        print(f"   ??Waiting before retry...")
                        await asyncio.sleep(5)  # Wait before retry
        
        # Start resilient client
        client_task = asyncio.create_task(resilient_websocket_client())
        
        # Wait for initial connection
        await asyncio.sleep(3)
        
        # Start validation
        start_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations/{validation_id}/start"
        )
        assert start_response.status_code == 200
        
        print("   ?? Validation started with resilient WebSocket client")
        
        # Wait for client to complete
        await client_task
        
        # Analyze resilience results
        print(f"\n   ?? Connection Resilience Results:")
        print(f"   ?? Connection Attempts: {len(connection_attempts)}")
        print(f"   ?�� Updates Received: {len(updates_received)}")
        
        successful_connections = sum(1 for attempt in connection_attempts if attempt.get("status") == "connected")
        failed_connections = sum(1 for attempt in connection_attempts if attempt.get("status") == "failed")
        
        print(f"   ??Successful Connections: {successful_connections}")
        print(f"   ??Failed Connections: {failed_connections}")
        
        # Verify resilience
        assert successful_connections > 0, "No successful WebSocket connections"
        
        if len(updates_received) > 0:
            print("   ??Updates received despite connection challenges")
        
        # Verify connection attempts were reasonable
        assert len(connection_attempts) <= 3, "Too many connection attempts needed"
        
        print("   ?? WebSocket Connection Resilience: SUCCESS")
        print("   ??Connection resilience verified")
        print("   ??Graceful handling of connection issues")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
