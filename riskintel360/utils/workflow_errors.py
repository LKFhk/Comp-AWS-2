"""
Workflow-specific error handling and recovery mechanisms.

This module provides specialized error handling for workflow orchestration,
state management, and multi-agent coordination.
"""

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict

from .error_handling import (
    WorkflowStateManager, WorkflowCheckpoint, ErrorContext, 
    ErrorSeverity, RecoveryAction
)
from .agent_errors import AgentErrorHandler, AgentError

logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """Workflow execution states."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERING = "recovering"


class WorkflowErrorType(Enum):
    """Types of workflow errors."""
    ORCHESTRATION_ERROR = "orchestration_error"
    AGENT_COORDINATION_ERROR = "agent_coordination_error"
    STATE_CORRUPTION_ERROR = "state_corruption_error"
    TIMEOUT_ERROR = "timeout_error"
    DEPENDENCY_ERROR = "dependency_error"
    RESOURCE_EXHAUSTION_ERROR = "resource_exhaustion_error"


@dataclass
class WorkflowStep:
    """Individual workflow step definition."""
    step_id: str
    step_name: str
    agent_name: Optional[str]
    dependencies: List[str]
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    workflow_id: str
    workflow_name: str
    steps: List[WorkflowStep]
    max_execution_time: int = 7200  # 2 hours
    checkpoint_interval: int = 300   # 5 minutes
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class WorkflowExecutionContext:
    """Context for workflow execution."""
    
    def __init__(self, workflow_def: WorkflowDefinition):
        self.workflow_def = workflow_def
        self.state = WorkflowState.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.current_step: Optional[str] = None
        self.completed_steps: List[str] = []
        self.failed_steps: List[str] = []
        self.step_results: Dict[str, Any] = {}
        self.error_history: List[Dict[str, Any]] = []
        self.checkpoint_history: List[str] = []
        self.recovery_attempts: int = 0
        self.max_recovery_attempts: int = 3


class WorkflowErrorHandler:
    """
    Comprehensive workflow error handling and recovery system.
    
    Manages workflow execution, error recovery, state persistence,
    and coordination between multiple agents.
    """
    
    def __init__(self):
        self.state_manager = WorkflowStateManager()
        self.agent_handler = AgentErrorHandler()
        self.active_workflows: Dict[str, WorkflowExecutionContext] = {}
        self.workflow_locks: Dict[str, asyncio.Lock] = {}
    
    async def execute_workflow(
        self,
        workflow_def: WorkflowDefinition,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow with comprehensive error handling.
        
        Args:
            workflow_def: Workflow definition
            initial_data: Initial data for workflow execution
            
        Returns:
            Workflow execution results
        """
        workflow_id = workflow_def.workflow_id
        
        # Create execution context
        context = WorkflowExecutionContext(workflow_def)
        context.start_time = datetime.now()
        context.state = WorkflowState.RUNNING
        
        self.active_workflows[workflow_id] = context
        self.workflow_locks[workflow_id] = asyncio.Lock()
        
        try:
            # Check for existing checkpoint
            latest_checkpoint = await self.state_manager.get_latest_checkpoint(workflow_id)
            if latest_checkpoint:
                logger.info(f"Resuming workflow {workflow_id} from checkpoint")
                context = await self._restore_from_checkpoint(context, latest_checkpoint)
            
            # Execute workflow steps
            result = await self._execute_workflow_steps(context, initial_data or {})
            
            # Mark as completed
            context.state = WorkflowState.COMPLETED
            context.end_time = datetime.now()
            
            return {
                'workflow_id': workflow_id,
                'status': 'completed',
                'results': result,
                'execution_time': (context.end_time - context.start_time).total_seconds(),
                'steps_completed': len(context.completed_steps),
                'checkpoints_created': len(context.checkpoint_history)
            }
        
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            context.state = WorkflowState.FAILED
            context.end_time = datetime.now()
            
            # Record error
            context.error_history.append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'error_type': type(e).__name__,
                'current_step': context.current_step
            })
            
            # Attempt recovery
            if context.recovery_attempts < context.max_recovery_attempts:
                logger.info(f"Attempting recovery for workflow {workflow_id}")
                return await self._attempt_workflow_recovery(context, e)
            else:
                logger.error(f"Max recovery attempts exceeded for workflow {workflow_id}")
                raise e
        
        finally:
            # Cleanup
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            if workflow_id in self.workflow_locks:
                del self.workflow_locks[workflow_id]
    
    async def _execute_workflow_steps(
        self,
        context: WorkflowExecutionContext,
        workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute all workflow steps with dependency management."""
        workflow_def = context.workflow_def
        steps_by_id = {step.step_id: step for step in workflow_def.steps}
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(workflow_def.steps)
        
        # Execute steps in dependency order
        while len(context.completed_steps) < len(workflow_def.steps):
            # Find ready steps (dependencies satisfied)
            ready_steps = self._get_ready_steps(
                workflow_def.steps, 
                context.completed_steps, 
                context.failed_steps
            )
            
            if not ready_steps:
                if context.failed_steps:
                    raise Exception(f"Workflow blocked by failed steps: {context.failed_steps}")
                else:
                    raise Exception("No ready steps found - possible circular dependency")
            
            # Execute ready steps in parallel
            step_tasks = []
            for step_id in ready_steps:
                step = steps_by_id[step_id]
                task = self._execute_step_with_recovery(context, step, workflow_data)
                step_tasks.append((step_id, task))
            
            # Wait for step completion
            for step_id, task in step_tasks:
                try:
                    result = await task
                    context.step_results[step_id] = result
                    context.completed_steps.append(step_id)
                    
                    # Update workflow data with step results
                    if isinstance(result, dict):
                        workflow_data.update(result)
                    
                    logger.info(f"Step {step_id} completed successfully")
                
                except Exception as e:
                    logger.error(f"Step {step_id} failed: {e}")
                    context.failed_steps.append(step_id)
                    
                    # Record step error
                    steps_by_id[step_id].error = str(e)
                    steps_by_id[step_id].status = "failed"
                    
                    # Check if this is a critical step
                    if self._is_critical_step(step_id, workflow_def):
                        raise Exception(f"Critical step {step_id} failed: {e}")
            
            # Create checkpoint periodically
            if self._should_create_checkpoint(context):
                await self._create_workflow_checkpoint(context, workflow_data)
        
        return workflow_data
    
    async def _execute_step_with_recovery(
        self,
        context: WorkflowExecutionContext,
        step: WorkflowStep,
        workflow_data: Dict[str, Any]
    ) -> Any:
        """Execute a single step with error handling and recovery."""
        step.start_time = datetime.now()
        step.status = "running"
        context.current_step = step.step_id
        
        try:
            # Set timeout for step execution
            result = await asyncio.wait_for(
                self._execute_single_step(step, workflow_data),
                timeout=step.timeout_seconds
            )
            
            step.status = "completed"
            step.end_time = datetime.now()
            step.result = result
            
            return result
        
        except asyncio.TimeoutError:
            step.status = "timeout"
            step.error = f"Step timed out after {step.timeout_seconds} seconds"
            
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                logger.warning(f"Step {step.step_id} timed out, retrying ({step.retry_count}/{step.max_retries})")
                await asyncio.sleep(min(2 ** step.retry_count, 30))  # Exponential backoff
                return await self._execute_step_with_recovery(context, step, workflow_data)
            else:
                raise Exception(f"Step {step.step_id} failed after {step.max_retries} timeout retries")
        
        except Exception as e:
            step.status = "error"
            step.error = str(e)
            step.end_time = datetime.now()
            
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                logger.warning(f"Step {step.step_id} failed, retrying ({step.retry_count}/{step.max_retries}): {e}")
                await asyncio.sleep(min(2 ** step.retry_count, 30))  # Exponential backoff
                return await self._execute_step_with_recovery(context, step, workflow_data)
            else:
                logger.error(f"Step {step.step_id} failed after {step.max_retries} retries: {e}")
                raise e
    
    async def _execute_single_step(self, step: WorkflowStep, workflow_data: Dict[str, Any]) -> Any:
        """Execute a single workflow step."""
        if step.agent_name:
            # Execute through agent
            agent_task = self._get_agent_task_function(step.agent_name, step.step_name)
            return await self.agent_handler.execute_agent_task(
                step.agent_name,
                agent_task,
                step.step_name,
                workflow_data
            )
        else:
            # Execute as direct function call
            task_function = self._get_task_function(step.step_name)
            return await task_function(workflow_data)
    
    def _get_agent_task_function(self, agent_name: str, task_name: str) -> Callable:
        """Get the task function for an agent."""
        # This would map to actual agent methods
        async def mock_agent_task(data: Dict[str, Any]) -> Dict[str, Any]:
            logger.info(f"Executing {task_name} on {agent_name}")
            await asyncio.sleep(0.1)  # Simulate work
            return {'agent': agent_name, 'task': task_name, 'status': 'completed'}
        
        return mock_agent_task
    
    def _get_task_function(self, task_name: str) -> Callable:
        """Get the task function for a workflow step."""
        # This would map to actual task implementations
        async def mock_task(data: Dict[str, Any]) -> Dict[str, Any]:
            logger.info(f"Executing task {task_name}")
            await asyncio.sleep(0.1)  # Simulate work
            return {'task': task_name, 'status': 'completed'}
        
        return mock_task
    
    def _build_dependency_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """Build dependency graph from workflow steps."""
        graph = {}
        for step in steps:
            graph[step.step_id] = step.dependencies
        return graph
    
    def _get_ready_steps(
        self,
        steps: List[WorkflowStep],
        completed_steps: List[str],
        failed_steps: List[str]
    ) -> List[str]:
        """Get steps that are ready to execute (dependencies satisfied)."""
        ready = []
        
        for step in steps:
            if step.step_id in completed_steps or step.step_id in failed_steps:
                continue
            
            # Check if all dependencies are satisfied
            dependencies_satisfied = all(
                dep in completed_steps for dep in step.dependencies
            )
            
            if dependencies_satisfied:
                ready.append(step.step_id)
        
        return ready
    
    def _is_critical_step(self, step_id: str, workflow_def: WorkflowDefinition) -> bool:
        """Check if a step is critical for workflow completion."""
        # For now, consider all steps critical
        # This could be enhanced with step metadata
        return True
    
    def _should_create_checkpoint(self, context: WorkflowExecutionContext) -> bool:
        """Determine if a checkpoint should be created."""
        if not context.checkpoint_history:
            return True
        
        # Create checkpoint every 5 completed steps or 5 minutes
        steps_since_checkpoint = len(context.completed_steps) - len(context.checkpoint_history) * 5
        time_since_start = (datetime.now() - context.start_time).total_seconds()
        
        return steps_since_checkpoint >= 5 or time_since_start % context.workflow_def.checkpoint_interval < 60
    
    async def _create_workflow_checkpoint(
        self,
        context: WorkflowExecutionContext,
        workflow_data: Dict[str, Any]
    ):
        """Create a checkpoint for workflow recovery."""
        checkpoint_data = {
            'workflow_data': workflow_data,
            'step_results': context.step_results,
            'execution_context': {
                'state': context.state.value,
                'current_step': context.current_step,
                'recovery_attempts': context.recovery_attempts,
                'error_history': context.error_history
            }
        }
        
        checkpoint_id = await self.state_manager.create_checkpoint(
            workflow_id=context.workflow_def.workflow_id,
            state_data=checkpoint_data,
            completed_steps=context.completed_steps,
            current_step=context.current_step or "unknown",
            metadata={'checkpoint_type': 'workflow_progress'}
        )
        
        context.checkpoint_history.append(checkpoint_id)
        logger.info(f"Created checkpoint {checkpoint_id} for workflow {context.workflow_def.workflow_id}")
    
    async def _restore_from_checkpoint(
        self,
        context: WorkflowExecutionContext,
        checkpoint: WorkflowCheckpoint
    ) -> WorkflowExecutionContext:
        """Restore workflow context from checkpoint."""
        logger.info(f"Restoring workflow {context.workflow_def.workflow_id} from checkpoint {checkpoint.checkpoint_id}")
        
        # Restore basic state
        context.completed_steps = checkpoint.completed_steps.copy()
        context.current_step = checkpoint.current_step
        
        # Restore detailed state from checkpoint data
        if 'execution_context' in checkpoint.state_data:
            exec_context = checkpoint.state_data['execution_context']
            context.recovery_attempts = exec_context.get('recovery_attempts', 0)
            context.error_history = exec_context.get('error_history', [])
        
        if 'step_results' in checkpoint.state_data:
            context.step_results = checkpoint.state_data['step_results']
        
        context.state = WorkflowState.RECOVERING
        return context
    
    async def _attempt_workflow_recovery(
        self,
        context: WorkflowExecutionContext,
        error: Exception
    ) -> Dict[str, Any]:
        """Attempt to recover a failed workflow."""
        context.recovery_attempts += 1
        context.state = WorkflowState.RECOVERING
        
        logger.info(f"Recovery attempt {context.recovery_attempts} for workflow {context.workflow_def.workflow_id}")
        
        # Try to find a recovery checkpoint
        latest_checkpoint = await self.state_manager.get_latest_checkpoint(context.workflow_def.workflow_id)
        if latest_checkpoint:
            # Restore from checkpoint and retry
            context = await self._restore_from_checkpoint(context, latest_checkpoint)
            
            # Clear failed steps to retry them
            context.failed_steps = []
            
            # Reset step states
            for step in context.workflow_def.steps:
                if step.step_id not in context.completed_steps:
                    step.status = "pending"
                    step.retry_count = 0
                    step.error = None
            
            # Retry workflow execution
            workflow_data = latest_checkpoint.state_data.get('workflow_data', {})
            return await self._execute_workflow_steps(context, workflow_data)
        else:
            # No checkpoint available, restart from beginning
            logger.warning(f"No checkpoint found for workflow {context.workflow_def.workflow_id}, restarting")
            context.completed_steps = []
            context.failed_steps = []
            context.step_results = {}
            context.current_step = None
            
            return await self._execute_workflow_steps(context, {})
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow."""
        if workflow_id in self.active_workflows:
            context = self.active_workflows[workflow_id]
            context.state = WorkflowState.PAUSED
            
            # Create checkpoint before pausing
            await self._create_workflow_checkpoint(context, context.step_results)
            
            logger.info(f"Paused workflow {workflow_id}")
            return True
        return False
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow."""
        if workflow_id in self.active_workflows:
            context = self.active_workflows[workflow_id]
            if context.state == WorkflowState.PAUSED:
                context.state = WorkflowState.RUNNING
                logger.info(f"Resumed workflow {workflow_id}")
                return True
        return False
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow."""
        if workflow_id not in self.active_workflows:
            return None
        
        context = self.active_workflows[workflow_id]
        
        return {
            'workflow_id': workflow_id,
            'state': context.state.value,
            'current_step': context.current_step,
            'completed_steps': len(context.completed_steps),
            'total_steps': len(context.workflow_def.steps),
            'failed_steps': len(context.failed_steps),
            'recovery_attempts': context.recovery_attempts,
            'execution_time': (datetime.now() - context.start_time).total_seconds() if context.start_time else 0,
            'checkpoints_created': len(context.checkpoint_history),
            'error_count': len(context.error_history)
        }


# Global workflow error handler instance
workflow_error_handler = WorkflowErrorHandler()
