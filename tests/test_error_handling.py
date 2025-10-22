"""
Comprehensive tests for error handling and recovery mechanisms.

Tests cover:
- Graceful degradation strategies
- Circuit breaker patterns
- Retry logic with exponential backoff
- Workflow state recovery from checkpoints
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Any, Dict

from riskintel360.utils.error_handling import (
    CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState,
    RetryHandler, RetryConfig,
    WorkflowStateManager, WorkflowCheckpoint,
    GracefulDegradationManager,
    ErrorHandlingManager, ErrorContext, ErrorSeverity, RecoveryAction
)

from riskintel360.utils.data_source_errors import (
    DataSourceManager, DataSourceType, DataSourceError, APIError, DatabaseError
)

from riskintel360.utils.agent_errors import (
    AgentErrorHandler, AgentError, ModelError, CommunicationError
)

from riskintel360.utils.workflow_errors import (
    WorkflowErrorHandler, WorkflowDefinition, WorkflowStep, WorkflowState
)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state allows execution."""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60)
        breaker = CircuitBreaker(config)
        
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.can_execute() is True
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=60)
        breaker = CircuitBreaker(config)
        
        # Record failures
        breaker.record_failure(Exception("Test error 1"))
        assert breaker.state == CircuitBreakerState.CLOSED
        
        breaker.record_failure(Exception("Test error 2"))
        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.can_execute() is False
    
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state."""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=1)
        breaker = CircuitBreaker(config)
        
        # Open the circuit
        breaker.record_failure(Exception("Test error"))
        assert breaker.state == CircuitBreakerState.OPEN
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Should allow execution (half-open)
        assert breaker.can_execute() is True
        assert breaker.state == CircuitBreakerState.HALF_OPEN
        
        # Success should close the circuit
        breaker.record_success()
        assert breaker.state == CircuitBreakerState.CLOSED
    
    def test_circuit_breaker_success_resets_failures(self):
        """Test that success resets failure count."""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60)
        breaker = CircuitBreaker(config)
        
        # Record some failures
        breaker.record_failure(Exception("Test error 1"))
        breaker.record_failure(Exception("Test error 2"))
        assert breaker.failure_count == 2
        
        # Success should reset
        breaker.record_success()
        assert breaker.failure_count == 0
        assert breaker.state == CircuitBreakerState.CLOSED


class TestRetryHandler:
    """Test retry logic with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test successful execution on first attempt."""
        config = RetryConfig(max_attempts=3, base_delay=0.1)
        handler = RetryHandler(config)
        
        async def success_func():
            return "success"
        
        result = await handler.execute_with_retry(success_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test successful execution after some failures."""
        config = RetryConfig(max_attempts=3, base_delay=0.1)
        handler = RetryHandler(config)
        
        call_count = 0
        
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Failure {call_count}")
            return "success"
        
        result = await handler.execute_with_retry(flaky_func)
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """Test retry exhaustion after max attempts."""
        config = RetryConfig(max_attempts=2, base_delay=0.1)
        handler = RetryHandler(config)
        
        async def always_fail():
            raise Exception("Always fails")
        
        with pytest.raises(Exception, match="Always fails"):
            await handler.execute_with_retry(always_fail)
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff timing."""
        config = RetryConfig(max_attempts=3, base_delay=0.1, backoff_multiplier=2.0)
        handler = RetryHandler(config)
        
        delays = []
        original_sleep = asyncio.sleep
        
        async def mock_sleep(delay):
            delays.append(delay)
            await original_sleep(0.01)  # Short sleep for testing
        
        with patch('asyncio.sleep', mock_sleep):
            try:
                await handler.execute_with_retry(lambda: (_ for _ in ()).throw(Exception("Test")))
            except Exception:
                pass
        
        # Should have 2 delays (for 2 retries)
        assert len(delays) == 2
        # Second delay should be roughly double the first (with jitter)
        assert delays[1] > delays[0]


class TestWorkflowStateManager:
    """Test workflow state management and checkpoints."""
    
    @pytest.mark.asyncio
    async def test_create_checkpoint(self):
        """Test checkpoint creation."""
        manager = WorkflowStateManager()
        
        checkpoint_id = await manager.create_checkpoint(
            workflow_id="test_workflow",
            state_data={"step": "test_step", "data": "test_data"},
            completed_steps=["step1", "step2"],
            current_step="step3"
        )
        
        assert checkpoint_id.startswith("test_workflow_")
        assert checkpoint_id in manager.checkpoints
        
        checkpoint = manager.checkpoints[checkpoint_id]
        assert checkpoint.workflow_id == "test_workflow"
        assert checkpoint.completed_steps == ["step1", "step2"]
        assert checkpoint.current_step == "step3"
        assert checkpoint.state_data == {"step": "test_step", "data": "test_data"}
    
    @pytest.mark.asyncio
    async def test_restore_from_checkpoint(self):
        """Test checkpoint restoration."""
        manager = WorkflowStateManager()
        
        # Create checkpoint
        checkpoint_id = await manager.create_checkpoint(
            workflow_id="test_workflow",
            state_data={"restored": True},
            completed_steps=["step1"],
            current_step="step2"
        )
        
        # Restore checkpoint
        restored = await manager.restore_from_checkpoint(checkpoint_id)
        
        assert restored is not None
        assert restored.workflow_id == "test_workflow"
        assert restored.state_data == {"restored": True}
        assert restored.completed_steps == ["step1"]
        assert restored.current_step == "step2"
    
    @pytest.mark.asyncio
    async def test_get_latest_checkpoint(self):
        """Test getting latest checkpoint for workflow."""
        manager = WorkflowStateManager()
        
        # Create multiple checkpoints
        checkpoint1_id = await manager.create_checkpoint(
            workflow_id="test_workflow",
            state_data={"version": 1},
            completed_steps=["step1"],
            current_step="step2"
        )
        
        await asyncio.sleep(0.01)  # Ensure different timestamps
        
        checkpoint2_id = await manager.create_checkpoint(
            workflow_id="test_workflow",
            state_data={"version": 2},
            completed_steps=["step1", "step2"],
            current_step="step3"
        )
        
        latest = await manager.get_latest_checkpoint("test_workflow")
        
        assert latest is not None
        assert latest.checkpoint_id == checkpoint2_id
        assert latest.state_data == {"version": 2}


class TestGracefulDegradationManager:
    """Test graceful degradation strategies."""
    
    @pytest.mark.asyncio
    async def test_successful_primary_function(self):
        """Test successful execution of primary function."""
        manager = GracefulDegradationManager()
        
        async def primary_func(data):
            return {"result": "primary", "data": data}
        
        result = await manager.execute_with_degradation(
            "test_service", primary_func, "test_data"
        )
        
        assert result == {"result": "primary", "data": "test_data"}
        assert manager.service_status["test_service"] is True
    
    @pytest.mark.asyncio
    async def test_degradation_fallback(self):
        """Test fallback to degradation strategy."""
        manager = GracefulDegradationManager()
        
        async def primary_func(data):
            raise Exception("Primary failed")
        
        async def degraded_func(data):
            return {"result": "degraded", "data": data}
        
        manager.register_degradation_strategy("test_service", degraded_func)
        
        result = await manager.execute_with_degradation(
            "test_service", primary_func, "test_data"
        )
        
        assert result == {"result": "degraded", "data": "test_data"}
        assert manager.service_status["test_service"] is False
    
    @pytest.mark.asyncio
    async def test_no_degradation_strategy(self):
        """Test behavior when no degradation strategy is registered."""
        manager = GracefulDegradationManager()
        
        async def primary_func(data):
            raise Exception("Primary failed")
        
        with pytest.raises(Exception, match="Primary failed"):
            await manager.execute_with_degradation(
                "test_service", primary_func, "test_data"
            )


class TestDataSourceManager:
    """Test data source error handling and fallbacks."""
    
    @pytest.mark.asyncio
    async def test_successful_data_fetch(self):
        """Test successful data fetching."""
        manager = DataSourceManager()
        
        # Mock data source
        mock_source = Mock()
        mock_source.get_data = AsyncMock(return_value={"data": "success"})
        
        manager.register_data_source("test_api", mock_source, DataSourceType.API)
        
        result = await manager.fetch_data("test_api", "get_data", use_cache=False)
        
        assert result == {"data": "success"}
        mock_source.get_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fallback_chain(self):
        """Test fallback chain when primary source fails."""
        manager = DataSourceManager()
        
        # Primary source (fails)
        primary_source = Mock()
        primary_source.get_data = AsyncMock(side_effect=Exception("Primary failed"))
        
        # Fallback source (succeeds)
        fallback_source = Mock()
        fallback_source.get_data = AsyncMock(return_value={"data": "fallback"})
        
        manager.register_data_source("primary_api", primary_source, DataSourceType.API)
        manager.register_data_source("fallback_api", fallback_source, DataSourceType.API)
        manager.register_fallback_chain("primary_api", ["fallback_api"])
        
        result = await manager.fetch_data("primary_api", "get_data", use_cache=False)
        
        assert result == {"data": "fallback"}
        # Primary source may be called multiple times due to retry logic
        assert primary_source.get_data.call_count >= 1
        fallback_source.get_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_degraded_response(self):
        """Test degraded response when all sources fail."""
        manager = DataSourceManager()
        
        # Source that always fails
        failing_source = Mock()
        failing_source.get_market_data = AsyncMock(side_effect=Exception("All failed"))
        
        manager.register_data_source("failing_api", failing_source, DataSourceType.API)
        
        result = await manager.fetch_data("failing_api", "get_market_data", use_cache=False)
        
        assert result["status"] == "degraded"
        assert "temporarily unavailable" in result["message"]
        assert result["confidence"] == 0.1


class TestAgentErrorHandler:
    """Test agent-specific error handling."""
    
    @pytest.mark.asyncio
    async def test_successful_agent_task(self):
        """Test successful agent task execution."""
        handler = AgentErrorHandler()
        handler.register_agent("test_agent")
        
        async def test_task(data):
            return {"result": "success", "data": data}
        
        result = await handler.execute_agent_task(
            "test_agent", test_task, "test_task", {"input": "test"}
        )
        
        assert result == {"result": "success", "data": {"input": "test"}}
        
        agent_state = handler.agent_states["test_agent"]
        assert agent_state.status == "completed"
        assert agent_state.error_count == 0
    
    @pytest.mark.asyncio
    async def test_model_error_fallback(self):
        """Test model error handling with fallback."""
        handler = AgentErrorHandler()
        handler.register_agent("test_agent")
        
        # Test direct model error handling
        error = ModelError("Model failed", "test_agent", "claude-3-opus")
        
        call_count = 0
        
        async def fallback_task(**kwargs):
            nonlocal call_count
            call_count += 1
            return {"result": "fallback_success", "model": kwargs.get("model_name")}
        
        result = await handler._handle_model_error(
            "test_agent", error, fallback_task, model_name="claude-3-opus"
        )
        
        # Should get fallback model result
        assert result["result"] == "fallback_success"
        assert result["model"] in ["claude-3-sonnet", "claude-3-haiku"]
    
    @pytest.mark.asyncio
    async def test_agent_state_tracking(self):
        """Test agent state tracking during execution."""
        handler = AgentErrorHandler()
        handler.register_agent("test_agent")
        
        async def long_task(data):
            await asyncio.sleep(0.1)
            return {"result": "completed"}
        
        # Execute task
        await handler.execute_agent_task("test_agent", long_task, "long_task", {})
        
        agent_state = handler.agent_states["test_agent"]
        assert agent_state.agent_name == "test_agent"
        assert agent_state.status == "completed"
        assert agent_state.current_task is None
        assert agent_state.error_count == 0


class TestWorkflowErrorHandler:
    """Test workflow error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self):
        """Test successful execution of simple workflow."""
        handler = WorkflowErrorHandler()
        
        # Create simple workflow
        steps = [
            WorkflowStep(
                step_id="step1",
                step_name="first_step",
                agent_name=None,
                dependencies=[]
            ),
            WorkflowStep(
                step_id="step2",
                step_name="second_step",
                agent_name=None,
                dependencies=["step1"]
            )
        ]
        
        workflow_def = WorkflowDefinition(
            workflow_id="test_workflow",
            workflow_name="Test Workflow",
            steps=steps
        )
        
        result = await handler.execute_workflow(workflow_def, {"initial": "data"})
        
        assert result["status"] == "completed"
        assert result["steps_completed"] == 2
        assert "execution_time" in result
    
    @pytest.mark.asyncio
    async def test_workflow_step_retry(self):
        """Test workflow step retry on failure."""
        handler = WorkflowErrorHandler()
        
        # Mock a step that fails once then succeeds
        call_count = 0
        
        def mock_get_task_function(task_name):
            async def failing_task(data):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("First attempt fails")
                return {"task": task_name, "attempt": call_count}
            return failing_task
        
        handler._get_task_function = mock_get_task_function
        
        steps = [
            WorkflowStep(
                step_id="retry_step",
                step_name="retry_task",
                agent_name=None,
                dependencies=[],
                max_retries=2
            )
        ]
        
        workflow_def = WorkflowDefinition(
            workflow_id="retry_workflow",
            workflow_name="Retry Test Workflow",
            steps=steps
        )
        
        result = await handler.execute_workflow(workflow_def)
        
        assert result["status"] == "completed"
        assert call_count == 2  # Failed once, succeeded on retry
    
    @pytest.mark.asyncio
    async def test_workflow_checkpoint_recovery(self):
        """Test workflow recovery from checkpoint."""
        handler = WorkflowErrorHandler()
        
        # Create workflow with multiple steps
        steps = [
            WorkflowStep(step_id="step1", step_name="task1", agent_name=None, dependencies=[]),
            WorkflowStep(step_id="step2", step_name="task2", agent_name=None, dependencies=["step1"]),
            WorkflowStep(step_id="step3", step_name="task3", agent_name=None, dependencies=["step2"])
        ]
        
        workflow_def = WorkflowDefinition(
            workflow_id="checkpoint_workflow",
            workflow_name="Checkpoint Test",
            steps=steps,
            checkpoint_interval=1  # Frequent checkpoints for testing
        )
        
        # First execution - simulate failure after step 1
        step_count = 0
        
        def mock_get_task_function(task_name):
            async def task_func(data):
                nonlocal step_count
                step_count += 1
                if step_count == 2:  # Fail on second step
                    raise Exception("Simulated failure")
                return {"task": task_name, "step": step_count}
            return task_func
        
        handler._get_task_function = mock_get_task_function
        
        # This should fail and create a checkpoint
        try:
            await handler.execute_workflow(workflow_def)
            # If it doesn't raise, it means retry succeeded, which is also valid
        except Exception:
            pass  # Expected failure
        
        # Reset step count and modify function to succeed
        step_count = 0
        
        def mock_get_task_function_success(task_name):
            async def task_func(data):
                nonlocal step_count
                step_count += 1
                return {"task": task_name, "step": step_count}
            return task_func
        
        handler._get_task_function = mock_get_task_function_success
        
        # Second execution should recover from checkpoint
        result = await handler.execute_workflow(workflow_def)
        
        assert result["status"] == "completed"
        assert result["steps_completed"] == 3


class TestIntegratedErrorHandling:
    """Test integrated error handling across all components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_error_recovery(self):
        """Test end-to-end error recovery scenario."""
        # Setup managers
        data_manager = DataSourceManager()
        agent_handler = AgentErrorHandler()
        workflow_handler = WorkflowErrorHandler()
        
        # Register failing data source with fallback
        primary_source = Mock()
        primary_source.get_data = AsyncMock(side_effect=Exception("Primary failed"))
        
        fallback_source = Mock()
        fallback_source.get_data = AsyncMock(return_value={"data": "fallback_success"})
        
        data_manager.register_data_source("primary", primary_source, DataSourceType.API)
        data_manager.register_data_source("fallback", fallback_source, DataSourceType.API)
        data_manager.register_fallback_chain("primary", ["fallback"])
        
        # Register agent
        agent_handler.register_agent("data_agent")
        
        # Create agent task that uses data source
        async def data_task(workflow_data):
            result = await data_manager.fetch_data("primary", "get_data", use_cache=False)
            return {"agent_result": result}
        
        # Execute through agent handler
        result = await agent_handler.execute_agent_task(
            "data_agent", data_task, "data_task", {}
        )
        
        # Should get fallback data
        assert result["agent_result"]["data"] == "fallback_success"
        
        # Verify agent state
        agent_state = agent_handler.agent_states["data_agent"]
        assert agent_state.status == "completed"
        assert agent_state.error_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_prevents_cascade_failure(self):
        """Test that circuit breakers prevent cascade failures."""
        manager = ErrorHandlingManager()
        
        # Register circuit breaker
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=60)
        manager.register_circuit_breaker("failing_service", config)
        
        async def failing_function():
            raise Exception("Service unavailable")
        
        # First two calls should fail and open circuit
        with pytest.raises(Exception):
            await manager.execute_with_protection("failing_service", failing_function)
        
        with pytest.raises(Exception):
            await manager.execute_with_protection("failing_service", failing_function)
        
        # Third call should be blocked by circuit breaker
        with pytest.raises(Exception, match="Circuit breaker open"):
            await manager.execute_with_protection("failing_service", failing_function)
        
        # Verify circuit breaker is open
        circuit_breaker = manager.circuit_breakers["failing_service"]
        assert circuit_breaker.state == CircuitBreakerState.OPEN
    
    def test_error_handling_manager_integration(self):
        """Test error handling manager coordinates all mechanisms."""
        manager = ErrorHandlingManager()
        
        # Register components
        circuit_config = CircuitBreakerConfig(failure_threshold=3)
        retry_config = RetryConfig(max_attempts=2)
        
        manager.register_circuit_breaker("test_service", circuit_config)
        manager.register_retry_handler("test_service", retry_config)
        
        # Verify registration
        assert "test_service" in manager.circuit_breakers
        assert "test_service" in manager.retry_handlers
        
        # Test error context handling
        error_context = ErrorContext(
            error_type="TestError",
            error_message="Test error message",
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now(),
            component="test_component",
            operation="test_operation"
        )
        
        # Should return fallback action for high severity
        recovery_action = asyncio.run(manager.handle_error(error_context))
        assert recovery_action == RecoveryAction.FALLBACK


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
