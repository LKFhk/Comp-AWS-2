"""
Mock Services for E2E Testing

This module provides comprehensive mocking for external services to enable
E2E testing without requiring actual external connectivity.
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, Mock, MagicMock
import numpy as np


class MockAPIServer:
    """Mock API server for E2E testing"""
    
    def __init__(self):
        self.workflows = {}
        self.users = {}
        self.sessions = {}
        self._setup_default_data()
    
    def _setup_default_data(self):
        """Setup default test data"""
        # Default test user
        self.users["fintech.analyst@riskintel360.com"] = {
            "user_id": "fintech-analyst-001",
            "email": "fintech.analyst@riskintel360.com",
            "tenant_id": "riskintel360-demo",
            "roles": ["fintech_analyst", "risk_manager"],
            "password_hash": "hashed_password"
        }
    
    async def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """Mock authentication"""
        if email in self.users:
            return {
                "access_token": f"mock_token_{email}",
                "token_type": "bearer",
                "expires_in": 3600,
                "user_id": self.users[email]["user_id"]
            }
        raise ValueError("Invalid credentials")
    
    async def create_risk_analysis(
        self, 
        user_id: str, 
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock risk analysis creation"""
        workflow_id = f"workflow_{len(self.workflows) + 1:06d}"
        
        self.workflows[workflow_id] = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "status": "created",
            "analysis_data": analysis_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "agent_statuses": {
                "regulatory_compliance": {"status": "pending", "progress": 0},
                "fraud_detection": {"status": "pending", "progress": 0},
                "market_analysis": {"status": "pending", "progress": 0},
                "kyc_verification": {"status": "pending", "progress": 0},
                "risk_assessment": {"status": "pending", "progress": 0}
            },
            "results": {}
        }
        
        return {"workflow_id": workflow_id, "status": "created"}
    
    async def start_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Mock workflow start"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        self.workflows[workflow_id]["status"] = "running"
        self.workflows[workflow_id]["started_at"] = datetime.now(timezone.utc).isoformat()
        
        # Simulate agent execution asynchronously
        asyncio.create_task(self._simulate_workflow_execution(workflow_id))
        
        return {"status": "started", "workflow_id": workflow_id}
    
    async def _simulate_workflow_execution(self, workflow_id: str):
        """Simulate workflow execution with realistic timing"""
        workflow = self.workflows[workflow_id]
        agents = list(workflow["agent_statuses"].keys())
        
        # Simulate each agent completing
        for i, agent_id in enumerate(agents):
            await asyncio.sleep(0.5)  # Simulate processing time
            
            workflow["agent_statuses"][agent_id] = {
                "status": "completed",
                "progress": 100,
                "execution_time_ms": np.random.randint(1000, 4000),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Generate mock results for each agent
            workflow["results"][agent_id] = self._generate_agent_results(agent_id, workflow["analysis_data"])
        
        # Mark workflow as completed
        workflow["status"] = "completed"
        workflow["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Calculate business value
        workflow["business_value"] = self._calculate_business_value(workflow["analysis_data"])
        workflow["efficiency_metrics"] = {
            "time_reduction_percentage": 0.95,
            "cost_reduction_percentage": 0.80
        }
    
    def _generate_agent_results(self, agent_id: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock results for an agent"""
        base_results = {
            "agent_id": agent_id,
            "confidence_score": np.random.uniform(0.75, 0.95),
            "processing_time_ms": np.random.randint(1000, 4000),
            "data_sources_used": ["public_data"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if agent_id == "regulatory_compliance":
            base_results.update({
                "compliance_status": "compliant",
                "regulations_analyzed": ["SEC", "FINRA", "CFPB"],
                "compliance_gaps": [],
                "recommendations": ["Maintain current compliance posture"]
            })
        elif agent_id == "fraud_detection":
            base_results.update({
                "fraud_risk_level": "low",
                "anomalies_detected": 5,
                "false_positive_rate": 0.05,
                "confidence_scores": [0.85, 0.90, 0.88, 0.92, 0.87]
            })
        elif agent_id == "market_analysis":
            base_results.update({
                "market_trend": "bullish",
                "volatility_level": "medium",
                "opportunities": ["Digital banking expansion", "AI-powered lending"],
                "risks": ["Regulatory changes", "Market competition"]
            })
        elif agent_id == "kyc_verification":
            base_results.update({
                "verification_status": "verified",
                "risk_score": 0.15,
                "identity_confidence": 0.95,
                "sanctions_check": "clear"
            })
        elif agent_id == "risk_assessment":
            base_results.update({
                "overall_risk_score": 0.25,
                "risk_categories": {
                    "credit_risk": 0.20,
                    "market_risk": 0.30,
                    "operational_risk": 0.25,
                    "regulatory_risk": 0.15
                },
                "mitigation_strategies": ["Diversification", "Hedging", "Compliance monitoring"]
            })
        
        return base_results
    
    def _calculate_business_value(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate mock business value metrics"""
        company_type = analysis_data.get("custom_parameters", {}).get("company_type", "fintech_startup")
        
        # Base values by company type
        value_multipliers = {
            "fintech_startup": 1.0,
            "digital_bank": 10.0,
            "traditional_bank": 100.0,
            "payment_processor": 50.0,
            "crypto_exchange": 75.0
        }
        
        multiplier = value_multipliers.get(company_type, 1.0)
        
        return {
            "fraud_prevention_annual": int(100000 * multiplier),
            "compliance_cost_savings_annual": int(50000 * multiplier),
            "risk_reduction_value": int(75000 * multiplier),
            "total_annual_value": int(225000 * multiplier),
            "roi_multiplier": 10.0,
            "payback_period_months": 6
        }
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        return {
            "workflow_id": workflow_id,
            "status": workflow["status"],
            "agent_statuses": workflow["agent_statuses"],
            "progress": self._calculate_progress(workflow),
            "created_at": workflow["created_at"],
            "started_at": workflow.get("started_at"),
            "completed_at": workflow.get("completed_at")
        }
    
    def _calculate_progress(self, workflow: Dict[str, Any]) -> float:
        """Calculate overall workflow progress"""
        agent_statuses = workflow["agent_statuses"]
        total_progress = sum(
            status.get("progress", 0) 
            for status in agent_statuses.values()
        )
        return total_progress / len(agent_statuses) if agent_statuses else 0
    
    async def get_workflow_results(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow results"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        if workflow["status"] != "completed":
            return {
                "workflow_id": workflow_id,
                "status": workflow["status"],
                "message": "Workflow not yet completed"
            }
        
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "agent_results": workflow["results"],
            "business_value": workflow.get("business_value", {}),
            "efficiency_metrics": workflow.get("efficiency_metrics", {}),
            "completed_at": workflow["completed_at"]
        }
    
    async def execute_fraud_detection(
        self, 
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock fraud detection execution"""
        transactions = transaction_data.get("transactions", [])
        known_fraud_indices = transaction_data.get("known_fraud_indices", [])
        
        # Simulate ML-based fraud detection with high precision
        detected_fraud_indices = []
        confidence_scores = []
        
        # Set seed for reproducible results
        np.random.seed(42)
        
        for i, txn in enumerate(transactions):
            # Simulate detection with high accuracy for known fraud
            if i in known_fraud_indices:
                # 85% chance of detecting known fraud (high recall)
                if np.random.random() < 0.85:
                    detected_fraud_indices.append(i)
                    confidence_scores.append(np.random.uniform(0.80, 0.95))
            else:
                # Very low false positive rate (2%) for high precision
                if np.random.random() < 0.02:
                    detected_fraud_indices.append(i)
                    confidence_scores.append(np.random.uniform(0.60, 0.75))
        
        # Calculate metrics
        true_positives = len(set(detected_fraud_indices) & set(known_fraud_indices))
        false_positives = len(set(detected_fraud_indices) - set(known_fraud_indices))
        false_negatives = len(set(known_fraud_indices) - set(detected_fraud_indices))
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        
        return {
            "total_transactions": len(transactions),
            "fraud_detected": len(detected_fraud_indices),
            "detected_fraud_indices": detected_fraud_indices,
            "confidence_scores": confidence_scores,
            "average_confidence": np.mean(confidence_scores) if confidence_scores else 0,
            "metrics": {
                "precision": precision,
                "recall": recall,
                "f1_score": 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0,
                "false_positive_rate": false_positives / len(transactions) if transactions else 0
            },
            "processing_time_ms": np.random.randint(2000, 4500)
        }
    
    async def analyze_regulatory_compliance(
        self, 
        compliance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock regulatory compliance analysis"""
        requirements = compliance_data.get("compliance_requirements", [])
        
        return {
            "compliance_status": "compliant",
            "regulations_analyzed": requirements,
            "data_sources": ["SEC", "FINRA", "CFPB"],
            "compliance_score": np.random.uniform(0.85, 0.95),
            "gaps_identified": [],
            "recommendations": [
                "Continue monitoring regulatory updates",
                "Maintain current compliance documentation",
                "Schedule quarterly compliance reviews"
            ],
            "estimated_compliance_cost": 50000,
            "processing_time_ms": np.random.randint(3000, 5000)
        }


class MockHTTPClient:
    """Mock HTTP client for testing"""
    
    def __init__(self, mock_server: MockAPIServer):
        self.mock_server = mock_server
        self.base_url = "http://test-api:8000"
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def post(self, url: str, json: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Mock:
        """Mock POST request"""
        response = Mock()
        response.status_code = 200
        
        # Route to appropriate handler
        if "/auth/login" in url:
            result = await self.mock_server.authenticate(
                json.get("email"), 
                json.get("password")
            )
            response.json = lambda: result
            
        elif "/fintech/risk-analysis" in url:
            # Extract user_id from token
            token = headers.get("Authorization", "").replace("Bearer ", "")
            user_id = token.split("_")[-1] if "_" in token else "test_user"
            
            result = await self.mock_server.create_risk_analysis(user_id, json)
            response.status_code = 201
            response.json = lambda: result
            
        elif "/workflows/" in url and "/start" in url:
            workflow_id = url.split("/workflows/")[1].split("/start")[0]
            result = await self.mock_server.start_workflow(workflow_id)
            response.json = lambda: result
            
        elif "/fraud-detection" in url:
            result = await self.mock_server.execute_fraud_detection(json)
            response.json = lambda: result
            
        elif "/compliance-check" in url:
            result = await self.mock_server.analyze_regulatory_compliance(json)
            response.json = lambda: result
        
        else:
            response.json = lambda: {"status": "success", "message": "Mock response"}
        
        return response
    
    async def get(self, url: str, headers: Dict[str, str] = None) -> Mock:
        """Mock GET request"""
        response = Mock()
        response.status_code = 200
        
        # Route to appropriate handler
        if "/workflows/" in url and "/status" in url:
            workflow_id = url.split("/workflows/")[1].split("/status")[0]
            result = await self.mock_server.get_workflow_status(workflow_id)
            response.json = lambda: result
            
        elif "/workflows/" in url and "/results" in url:
            workflow_id = url.split("/workflows/")[1].split("/results")[0]
            result = await self.mock_server.get_workflow_results(workflow_id)
            response.json = lambda: result
        
        else:
            response.json = lambda: {"status": "success", "data": {}}
        
        return response


class MockWebSocketClient:
    """Mock WebSocket client for testing"""
    
    def __init__(self):
        self.messages = []
        self.connected = False
    
    async def __aenter__(self):
        self.connected = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.connected = False
    
    async def send(self, message: str):
        """Mock send message"""
        self.messages.append({"type": "sent", "message": message, "timestamp": datetime.now().isoformat()})
    
    async def recv(self) -> str:
        """Mock receive message"""
        # Simulate receiving workflow updates
        update = {
            "type": "workflow_update",
            "status": "running",
            "progress": np.random.randint(0, 100),
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(update)


def create_mock_http_client(mock_server: MockAPIServer = None):
    """Factory function to create mock HTTP client"""
    if mock_server is None:
        mock_server = MockAPIServer()
    return MockHTTPClient(mock_server)


def create_mock_websocket_client():
    """Factory function to create mock WebSocket client"""
    return MockWebSocketClient()
