"""
Agent-specific error handling and recovery mechanisms.

This module provides specialized error handling for AI agents including
model failures, communication errors, and workflow recovery.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from .error_handling import (
    ErrorHandlingManager, CircuitBreakerConfig, RetryConfig,
    WorkflowStateManager, ErrorContext, ErrorSeverity, RecoveryAction
)

logger = logging.getLogger(__name__)


class AgentErrorType(Enum):
    """Types of agent errors."""
    MODEL_ERROR = "model_error"
    COMMUNICATION_ERROR = "communication_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    RESOURCE_ERROR = "resource_error"
    WORKFLOW_ERROR = "workflow_error"


class AgentError(Exception):
    """Base exception for agent errors."""
    
    def __init__(self, message: str, agent_name: str, error_type: AgentErrorType):
        super().__init__(message)
        self.agent_name = agent_name
        self.error_type = error_type
        self.timestamp = datetime.now()


class ModelError(AgentError):
    """Model-specific error (Bedrock, API failures)."""
    
    def __init__(self, message: str, agent_name: str, model_name: Optional[str] = None):
        super().__init__(message, agent_name, AgentErrorType.MODEL_ERROR)
        self.model_name = model_name


class CommunicationError(AgentError):
    """Inter-agent communication error."""
    
    def __init__(self, message: str, sender_agent: str, recipient_agent: str):
        super().__init__(message, sender_agent, AgentErrorType.COMMUNICATION_ERROR)
        self.recipient_agent = recipient_agent


class WorkflowError(AgentError):
    """Workflow orchestration error."""
    
    def __init__(self, message: str, workflow_id: str, step: str):
        super().__init__(message, workflow_id, AgentErrorType.WORKFLOW_ERROR)
        self.step = step


@dataclass
class AgentState:
    """Agent state information."""
    agent_name: str
    status: str
    last_activity: datetime
    current_task: Optional[str] = None
    error_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AgentErrorHandler:
    """
    Specialized error handler for AI agents.
    
    Provides agent-specific error handling, recovery strategies,
    and workflow state management.
    """
    
    def __init__(self):
        self.error_manager = ErrorHandlingManager()
        self.workflow_manager = WorkflowStateManager()
        self.agent_states: Dict[str, AgentState] = {}
        self.model_fallbacks: Dict[str, List[str]] = {}
        self._setup_agent_error_handling()
    
    def _setup_agent_error_handling(self):
        """Setup error handling configurations for agents."""
        
        # Model circuit breakers
        model_circuit_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60,
            expected_exception=ModelError
        )
        
        # Communication circuit breakers
        comm_circuit_config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=30,
            expected_exception=CommunicationError
        )
        
        # Retry configurations
        model_retry_config = RetryConfig(
            max_attempts=3,
            base_delay=2.0,
            max_delay=60.0,
            backoff_multiplier=2.0
        )
        
        comm_retry_config = RetryConfig(
            max_attempts=2,
            base_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=1.5
        )
        
        # Register configurations
        self.error_manager.register_circuit_breaker("model", model_circuit_config)
        self.error_manager.register_circuit_breaker("communication", comm_circuit_config)
        
        self.error_manager.register_retry_handler("model", model_retry_config)
        self.error_manager.register_retry_handler("communication", comm_retry_config)
        
        # Setup model fallbacks
        self.model_fallbacks = {
            "claude-3-opus": ["claude-3-sonnet", "claude-3-haiku"],
            "claude-3-sonnet": ["claude-3-haiku", "claude-3-opus"],
            "claude-3-haiku": ["claude-3-sonnet"]
        }
    
    def register_agent(self, agent_name: str, initial_status: str = "idle"):
        """Register an agent for monitoring."""
        self.agent_states[agent_name] = AgentState(
            agent_name=agent_name,
            status=initial_status,
            last_activity=datetime.now()
        )
        logger.info(f"Registered agent: {agent_name}")
    
    async def execute_agent_task(
        self,
        agent_name: str,
        task_func: Callable,
        task_name: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute agent task with comprehensive error handling."""
        if agent_name not in self.agent_states:
            self.register_agent(agent_name)
        
        agent_state = self.agent_states[agent_name]
        agent_state.current_task = task_name
        agent_state.status = "running"
        agent_state.last_activity = datetime.now()
        
        try:
            # Execute with error protection
            result = await self.error_manager.execute_with_protection(
                agent_name, task_func, *args, **kwargs
            )
            
            # Update success state
            agent_state.status = "completed"
            agent_state.current_task = None
            agent_state.error_count = 0
            
            return result
        
        except Exception as e:
            # Update error state
            agent_state.error_count += 1
            agent_state.status = "error"
            
            # Handle specific error types
            if isinstance(e, ModelError):
                result = await self._handle_model_error(agent_name, e, task_func, *args, **kwargs)
                # Update state if recovery was successful
                if result and not (isinstance(result, dict) and result.get("status") == "degraded"):
                    agent_state.status = "completed"
                    agent_state.error_count = 0
                return result
            elif isinstance(e, CommunicationError):
                return await self._handle_communication_error(agent_name, e, task_func, *args, **kwargs)
            elif isinstance(e, WorkflowError):
                return await self._handle_workflow_error(agent_name, e, task_func, *args, **kwargs)
            else:
                # Generic error handling
                return await self._handle_generic_error(agent_name, e, task_func, *args, **kwargs)
    
    async def _handle_model_error(
        self,
        agent_name: str,
        error: ModelError,
        task_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Handle model-specific errors with fallback models."""
        logger.warning(f"Model error in {agent_name}: {error}")
        
        # Try fallback models
        if error.model_name and error.model_name in self.model_fallbacks:
            for fallback_model in self.model_fallbacks[error.model_name]:
                try:
                    logger.info(f"Trying fallback model {fallback_model} for {agent_name}")
                    
                    # Update kwargs with fallback model
                    fallback_kwargs = kwargs.copy()
                    fallback_kwargs['model_name'] = fallback_model
                    
                    result = await task_func(*args, **fallback_kwargs)
                    
                    logger.info(f"Fallback model {fallback_model} succeeded for {agent_name}")
                    return result
                
                except Exception as fallback_error:
                    logger.warning(f"Fallback model {fallback_model} failed: {fallback_error}")
                    continue
        
        # All models failed, return degraded response
        return await self._get_degraded_agent_response(agent_name, error)
    
    async def _handle_communication_error(
        self,
        agent_name: str,
        error: CommunicationError,
        task_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Handle inter-agent communication errors."""
        logger.warning(f"Communication error in {agent_name}: {error}")
        
        # Try alternative communication channels
        try:
            # Implement alternative communication logic here
            # For now, retry with exponential backoff
            await asyncio.sleep(2.0)
            return await task_func(*args, **kwargs)
        except Exception:
            # Return partial result or cached data
            return await self._get_cached_agent_result(agent_name, task_func.__name__)
    
    async def _handle_workflow_error(
        self,
        agent_name: str,
        error: WorkflowError,
        task_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Handle workflow orchestration errors."""
        logger.warning(f"Workflow error in {agent_name}: {error}")
        
        # Try to recover from checkpoint
        latest_checkpoint = await self.workflow_manager.get_latest_checkpoint(agent_name)
        if latest_checkpoint:
            logger.info(f"Attempting workflow recovery for {agent_name}")
            
            # Restore state and continue from checkpoint
            try:
                # This would need to be implemented based on specific workflow logic
                return await self._recover_from_checkpoint(latest_checkpoint, task_func, *args, **kwargs)
            except Exception as recovery_error:
                logger.error(f"Workflow recovery failed: {recovery_error}")
        
        # Restart workflow from beginning
        logger.info(f"Restarting workflow for {agent_name}")
        return await task_func(*args, **kwargs)
    
    async def _handle_generic_error(
        self,
        agent_name: str,
        error: Exception,
        task_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Handle generic errors."""
        logger.error(f"Generic error in {agent_name}: {error}")
        
        # Create error context
        error_context = ErrorContext(
            error_type=type(error).__name__,
            error_message=str(error),
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            component=agent_name,
            operation=task_func.__name__
        )
        
        # Get recovery action
        recovery_action = await self.error_manager.handle_error(error_context)
        
        if recovery_action == RecoveryAction.RETRY:
            await asyncio.sleep(1.0)
            return await task_func(*args, **kwargs)
        elif recovery_action == RecoveryAction.FALLBACK:
            return await self._get_degraded_agent_response(agent_name, error)
        elif recovery_action == RecoveryAction.ESCALATE:
            logger.critical(f"Escalating error in {agent_name}: {error}")
            raise error
        else:
            return await self._get_degraded_agent_response(agent_name, error)
    
    async def _get_degraded_agent_response(self, agent_name: str, error: Exception) -> Dict[str, Any]:
        """Get degraded response when agent fails."""
        logger.info(f"Generating degraded response for {agent_name}")
        
        return {
            'status': 'degraded',
            'agent': agent_name,
            'message': f'Agent temporarily unavailable: {str(error)}',
            'confidence': 0.1,
            'timestamp': datetime.now().isoformat(),
            'data': {}
        }
    
    async def _get_cached_agent_result(self, agent_name: str, operation: str) -> Optional[Dict[str, Any]]:
        """Get cached result for agent operation."""
        # This would integrate with the caching system
        logger.info(f"Attempting to get cached result for {agent_name}:{operation}")
        return None
    
    async def _recover_from_checkpoint(
        self,
        checkpoint,
        task_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Recover workflow from checkpoint."""
        # This would need specific implementation based on workflow structure
        logger.info(f"Recovering from checkpoint {checkpoint.checkpoint_id}")
        
        # For now, just retry the task
        return await task_func(*args, **kwargs)
    
    async def create_workflow_checkpoint(
        self,
        workflow_id: str,
        agent_states: Dict[str, Any],
        completed_steps: List[str],
        current_step: str
    ) -> str:
        """Create a checkpoint for workflow recovery."""
        return await self.workflow_manager.create_checkpoint(
            workflow_id=workflow_id,
            state_data=agent_states,
            completed_steps=completed_steps,
            current_step=current_step,
            metadata={'agents': list(agent_states.keys())}
        )
    
    def get_agent_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all agents."""
        health_status = {}
        
        for agent_name, state in self.agent_states.items():
            time_since_activity = (datetime.now() - state.last_activity).total_seconds()
            
            health_status[agent_name] = {
                'status': state.status,
                'current_task': state.current_task,
                'error_count': state.error_count,
                'last_activity': state.last_activity.isoformat(),
                'time_since_activity': time_since_activity,
                'is_healthy': state.error_count < 5 and time_since_activity < 3600,
                'metadata': state.metadata
            }
        
        return health_status
    
    async def reset_agent_state(self, agent_name: str):
        """Reset agent state after recovery."""
        if agent_name in self.agent_states:
            state = self.agent_states[agent_name]
            state.status = "idle"
            state.current_task = None
            state.error_count = 0
            state.last_activity = datetime.now()
            logger.info(f"Reset state for agent {agent_name}")


# Global agent error handler instance
agent_error_handler = AgentErrorHandler()
