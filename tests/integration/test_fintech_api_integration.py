"""
Integration tests for fintech API endpoint workflows.
Tests complete API workflows, authentication, and business logic integration.
"""

import pytest
import pytest_asyncio
import asyncio
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from httpx import AsyncClient

from riskintel360.api.main import app
from riskintel360.api.fintech_endpoints import (
    RiskAnalysisRequest, ComplianceCheckRequest, FraudDetectionRequest,
    MarketIntelligenceRequest, KYCVerificationRequest
)
from riskintel360.services.workflow_orchestrator import SupervisorAgent
from riskintel360.services.bedrock_client import BedrockClient
from riskintel360.agents.agent_factory import AgentFactory
from riskintel360.models.agent_models import AgentType


class TestFinTechAPIEndpointIntegration:
    """Integration tests for fintech API endpoints"""
    
    @pytest.fixture
    def test_client(self):
        """Create test client for FastAPI application"""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Create async test client for FastAPI application"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.fixture
    def mock_workflow_orchestrator(self):
        """Mock workflow orchestrator for testing"""
        mock_orchestrator = Mock(spec=SupervisorAgent)
        mock_orchestrator.start_workflow = AsyncMock()
        mock_orchestrator.get_workflow_status = Mock()
        mock_orchestrator.get_workflow_results = AsyncMock()
        return mock_orchestrator
    
    @pytest.fixture
    def mock_agent_factory(self):
        """Mock agent factory for testing"""
        mock_factory = Mock(spec=AgentFactory)
        mock_factory.create_agent = Mock()
        return mock_factory
    
    @pytest.mark.integration
    def test_risk_analysis_endpoint_structure(self, test_client):
        """Test risk analysis endpoint structure and validation"""
        # Test valid risk analysis request
        valid_request = {
            "entity_id": "fintech_startup_123",
            "entity_type": "payment_processor",
            "analysis_scope": ["regulatory", "fraud", "market", "credit"],
            "urgency": "high",
            "business_context": {
                "industry": "payments",
                "stage": "series_a",
                "geography": "US"
            }
        }
        
        with patch('riskintel360.api.fintech_endpoints.get_workflow_orchestrator') as mock_get_orchestrator:
            mock_orchestrator = Mock()
            mock_orchestrator.start_fintech_workflow = AsyncMock(return_value="workflow_001")
            mock_get_orchestrator.return_value = mock_orchestrator
            
            response = test_client.post("/api/v1/risk-analysis", json=valid_request)
            
            # Verify response structure
            assert response.status_code == 200
            response_data = response.json()
            
            assert "workflow_id" in response_data
            assert "status" in response_data
            assert "estimated_completion_time" in response_data
            assert response_data["status"] == "initiated"
    
    @pytest.mark.integration
    def test_compliance_check_endpoint_structure(self, test_client):
        """Test compliance check endpoint structure and validation"""
        # Test valid compliance check request
        valid_request = {
            "entity_id": "fintech_startup_123",
            "business_type": "digital_wallet",
            "jurisdiction": "US",
            "regulations": ["SEC", "FINRA", "CFPB", "BSA"],
            "compliance_scope": "comprehensive"
        }
        
        with patch('riskintel360.api.fintech_endpoints.get_regulatory_compliance_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.analyze_compliance = AsyncMock(return_value={
                "compliance_status": "compliant",
                "risk_level": "medium",
                "confidence_score": 0.85,
                "analysis_id": "compliance_001"
            })
            mock_get_agent.return_value = mock_agent
            
            response = test_client.post("/api/v1/compliance-check", json=valid_request)
            
            # Verify response structure
            assert response.status_code == 200
            response_data = response.json()
            
            assert "analysis_id" in response_data
            assert "compliance_status" in response_data
            assert "risk_level" in response_data
            assert "confidence_score" in response_data
            assert response_data["compliance_status"] == "compliant"
    
    @pytest.mark.integration
    def test_fraud_detection_endpoint_structure(self, test_client):
        """Test fraud detection endpoint structure and validation"""
        # Test valid fraud detection request
        valid_request = {
            "transaction_batch_id": "batch_001",
            "transactions": [
                {
                    "transaction_id": "txn_001",
                    "amount": 100.00,
                    "currency": "USD",
                    "merchant": "grocery_store",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                {
                    "transaction_id": "txn_002", 
                    "amount": 50000.00,
                    "currency": "USD",
                    "merchant": "luxury_goods",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ],
            "analysis_type": "real_time",
            "ml_models": ["isolation_forest", "autoencoder"]
        }
        
        with patch('riskintel360.api.fintech_endpoints.get_fraud_detection_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.detect_fraud = AsyncMock(return_value={
                "analysis_id": "fraud_001",
                "fraud_alerts": [
                    {
                        "transaction_id": "txn_002",
                        "fraud_probability": 0.92,
                        "risk_factors": ["amount_anomaly", "merchant_category"],
                        "recommended_action": "block"
                    }
                ],
                "overall_risk_score": 0.46,
                "processing_time": 2.3
            })
            mock_get_agent.return_value = mock_agent
            
            response = test_client.post("/api/v1/fraud-detection", json=valid_request)
            
            # Verify response structure
            assert response.status_code == 200
            response_data = response.json()
            
            assert "analysis_id" in response_data
            assert "fraud_alerts" in response_data
            assert "overall_risk_score" in response_data
            assert "processing_time" in response_data
            assert len(response_data["fraud_alerts"]) > 0
    
    @pytest.mark.integration
    def test_market_intelligence_endpoint_structure(self, test_client):
        """Test market intelligence endpoint structure and validation"""
        # Test valid market intelligence request
        valid_request = {
            "analysis_type": "fintech_sector_analysis",
            "market_segment": "digital_payments",
            "time_horizon": "1Y",
            "data_sources": ["FRED", "yahoo_finance", "news_sentiment"],
            "focus_areas": ["trends", "volatility", "opportunities", "risks"]
        }
        
        with patch('riskintel360.api.fintech_endpoints.get_market_analysis_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.analyze_market_intelligence = AsyncMock(return_value={
                "analysis_id": "market_001",
                "trend_direction": "bullish",
                "volatility_level": 0.35,
                "key_drivers": ["regulatory_clarity", "adoption_growth"],
                "risk_factors": ["market_saturation", "competition"],
                "opportunities": ["cross_border_payments", "embedded_finance"],
                "confidence_score": 0.82
            })
            mock_get_agent.return_value = mock_agent
            
            response = test_client.post("/api/v1/market-intelligence", json=valid_request)
            
            # Verify response structure
            assert response.status_code == 200
            response_data = response.json()
            
            assert "analysis_id" in response_data
            assert "trend_direction" in response_data
            assert "volatility_level" in response_data
            assert "key_drivers" in response_data
            assert "confidence_score" in response_data
    
    @pytest.mark.integration
    def test_kyc_verification_endpoint_structure(self, test_client):
        """Test KYC verification endpoint structure and validation"""
        # Test valid KYC verification request
        valid_request = {
            "customer_id": "cust_123",
            "verification_level": "enhanced",
            "documents": [
                {
                    "document_type": "identity",
                    "document_id": "doc_001",
                    "verification_method": "automated"
                },
                {
                    "document_type": "address",
                    "document_id": "doc_002", 
                    "verification_method": "automated"
                }
            ],
            "risk_assessment": True,
            "sanctions_screening": True
        }
        
        with patch('riskintel360.api.fintech_endpoints.get_kyc_verification_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.verify_customer = AsyncMock(return_value={
                "verification_id": "kyc_001",
                "verification_status": "approved",
                "risk_score": 0.25,
                "document_verification": {
                    "identity": "verified",
                    "address": "verified"
                },
                "sanctions_check": "clear",
                "confidence_score": 0.95
            })
            mock_get_agent.return_value = mock_agent
            
            response = test_client.post("/api/v1/kyc-verification", json=valid_request)
            
            # Verify response structure
            assert response.status_code == 200
            response_data = response.json()
            
            assert "verification_id" in response_data
            assert "verification_status" in response_data
            assert "risk_score" in response_data
            assert "document_verification" in response_data
            assert "confidence_score" in response_data


class TestFinTechAPIWorkflowIntegration:
    """Integration tests for complete fintech API workflows"""
    
    @pytest.fixture
    async def async_client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_comprehensive_risk_analysis_workflow(self, async_client):
        """Test complete risk analysis workflow integration"""
        # Mock all required services
        with patch('riskintel360.api.fintech_endpoints.get_workflow_orchestrator') as mock_get_orchestrator, \
             patch('riskintel360.api.fintech_endpoints.get_agent_factory') as mock_get_factory:
            
            # Setup mocks
            mock_orchestrator = Mock()
            mock_orchestrator.start_fintech_workflow = AsyncMock(return_value="workflow_001")
            mock_orchestrator.get_workflow_status = Mock(return_value={
                "workflow_id": "workflow_001",
                "status": "in_progress",
                "progress": 0.75,
                "current_phase": "result_synthesis",
                "estimated_completion": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
            })
            mock_get_orchestrator.return_value = mock_orchestrator
            
            mock_factory = Mock()
            mock_get_factory.return_value = mock_factory
            
            # Step 1: Initiate risk analysis
            risk_request = {
                "entity_id": "fintech_startup_123",
                "entity_type": "payment_processor",
                "analysis_scope": ["regulatory", "fraud", "market", "credit"],
                "urgency": "high",
                "business_context": {
                    "industry": "payments",
                    "stage": "series_a",
                    "geography": "US"
                }
            }
            
            response = await async_client.post("/api/v1/risk-analysis", json=risk_request)
            assert response.status_code == 200
            
            workflow_data = response.json()
            workflow_id = workflow_data["workflow_id"]
            
            # Step 2: Check workflow status
            status_response = await async_client.get(f"/api/v1/workflow/{workflow_id}/status")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            assert status_data["workflow_id"] == workflow_id
            assert status_data["status"] == "in_progress"
            assert status_data["progress"] == 0.75
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fraud_detection_real_time_workflow(self, async_client):
        """Test real-time fraud detection workflow"""
        with patch('riskintel360.api.fintech_endpoints.get_fraud_detection_agent') as mock_get_agent:
            # Setup fraud detection agent mock
            mock_agent = Mock()
            mock_agent.detect_fraud = AsyncMock(return_value={
                "analysis_id": "fraud_001",
                "fraud_alerts": [
                    {
                        "transaction_id": "txn_002",
                        "fraud_probability": 0.92,
                        "anomaly_score": 0.88,
                        "risk_factors": ["amount_anomaly", "velocity_check"],
                        "recommended_action": "block",
                        "confidence": 0.94
                    }
                ],
                "overall_risk_score": 0.46,
                "processing_time": 1.8,
                "ml_model_version": "v2.1"
            })
            mock_get_agent.return_value = mock_agent
            
            # Test real-time fraud detection
            fraud_request = {
                "transaction_batch_id": "batch_001",
                "transactions": [
                    {
                        "transaction_id": "txn_001",
                        "amount": 100.00,
                        "currency": "USD",
                        "merchant": "grocery_store",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    {
                        "transaction_id": "txn_002",
                        "amount": 50000.00,
                        "currency": "USD", 
                        "merchant": "luxury_goods",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                ],
                "analysis_type": "real_time",
                "ml_models": ["isolation_forest", "autoencoder"]
            }
            
            # Measure response time
            start_time = datetime.now(timezone.utc)
            response = await async_client.post("/api/v1/fraud-detection", json=fraud_request)
            end_time = datetime.now(timezone.utc)
            
            response_time = (end_time - start_time).total_seconds()
            
            # Verify response
            assert response.status_code == 200
            fraud_data = response.json()
            
            # Verify performance requirement (< 5 seconds)
            assert response_time < 5.0, f"Fraud detection took {response_time:.2f}s, should be < 5s"
            
            # Verify fraud detection results
            assert fraud_data["processing_time"] < 5.0
            assert len(fraud_data["fraud_alerts"]) > 0
            assert fraud_data["fraud_alerts"][0]["fraud_probability"] > 0.9
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compliance_monitoring_workflow(self, async_client):
        """Test compliance monitoring workflow"""
        with patch('riskintel360.api.fintech_endpoints.get_regulatory_compliance_agent') as mock_get_agent:
            # Setup compliance agent mock
            mock_agent = Mock()
            mock_agent.analyze_compliance = AsyncMock(return_value={
                "analysis_id": "compliance_001",
                "compliance_status": "non_compliant",
                "risk_level": "high",
                "violations": [
                    {
                        "regulation": "CFPB_1033",
                        "violation_type": "data_sharing_requirement",
                        "severity": "high",
                        "remediation_required": True
                    }
                ],
                "remediation_plan": {
                    "immediate_actions": ["implement_data_sharing_api"],
                    "timeline": "90_days",
                    "estimated_cost": 50000
                },
                "confidence_score": 0.88,
                "data_sources_used": ["SEC", "CFPB", "FINRA"]
            })
            mock_get_agent.return_value = mock_agent
            
            # Test compliance check
            compliance_request = {
                "entity_id": "fintech_startup_123",
                "business_type": "digital_wallet",
                "jurisdiction": "US",
                "regulations": ["SEC", "FINRA", "CFPB", "BSA"],
                "compliance_scope": "comprehensive"
            }
            
            response = await async_client.post("/api/v1/compliance-check", json=compliance_request)
            assert response.status_code == 200
            
            compliance_data = response.json()
            
            # Verify compliance analysis
            assert compliance_data["compliance_status"] == "non_compliant"
            assert compliance_data["risk_level"] == "high"
            assert len(compliance_data["violations"]) > 0
            assert "remediation_plan" in compliance_data
            assert compliance_data["confidence_score"] >= 0.8
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_market_intelligence_workflow(self, async_client):
        """Test market intelligence workflow"""
        with patch('riskintel360.api.fintech_endpoints.get_market_analysis_agent') as mock_get_agent:
            # Setup market analysis agent mock
            mock_agent = Mock()
            mock_agent.analyze_market_intelligence = AsyncMock(return_value={
                "analysis_id": "market_001",
                "trend_direction": "bullish",
                "volatility_level": 0.35,
                "key_drivers": [
                    "regulatory_clarity_improvement",
                    "digital_payment_adoption",
                    "fintech_investment_growth"
                ],
                "risk_factors": [
                    "market_saturation_risk",
                    "regulatory_uncertainty",
                    "cybersecurity_threats"
                ],
                "opportunities": [
                    "cross_border_payments",
                    "embedded_finance",
                    "defi_integration"
                ],
                "market_conditions": {
                    "fintech_index_performance": 0.15,
                    "sector_volatility": 0.35,
                    "investment_flow": "positive"
                },
                "confidence_score": 0.82,
                "data_sources_used": ["FRED", "yahoo_finance", "news_sentiment"]
            })
            mock_get_agent.return_value = mock_agent
            
            # Test market intelligence
            market_request = {
                "analysis_type": "fintech_sector_analysis",
                "market_segment": "digital_payments",
                "time_horizon": "1Y",
                "data_sources": ["FRED", "yahoo_finance", "news_sentiment"],
                "focus_areas": ["trends", "volatility", "opportunities", "risks"]
            }
            
            response = await async_client.post("/api/v1/market-intelligence", json=market_request)
            assert response.status_code == 200
            
            market_data = response.json()
            
            # Verify market intelligence
            assert market_data["trend_direction"] == "bullish"
            assert 0.0 <= market_data["volatility_level"] <= 1.0
            assert len(market_data["key_drivers"]) > 0
            assert len(market_data["opportunities"]) > 0
            assert market_data["confidence_score"] >= 0.8


class TestFinTechAPIErrorHandling:
    """Integration tests for API error handling and validation"""
    
    @pytest.fixture
    def test_client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.mark.integration
    def test_invalid_request_validation(self, test_client):
        """Test API request validation and error handling"""
        # Test invalid risk analysis request
        invalid_request = {
            "entity_id": "",  # Empty entity ID
            "entity_type": "invalid_type",  # Invalid entity type
            "analysis_scope": [],  # Empty analysis scope
            "urgency": "invalid_urgency"  # Invalid urgency
        }
        
        response = test_client.post("/api/v1/risk-analysis", json=invalid_request)
        
        # Should return validation error
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)
    
    @pytest.mark.integration
    def test_missing_required_fields(self, test_client):
        """Test handling of missing required fields"""
        # Test compliance check with missing fields
        incomplete_request = {
            "entity_id": "test_entity"
            # Missing required fields: business_type, jurisdiction, regulations
        }
        
        response = test_client.post("/api/v1/compliance-check", json=incomplete_request)
        
        # Should return validation error
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
    
    @pytest.mark.integration
    def test_service_unavailable_handling(self, test_client):
        """Test handling of service unavailability"""
        with patch('riskintel360.api.fintech_endpoints.get_fraud_detection_agent') as mock_get_agent:
            # Mock service unavailable
            mock_get_agent.side_effect = Exception("Service temporarily unavailable")
            
            fraud_request = {
                "transaction_batch_id": "batch_001",
                "transactions": [
                    {
                        "transaction_id": "txn_001",
                        "amount": 100.00,
                        "currency": "USD",
                        "merchant": "test_merchant",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                ],
                "analysis_type": "real_time"
            }
            
            response = test_client.post("/api/v1/fraud-detection", json=fraud_request)
            
            # Should return service error
            assert response.status_code == 503
            error_data = response.json()
            assert "error" in error_data
            assert "service" in error_data["error"].lower()


class TestFinTechAPIPerformance:
    """Integration tests for API performance requirements"""
    
    @pytest.fixture
    async def async_client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, async_client):
        """Test concurrent API request handling (50+ requests requirement)"""
        with patch('riskintel360.api.fintech_endpoints.get_fraud_detection_agent') as mock_get_agent:
            # Setup fast-responding mock
            mock_agent = Mock()
            mock_agent.detect_fraud = AsyncMock(return_value={
                "analysis_id": "fraud_concurrent",
                "fraud_alerts": [],
                "overall_risk_score": 0.1,
                "processing_time": 0.5
            })
            mock_get_agent.return_value = mock_agent
            
            # Create concurrent requests
            async def make_fraud_request(request_id: int):
                fraud_request = {
                    "transaction_batch_id": f"batch_{request_id}",
                    "transactions": [
                        {
                            "transaction_id": f"txn_{request_id}",
                            "amount": 100.00,
                            "currency": "USD",
                            "merchant": "test_merchant",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    ],
                    "analysis_type": "real_time"
                }
                
                return await async_client.post("/api/v1/fraud-detection", json=fraud_request)
            
            # Execute 25 concurrent requests (scaled for testing)
            start_time = datetime.now(timezone.utc)
            tasks = [make_fraud_request(i) for i in range(25)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = datetime.now(timezone.utc)
            
            total_time = (end_time - start_time).total_seconds()
            
            # Verify performance
            successful_responses = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 200]
            assert len(successful_responses) == 25, "All concurrent requests should succeed"
            assert total_time < 10.0, f"25 concurrent requests took {total_time:.2f}s, should be < 10s"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_api_response_time_requirements(self, async_client):
        """Test API response time requirements (< 5 seconds)"""
        with patch('riskintel360.api.fintech_endpoints.get_market_analysis_agent') as mock_get_agent:
            # Setup mock with realistic processing time
            mock_agent = Mock()
            mock_agent.analyze_market_intelligence = AsyncMock(return_value={
                "analysis_id": "market_perf_test",
                "trend_direction": "neutral",
                "volatility_level": 0.5,
                "key_drivers": ["test_driver"],
                "confidence_score": 0.8
            })
            mock_get_agent.return_value = mock_agent
            
            # Test different endpoint response times
            endpoints_tests = [
                {
                    "endpoint": "/api/v1/market-intelligence",
                    "request": {
                        "analysis_type": "fintech_sector_analysis",
                        "market_segment": "digital_payments",
                        "time_horizon": "1Y"
                    },
                    "max_time": 5.0
                }
            ]
            
            for test in endpoints_tests:
                start_time = datetime.now(timezone.utc)
                response = await async_client.post(test["endpoint"], json=test["request"])
                end_time = datetime.now(timezone.utc)
                
                response_time = (end_time - start_time).total_seconds()
                
                # Verify response time requirement
                assert response.status_code == 200
                assert response_time < test["max_time"], \
                    f"{test['endpoint']} response time {response_time:.2f}s exceeds {test['max_time']}s limit"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
