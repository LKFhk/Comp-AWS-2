"""
Integration tests for performance metrics collection.

Tests the integration of performance monitoring with actual agent execution,
workflow orchestration, and external systems.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from riskintel360.services.performance_monitor import PerformanceMonitor, performance_monitor
from riskintel360.services.workflow_orchestrator import SupervisorAgent
from riskintel360.agents.base_agent import BaseAgent, AgentConfig
from riskintel360.models.agent_models import AgentType


class MockAgent(BaseAgent):
    """Mock agent for testing performance monitoring integration"""
    
    def __init__(self, config: AgentConfig, response_delay: float = 1.0):
        super().__init__(config)
        self.response_delay = response_delay
    
    async def execute_task(self, task_type: str, parameters: dict) -> dict:
        """Mock task execution with configurable delay"""
        await asyncio.sleep(self.response_delay)
        return {
            'status': 'completed',
            'result': f'Mock result for {task_type}',
            'execution_time': self.response_delay
        }
    
    def get_capabilities(self) -> list:
        return ['mock_capability']


@pytest.fixture
def performance_monitor_instance():
    """Create a fresh performance monitor for testing"""
    monitor = PerformanceMonitor()
    monitor.reset_metrics()
    return monitor


@pytest.fixture
def mock_supervisor():
    """Create a mock supervisor agent"""
    with patch('riskintel360.services.workflow_orchestrator.SupervisorAgent') as mock:
        supervisor = Mock(spec=SupervisorAgent)
        supervisor.bedrock_client = Mock()
        supervisor.bedrock_client.invoke_for_agent = AsyncMock(
            return_value=Mock(content="Mock LLM response")
        )
        yield supervisor


class TestPerformanceMonitoringIntegration:
    """Test performance monitoring integration with agents and workflows"""
    
    @pytest.mark.asyncio
    async def test_agent_performance_tracking_integration(self, performance_monitor_instance):
        """Test performance tracking integration with actual agent execution"""
        monitor = performance_monitor_instance
        
        # Create mock agents with different response times
        from unittest.mock import Mock
        mock_bedrock_client = Mock()
        
        fast_agent_config = AgentConfig(
            agent_id="fast_agent_1",
            agent_type=AgentType.REGULATORY_COMPLIANCE,
            bedrock_client=mock_bedrock_client
        )
        slow_agent_config = AgentConfig(
            agent_id="slow_agent_1", 
            agent_type=AgentType.FRAUD_DETECTION,
            bedrock_client=mock_bedrock_client
        )
        
        fast_agent = MockAgent(fast_agent_config, response_delay=0.5)
        slow_agent = MockAgent(slow_agent_config, response_delay=2.0)
        
        # Execute tasks with performance tracking
        async def execute_with_tracking(agent, agent_type_str, task_type):
            request_id = f"{agent_type_str}_{int(time.time())}"
            async with monitor.track_agent_request(agent_type_str, request_id):
                return await agent.execute_task(task_type, {})
        
        # Execute multiple tasks
        tasks = [
            execute_with_tracking(fast_agent, 'regulatory_compliance', 'compliance_check'),
            execute_with_tracking(fast_agent, 'regulatory_compliance', 'risk_assessment'),
            execute_with_tracking(slow_agent, 'fraud_detection', 'anomaly_detection'),
            execute_with_tracking(slow_agent, 'fraud_detection', 'pattern_analysis')
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all tasks completed successfully
        assert len(results) == 4
        for result in results:
            assert result['status'] == 'completed'
        
        # Verify performance metrics were collected
        metrics = monitor.get_current_metrics()
        
        assert 'regulatory_compliance' in metrics['agent_metrics']
        assert 'fraud_detection' in metrics['agent_metrics']
        
        # Check response times
        reg_metrics = metrics['agent_metrics']['regulatory_compliance']
        fraud_metrics = metrics['agent_metrics']['fraud_detection']
        
        assert reg_metrics['total_requests'] == 2
        assert fraud_metrics['total_requests'] == 2
        assert reg_metrics['avg_response_time'] < fraud_metrics['avg_response_time']
        
        # Verify all requests completed within reasonable time
        assert reg_metrics['avg_response_time'] < 1.0  # Fast agent
        assert fraud_metrics['avg_response_time'] > 1.5  # Slow agent
    
    @pytest.mark.asyncio
    async def test_workflow_performance_tracking_integration(self, performance_monitor_instance):
        """Test performance tracking integration with workflow execution"""
        monitor = performance_monitor_instance
        
        # Simulate a complete workflow with multiple agents
        async def simulate_fintech_workflow(workflow_id: str):
            async with monitor.track_workflow_execution(workflow_id):
                # Simulate regulatory compliance check
                async with monitor.track_agent_request('regulatory_compliance', f'{workflow_id}_reg'):
                    await asyncio.sleep(0.8)  # Regulatory analysis
                
                # Simulate fraud detection
                async with monitor.track_agent_request('fraud_detection', f'{workflow_id}_fraud'):
                    await asyncio.sleep(1.2)  # ML-based fraud detection
                
                # Simulate risk assessment
                async with monitor.track_agent_request('risk_assessment', f'{workflow_id}_risk'):
                    await asyncio.sleep(0.6)  # Risk calculation
                
                # Simulate market analysis
                async with monitor.track_agent_request('market_analysis', f'{workflow_id}_market'):
                    await asyncio.sleep(0.9)  # Market data analysis
                
                return {'status': 'completed', 'total_agents': 4}
        
        # Execute workflow
        workflow_id = 'integration_test_workflow'
        result = await simulate_fintech_workflow(workflow_id)
        
        # Verify workflow completed successfully
        assert result['status'] == 'completed'
        
        # Verify performance metrics
        metrics = monitor.get_current_metrics()
        
        # Check workflow metrics
        workflow_metrics = metrics['workflow_metrics']
        assert workflow_metrics['completed_workflows'] == 1
        assert workflow_metrics['avg_execution_time'] > 3.0  # Sum of all agent times
        assert workflow_metrics['avg_execution_time'] < 5.0  # Should be reasonable
        
        # Check agent metrics
        assert len(metrics['agent_metrics']) == 4
        for agent_type in ['regulatory_compliance', 'fraud_detection', 'risk_assessment', 'market_analysis']:
            assert agent_type in metrics['agent_metrics']
            assert metrics['agent_metrics'][agent_type]['total_requests'] == 1
        
        # Verify system metrics
        system_metrics = metrics['system_metrics']
        assert system_metrics['total_requests'] == 4
        assert system_metrics['failed_requests'] == 0
        assert system_metrics['success_rate'] == 100.0
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling_integration(self, performance_monitor_instance):
        """Test concurrent request handling with performance monitoring"""
        monitor = performance_monitor_instance
        
        async def concurrent_agent_task(agent_id: str, delay: float):
            request_id = f"concurrent_request_{agent_id}"
            async with monitor.track_agent_request('load_test_agent', request_id):
                await asyncio.sleep(delay)
                return f"Completed {agent_id}"
        
        # Create 60 concurrent tasks to test 50+ requirement
        num_concurrent = 60
        tasks = [
            asyncio.create_task(concurrent_agent_task(f"agent_{i}", 0.5))
            for i in range(num_concurrent)
        ]
        
        # Execute all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Verify all tasks completed
        assert len(results) == num_concurrent
        
        # Verify performance metrics
        metrics = monitor.get_current_metrics()
        
        # Check concurrent request handling
        system_metrics = metrics['system_metrics']
        assert system_metrics['total_requests'] == num_concurrent
        assert system_metrics['max_concurrent_requests'] >= 50  # Meets requirement
        assert system_metrics['concurrent_requests'] == 0  # All completed
        
        # Verify execution time was reasonable (should be close to delay due to concurrency)
        total_execution_time = end_time - start_time
        assert total_execution_time < 2.0  # Should be much less than sequential execution
        
        # Check performance requirements
        dashboard_data = monitor.get_performance_dashboard_data()
        requirements = dashboard_data['performance_requirements']
        assert requirements['concurrent_requests']['status'] is True
    
    @pytest.mark.asyncio
    async def test_performance_alert_integration(self, performance_monitor_instance):
        """Test performance alert integration with actual threshold violations"""
        monitor = performance_monitor_instance
        
        alerts_triggered = []
        
        # Mock alert triggering to capture alerts
        async def mock_trigger_alert(alert_type: str, details: dict):
            alerts_triggered.append({'type': alert_type, 'details': details})
        
        monitor._trigger_alert = mock_trigger_alert
        
        # Execute agent request that exceeds response time threshold
        async with monitor.track_agent_request('slow_agent', 'threshold_test'):
            await asyncio.sleep(6.0)  # Exceed 5 second threshold
        
        # Execute workflow that exceeds execution time threshold
        async with monitor.track_workflow_execution('slow_workflow'):
            await asyncio.sleep(0.1)  # Short delay for testing
            # Manually set a high execution time to trigger alert
            monitor.metrics.workflow_execution_times['slow_workflow'] = 8000.0  # > 2 hours
        
        # Verify alerts were triggered
        assert len(alerts_triggered) >= 1
        
        # Check agent response time alert
        agent_alert = next((a for a in alerts_triggered if a['type'] == 'agent_response_time_exceeded'), None)
        assert agent_alert is not None
        assert agent_alert['details']['agent_type'] == 'slow_agent'
        assert agent_alert['details']['response_time'] > 5.0
    
    @pytest.mark.asyncio
    async def test_system_availability_tracking_integration(self, performance_monitor_instance):
        """Test system availability tracking integration"""
        monitor = performance_monitor_instance
        
        # Record some downtime events
        monitor.record_downtime_event(60.0, "Database maintenance")
        monitor.record_downtime_event(30.0, "Network issue")
        
        # Verify availability calculation
        availability = monitor.metrics.get_availability_percentage()
        
        # With short uptime and 90 seconds downtime, availability should be affected
        assert availability < 100.0
        
        # Verify availability events were recorded
        assert len(monitor.metrics.availability_events) == 2
        
        # Check dashboard data includes availability information
        dashboard_data = monitor.get_performance_dashboard_data()
        assert 'availability' in dashboard_data['summary']
        
        # Verify availability requirement checking
        requirements = dashboard_data['performance_requirements']
        assert 'system_availability' in requirements
    
    @pytest.mark.asyncio
    async def test_performance_dashboard_integration(self, performance_monitor_instance):
        """Test performance dashboard data integration with real metrics"""
        monitor = performance_monitor_instance
        
        # Generate realistic performance data
        agents = ['regulatory_compliance', 'fraud_detection', 'risk_assessment', 'market_analysis']
        
        for agent_type in agents:
            for i in range(5):  # 5 requests per agent
                request_id = f"{agent_type}_req_{i}"
                async with monitor.track_agent_request(agent_type, request_id):
                    # Variable response times
                    delay = 0.5 + (i * 0.3)  # 0.5s to 1.7s
                    await asyncio.sleep(delay)
        
        # Execute a couple of workflows
        for workflow_num in range(2):
            workflow_id = f"dashboard_test_workflow_{workflow_num}"
            async with monitor.track_workflow_execution(workflow_id):
                await asyncio.sleep(1.0)  # 1 second workflow
        
        # Get dashboard data
        dashboard_data = monitor.get_performance_dashboard_data()
        
        # Verify dashboard structure and content
        assert 'summary' in dashboard_data
        assert 'agent_performance' in dashboard_data
        assert 'workflow_performance' in dashboard_data
        assert 'performance_requirements' in dashboard_data
        
        # Check summary data
        summary = dashboard_data['summary']
        assert summary['total_requests'] == 20  # 4 agents * 5 requests
        assert summary['success_rate'] == '100.00%'
        assert int(summary['concurrent_requests']) == 0
        
        # Check agent performance data
        agent_performance = dashboard_data['agent_performance']
        assert len(agent_performance) == 4
        
        for agent_data in agent_performance:
            assert agent_data['agent_type'] in agents
            assert agent_data['total_requests'] == 5
            assert agent_data['status'] == 'OK'  # All should be under 5s
            assert 'avg_response_time' in agent_data
        
        # Check workflow performance
        workflow_perf = dashboard_data['workflow_performance']
        assert workflow_perf['completed_workflows'] == 2
        assert workflow_perf['active_workflows'] == 0
        
        # Check performance requirements
        requirements = dashboard_data['performance_requirements']
        
        # All requirements should be met
        assert requirements['agent_response_time']['status'] is True
        assert requirements['workflow_execution_time']['status'] is True
        assert requirements['system_availability']['status'] is True
    
    def test_global_performance_monitor_integration(self):
        """Test integration with global performance monitor instance"""
        # Reset global instance
        performance_monitor.reset_metrics()
        
        # Add some test data to global instance
        performance_monitor.metrics.total_requests = 50
        performance_monitor.metrics.max_concurrent_requests = 75
        
        # Verify global instance works
        metrics = performance_monitor.get_current_metrics()
        assert metrics['system_metrics']['total_requests'] == 50
        assert metrics['system_metrics']['max_concurrent_requests'] == 75
        
        # Verify performance requirements
        dashboard_data = performance_monitor.get_performance_dashboard_data()
        requirements = dashboard_data['performance_requirements']
        assert requirements['concurrent_requests']['status'] is True  # 75 >= 50
        
        # Reset for other tests
        performance_monitor.reset_metrics()


class TestPerformanceRequirementsValidation:
    """Test validation of AWS competition performance requirements"""
    
    @pytest.mark.asyncio
    async def test_agent_response_time_requirement_validation(self, performance_monitor_instance):
        """Test validation of < 5 second agent response time requirement"""
        monitor = performance_monitor_instance
        
        # Test agents that meet requirement
        for i in range(10):
            async with monitor.track_agent_request('fast_agent', f'req_{i}'):
                await asyncio.sleep(0.1 + (i * 0.1))  # 0.1s to 1.0s
        
        # Test agents that violate requirement
        for i in range(3):
            async with monitor.track_agent_request('slow_agent', f'slow_req_{i}'):
                await asyncio.sleep(6.0 + i)  # 6s to 8s
        
        # Verify requirement validation
        dashboard_data = monitor.get_performance_dashboard_data()
        requirements = dashboard_data['performance_requirements']
        
        # Fast agent should meet requirement
        fast_agent_perf = next(
            (a for a in dashboard_data['agent_performance'] if a['agent_type'] == 'fast_agent'),
            None
        )
        assert fast_agent_perf is not None
        assert fast_agent_perf['status'] == 'OK'
        
        # Slow agent should violate requirement
        slow_agent_perf = next(
            (a for a in dashboard_data['agent_performance'] if a['agent_type'] == 'slow_agent'),
            None
        )
        assert slow_agent_perf is not None
        assert slow_agent_perf['status'] == 'WARNING'
    
    @pytest.mark.asyncio
    async def test_workflow_execution_time_requirement_validation(self, performance_monitor_instance):
        """Test validation of < 2 hour workflow execution time requirement"""
        monitor = performance_monitor_instance
        
        # Execute fast workflow (meets requirement)
        async with monitor.track_workflow_execution('fast_workflow'):
            await asyncio.sleep(0.1)  # Very fast for testing
        
        # Simulate slow workflow (violates requirement)
        monitor.metrics.workflow_execution_times['slow_workflow'] = 8000.0  # > 2 hours
        
        # Verify requirement validation
        dashboard_data = monitor.get_performance_dashboard_data()
        requirements = dashboard_data['performance_requirements']
        
        # Should fail because one workflow exceeds 2 hours
        assert requirements['workflow_execution_time']['status'] is False
    
    def test_system_availability_requirement_validation(self, performance_monitor_instance):
        """Test validation of 99.9% system availability requirement"""
        monitor = performance_monitor_instance
        
        # Set system uptime to 1000 hours for testing
        monitor.metrics.system_uptime_start = datetime.now() - timedelta(hours=1000)
        
        # Test with minimal downtime (meets requirement)
        monitor.metrics.availability_events = [
            {'type': 'downtime', 'duration': 1800}  # 30 minutes
        ]
        
        availability = monitor.metrics.get_availability_percentage()
        assert availability > 99.9
        
        # Test with excessive downtime (violates requirement)
        monitor.metrics.availability_events = [
            {'type': 'downtime', 'duration': 7200}  # 2 hours
        ]
        
        availability = monitor.metrics.get_availability_percentage()
        assert availability < 99.9
    
    @pytest.mark.asyncio
    async def test_concurrent_request_requirement_validation(self, performance_monitor_instance):
        """Test validation of 50+ concurrent request handling requirement"""
        monitor = performance_monitor_instance
        
        # Simulate 60 concurrent requests
        async def concurrent_task(task_id: int):
            async with monitor.track_agent_request('test_agent', f'task_{task_id}'):
                await asyncio.sleep(0.2)
        
        tasks = [asyncio.create_task(concurrent_task(i)) for i in range(60)]
        await asyncio.gather(*tasks)
        
        # Verify requirement is met
        dashboard_data = monitor.get_performance_dashboard_data()
        requirements = dashboard_data['performance_requirements']
        
        assert requirements['concurrent_requests']['status'] is True
        assert monitor.metrics.max_concurrent_requests >= 50


@pytest.mark.asyncio
async def test_end_to_end_performance_monitoring():
    """End-to-end test of performance monitoring with realistic fintech workflow"""
    monitor = PerformanceMonitor()
    monitor.reset_metrics()
    
    # Simulate complete RiskIntel360 workflow
    async def complete_fintech_analysis(company_id: str):
        workflow_id = f"fintech_analysis_{company_id}"
        
        async with monitor.track_workflow_execution(workflow_id):
            # Regulatory compliance analysis
            async with monitor.track_agent_request('regulatory_compliance', f'{workflow_id}_reg'):
                await asyncio.sleep(0.8)  # SEC/FINRA data analysis
            
            # Advanced fraud detection with ML
            async with monitor.track_agent_request('fraud_detection', f'{workflow_id}_fraud'):
                await asyncio.sleep(1.5)  # ML model execution
            
            # Risk assessment
            async with monitor.track_agent_request('risk_assessment', f'{workflow_id}_risk'):
                await asyncio.sleep(0.6)  # Risk calculations
            
            # Market analysis
            async with monitor.track_agent_request('market_analysis', f'{workflow_id}_market'):
                await asyncio.sleep(0.9)  # Market data processing
            
            # KYC verification
            async with monitor.track_agent_request('kyc_verification', f'{workflow_id}_kyc'):
                await asyncio.sleep(0.7)  # Identity verification
            
            return {
                'status': 'completed',
                'company_id': company_id,
                'risk_score': 0.75,
                'compliance_status': 'compliant',
                'fraud_alerts': 0
            }
    
    # Execute multiple concurrent fintech analyses
    companies = ['fintech_startup_1', 'bank_2', 'investment_firm_3']
    tasks = [complete_fintech_analysis(company) for company in companies]
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    # Verify all analyses completed successfully
    assert len(results) == 3
    for result in results:
        assert result['status'] == 'completed'
    
    # Verify performance metrics
    metrics = monitor.get_current_metrics()
    
    # Check that all agent types were used
    expected_agents = ['regulatory_compliance', 'fraud_detection', 'risk_assessment', 'market_analysis', 'kyc_verification']
    for agent_type in expected_agents:
        assert agent_type in metrics['agent_metrics']
        assert metrics['agent_metrics'][agent_type]['total_requests'] == 3
    
    # Check workflow performance
    assert metrics['workflow_metrics']['completed_workflows'] == 3
    assert metrics['workflow_metrics']['avg_execution_time'] > 3.0  # Sum of agent times
    assert metrics['workflow_metrics']['avg_execution_time'] < 10.0  # Should be reasonable
    
    # Check system performance
    assert metrics['system_metrics']['total_requests'] == 15  # 5 agents * 3 companies
    assert metrics['system_metrics']['failed_requests'] == 0
    assert metrics['system_metrics']['success_rate'] == 100.0
    
    # Verify competition requirements are met
    dashboard_data = monitor.get_performance_dashboard_data()
    requirements = dashboard_data['performance_requirements']
    
    # All agent response times should be under 5 seconds
    assert requirements['agent_response_time']['status'] is True
    
    # All workflows should complete under 2 hours
    assert requirements['workflow_execution_time']['status'] is True
    
    # Total execution time should be reasonable for concurrent execution
    total_time = end_time - start_time
    assert total_time < 5.0  # Should complete quickly due to concurrency
    
    print(f"End-to-end test completed in {total_time:.2f} seconds")
    print(f"Dashboard summary: {dashboard_data['summary']}")
    print(f"Performance requirements: {requirements}")
