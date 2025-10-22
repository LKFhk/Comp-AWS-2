"""
Error handling and recovery mechanisms for the RiskIntel360 platform.

This module provides comprehensive error handling capabilities including:
- Graceful degradation strategies
- Circuit breaker patterns
- Retry logic with exponential backoff
- Workflow state recovery
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import traceback

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for classification and handling."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryAction(Enum):
    """Available recovery actions for error scenarios."""
    RETRY = "retry"
    FALLBACK = "fallback"
    DEGRADE = "degrade"
    ESCALATE = "escalate"
    ABORT = "abort"


@dataclass
class ErrorContext:
    """Context information for error handling decisions."""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    timestamp: datetime
    component: str
    operation: str
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryStrategy:
    """Recovery strategy configuration."""
    action: RecoveryAction
    max_retries: int = 3
    backoff_multiplier: float = 2.0
    base_delay: float = 1.0
    max_delay: float = 60.0
    fallback_function: Optional[Callable] = None
    degraded_function: Optional[Callable] = None


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: Type[Exception] = Exception


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascade failures.
    
    The circuit breaker monitors failures and opens when threshold is exceeded,
    preventing further calls until recovery timeout expires.
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0
        
    def can_execute(self) -> bool:
        """Check if execution is allowed based on circuit breaker state."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful execution."""
        self.failure_count = 0
        self.success_count += 1
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.success_count = 0
    
    def record_failure(self, exception: Exception):
        """Record failed execution."""
        if isinstance(exception, self.config.expected_exception):
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout


class RetryConfig:
    """Configuration for retry logic."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter


class RetryHandler:
    """
    Retry handler with exponential backoff and jitter.
    
    Implements intelligent retry logic for transient failures with
    configurable backoff strategies.
    """
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        retryable_exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                return result
            except retryable_exceptions as e:
                last_exception = e
                if attempt == self.config.max_attempts - 1:
                    break
                
                delay = self._calculate_delay(attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt."""
        delay = self.config.base_delay * (self.config.backoff_multiplier ** attempt)
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay


@dataclass
class WorkflowCheckpoint:
    """Workflow state checkpoint for recovery."""
    checkpoint_id: str
    workflow_id: str
    timestamp: datetime
    state_data: Dict[str, Any]
    completed_steps: List[str]
    current_step: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowStateManager:
    """
    Manages workflow state and checkpoints for recovery.
    
    Provides checkpoint creation, state persistence, and recovery
    capabilities for long-running workflows.
    """
    
    def __init__(self, storage_backend: Optional[Any] = None):
        self.storage_backend = storage_backend
        self.checkpoints: Dict[str, WorkflowCheckpoint] = {}
    
    async def create_checkpoint(
        self,
        workflow_id: str,
        state_data: Dict[str, Any],
        completed_steps: List[str],
        current_step: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a workflow checkpoint."""
        checkpoint_id = f"{workflow_id}_{int(time.time())}"
        checkpoint = WorkflowCheckpoint(
            checkpoint_id=checkpoint_id,
            workflow_id=workflow_id,
            timestamp=datetime.now(),
            state_data=state_data.copy(),
            completed_steps=completed_steps.copy(),
            current_step=current_step,
            metadata=metadata or {}
        )
        
        self.checkpoints[checkpoint_id] = checkpoint
        
        if self.storage_backend:
            await self._persist_checkpoint(checkpoint)
        
        logger.info(f"Created checkpoint {checkpoint_id} for workflow {workflow_id}")
        return checkpoint_id
    
    async def restore_from_checkpoint(self, checkpoint_id: str) -> Optional[WorkflowCheckpoint]:
        """Restore workflow state from checkpoint."""
        if checkpoint_id in self.checkpoints:
            checkpoint = self.checkpoints[checkpoint_id]
            logger.info(f"Restored workflow {checkpoint.workflow_id} from checkpoint {checkpoint_id}")
            return checkpoint
        
        if self.storage_backend:
            checkpoint = await self._load_checkpoint(checkpoint_id)
            if checkpoint:
                self.checkpoints[checkpoint_id] = checkpoint
                return checkpoint
        
        logger.warning(f"Checkpoint {checkpoint_id} not found")
        return None
    
    async def get_latest_checkpoint(self, workflow_id: str) -> Optional[WorkflowCheckpoint]:
        """Get the latest checkpoint for a workflow."""
        workflow_checkpoints = [
            cp for cp in self.checkpoints.values()
            if cp.workflow_id == workflow_id
        ]
        
        if not workflow_checkpoints:
            return None
        
        return max(workflow_checkpoints, key=lambda cp: cp.timestamp)
    
    async def _persist_checkpoint(self, checkpoint: WorkflowCheckpoint):
        """Persist checkpoint to storage backend."""
        # Implementation depends on storage backend
        pass
    
    async def _load_checkpoint(self, checkpoint_id: str) -> Optional[WorkflowCheckpoint]:
        """Load checkpoint from storage backend."""
        # Implementation depends on storage backend
        return None


class GracefulDegradationManager:
    """
    Manages graceful degradation strategies for service failures.
    
    Provides fallback mechanisms and degraded service modes when
    primary services are unavailable.
    """
    
    def __init__(self):
        self.degradation_strategies: Dict[str, Callable] = {}
        self.service_status: Dict[str, bool] = {}
    
    def register_degradation_strategy(self, service_name: str, strategy: Callable):
        """Register a degradation strategy for a service."""
        self.degradation_strategies[service_name] = strategy
        logger.info(f"Registered degradation strategy for {service_name}")
    
    async def execute_with_degradation(
        self,
        service_name: str,
        primary_function: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with graceful degradation fallback."""
        try:
            result = await primary_function(*args, **kwargs) if asyncio.iscoroutinefunction(primary_function) else primary_function(*args, **kwargs)
            self.service_status[service_name] = True
            return result
        except Exception as e:
            logger.warning(f"Primary service {service_name} failed: {str(e)}")
            self.service_status[service_name] = False
            
            if service_name in self.degradation_strategies:
                logger.info(f"Executing degradation strategy for {service_name}")
                degraded_function = self.degradation_strategies[service_name]
                return await degraded_function(*args, **kwargs) if asyncio.iscoroutinefunction(degraded_function) else degraded_function(*args, **kwargs)
            else:
                raise e
    
    def get_service_status(self) -> Dict[str, bool]:
        """Get current status of all monitored services."""
        return self.service_status.copy()


class ErrorHandlingManager:
    """
    Central error handling manager that coordinates all error handling mechanisms.
    
    Provides a unified interface for error handling, recovery, and degradation
    across the entire platform.
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_handlers: Dict[str, RetryHandler] = {}
        self.workflow_state_manager = WorkflowStateManager()
        self.degradation_manager = GracefulDegradationManager()
        self.error_strategies: Dict[str, RecoveryStrategy] = {}
    
    def register_circuit_breaker(self, name: str, config: CircuitBreakerConfig):
        """Register a circuit breaker for a service."""
        self.circuit_breakers[name] = CircuitBreaker(config)
        logger.info(f"Registered circuit breaker for {name}")
    
    def register_retry_handler(self, name: str, config: RetryConfig):
        """Register a retry handler for a service."""
        self.retry_handlers[name] = RetryHandler(config)
        logger.info(f"Registered retry handler for {name}")
    
    def register_error_strategy(self, error_type: str, strategy: RecoveryStrategy):
        """Register an error recovery strategy."""
        self.error_strategies[error_type] = strategy
        logger.info(f"Registered error strategy for {error_type}")
    
    async def execute_with_protection(
        self,
        service_name: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with full error protection."""
        circuit_breaker = self.circuit_breakers.get(service_name)
        retry_handler = self.retry_handlers.get(service_name)
        
        # Check circuit breaker
        if circuit_breaker and not circuit_breaker.can_execute():
            raise Exception(f"Circuit breaker open for {service_name}")
        
        try:
            if retry_handler:
                result = await retry_handler.execute_with_retry(func, *args, **kwargs)
            else:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            if circuit_breaker:
                circuit_breaker.record_success()
            
            return result
        except Exception as e:
            if circuit_breaker:
                circuit_breaker.record_failure(e)
            
            # Try graceful degradation
            try:
                return await self.degradation_manager.execute_with_degradation(
                    service_name, func, *args, **kwargs
                )
            except Exception:
                raise e
    
    async def handle_error(self, error_context: ErrorContext) -> RecoveryAction:
        """Handle error based on registered strategies."""
        error_type = error_context.error_type
        
        if error_type in self.error_strategies:
            strategy = self.error_strategies[error_type]
            logger.info(f"Applying recovery strategy {strategy.action} for {error_type}")
            return strategy.action
        
        # Default strategy based on severity
        if error_context.severity == ErrorSeverity.CRITICAL:
            return RecoveryAction.ESCALATE
        elif error_context.severity == ErrorSeverity.HIGH:
            return RecoveryAction.FALLBACK
        elif error_context.severity == ErrorSeverity.MEDIUM:
            return RecoveryAction.RETRY
        else:
            return RecoveryAction.DEGRADE


# Global error handling manager instance
error_manager = ErrorHandlingManager()
