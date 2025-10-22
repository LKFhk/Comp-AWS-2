"""
Agent Models for RiskIntel360 Platform
Data models for agent sessions, states, and communication.
"""

from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uuid


class SessionStatus(Enum):
    """Agent session status enumeration"""
    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class AgentType(Enum):
    """Agent type enumeration for RiskIntel360 fintech agents"""
    # Core fintech agents (exactly 5 as per Requirement 2.1)
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    RISK_ASSESSMENT = "risk_assessment"
    MARKET_ANALYSIS = "market_analysis"
    CUSTOMER_BEHAVIOR_INTELLIGENCE = "customer_behavior_intelligence"
    FRAUD_DETECTION = "fraud_detection"
    
    # Additional fintech agents
    KYC_VERIFICATION = "kyc_verification"
    
    # System agents
    SUPERVISOR = "supervisor"


class MessageType(Enum):
    """Agent message type enumeration"""
    TASK_ASSIGNMENT = "task_assignment"
    DATA_SHARING = "data_sharing"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"
    COMPLETION_NOTICE = "completion_notice"
    REQUEST_DATA = "request_data"
    PROVIDE_DATA = "provide_data"


class Priority(Enum):
    """Priority levels for tasks and messages"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentState(BaseModel):
    """Agent state data model"""
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: AgentType = Field(..., description="Type of agent")
    status: SessionStatus = Field(..., description="Current agent status")
    current_task: Optional[str] = Field(None, description="Current task being executed")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Task progress (0-1)")
    last_activity: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last activity timestamp")
    error_count: int = Field(0, ge=0, description="Number of errors encountered")
    memory_usage_mb: float = Field(0.0, ge=0.0, description="Current memory usage in MB")
    
    # Fintech-specific fields for RiskIntel360
    compliance_status: str = Field("unknown", description="Current compliance status")
    risk_score: float = Field(0.0, ge=0.0, le=1.0, description="Current risk score")
    fraud_alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Active fraud alerts")
    regulatory_updates: List[Dict[str, Any]] = Field(default_factory=list, description="Recent regulatory updates")
    ml_model_version: str = Field("v1.0", description="ML model version in use")
    
    @field_validator('agent_type', mode='before')
    @classmethod
    def validate_agent_type(cls, v):
        """Ensure agent_type is properly converted to enum"""
        if isinstance(v, str):
            return AgentType(v)
        return v
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        """Ensure status is properly converted to enum"""
        if isinstance(v, str):
            return SessionStatus(v)
        return v
    
    model_config = ConfigDict(use_enum_values=False)


class AgentSession(BaseModel):
    """Agent session data model"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique session identifier")
    agent_type: AgentType = Field(..., description="Type of agent for this session")
    user_id: str = Field(..., description="User who owns this session")
    status: SessionStatus = Field(SessionStatus.CREATED, description="Current session status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Session creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last update timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    state_data: Dict[str, Any] = Field(default_factory=dict, description="Session state data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")
    
    @field_validator('updated_at', mode='before')
    @classmethod
    def set_updated_at(cls, v):
        return datetime.now(UTC)
    
    @field_validator('agent_type', mode='before')
    @classmethod
    def validate_agent_type(cls, v):
        """Ensure agent_type is properly converted to enum"""
        if isinstance(v, str):
            return AgentType(v)
        return v
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        """Ensure status is properly converted to enum"""
        if isinstance(v, str):
            return SessionStatus(v)
        return v
    
    model_config = ConfigDict(use_enum_values=False)


class AgentMessage(BaseModel):
    """Agent communication message model"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique message identifier")
    sender_id: str = Field(..., description="Sender agent identifier")
    recipient_id: str = Field(..., description="Recipient agent identifier")
    message_type: MessageType = Field(..., description="Type of message")
    content: Dict[str, Any] = Field(..., description="Message content")
    priority: Priority = Field(Priority.MEDIUM, description="Message priority")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Message timestamp")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for message tracking")
    expires_at: Optional[datetime] = Field(None, description="Message expiration timestamp")
    
    @field_validator('message_type', mode='before')
    @classmethod
    def validate_message_type(cls, v):
        """Ensure message_type is properly converted to enum"""
        if isinstance(v, str):
            return MessageType(v)
        return v
    
    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority(cls, v):
        """Ensure priority is properly converted to enum"""
        if isinstance(v, str):
            return Priority(v)
        return v
    
    model_config = ConfigDict(use_enum_values=False)  # Keep enum objects for proper comparison
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum values as strings for serialization"""
        data = self.model_dump()
        data['message_type'] = self.message_type.value
        data['priority'] = self.priority.value
        return data


class TaskAssignment(BaseModel):
    """Task assignment model for agent coordination"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique task identifier")
    assigned_to: str = Field(..., description="Agent ID assigned to this task")
    task_type: str = Field(..., description="Type of task")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    priority: Priority = Field(Priority.MEDIUM, description="Task priority")
    deadline: Optional[datetime] = Field(None, description="Task deadline")
    dependencies: List[str] = Field(default_factory=list, description="List of dependent task IDs")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Task creation timestamp")
    
    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority(cls, v):
        """Ensure priority is properly converted to enum"""
        if isinstance(v, str):
            return Priority(v)
        return v
    
    model_config = ConfigDict(use_enum_values=False)


class AgentCapability(BaseModel):
    """Agent capability definition"""
    capability_id: str = Field(..., description="Unique capability identifier")
    name: str = Field(..., description="Capability name")
    description: str = Field(..., description="Capability description")
    input_schema: Dict[str, Any] = Field(..., description="Input data schema")
    output_schema: Dict[str, Any] = Field(..., description="Output data schema")
    execution_time_estimate: float = Field(..., ge=0.0, description="Estimated execution time in seconds")
    resource_requirements: Dict[str, Any] = Field(default_factory=dict, description="Resource requirements")


class AgentPerformanceMetrics(BaseModel):
    """Agent performance metrics"""
    agent_id: str = Field(..., description="Agent identifier")
    session_id: str = Field(..., description="Session identifier")
    tasks_completed: int = Field(0, ge=0, description="Number of tasks completed")
    tasks_failed: int = Field(0, ge=0, description="Number of tasks failed")
    average_response_time: float = Field(0.0, ge=0.0, description="Average response time in seconds")
    total_execution_time: float = Field(0.0, ge=0.0, description="Total execution time in seconds")
    memory_peak_mb: float = Field(0.0, ge=0.0, description="Peak memory usage in MB")
    error_rate: float = Field(0.0, ge=0.0, le=1.0, description="Error rate (0-1)")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last metrics update")
    
    model_config = ConfigDict(use_enum_values=True)


class WorkflowState(BaseModel):
    """Multi-agent workflow state"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique workflow identifier")
    user_id: str = Field(..., description="User who initiated the workflow")
    status: SessionStatus = Field(SessionStatus.CREATED, description="Workflow status")
    agent_sessions: List[str] = Field(default_factory=list, description="List of agent session IDs")
    current_phase: str = Field("initialization", description="Current workflow phase")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Overall workflow progress")
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Workflow start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Workflow completion timestamp")
    results: Dict[str, Any] = Field(default_factory=dict, description="Workflow results")
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        """Ensure status is properly converted to enum"""
        if isinstance(v, str):
            return SessionStatus(v)
        return v
    
    model_config = ConfigDict(use_enum_values=False)


class AgentHealthCheck(BaseModel):
    """Agent health check model"""
    agent_id: str = Field(..., description="Agent identifier")
    status: str = Field(..., description="Health status")
    last_heartbeat: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last heartbeat timestamp")
    response_time_ms: float = Field(..., ge=0.0, description="Response time in milliseconds")
    memory_usage_mb: float = Field(..., ge=0.0, description="Current memory usage in MB")
    cpu_usage_percent: float = Field(..., ge=0.0, le=100.0, description="CPU usage percentage")
    active_tasks: int = Field(0, ge=0, description="Number of active tasks")
    error_count: int = Field(0, ge=0, description="Recent error count")
    
    @property
    def is_healthy(self) -> bool:
        """Check if agent is healthy"""
        return (
            self.status == "healthy" and
            self.response_time_ms < 5000 and  # Less than 5 seconds
            self.memory_usage_mb < 500 and    # Less than 500MB
            self.cpu_usage_percent < 80       # Less than 80% CPU
        )
