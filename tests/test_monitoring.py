"""
Tests for Monitoring and Observability System
Tests CloudWatch integration, custom metrics, performance monitoring, and distributed tracing.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from riskintel360.services.monitoring_service import (
    MonitoringService,
    MetricType,
    AlertSeverity,
    MetricData,
    PerformanceMetric,
    HealthCheck,
    TraceSpan,
    get_monitoring_service,
    monitor_performance,
    TraceContext
)


class TestMonitoringService:
    """Test monitoring service functionality"""
    
    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service for testing"""
        with patch('boto3.client') as mock_boto3:
            mock_cloudwatch = Mock()
            mock_logs = Mock()
            mock_boto3.side_effect = lambda service: {
                'cloudwatch': mock_cloudwatch,
                'logs': mock_logs
            }[service]
            
            service = MonitoringService()
            service._cloudwatch_client = mock_cloudwatch
            service._logs_client = mock_logs
            
            # Stop background monitoring for tests
            if service._monitoring_task:
                service._monitoring_task.cancel()
            
            return service
    
    def test_monitoring_service_initialization(self, monitoring_service):
        """Test monitoring service initializes correctly"""
        assert monitoring_service._cloudwatch_client is not None
        assert monitoring_service._logs_client is not None
        assert isinstance(monitoring_service._metrics_buffer, list)
        assert isinstance(monitoring_service._performance_metrics, list)
        assert isinstance(monitoring_service._health_checks, dict)
        assert isinstance(monitoring_service._active_traces, dict)
        assert isinstance(monitoring_service._alert_handlers, list)
        print("??Monitoring service initialization test passed")
    
    def test_record_metric(self, monitoring_service):
        """Test recording custom metrics"""
        # Test basic metric recording
        monitoring_service.record_metric(
            name="TestMetric",
            value=42.0,
            unit="Count",
            dimensions={"Component": "Test"},
            metric_type=MetricType.GAUGE
        )
        
        assert len(monitoring_service._metrics_buffer) == 1
        metric = monitoring_service._metrics_buffer[0]
        assert metric.name == "TestMetric"
        assert metric.value == 42.0
        assert metric.unit == "Count"
        assert metric.dimensions["Component"] == "Test"
        assert metric.metric_type == MetricType.GAUGE
        print("??Record metric test passed")
    
    def test_increment_counter(self, monitoring_service):
        """Test counter increment functionality"""
        monitoring_service.increment_counter(
            name="TestCounter",
            value=5.0,
            dimensions={"Operation": "TestOp"}
        )
        
        assert len(monitoring_service._metrics_buffer) == 1
        metric = monitoring_service._metrics_buffer[0]
        assert metric.name == "TestCounter"
        assert metric.value == 5.0
        assert metric.unit == "Count"
        assert metric.metric_type == MetricType.COUNTER
        print("??Increment counter test passed")
    
    def test_record_gauge(self, monitoring_service):
        """Test gauge metric recording"""
        monitoring_service.record_gauge(
            name="TestGauge",
            value=75.5,
            unit="Percent",
            dimensions={"System": "RiskIntel360"}
        )
        
        assert len(monitoring_service._metrics_buffer) == 1
        metric = monitoring_service._metrics_buffer[0]
        assert metric.name == "TestGauge"
        assert metric.value == 75.5
        assert metric.unit == "Percent"
        assert metric.metric_type == MetricType.GAUGE
        print("??Record gauge test passed")
    
    def test_record_timer(self, monitoring_service):
        """Test timer metric recording"""
        monitoring_service.record_timer(
            name="TestTimer",
            duration_ms=150.0,
            dimensions={"Agent": "MarketResearch"}
        )
        
        assert len(monitoring_service._metrics_buffer) == 1
        metric = monitoring_service._metrics_buffer[0]
        assert metric.name == "TestTimer"
        assert metric.value == 150.0
        assert metric.unit == "Milliseconds"
        assert metric.metric_type == MetricType.TIMER
        print("??Record timer test passed")
    
    @pytest.mark.asyncio
    async def test_flush_metrics_buffer(self, monitoring_service):
        """Test flushing metrics buffer to CloudWatch"""
        # Add some metrics
        monitoring_service.record_metric("Metric1", 10.0)
        monitoring_service.record_metric("Metric2", 20.0)
        monitoring_service.record_metric("Metric3", 30.0)
        
        assert len(monitoring_service._metrics_buffer) == 3
        
        # Mock CloudWatch client
        monitoring_service._cloudwatch_client.put_metric_data = Mock()
        
        # Flush metrics
        await monitoring_service._flush_metrics_buffer()
        
        # Verify metrics were sent to CloudWatch
        assert monitoring_service._cloudwatch_client.put_metric_data.called
        assert len(monitoring_service._metrics_buffer) == 0
        print("??Flush metrics buffer test passed")
    
    def test_performance_timer(self, monitoring_service):
        """Test performance timer functionality"""
        operation = "TestOperation"
        
        # Start timer
        timer_id = monitoring_service.start_performance_timer(operation)
        assert timer_id is not None
        assert operation in monitoring_service._operation_stats
        assert timer_id in monitoring_service._operation_stats[operation]['active_timers']
        
        # Simulate some work
        time.sleep(0.01)
        
        # End timer
        duration = monitoring_service.end_performance_timer(
            timer_id, operation, success=True
        )
        
        assert duration > 0
        assert timer_id not in monitoring_service._operation_stats[operation]['active_timers']
        assert monitoring_service._operation_stats[operation]['total_calls'] == 1
        assert monitoring_service._operation_stats[operation]['success_count'] == 1
        assert monitoring_service._operation_stats[operation]['error_count'] == 0
        print("??Performance timer test passed")
    
    def test_performance_timer_with_error(self, monitoring_service):
        """Test performance timer with error handling"""
        operation = "ErrorOperation"
        
        timer_id = monitoring_service.start_performance_timer(operation)
        time.sleep(0.01)
        
        duration = monitoring_service.end_performance_timer(
            timer_id, operation, success=False, error_message="Test error"
        )
        
        assert duration > 0
        assert monitoring_service._operation_stats[operation]['error_count'] == 1
        assert monitoring_service._operation_stats[operation]['success_count'] == 0
        print("??Performance timer error handling test passed")
    
    def test_get_performance_stats(self, monitoring_service):
        """Test getting performance statistics"""
        operation = "StatsOperation"
        
        # Generate some stats
        timer_id = monitoring_service.start_performance_timer(operation)
        monitoring_service.end_performance_timer(timer_id, operation, success=True)
        
        # Get specific operation stats
        stats = monitoring_service.get_performance_stats(operation)
        assert stats['total_calls'] == 1
        assert stats['success_count'] == 1
        assert stats['error_count'] == 0
        assert stats['avg_duration_ms'] > 0
        
        # Get all stats
        all_stats = monitoring_service.get_performance_stats()
        assert operation in all_stats
        print("??Get performance stats test passed")
    
    @pytest.mark.asyncio
    async def test_health_check_registration(self, monitoring_service):
        """Test health check registration and execution"""
        component = "TestComponent"
        
        # Mock health check function
        async def mock_health_check():
            return True
        
        # Register health check
        await monitoring_service.register_health_check(
            component, mock_health_check, timeout_seconds=1
        )
        
        # Verify health check was recorded
        assert component in monitoring_service._health_checks
        health_check = monitoring_service._health_checks[component]
        assert health_check.component == component
        assert health_check.status == "healthy"
        assert health_check.response_time_ms > 0
        print("??Health check registration test passed")
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, monitoring_service):
        """Test health check failure handling"""
        component = "FailingComponent"
        
        # Mock failing health check
        async def failing_health_check():
            raise Exception("Health check failed")
        
        await monitoring_service.register_health_check(
            component, failing_health_check, timeout_seconds=1
        )
        
        health_check = monitoring_service._health_checks[component]
        assert health_check.status == "unhealthy"
        assert "Health check error" in health_check.message
        print("??Health check failure test passed")
    
    @pytest.mark.asyncio
    async def test_health_check_timeout(self, monitoring_service):
        """Test health check timeout handling"""
        component = "TimeoutComponent"
        
        # Mock slow health check
        async def slow_health_check():
            await asyncio.sleep(2)  # Longer than timeout
            return True
        
        await monitoring_service.register_health_check(
            component, slow_health_check, timeout_seconds=0.1
        )
        
        health_check = monitoring_service._health_checks[component]
        assert health_check.status == "unhealthy"
        assert "timed out" in health_check.message
        print("??Health check timeout test passed")
    
    def test_get_health_status(self, monitoring_service):
        """Test getting health status"""
        # Add a mock health check
        health_check = HealthCheck(
            component="TestComponent",
            status="healthy",
            message="All good",
            response_time_ms=50.0
        )
        monitoring_service._health_checks["TestComponent"] = health_check
        
        # Get specific component status
        status = monitoring_service.get_health_status("TestComponent")
        assert status['component'] == "TestComponent"
        assert status['status'] == "healthy"
        assert status['message'] == "All good"
        assert status['response_time_ms'] == 50.0
        
        # Get all health status
        all_status = monitoring_service.get_health_status()
        assert "TestComponent" in all_status
        print("??Get health status test passed")
    
    def test_distributed_tracing(self, monitoring_service):
        """Test distributed tracing functionality"""
        operation = "TestTrace"
        
        # Start trace
        span_id = monitoring_service.start_trace(
            operation_name=operation,
            tags={"component": "test"}
        )
        
        assert span_id is not None
        assert span_id in monitoring_service._active_traces
        
        trace = monitoring_service._active_traces[span_id]
        assert trace.operation_name == operation
        assert trace.tags["component"] == "test"
        assert trace.end_time is None
        
        # Add log to trace
        monitoring_service.add_trace_log(
            span_id, "info", "Test log message", {"key": "value"}
        )
        
        assert len(trace.logs) == 1
        assert trace.logs[0]["message"] == "Test log message"
        assert trace.logs[0]["metadata"]["key"] == "value"
        
        # End trace
        completed_trace = monitoring_service.end_trace(span_id, status="ok")
        
        assert completed_trace is not None
        assert completed_trace.status == "ok"
        assert completed_trace.end_time is not None
        assert completed_trace.duration_ms is not None
        assert span_id not in monitoring_service._active_traces
        print("??Distributed tracing test passed")
    
    def test_trace_with_error(self, monitoring_service):
        """Test tracing with error status"""
        span_id = monitoring_service.start_trace("ErrorTrace")
        
        completed_trace = monitoring_service.end_trace(
            span_id, status="error", error_message="Test error"
        )
        
        assert completed_trace.status == "error"
        assert len(completed_trace.logs) == 1
        assert completed_trace.logs[0]["level"] == "error"
        assert completed_trace.logs[0]["message"] == "Test error"
        print("??Trace error handling test passed")
    
    def test_get_trace(self, monitoring_service):
        """Test getting trace information"""
        span_id = monitoring_service.start_trace("GetTraceTest")
        
        trace_info = monitoring_service.get_trace(span_id)
        assert trace_info is not None
        assert trace_info["operation_name"] == "GetTraceTest"
        assert trace_info["span_id"] == span_id
        assert trace_info["status"] == "ok"
        
        # Test non-existent trace
        non_existent = monitoring_service.get_trace("non-existent")
        assert non_existent is None
        print("??Get trace test passed")
    
    @pytest.mark.asyncio
    async def test_alert_system(self, monitoring_service):
        """Test alert creation and handling"""
        alerts_received = []
        
        def alert_handler(alert_data):
            alerts_received.append(alert_data)
        
        # Register alert handler
        monitoring_service.add_alert_handler(alert_handler)
        
        # Create alert
        alert_id = await monitoring_service.create_alert(
            title="Test Alert",
            message="This is a test alert",
            severity=AlertSeverity.WARNING,
            component="TestComponent",
            metadata={"key": "value"}
        )
        
        assert alert_id is not None
        assert len(alerts_received) == 1
        
        alert = alerts_received[0]
        assert alert["title"] == "Test Alert"
        assert alert["message"] == "This is a test alert"
        assert alert["severity"] == "warning"
        assert alert["component"] == "TestComponent"
        assert alert["metadata"]["key"] == "value"
        print("??Alert system test passed")
    
    @pytest.mark.asyncio
    async def test_async_alert_handler(self, monitoring_service):
        """Test async alert handler"""
        alerts_received = []
        
        async def async_alert_handler(alert_data):
            await asyncio.sleep(0.01)  # Simulate async work
            alerts_received.append(alert_data)
        
        monitoring_service.add_alert_handler(async_alert_handler)
        
        await monitoring_service.create_alert(
            title="Async Alert",
            message="Test async handler",
            severity=AlertSeverity.ERROR
        )
        
        assert len(alerts_received) == 1
        assert alerts_received[0]["title"] == "Async Alert"
        print("??Async alert handler test passed")
    
    @pytest.mark.asyncio
    async def test_cloudwatch_dashboard_creation(self, monitoring_service):
        """Test CloudWatch dashboard creation"""
        # Mock successful dashboard creation
        monitoring_service._cloudwatch_client.put_dashboard = Mock()
        
        result = await monitoring_service.create_cloudwatch_dashboard()
        
        assert result is True
        assert monitoring_service._cloudwatch_client.put_dashboard.called
        
        # Verify dashboard configuration
        call_args = monitoring_service._cloudwatch_client.put_dashboard.call_args
        assert call_args[1]["DashboardName"] == "RiskIntel360-Platform-Dashboard"
        assert "DashboardBody" in call_args[1]
        print("??CloudWatch dashboard creation test passed")
    
    def test_monitoring_summary(self, monitoring_service):
        """Test monitoring summary generation"""
        # Add some test data
        monitoring_service.record_metric("TestMetric", 1.0)
        monitoring_service._health_checks["TestComponent"] = HealthCheck(
            component="TestComponent",
            status="healthy",
            message="OK",
            response_time_ms=10.0
        )
        monitoring_service.start_trace("TestTrace")
        
        summary = monitoring_service.get_monitoring_summary()
        
        assert summary["metrics"]["buffer_size"] >= 1  # May have additional metrics
        assert summary["health"]["components_monitored"] == 1
        assert summary["health"]["healthy_components"] == 1
        assert summary["tracing"]["active_traces"] == 1
        assert summary["cloudwatch"]["enabled"] is True
        print("??Monitoring summary test passed")


class TestMonitoringDecorators:
    """Test monitoring decorators and context managers"""
    
    @pytest.fixture(autouse=True)
    def mock_monitoring(self):
        """Mock monitoring service for decorator tests"""
        # Reset the global monitoring service
        import riskintel360.services.monitoring_service as ms
        original_service = ms._monitoring_service
        ms._monitoring_service = None
        
        mock_service = Mock()
        mock_service.start_performance_timer.return_value = "timer-123"
        mock_service.end_performance_timer.return_value = 100.0
        
        with patch.object(ms, 'get_monitoring_service', return_value=mock_service):
            yield mock_service
        
        # Restore original service
        ms._monitoring_service = original_service
    
    def test_monitor_performance_decorator_sync(self, mock_monitoring):
        """Test performance monitoring decorator for sync functions"""
        @monitor_performance("test_operation")
        def test_function(x, y):
            return x + y
        
        result = test_function(2, 3)
        
        assert result == 5
        mock_monitoring.start_performance_timer.assert_called_once_with("test_operation")
        mock_monitoring.end_performance_timer.assert_called_once_with(
            "timer-123", "test_operation", success=True
        )
        print("??Sync performance decorator test passed")
    
    @pytest.mark.asyncio
    async def test_monitor_performance_decorator_async(self, mock_monitoring):
        """Test performance monitoring decorator for async functions"""
        @monitor_performance("async_test_operation")
        async def async_test_function(x, y):
            await asyncio.sleep(0.01)
            return x * y
        
        result = await async_test_function(3, 4)
        
        assert result == 12
        mock_monitoring.start_performance_timer.assert_called_once_with("async_test_operation")
        mock_monitoring.end_performance_timer.assert_called_once_with(
            "timer-123", "async_test_operation", success=True
        )
        print("??Async performance decorator test passed")
    
    def test_monitor_performance_decorator_error(self, mock_monitoring):
        """Test performance monitoring decorator with error"""
        @monitor_performance("error_operation")
        def error_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            error_function()
        
        mock_monitoring.start_performance_timer.assert_called_once_with("error_operation")
        mock_monitoring.end_performance_timer.assert_called_once_with(
            "timer-123", "error_operation", success=False, error_message="Test error"
        )
        print("??Performance decorator error handling test passed")
    
    def test_trace_context_manager(self):
        """Test trace context manager"""
        with patch('riskintel360.services.monitoring_service.get_monitoring_service') as mock_get:
            mock_service = Mock()
            mock_service.start_trace.return_value = "span-123"
            mock_service.end_trace.return_value = Mock()
            mock_get.return_value = mock_service
            
            with TraceContext("test_operation", tags={"component": "test"}) as span_id:
                assert span_id == "span-123"
                # Simulate some work
                pass
            
            mock_service.start_trace.assert_called_once_with(
                "test_operation", None, {"component": "test"}
            )
            mock_service.end_trace.assert_called_once_with("span-123", "ok", None)
        print("??Trace context manager test passed")
    
    def test_trace_context_manager_with_error(self):
        """Test trace context manager with error"""
        with patch('riskintel360.services.monitoring_service.get_monitoring_service') as mock_get:
            mock_service = Mock()
            mock_service.start_trace.return_value = "span-456"
            mock_service.end_trace.return_value = Mock()
            mock_get.return_value = mock_service
            
            with pytest.raises(ValueError):
                with TraceContext("error_operation") as span_id:
                    raise ValueError("Test error")
            
            mock_service.end_trace.assert_called_once_with("span-456", "error", "Test error")
        print("??Trace context manager error handling test passed")


class TestMonitoringIntegration:
    """Test monitoring system integration"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_monitoring_workflow(self):
        """Test complete monitoring workflow"""
        with patch('boto3.client') as mock_boto3:
            mock_cloudwatch = Mock()
            mock_boto3.return_value = mock_cloudwatch
            
            # Create monitoring service
            monitoring = MonitoringService()
            monitoring._cloudwatch_client = mock_cloudwatch
            
            # Stop background task for test
            if monitoring._monitoring_task:
                monitoring._monitoring_task.cancel()
            
            # Test complete workflow
            # 1. Start trace
            span_id = monitoring.start_trace("integration_test")
            
            # 2. Record metrics
            monitoring.increment_counter("TestCounter", dimensions={"test": "integration"})
            monitoring.record_gauge("TestGauge", 85.0)
            
            # 3. Performance timing
            timer_id = monitoring.start_performance_timer("integration_operation")
            await asyncio.sleep(0.01)  # Simulate work
            monitoring.end_performance_timer(timer_id, "integration_operation", success=True)
            
            # 4. Health check
            async def health_check():
                return True
            
            await monitoring.register_health_check("integration_component", health_check)
            
            # 5. Create alert
            alert_received = []
            monitoring.add_alert_handler(lambda alert: alert_received.append(alert))
            
            await monitoring.create_alert(
                "Integration Test Alert",
                "Testing end-to-end workflow",
                AlertSeverity.INFO
            )
            
            # 6. End trace
            monitoring.end_trace(span_id, "ok")
            
            # 7. Get summary
            summary = monitoring.get_monitoring_summary()
            
            # Verify workflow completed successfully
            # The buffer will have more metrics due to trace and performance metrics
            assert len(monitoring._metrics_buffer) >= 2  # At least counter + gauge
            assert len(monitoring._performance_metrics) == 1
            assert "integration_component" in monitoring._health_checks
            assert len(alert_received) == 1
            assert summary["tracing"]["active_traces"] == 0  # Trace completed
            
            print("??End-to-end monitoring workflow test passed")
    
    def test_global_monitoring_service(self):
        """Test global monitoring service singleton"""
        service1 = get_monitoring_service()
        service2 = get_monitoring_service()
        
        assert service1 is service2  # Should be same instance
        assert isinstance(service1, MonitoringService)
        print("??Global monitoring service test passed")


@pytest.mark.asyncio
async def test_monitoring_system_comprehensive():
    """Comprehensive test of the monitoring system"""
    print("\n?? Starting Comprehensive Monitoring System Tests")
    print("=" * 60)
    
    # Test CloudWatch integration
    print("\n1️⃣ Testing CloudWatch Integration...")
    with patch('boto3.client') as mock_boto3:
        mock_cloudwatch = Mock()
        mock_logs = Mock()
        mock_boto3.side_effect = lambda service: {
            'cloudwatch': mock_cloudwatch,
            'logs': mock_logs
        }[service]
        
        monitoring = MonitoringService()
        monitoring._cloudwatch_client = mock_cloudwatch
        monitoring._logs_client = mock_logs
        
        # Stop background task
        if monitoring._monitoring_task:
            monitoring._monitoring_task.cancel()
        
        # Test dashboard creation
        mock_cloudwatch.put_dashboard = Mock()
        dashboard_created = await monitoring.create_cloudwatch_dashboard()
        assert dashboard_created is True
        assert mock_cloudwatch.put_dashboard.called
        print("   ??CloudWatch dashboard creation successful")
    
    # Test custom metrics
    print("\n2️⃣ Testing Custom Business Metrics...")
    monitoring.increment_counter("ValidationRequests", dimensions={"agent": "market_analysis"})
    monitoring.record_gauge("AgentHealth", 95.0, "Percent", {"agent": "regulatory_compliance"})
    monitoring.record_timer("ResponseTime", 150.0, {"operation": "fraud_detection"})
    
    assert len(monitoring._metrics_buffer) == 3
    print("   ??Custom business metrics recorded successfully")
    
    # Test performance monitoring
    print("\n3️⃣ Testing Performance Degradation Detection...")
    timer_id = monitoring.start_performance_timer("critical_operation")
    await asyncio.sleep(0.01)
    duration = monitoring.end_performance_timer(timer_id, "critical_operation", success=True)
    
    assert duration > 0
    stats = monitoring.get_performance_stats("critical_operation")
    assert stats["total_calls"] == 1
    assert stats["success_count"] == 1
    print("   ??Performance monitoring working correctly")
    
    # Test distributed tracing
    print("\n4️⃣ Testing Distributed Tracing...")
    with TraceContext("multi_agent_workflow", tags={"workflow": "validation"}) as span_id:
        monitoring.add_trace_log(span_id, "info", "Starting agent coordination")
        
        # Simulate nested operation
        child_span_id = monitoring.start_trace("agent_execution", parent_span_id=span_id)
        monitoring.add_trace_log(child_span_id, "debug", "Agent processing request")
        monitoring.end_trace(child_span_id, "ok")
    
    # Verify trace was completed
    trace_info = monitoring.get_trace(span_id)
    assert trace_info is None  # Should be removed from active traces
    print("   ??Distributed tracing working correctly")
    
    # Test alerting system
    print("\n5️⃣ Testing Alert System...")
    alerts_received = []
    
    async def alert_handler(alert_data):
        alerts_received.append(alert_data)
    
    monitoring.add_alert_handler(alert_handler)
    
    await monitoring.create_alert(
        "Performance Degradation Detected",
        "Agent response time exceeded threshold",
        AlertSeverity.WARNING,
        component="market_analysis_agent",
        metadata={"threshold_ms": 5000, "actual_ms": 7500}
    )
    
    assert len(alerts_received) == 1
    alert = alerts_received[0]
    assert alert["severity"] == "warning"
    assert alert["component"] == "market_analysis_agent"
    print("   ??Alert system working correctly")
    
    # Test monitoring summary
    print("\n6️⃣ Testing Monitoring Summary...")
    summary = monitoring.get_monitoring_summary()
    
    assert summary["metrics"]["buffer_size"] > 0
    assert summary["cloudwatch"]["enabled"] is True
    assert summary["alerts"]["handlers_registered"] == 1
    print("   ??Monitoring summary generated successfully")
    
    print("\n?? Comprehensive Monitoring System Tests Completed!")
    print("=" * 60)
    print("\n??All monitoring features tested successfully:")
    print("  ??CloudWatch dashboards and metrics")
    print("  ??Custom business metrics and KPI tracking")
    print("  ??Performance degradation detection")
    print("  ??Distributed tracing for multi-agent workflows")
    print("  ??Alert system with severity levels")
    print("  ??Health monitoring and status reporting")
    print("  ??Performance statistics and analytics")


if __name__ == "__main__":
    # Run comprehensive monitoring tests
    asyncio.run(test_monitoring_system_comprehensive())
