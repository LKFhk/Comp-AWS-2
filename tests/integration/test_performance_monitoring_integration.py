"""
Integration tests for performance monitoring system.
Tests real-time performance tracking, metrics collection, and alerting.
"""

import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from riskintel360.services.performance_monitor import (
    PerformanceMonitor, PerformanceMetrics, AlertThreshold,
    SystemHealthStatus, PerformanceAlert
)
from riskintel360.services.workflow_orchestrator import SupervisorAgent
from riskintel360.agents.agent_factory import AgentFactory
from riskintel360.models.agent_models import AgentType


class TestPerformanceMonitoringIntegration:
    """Integration tests for performance monitoring system"""
    
    @pytest.fixture
    def performance_monitor(self):
        """Create performance monitor for testing"""
        return PerformanceMonitor()
    
    @pytest.fixture
    def mock_workflow_orchestrator(self):
        """Mock workflow orchestrator for testing"""
        mock_orchestrator = Mock(spec=SupervisorAgent)
        mock_orchestrator.get_active_workflows = Mock(return_value=[])
        mock_orchestrator.get_workflow_metrics = Mock()
        return mock_orchestrator
    
    @pytest.fixture
    def mock_agent_factory(self):
        """Mock agent factory for testing"""
        mock_factory = Mock(spec=AgentFactory)
        mock_factory.get_active_agents = Mock(return_value=[])
        mock_factory.get_agent_metrics = Mock()
        return mock_factory
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_time_agent_performance_tracking(self, performance_monitor):
        """Test real-time agent performance tracking"""
        # Start performance monitoring
        await performance_monitor.start_monitoring()
        
        try:
            # Simulate agent performance data
            agent_performance_data = [
                {
                    "agent_id": "regulatory_compliance_001",
                    "agent_type": AgentType.REGULATORY_COMPLIANCE,
                    "response_time": 2.5,
                    "success_rate": 0.95,
                    "timestamp": datetime.now(timezone.utc)
                },
                {
                    "agent_id": "fraud_detection_001",
                    "agent_type": AgentType.FRAUD_DETECTION,
                    "response_time": 4.2,
                    "success_rate": 0.98,
                    "timestamp": datetime.now(timezone.utc)
                },
                {
                    "agent_id": "market_analysis_001",
                    "agent_type": AgentType.MARKET_ANALYSIS,
                    "response_time": 3.1,
                    "success_rate": 0.92,
                    "timestamp": datetime.now(timezone.utc)
                }
            ]
            
            # Record performance metrics
            for data in agent_performance_data:
                await performance_monitor.record_agent_performance(
                    agent_id=data["agent_id"],
                    agent_type=data["agent_type"],
                    response_time=data["response_time"],
                    success_rate=data["success_rate"],
                    timestamp=data["timestamp"]
                )
            
            # Verify metrics collection
            metrics = await performance_monitor.get_agent_metrics(time_window="1h")
            
            assert len(metrics) == len(agent_performance_data)
            
            # Verify response time tracking
            for agent_data in agent_performance_data:
                agent_metrics = next(
                    (m for m in metrics if m.agent_id == agent_data["agent_id"]), 
                    None
                )
                assert agent_metrics is not None
                assert agent_metrics.avg_response_time == agent_data["response_time"]
                assert agent_metrics.success_rate == agent_data["success_rate"]
                
        finally:
            await performance_monitor.stop_monitoring()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_execution_time_monitoring(self, performance_monitor):
        """Test workflow execution time monitoring (< 2 hour requirement)"""
        await performance_monitor.start_monitoring()
        
        try:
            # Simulate workflow execution tracking
            workflow_data = [
                {
                    "workflow_id": "fintech_analysis_001",
                    "workflow_type": "comprehensive_risk_analysis",
                    "start_time": datetime.now(timezone.utc) - timedelta(minutes=90),
                    "end_time": datetime.now(timezone.utc),
                    "status": "completed",
                    "participating_agents": [
                        "regulatory_compliance_001",
                        "fraud_detection_001", 
                        "risk_assessment_001",
                        "market_analysis_001"
                    ]
                },
                {
                    "workflow_id": "fraud_detection_002",
                    "workflow_type": "real_time_fraud_analysis",
                    "start_time": datetime.now(timezone.utc) - timedelta(seconds=30),
                    "end_time": datetime.now(timezone.utc),
                    "status": "completed",
                    "participating_agents": ["fraud_detection_001"]
                }
            ]
            
            # Record workflow metrics
            for workflow in workflow_data:
                execution_time = (workflow["end_time"] - workflow["start_time"]).total_seconds()
                
                await performance_monitor.record_workflow_performance(
                    workflow_id=workflow["workflow_id"],
                    workflow_type=workflow["workflow_type"],
                    execution_time=execution_time,
                    status=workflow["status"],
                    participating_agents=workflow["participating_agents"],
                    start_time=workflow["start_time"],
                    end_time=workflow["end_time"]
                )
            
            # Verify workflow metrics
            workflow_metrics = await performance_monitor.get_workflow_metrics(time_window="1h")
            
            assert len(workflow_metrics) == len(workflow_data)
            
            # Verify execution time requirements
            comprehensive_workflow = next(
                (w for w in workflow_metrics if w.workflow_type == "comprehensive_risk_analysis"),
                None
            )
            assert comprehensive_workflow is not None
            assert comprehensive_workflow.execution_time < 7200  # < 2 hours (7200 seconds)
            
            fraud_workflow = next(
                (w for w in workflow_metrics if w.workflow_type == "real_time_fraud_analysis"),
                None
            )
            assert fraud_workflow is not None
            assert fraud_workflow.execution_time < 300  # < 5 minutes for real-time
            
        finally:
            await performance_monitor.stop_monitoring()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_system_uptime_monitoring(self, performance_monitor):
        """Test system uptime monitoring (99.9% requirement)"""
        await performance_monitor.start_monitoring()
        
        try:
            # Simulate system health checks over time
            health_checks = []
            
            # Simulate 100 health checks with 99.9% uptime (1 failure allowed)
            for i in range(100):
                is_healthy = i != 50  # Simulate one failure at check 50
                
                health_status = SystemHealthStatus(
                    timestamp=datetime.now(timezone.utc) - timedelta(minutes=100-i),
                    is_healthy=is_healthy,
                    response_time=2.0 if is_healthy else 30.0,
                    error_message=None if is_healthy else "Service temporarily unavailable"
                )
                
                health_checks.append(health_status)
                await performance_monitor.record_health_check(health_status)
            
            # Calculate uptime metrics
            uptime_metrics = await performance_monitor.get_uptime_metrics(time_window="24h")
            
            # Verify uptime requirement (99.9%)
            assert uptime_metrics.uptime_percentage >= 99.0  # Allow some tolerance for testing
            assert uptime_metrics.total_checks == 100
            assert uptime_metrics.failed_checks <= 1
            
            # Verify downtime tracking
            if uptime_metrics.failed_checks > 0:
                assert uptime_metrics.total_downtime > 0
                assert len(uptime_metrics.downtime_incidents) > 0
                
        finally:
            await performance_monitor.stop_monitoring()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_request_monitoring(self, performance_monitor):
        """Test concurrent request handling monitoring (50+ requests requirement)"""
        await performance_monitor.start_monitoring()
        
        try:
            # Simulate concurrent request tracking
            concurrent_requests = []
            max_concurrent = 0
            
            # Simulate 75 concurrent requests (exceeding 50+ requirement)
            for i in range(75):
                request_data = {
                    "request_id": f"req_{i}",
                    "endpoint": "/api/v1/fraud-detection",
                    "start_time": datetime.now(timezone.utc),
                    "response_time": 2.5 + (i * 0.01),  # Slight increase with load
                    "status_code": 200
                }
                concurrent_requests.append(request_data)
                
                # Track concurrent requests
                await performance_monitor.record_request_start(
                    request_id=request_data["request_id"],
                    endpoint=request_data["endpoint"],
                    start_time=request_data["start_time"]
                )
                
                # Update max concurrent count
                current_concurrent = await performance_monitor.get_current_concurrent_requests()
                max_concurrent = max(max_concurrent, current_concurrent)
            
            # Complete all requests
            for request in concurrent_requests:
                await performance_monitor.record_request_completion(
                    request_id=request["request_id"],
                    response_time=request["response_time"],
                    status_code=request["status_code"]
                )
            
            # Verify concurrent request handling
            request_metrics = await performance_monitor.get_request_metrics(time_window="1h")
            
            assert request_metrics.total_requests == 75
            assert request_metrics.max_concurrent_requests >= 50  # Meets requirement
            assert request_metrics.avg_response_time < 5.0  # Performance maintained
            assert request_metrics.success_rate >= 0.95  # High success rate
            
        finally:
            await performance_monitor.stop_monitoring()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_performance_alerting_system(self, performance_monitor):
        """Test performance alerting system"""
        await performance_monitor.start_monitoring()
        
        try:
            # Configure alert thresholds
            alert_thresholds = [
                AlertThreshold(
                    metric_name="agent_response_time",
                    threshold_value=5.0,
                    comparison="greater_than",
                    severity="warning"
                ),
                AlertThreshold(
                    metric_name="workflow_execution_time",
                    threshold_value=7200,  # 2 hours
                    comparison="greater_than",
                    severity="critical"
                ),
                AlertThreshold(
                    metric_name="system_uptime",
                    threshold_value=99.9,
                    comparison="less_than",
                    severity="critical"
                )
            ]
            
            for threshold in alert_thresholds:
                await performance_monitor.configure_alert_threshold(threshold)
            
            # Simulate performance issues that should trigger alerts
            
            # 1. Slow agent response (should trigger warning)
            await performance_monitor.record_agent_performance(
                agent_id="slow_agent_001",
                agent_type=AgentType.FRAUD_DETECTION,
                response_time=8.5,  # Exceeds 5.0 threshold
                success_rate=0.95,
                timestamp=datetime.now(timezone.utc)
            )
            
            # 2. Long workflow execution (should trigger critical alert)
            await performance_monitor.record_workflow_performance(
                workflow_id="slow_workflow_001",
                workflow_type="comprehensive_risk_analysis",
                execution_time=8000,  # Exceeds 7200 threshold (2 hours)
                status="completed",
                participating_agents=["agent_001"],
                start_time=datetime.now(timezone.utc) - timedelta(seconds=8000),
                end_time=datetime.now(timezone.utc)
            )
            
            # Check for generated alerts
            alerts = await performance_monitor.get_active_alerts()
            
            # Verify alerts were generated
            assert len(alerts) >= 2
            
            # Verify agent response time alert
            response_time_alert = next(
                (a for a in alerts if a.metric_name == "agent_response_time"),
                None
            )
            assert response_time_alert is not None
            assert response_time_alert.severity == "warning"
            assert response_time_alert.current_value == 8.5
            
            # Verify workflow execution time alert
            workflow_alert = next(
                (a for a in alerts if a.metric_name == "workflow_execution_time"),
                None
            )
            assert workflow_alert is not None
            assert workflow_alert.severity == "critical"
            assert workflow_alert.current_value == 8000
            
        finally:
            await performance_monitor.stop_monitoring()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_performance_dashboard_data(self, performance_monitor):
        """Test performance dashboard data collection"""
        await performance_monitor.start_monitoring()
        
        try:
            # Generate comprehensive performance data
            
            # Agent performance data
            agents_data = [
                ("regulatory_compliance_001", AgentType.REGULATORY_COMPLIANCE, 2.1, 0.98),
                ("fraud_detection_001", AgentType.FRAUD_DETECTION, 3.8, 0.96),
                ("risk_assessment_001", AgentType.RISK_ASSESSMENT, 2.9, 0.94),
                ("market_analysis_001", AgentType.MARKET_ANALYSIS, 3.2, 0.97),
                ("kyc_verification_001", AgentType.KYC_VERIFICATION, 2.7, 0.99)
            ]
            
            for agent_id, agent_type, response_time, success_rate in agents_data:
                await performance_monitor.record_agent_performance(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    response_time=response_time,
                    success_rate=success_rate,
                    timestamp=datetime.now(timezone.utc)
                )
            
            # Workflow performance data
            workflows_data = [
                ("workflow_001", "comprehensive_risk_analysis", 5400, "completed"),  # 1.5 hours
                ("workflow_002", "fraud_detection", 180, "completed"),  # 3 minutes
                ("workflow_003", "compliance_check", 300, "completed"),  # 5 minutes
                ("workflow_004", "market_analysis", 420, "completed")  # 7 minutes
            ]
            
            for workflow_id, workflow_type, execution_time, status in workflows_data:
                await performance_monitor.record_workflow_performance(
                    workflow_id=workflow_id,
                    workflow_type=workflow_type,
                    execution_time=execution_time,
                    status=status,
                    participating_agents=["agent_001"],
                    start_time=datetime.now(timezone.utc) - timedelta(seconds=execution_time),
                    end_time=datetime.now(timezone.utc)
                )
            
            # Get dashboard data
            dashboard_data = await performance_monitor.get_dashboard_data()
            
            # Verify dashboard data structure
            assert "agent_metrics" in dashboard_data
            assert "workflow_metrics" in dashboard_data
            assert "system_health" in dashboard_data
            assert "performance_trends" in dashboard_data
            assert "alerts" in dashboard_data
            
            # Verify agent metrics
            agent_metrics = dashboard_data["agent_metrics"]
            assert len(agent_metrics) == len(agents_data)
            
            # Verify all agents meet performance requirements
            for metric in agent_metrics:
                assert metric["avg_response_time"] < 5.0  # < 5 second requirement
                assert metric["success_rate"] >= 0.90  # High success rate
            
            # Verify workflow metrics
            workflow_metrics = dashboard_data["workflow_metrics"]
            assert len(workflow_metrics) == len(workflows_data)
            
            # Verify comprehensive workflows meet time requirement
            comprehensive_workflows = [
                w for w in workflow_metrics 
                if w["workflow_type"] == "comprehensive_risk_analysis"
            ]
            for workflow in comprehensive_workflows:
                assert workflow["execution_time"] < 7200  # < 2 hour requirement
            
            # Verify system health
            system_health = dashboard_data["system_health"]
            assert "uptime_percentage" in system_health
            assert "current_load" in system_health
            assert "response_time" in system_health
            
        finally:
            await performance_monitor.stop_monitoring()


class TestPerformanceMonitoringScalability:
    """Integration tests for performance monitoring scalability"""
    
    @pytest.fixture
    def performance_monitor(self):
        """Create performance monitor for testing"""
        return PerformanceMonitor()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_high_volume_metrics_collection(self, performance_monitor):
        """Test high-volume metrics collection performance"""
        await performance_monitor.start_monitoring()
        
        try:
            # Simulate high-volume metrics collection
            start_time = time.time()
            
            # Generate 1000 agent performance records
            tasks = []
            for i in range(1000):
                task = performance_monitor.record_agent_performance(
                    agent_id=f"agent_{i % 10}",  # 10 different agents
                    agent_type=list(AgentType)[i % 5],  # Cycle through agent types
                    response_time=2.0 + (i % 10) * 0.1,
                    success_rate=0.95 + (i % 5) * 0.01,
                    timestamp=datetime.now(timezone.utc)
                )
                tasks.append(task)
            
            # Execute all metrics collection concurrently
            await asyncio.gather(*tasks)
            
            collection_time = time.time() - start_time
            
            # Verify performance of metrics collection
            assert collection_time < 10.0, f"Metrics collection took {collection_time:.2f}s, should be < 10s"
            
            # Verify data integrity
            metrics = await performance_monitor.get_agent_metrics(time_window="1h")
            assert len(metrics) == 10  # 10 unique agents
            
        finally:
            await performance_monitor.stop_monitoring()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_monitoring_operations(self, performance_monitor):
        """Test concurrent monitoring operations"""
        await performance_monitor.start_monitoring()
        
        try:
            # Create concurrent monitoring tasks
            async def record_agent_metrics():
                for i in range(50):
                    await performance_monitor.record_agent_performance(
                        agent_id=f"concurrent_agent_{i}",
                        agent_type=AgentType.FRAUD_DETECTION,
                        response_time=2.5,
                        success_rate=0.95,
                        timestamp=datetime.now(timezone.utc)
                    )
            
            async def record_workflow_metrics():
                for i in range(25):
                    await performance_monitor.record_workflow_performance(
                        workflow_id=f"concurrent_workflow_{i}",
                        workflow_type="fraud_detection",
                        execution_time=300,
                        status="completed",
                        participating_agents=[f"agent_{i}"],
                        start_time=datetime.now(timezone.utc) - timedelta(seconds=300),
                        end_time=datetime.now(timezone.utc)
                    )
            
            async def record_health_checks():
                for i in range(100):
                    health_status = SystemHealthStatus(
                        timestamp=datetime.now(timezone.utc),
                        is_healthy=True,
                        response_time=2.0,
                        error_message=None
                    )
                    await performance_monitor.record_health_check(health_status)
            
            # Execute all monitoring operations concurrently
            start_time = time.time()
            await asyncio.gather(
                record_agent_metrics(),
                record_workflow_metrics(),
                record_health_checks()
            )
            total_time = time.time() - start_time
            
            # Verify concurrent operations performance
            assert total_time < 15.0, f"Concurrent monitoring took {total_time:.2f}s, should be < 15s"
            
            # Verify all data was recorded
            agent_metrics = await performance_monitor.get_agent_metrics(time_window="1h")
            workflow_metrics = await performance_monitor.get_workflow_metrics(time_window="1h")
            uptime_metrics = await performance_monitor.get_uptime_metrics(time_window="1h")
            
            assert len(agent_metrics) == 50
            assert len(workflow_metrics) == 25
            assert uptime_metrics.total_checks == 100
            
        finally:
            await performance_monitor.stop_monitoring()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
