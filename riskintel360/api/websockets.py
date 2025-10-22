"""
WebSocket endpoints for real-time updates in RiskIntel360 Platform
Provides real-time progress updates for validation workflows.
"""

import logging
import json
import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.websockets import WebSocketState

from riskintel360.models import data_manager
from pydantic import BaseModel
from datetime import datetime
# Note: WebSocket auth is simplified for demo purposes

logger = logging.getLogger(__name__)

router = APIRouter()

class ProgressUpdate(BaseModel):
    """Progress update model for WebSocket messages"""
    validation_id: str
    status: str
    progress_percentage: float
    message: str
    timestamp: datetime = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now()
        super().__init__(**data)

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, validation_id: str):
        """Connect a WebSocket to a validation"""
        await websocket.accept()
        
        if validation_id not in self.active_connections:
            self.active_connections[validation_id] = set()
        
        self.active_connections[validation_id].add(websocket)
        logger.info(f"WebSocket connected for validation {validation_id}")
    
    def disconnect(self, websocket: WebSocket, validation_id: str):
        """Disconnect a WebSocket from a validation"""
        if validation_id in self.active_connections:
            self.active_connections[validation_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[validation_id]:
                del self.active_connections[validation_id]
        
        logger.info(f"WebSocket disconnected for validation {validation_id}")
    
    async def send_progress_update(self, validation_id: str, data: dict):
        """Send progress update to all connected clients for a validation"""
        if validation_id in self.active_connections:
            disconnected = set()
            
            for websocket in self.active_connections[validation_id]:
                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_text(json.dumps(data))
                    else:
                        disconnected.add(websocket)
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
                    disconnected.add(websocket)
            
            # Remove disconnected websockets
            for websocket in disconnected:
                self.active_connections[validation_id].discard(websocket)

manager = ConnectionManager()

# Export connection manager for testing
connection_manager = manager

# Store active general WebSocket connections
class GeneralConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Connect a WebSocket for general updates"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("General WebSocket connected")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket"""
        self.active_connections.discard(websocket)
        logger.info("General WebSocket disconnected")
    
    async def broadcast(self, data: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        
        for websocket in self.active_connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps(data))
                else:
                    disconnected.add(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting WebSocket message: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected websockets
        for websocket in disconnected:
            self.active_connections.discard(websocket)

general_manager = GeneralConnectionManager()


@router.websocket("/ws")
async def websocket_general_updates(websocket: WebSocket):
    """
    General WebSocket endpoint for real-time fintech updates.
    """
    try:
        await general_manager.connect(websocket)
        
        # Send initial connection message
        initial_message = {
            "type": "connection",
            "message": "Connected to RiskIntel360 real-time updates",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(initial_message))
        
        # Keep connection alive and handle messages
        try:
            while True:
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    
                    # Handle client messages
                    try:
                        data = json.loads(message)
                        if data.get("type") == "ping":
                            await websocket.send_text(json.dumps({"type": "pong"}))
                        elif data.get("type") == "subscribe":
                            # Handle channel subscriptions
                            channels = data.get("channels", [])
                            await websocket.send_text(json.dumps({
                                "type": "subscribed",
                                "channels": channels,
                                "message": f"Subscribed to {len(channels)} channels"
                            }))
                    except json.JSONDecodeError:
                        pass
                        
                except asyncio.TimeoutError:
                    # Send periodic heartbeat
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
        except WebSocketDisconnect:
            pass
            
    except Exception as e:
        logger.error(f"General WebSocket error: {e}")
        try:
            await websocket.close(code=4000, reason="Internal server error")
        except:
            pass
    finally:
        general_manager.disconnect(websocket)


@router.websocket("/ws/validation/{validation_id}/progress")
async def websocket_validation_progress(
    websocket: WebSocket,
    validation_id: str
):
    """
    WebSocket endpoint for real-time validation progress updates.
    """
    try:
        # Verify validation exists and user has access
        # Note: WebSocket auth is simplified for demo purposes
        validation = await data_manager.get_validation_request(validation_id)
        if not validation:
            await websocket.close(code=4004, reason="Validation not found")
            return
        
        # Connect WebSocket
        await manager.connect(websocket, validation_id)
        
        # Send initial status
        initial_status = {
            "type": "status_update",
            "validation_id": validation_id,
            "status": validation.status or "pending",
            "progress_percentage": 0.0,
            "message": "Connected to validation progress updates"
        }
        await websocket.send_text(json.dumps(initial_status))
        
        # Keep connection alive and handle messages
        try:
            while True:
                # Wait for messages from client (ping/pong, etc.)
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    
                    # Handle client messages
                    try:
                        data = json.loads(message)
                        if data.get("type") == "ping":
                            await websocket.send_text(json.dumps({"type": "pong"}))
                    except json.JSONDecodeError:
                        pass
                        
                except asyncio.TimeoutError:
                    # Send periodic heartbeat
                    await websocket.send_text(json.dumps({"type": "heartbeat"}))
                    
        except WebSocketDisconnect:
            pass
            
    except Exception as e:
        logger.error(f"WebSocket error for validation {validation_id}: {e}")
        try:
            await websocket.close(code=4000, reason="Internal server error")
        except:
            pass
    finally:
        manager.disconnect(websocket, validation_id)


# Function to send progress updates from workflow orchestrator
async def send_progress_update(validation_id: str, progress_data: dict):
    """
    Send progress update to all connected WebSocket clients.
    Called by the workflow orchestrator.
    """
    try:
        await manager.send_progress_update(validation_id, {
            "type": "progress_update",
            "validation_id": validation_id,
            **progress_data
        })
    except Exception as e:
        logger.error(f"Failed to send progress update for {validation_id}: {e}")


# Function to send completion notification
async def send_validation_completion(validation_id: str, result_data: dict):
    """
    Send completion notification to all connected WebSocket clients.
    """
    try:
        await manager.send_progress_update(validation_id, {
            "type": "completion",
            "validation_id": validation_id,
            "status": "completed",
            "progress_percentage": 100.0,
            "message": "Validation completed successfully",
            **result_data
        })
    except Exception as e:
        logger.error(f"Failed to send completion notification for {validation_id}: {e}")


# Functions for general real-time updates
async def broadcast_fraud_alert(alert_data: dict):
    """Broadcast fraud alert to all connected clients"""
    try:
        await general_manager.broadcast({
            "type": "fraud_alert",
            "data": alert_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to broadcast fraud alert: {e}")


async def broadcast_compliance_update(compliance_data: dict):
    """Broadcast compliance update to all connected clients"""
    try:
        await general_manager.broadcast({
            "type": "compliance_alert",
            "data": compliance_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to broadcast compliance update: {e}")


async def broadcast_market_update(market_data: dict):
    """Broadcast market update to all connected clients"""
    try:
        await general_manager.broadcast({
            "type": "market_update",
            "data": market_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to broadcast market update: {e}")


async def broadcast_kyc_alert(kyc_data: dict):
    """Broadcast KYC alert to all connected clients"""
    try:
        await general_manager.broadcast({
            "type": "kyc_alert",
            "data": kyc_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to broadcast KYC alert: {e}")


async def broadcast_demo_progress(demo_data: dict):
    """Broadcast demo progress to all connected clients"""
    try:
        await general_manager.broadcast({
            "type": "demo_progress",
            "data": demo_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to broadcast demo progress: {e}")


async def broadcast_performance_update(performance_data: dict):
    """Broadcast performance update to all connected clients"""
    try:
        await general_manager.broadcast({
            "type": "performance_update",
            "data": performance_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to broadcast performance update: {e}")
