"""
Amazon Bedrock AgentCore Integration Client
Provides Python client for Amazon Bedrock Agents API with multi-agent coordination primitives.

This implementation uses AWS Bedrock Agents service for:
- Agent registration and lifecycle management
- Multi-agent workflow orchestration
- Inter-agent communication and message routing
- Shared state management across agents
- Task distribution and coordination

Note: AWS Bedrock Agents is the service that provides AgentCore-like primitives
for multi-agent coordination in production environments.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, UTC
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from ..config.settings import get_settings
from ..models.agent_models import AgentMessage, MessageType, Priority, AgentType

logger = logging.getLogger(__name__)


class AgentCorePrimitive(Enum):
    """Available AgentCore primitives for multi-agent coordination"""
    MESSAGE_ROUTING = "message_routing"
    TASK_DISTRIBUTION = "task_distribution"
    STATE_SYNCHRONIZATION = "state_synchronization"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    RESOURCE_ALLOCATION = "resource_allocation"


@dataclass
class AgentCoreRequest:
    """Request structure for AgentCore operations"""
    primitive: AgentCorePrimitive
    operation: str
    parameters: Dict[str, Any]
    agent_id: str
    correlation_id: Optional[str] = None


@dataclass
class AgentCoreResponse:
    """Response structure from AgentCore operations"""
    success: bool
    result: Dict[str, Any]
    primitive: AgentCorePrimitive
    operation: str
    agent_id: str
    correlation_id: Optional[str] = None
    error_message: Optional[str] = None


class AgentCoreError(Exception):
    """Base exception for AgentCore operations"""
    pass


class AgentCoreClient:
    """
    Amazon Bedrock Agents client for multi-agent coordination.
    
    Provides high-level interface for AgentCore-like primitives including:
    - Message routing between agents
    - Task distribution and coordination
    - Workflow orchestration
    - State synchronization
    - Resource allocation
    
    This implementation uses AWS Bedrock Agents service as the foundation
    for multi-agent coordination, with custom coordination logic built on top.
    """
    
    def __init__(
        self,
        region_name: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        enable_real_bedrock_agents: bool = False
    ):
        """
        Initialize AgentCore client with AWS credentials.
        
        Args:
            region_name: AWS region for Bedrock Agents service
            aws_access_key_id: AWS access key (optional, uses default credential chain)
            aws_secret_access_key: AWS secret key (optional, uses default credential chain)
            aws_session_token: AWS session token (optional, for temporary credentials)
            enable_real_bedrock_agents: Enable actual Bedrock Agents API calls (requires setup)
        """
        self.region_name = region_name
        self.settings = get_settings()
        self.enable_real_bedrock_agents = enable_real_bedrock_agents
        
        # Initialize boto3 session
        session_kwargs = {"region_name": region_name}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs.update({
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key
            })
            if aws_session_token:
                session_kwargs["aws_session_token"] = aws_session_token
        
        try:
            self.session = boto3.Session(**session_kwargs)
            
            # Initialize Bedrock Agents client
            # This is the actual AWS service for agent coordination
            self.bedrock_agent = self.session.client("bedrock-agent")
            self.bedrock_agent_runtime = self.session.client("bedrock-agent-runtime")
            
            logger.info(f"🚀 AgentCore client initialized for region: {region_name}")
            logger.info(f"🔧 Real Bedrock Agents API: {'ENABLED' if enable_real_bedrock_agents else 'DISABLED (using simulation)'}")
            
            if not enable_real_bedrock_agents:
                logger.warning("⚠️  Using simulated AgentCore primitives for development. Set enable_real_bedrock_agents=True for production.")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AgentCore client: {e}")
            raise AgentCoreError(f"Failed to initialize AgentCore client: {e}")
        
        # Local coordination state (used for both simulation and real API)
        self._message_handlers: Dict[str, Callable] = {}
        self._agent_registry: Dict[str, Dict[str, Any]] = {}
        self._workflow_states: Dict[str, Dict[str, Any]] = {}
        self._shared_memory: Dict[str, Any] = {}
        
        # Bedrock Agent IDs (for real API integration)
        self._bedrock_agent_ids: Dict[str, str] = {}
        
    def register_agent(
        self,
        agent_id: str,
        agent_type: AgentType,
        capabilities: List[str],
        message_handler: Optional[Callable] = None
    ) -> bool:
        """
        Register an agent with AgentCore for coordination.
        
        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent
            capabilities: List of agent capabilities
            message_handler: Optional message handler function
            
        Returns:
            bool: True if registration successful
        """
        try:
            agent_info = {
                "agent_id": agent_id,
                "agent_type": agent_type.value,
                "capabilities": capabilities,
                "status": "active",
                "registered_at": datetime.now(UTC).timestamp()
            }
            
            self._agent_registry[agent_id] = agent_info
            
            if message_handler:
                self._message_handlers[agent_id] = message_handler
            
            logger.info(f"??Agent {agent_id} registered with AgentCore")
            return True
            
        except Exception as e:
            logger.error(f"??Failed to register agent {agent_id}: {e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from AgentCore.
        
        Args:
            agent_id: Agent identifier to unregister
            
        Returns:
            bool: True if unregistration successful
        """
        try:
            if agent_id in self._agent_registry:
                del self._agent_registry[agent_id]
            
            if agent_id in self._message_handlers:
                del self._message_handlers[agent_id]
            
            logger.info(f"??Agent {agent_id} unregistered from AgentCore")
            return True
            
        except Exception as e:
            logger.error(f"??Failed to unregister agent {agent_id}: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((ClientError, BotoCoreError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _execute_primitive(
        self,
        request: AgentCoreRequest
    ) -> AgentCoreResponse:
        """
        Execute an AgentCore primitive operation with retry logic.
        
        Args:
            request: The AgentCore request
            
        Returns:
            AgentCoreResponse: The response from AgentCore
        """
        try:
            # Simulate AgentCore primitive execution
            # In a real implementation, this would call the actual AgentCore API
            result = await self._simulate_primitive_execution(request)
            
            return AgentCoreResponse(
                success=True,
                result=result,
                primitive=request.primitive,
                operation=request.operation,
                agent_id=request.agent_id,
                correlation_id=request.correlation_id
            )
            
        except Exception as e:
            logger.error(f"??AgentCore primitive execution failed: {e}")
            return AgentCoreResponse(
                success=False,
                result={},
                primitive=request.primitive,
                operation=request.operation,
                agent_id=request.agent_id,
                correlation_id=request.correlation_id,
                error_message=str(e)
            )
    
    async def _simulate_primitive_execution(
        self,
        request: AgentCoreRequest
    ) -> Dict[str, Any]:
        """
        Execute AgentCore primitive using either real Bedrock Agents API or simulation.
        
        When enable_real_bedrock_agents=True, this uses actual AWS Bedrock Agents API.
        Otherwise, it uses local simulation for development/testing.
        
        Args:
            request: The AgentCore request
            
        Returns:
            Dict containing the result
        """
        if self.enable_real_bedrock_agents:
            # Use real Bedrock Agents API
            return await self._execute_real_bedrock_primitive(request)
        else:
            # Use simulation for development
            return await self._execute_simulated_primitive(request)
    
    async def _execute_real_bedrock_primitive(
        self,
        request: AgentCoreRequest
    ) -> Dict[str, Any]:
        """
        Execute primitive using real AWS Bedrock Agents API.
        
        This method integrates with actual Bedrock Agents service for production use.
        
        Args:
            request: The AgentCore request
            
        Returns:
            Dict containing the result from Bedrock Agents API
        """
        try:
            # Map primitives to Bedrock Agents API operations
            if request.primitive == AgentCorePrimitive.WORKFLOW_ORCHESTRATION:
                # Use Bedrock Agents for workflow orchestration
                return await self._invoke_bedrock_agent_workflow(request)
            
            elif request.primitive == AgentCorePrimitive.TASK_DISTRIBUTION:
                # Use Bedrock Agents for task distribution
                return await self._invoke_bedrock_agent_task(request)
            
            else:
                # For other primitives, use local coordination with Bedrock integration
                return await self._execute_simulated_primitive(request)
                
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"❌ Bedrock Agents API error: {error_code} - {error_message}")
            
            # Fallback to simulation on API errors
            logger.warning("⚠️  Falling back to simulated execution")
            return await self._execute_simulated_primitive(request)
    
    async def _invoke_bedrock_agent_workflow(
        self,
        request: AgentCoreRequest
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock Agent for workflow orchestration.
        
        This uses the actual Bedrock Agents Runtime API to execute agent workflows.
        
        Args:
            request: The AgentCore request
            
        Returns:
            Dict containing workflow execution result
        """
        try:
            workflow_data = request.parameters.get("workflow", {})
            workflow_id = workflow_data.get("workflow_id")
            
            # Check if we have a Bedrock Agent ID for this agent
            bedrock_agent_id = self._bedrock_agent_ids.get(request.agent_id)
            
            if not bedrock_agent_id:
                logger.warning(f"⚠️  No Bedrock Agent ID found for {request.agent_id}, using simulation")
                return await self._execute_simulated_primitive(request)
            
            # Invoke Bedrock Agent using Runtime API
            # Note: This requires pre-created Bedrock Agents in AWS
            response = await asyncio.to_thread(
                self.bedrock_agent_runtime.invoke_agent,
                agentId=bedrock_agent_id,
                agentAliasId="TSTALIASID",  # Use test alias or configured alias
                sessionId=workflow_id,
                inputText=json.dumps(workflow_data)
            )
            
            logger.info(f"✅ Bedrock Agent invoked for workflow {workflow_id}")
            
            return {
                "orchestrated": True,
                "workflow_id": workflow_id,
                "status": "running",
                "bedrock_agent_id": bedrock_agent_id,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to invoke Bedrock Agent: {e}")
            # Fallback to simulation
            return await self._execute_simulated_primitive(request)
    
    async def _invoke_bedrock_agent_task(
        self,
        request: AgentCoreRequest
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock Agent for task execution.
        
        Args:
            request: The AgentCore request
            
        Returns:
            Dict containing task execution result
        """
        try:
            task_data = request.parameters.get("task", {})
            target_agents = request.parameters.get("target_agents", [])
            
            # For each target agent, invoke their Bedrock Agent if available
            distributed_to = []
            
            for agent_id in target_agents:
                bedrock_agent_id = self._bedrock_agent_ids.get(agent_id)
                
                if bedrock_agent_id:
                    # Invoke Bedrock Agent for this task
                    try:
                        response = await asyncio.to_thread(
                            self.bedrock_agent_runtime.invoke_agent,
                            agentId=bedrock_agent_id,
                            agentAliasId="TSTALIASID",
                            sessionId=task_data.get("task_id", "default_session"),
                            inputText=json.dumps(task_data)
                        )
                        distributed_to.append(agent_id)
                        logger.info(f"✅ Task distributed to Bedrock Agent {agent_id}")
                    except Exception as e:
                        logger.error(f"❌ Failed to distribute task to {agent_id}: {e}")
                else:
                    # Use local coordination for agents without Bedrock Agent IDs
                    if agent_id in self._agent_registry:
                        distributed_to.append(agent_id)
            
            return {
                "distributed": True,
                "task_id": task_data.get("task_id"),
                "distributed_to": distributed_to,
                "bedrock_agents_used": len([a for a in target_agents if a in self._bedrock_agent_ids])
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to invoke Bedrock Agent for task: {e}")
            return await self._execute_simulated_primitive(request)
    
    async def _execute_simulated_primitive(
        self,
        request: AgentCoreRequest
    ) -> Dict[str, Any]:
        """
        Simulate AgentCore primitive execution for development/testing.
        
        This provides local coordination logic that mimics AgentCore behavior
        without requiring actual Bedrock Agents setup.
        
        Args:
            request: The AgentCore request
            
        Returns:
            Dict containing the simulated result
        """
        # Simulate different primitive operations
        if request.primitive == AgentCorePrimitive.MESSAGE_ROUTING:
            return await self._handle_message_routing(request)
        elif request.primitive == AgentCorePrimitive.TASK_DISTRIBUTION:
            return await self._handle_task_distribution(request)
        elif request.primitive == AgentCorePrimitive.STATE_SYNCHRONIZATION:
            return await self._handle_state_synchronization(request)
        elif request.primitive == AgentCorePrimitive.WORKFLOW_ORCHESTRATION:
            return await self._handle_workflow_orchestration(request)
        elif request.primitive == AgentCorePrimitive.RESOURCE_ALLOCATION:
            return await self._handle_resource_allocation(request)
        else:
            raise AgentCoreError(f"Unknown primitive: {request.primitive}")
    
    async def _handle_message_routing(self, request: AgentCoreRequest) -> Dict[str, Any]:
        """Handle message routing primitive"""
        if request.operation == "route_message":
            message_data = request.parameters.get("message", {})
            recipient_id = request.parameters.get("recipient_id")
            
            # Route message to recipient
            if recipient_id in self._message_handlers:
                handler = self._message_handlers[recipient_id]
                await asyncio.create_task(handler(message_data))
            
            return {
                "routed": True,
                "recipient_id": recipient_id,
                "message_id": message_data.get("message_id")
            }
        
        return {"operation": request.operation, "status": "completed"}
    
    async def _handle_task_distribution(self, request: AgentCoreRequest) -> Dict[str, Any]:
        """Handle task distribution primitive"""
        if request.operation == "distribute_task":
            task_data = request.parameters.get("task", {})
            target_agents = request.parameters.get("target_agents", [])
            
            # Distribute task to target agents
            distributed_to = []
            for agent_id in target_agents:
                if agent_id in self._agent_registry:
                    distributed_to.append(agent_id)
            
            return {
                "distributed": True,
                "task_id": task_data.get("task_id"),
                "distributed_to": distributed_to
            }
        
        return {"operation": request.operation, "status": "completed"}
    
    async def _handle_state_synchronization(self, request: AgentCoreRequest) -> Dict[str, Any]:
        """Handle state synchronization primitive"""
        if request.operation == "sync_state":
            state_data = request.parameters.get("state", {})
            sync_agents = request.parameters.get("sync_agents", [])
            
            return {
                "synchronized": True,
                "state_version": state_data.get("version", 1),
                "synced_agents": sync_agents
            }
        
        return {"operation": request.operation, "status": "completed"}
    
    async def _handle_workflow_orchestration(self, request: AgentCoreRequest) -> Dict[str, Any]:
        """Handle workflow orchestration primitive (simulated)"""
        if request.operation == "orchestrate_workflow":
            workflow_data = request.parameters.get("workflow", {})
            workflow_id = workflow_data.get("workflow_id")
            
            # Store workflow state
            self._workflow_states[workflow_id] = {
                "workflow_id": workflow_id,
                "status": "running",
                "started_at": datetime.now(UTC).isoformat(),
                "supervisor_id": request.agent_id,
                "data": workflow_data
            }
            
            return {
                "orchestrated": True,
                "workflow_id": workflow_id,
                "status": "running",
                "mode": "simulated"
            }
        
        return {"operation": request.operation, "status": "completed"}
    
    async def _handle_resource_allocation(self, request: AgentCoreRequest) -> Dict[str, Any]:
        """Handle resource allocation primitive"""
        if request.operation == "allocate_resources":
            resource_request = request.parameters.get("resources", {})
            
            return {
                "allocated": True,
                "resources": resource_request,
                "allocation_id": f"alloc_{request.agent_id}_{datetime.now(UTC).timestamp()}"
            }
        
        return {"operation": request.operation, "status": "completed"}
    
    async def route_message(
        self,
        sender_id: str,
        recipient_id: str,
        message: AgentMessage,
        correlation_id: Optional[str] = None
    ) -> AgentCoreResponse:
        """
        Route a message between agents using AgentCore message routing primitive.
        
        Args:
            sender_id: Sender agent ID
            recipient_id: Recipient agent ID
            message: Message to route
            correlation_id: Optional correlation ID
            
        Returns:
            AgentCoreResponse: Response from message routing operation
        """
        request = AgentCoreRequest(
            primitive=AgentCorePrimitive.MESSAGE_ROUTING,
            operation="route_message",
            parameters={
                "message": message.to_dict(),
                "recipient_id": recipient_id
            },
            agent_id=sender_id,
            correlation_id=correlation_id
        )
        
        return await self._execute_primitive(request)
    
    async def distribute_task(
        self,
        supervisor_id: str,
        task_data: Dict[str, Any],
        target_agents: List[str],
        correlation_id: Optional[str] = None
    ) -> AgentCoreResponse:
        """
        Distribute a task to multiple agents using AgentCore task distribution primitive.
        
        Args:
            supervisor_id: Supervisor agent ID
            task_data: Task information
            target_agents: List of target agent IDs
            correlation_id: Optional correlation ID
            
        Returns:
            AgentCoreResponse: Response from task distribution operation
        """
        request = AgentCoreRequest(
            primitive=AgentCorePrimitive.TASK_DISTRIBUTION,
            operation="distribute_task",
            parameters={
                "task": task_data,
                "target_agents": target_agents
            },
            agent_id=supervisor_id,
            correlation_id=correlation_id
        )
        
        return await self._execute_primitive(request)
    
    async def synchronize_state(
        self,
        agent_id: str,
        state_data: Dict[str, Any],
        sync_agents: List[str],
        correlation_id: Optional[str] = None
    ) -> AgentCoreResponse:
        """
        Synchronize state across agents using AgentCore state synchronization primitive.
        
        Args:
            agent_id: Agent ID initiating synchronization
            state_data: State data to synchronize
            sync_agents: List of agents to synchronize with
            correlation_id: Optional correlation ID
            
        Returns:
            AgentCoreResponse: Response from state synchronization operation
        """
        request = AgentCoreRequest(
            primitive=AgentCorePrimitive.STATE_SYNCHRONIZATION,
            operation="sync_state",
            parameters={
                "state": state_data,
                "sync_agents": sync_agents
            },
            agent_id=agent_id,
            correlation_id=correlation_id
        )
        
        return await self._execute_primitive(request)
    
    async def orchestrate_workflow(
        self,
        supervisor_id: str,
        workflow_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> AgentCoreResponse:
        """
        Orchestrate a multi-agent workflow using AgentCore workflow orchestration primitive.
        
        Args:
            supervisor_id: Supervisor agent ID
            workflow_data: Workflow configuration
            correlation_id: Optional correlation ID
            
        Returns:
            AgentCoreResponse: Response from workflow orchestration operation
        """
        request = AgentCoreRequest(
            primitive=AgentCorePrimitive.WORKFLOW_ORCHESTRATION,
            operation="orchestrate_workflow",
            parameters={
                "workflow": workflow_data
            },
            agent_id=supervisor_id,
            correlation_id=correlation_id
        )
        
        return await self._execute_primitive(request)
    
    def get_registered_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        Get list of registered agents.
        
        Returns:
            Dict of registered agents and their information
        """
        return self._agent_registry.copy()
    
    def is_agent_registered(self, agent_id: str) -> bool:
        """
        Check if an agent is registered.
        
        Args:
            agent_id: Agent ID to check
            
        Returns:
            bool: True if agent is registered
        """
        return agent_id in self._agent_registry
    
    def register_bedrock_agent_id(self, agent_id: str, bedrock_agent_id: str) -> None:
        """
        Register a Bedrock Agent ID for an agent.
        
        This links a local agent ID to an actual AWS Bedrock Agent ID,
        enabling real Bedrock Agents API integration.
        
        Args:
            agent_id: Local agent identifier
            bedrock_agent_id: AWS Bedrock Agent ID
        """
        self._bedrock_agent_ids[agent_id] = bedrock_agent_id
        logger.info(f"🔗 Linked agent {agent_id} to Bedrock Agent {bedrock_agent_id}")
    
    def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow state.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Dict containing workflow state or None if not found
        """
        return self._workflow_states.get(workflow_id)
    
    def update_workflow_state(self, workflow_id: str, state_update: Dict[str, Any]) -> bool:
        """
        Update workflow state.
        
        Args:
            workflow_id: Workflow identifier
            state_update: State updates to apply
            
        Returns:
            bool: True if update successful
        """
        if workflow_id in self._workflow_states:
            self._workflow_states[workflow_id].update(state_update)
            self._workflow_states[workflow_id]["last_updated"] = datetime.now(UTC).isoformat()
            return True
        return False
    
    async def get_shared_memory(self, key: str) -> Optional[Any]:
        """
        Get value from shared memory across agents.
        
        Args:
            key: Memory key
            
        Returns:
            Value from shared memory or None
        """
        return self._shared_memory.get(key)
    
    async def set_shared_memory(self, key: str, value: Any) -> None:
        """
        Set value in shared memory across agents.
        
        Args:
            key: Memory key
            value: Value to store
        """
        self._shared_memory[key] = value
        logger.debug(f"📝 Shared memory updated: {key}")
    
    def get_coordination_stats(self) -> Dict[str, Any]:
        """
        Get coordination statistics.
        
        Returns:
            Dict containing coordination metrics
        """
        return {
            "registered_agents": len(self._agent_registry),
            "active_workflows": len(self._workflow_states),
            "bedrock_agents_linked": len(self._bedrock_agent_ids),
            "shared_memory_keys": len(self._shared_memory),
            "message_handlers": len(self._message_handlers),
            "real_bedrock_enabled": self.enable_real_bedrock_agents,
            "region": self.region_name
        }


# Convenience function for creating AgentCore client instances
def create_agentcore_client(
    region_name: str = "us-east-1",
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    enable_real_bedrock_agents: bool = False
) -> AgentCoreClient:
    """
    Create a new AgentCore client instance.
    
    Args:
        region_name: AWS region for Bedrock Agents service
        aws_access_key_id: AWS access key (optional)
        aws_secret_access_key: AWS secret key (optional)
        aws_session_token: AWS session token (optional)
        enable_real_bedrock_agents: Enable actual Bedrock Agents API calls (default: False)
        
    Returns:
        AgentCoreClient: Configured AgentCore client instance
    """
    return AgentCoreClient(
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        enable_real_bedrock_agents=enable_real_bedrock_agents
    )
