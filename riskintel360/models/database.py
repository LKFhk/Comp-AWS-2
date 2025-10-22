"""
Database schema definitions using SQLAlchemy.

This module provides SQLAlchemy ORM models that are compatible with both
PostgreSQL (local development) and Aurora Serverless (production).
"""

from datetime import datetime
from typing import Dict, Any, Optional
import json

from sqlalchemy import (
    Column, String, Text, DateTime, Float, Integer, Boolean,
    JSON, ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid


Base = declarative_base()


class TimestampMixin:
    """Mixin for adding timestamp fields to models."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ValidationRequestDB(Base, TimestampMixin):
    """
    Database model for validation requests.
    
    Stores validation requests with full audit trail and supports both
    PostgreSQL and Aurora Serverless deployments.
    """
    __tablename__ = 'validation_requests'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True)
    business_concept = Column(Text, nullable=False)
    target_market = Column(String(500), nullable=False)
    analysis_scope = Column(JSON, nullable=False, default=list)
    priority = Column(String(20), nullable=False, default='medium')
    deadline = Column(DateTime(timezone=True), nullable=True)
    custom_parameters = Column(JSON, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default='pending')
    
    # Relationships
    results = relationship("ValidationResultDB", back_populates="request", cascade="all, delete-orphan")
    workflow_states = relationship("WorkflowStateDB", back_populates="request", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_validation_requests_user_id', 'user_id'),
        Index('idx_validation_requests_status', 'status'),
        Index('idx_validation_requests_created_at', 'created_at'),
        Index('idx_validation_requests_priority', 'priority'),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name='check_priority'),
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')", name='check_status'),
    )
    
    @validates('analysis_scope')
    def validate_analysis_scope(self, key, value):
        """Validate analysis scope contains valid values."""
        if not isinstance(value, list):
            raise ValueError("Analysis scope must be a list")
        
        valid_scopes = {"market", "competitive", "financial", "risk", "customer", "synthesis"}
        invalid_scopes = set(value) - valid_scopes
        if invalid_scopes:
            raise ValueError(f"Invalid analysis scopes: {invalid_scopes}")
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'business_concept': self.business_concept,
            'target_market': self.target_market,
            'analysis_scope': self.analysis_scope,
            'priority': self.priority,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'custom_parameters': self.custom_parameters,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ValidationResultDB(Base, TimestampMixin):
    """
    Database model for validation results.
    
    Stores comprehensive validation results with support for large JSON payloads
    and efficient querying across both PostgreSQL and Aurora.
    """
    __tablename__ = 'validation_results'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(36), ForeignKey('validation_requests.id'), nullable=False, index=True)
    overall_score = Column(Float, nullable=False)
    confidence_level = Column(Float, nullable=False)
    
    # Analysis results stored as JSON for flexibility
    market_analysis = Column(JSON, nullable=True)
    competitive_analysis = Column(JSON, nullable=True)
    financial_analysis = Column(JSON, nullable=True)
    risk_analysis = Column(JSON, nullable=True)
    customer_analysis = Column(JSON, nullable=True)
    
    # Synthesis results
    strategic_recommendations = Column(JSON, nullable=False, default=list)
    key_insights = Column(JSON, nullable=False, default=list)
    success_factors = Column(JSON, nullable=False, default=list)
    
    # Metadata
    supporting_data = Column(JSON, nullable=False, default=dict)
    data_quality_score = Column(Float, nullable=False)
    analysis_completeness = Column(Float, nullable=False)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Relationships
    request = relationship("ValidationRequestDB", back_populates="results")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_validation_results_request_id', 'request_id'),
        Index('idx_validation_results_overall_score', 'overall_score'),
        Index('idx_validation_results_created_at', 'created_at'),
        CheckConstraint('overall_score >= 0 AND overall_score <= 100', name='check_overall_score'),
        CheckConstraint('confidence_level >= 0 AND confidence_level <= 1', name='check_confidence_level'),
        CheckConstraint('data_quality_score >= 0 AND data_quality_score <= 1', name='check_data_quality_score'),
        CheckConstraint('analysis_completeness >= 0 AND analysis_completeness <= 1', name='check_analysis_completeness'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'request_id': self.request_id,
            'overall_score': self.overall_score,
            'confidence_level': self.confidence_level,
            'market_analysis': self.market_analysis,
            'competitive_analysis': self.competitive_analysis,
            'financial_analysis': self.financial_analysis,
            'risk_analysis': self.risk_analysis,
            'customer_analysis': self.customer_analysis,
            'strategic_recommendations': self.strategic_recommendations,
            'key_insights': self.key_insights,
            'success_factors': self.success_factors,
            'supporting_data': self.supporting_data,
            'data_quality_score': self.data_quality_score,
            'analysis_completeness': self.analysis_completeness,
            'processing_time_seconds': self.processing_time_seconds,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class AgentMessageDB(Base, TimestampMixin):
    """
    Database model for inter-agent messages.
    
    Supports message queuing and delivery tracking for agent coordination.
    """
    __tablename__ = 'agent_messages'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = Column(String(255), nullable=False, index=True)
    recipient_id = Column(String(255), nullable=False, index=True)
    message_type = Column(String(50), nullable=False)
    content = Column(JSON, nullable=False)
    priority = Column(String(20), nullable=False, default='medium')
    correlation_id = Column(String(36), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    delivered = Column(Boolean, nullable=False, default=False)
    processed = Column(Boolean, nullable=False, default=False)
    
    # Indexes for message processing efficiency
    __table_args__ = (
        Index('idx_agent_messages_sender_id', 'sender_id'),
        Index('idx_agent_messages_recipient_id', 'recipient_id'),
        Index('idx_agent_messages_correlation_id', 'correlation_id'),
        Index('idx_agent_messages_message_type', 'message_type'),
        Index('idx_agent_messages_priority', 'priority'),
        Index('idx_agent_messages_delivered', 'delivered'),
        Index('idx_agent_messages_processed', 'processed'),
        Index('idx_agent_messages_expires_at', 'expires_at'),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name='check_message_priority'),
        CheckConstraint("message_type IN ('task_assignment', 'data_sharing', 'status_update', 'completion_notice', 'error_report', 'coordination_request')", name='check_message_type'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'message_type': self.message_type,
            'content': self.content,
            'priority': self.priority,
            'correlation_id': self.correlation_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'retry_count': self.retry_count,
            'delivered': self.delivered,
            'processed': self.processed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class WorkflowStateDB(Base, TimestampMixin):
    """
    Database model for workflow state tracking.
    
    Tracks the progress and state of validation workflows for monitoring
    and recovery purposes.
    """
    __tablename__ = 'workflow_states'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), nullable=False, unique=True, index=True)
    request_id = Column(String(36), ForeignKey('validation_requests.id'), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='pending')
    progress = Column(Float, nullable=False, default=0.0)
    active_agents = Column(JSON, nullable=False, default=list)
    completed_tasks = Column(JSON, nullable=False, default=list)
    pending_tasks = Column(JSON, nullable=False, default=list)
    error_count = Column(Integer, nullable=False, default=0)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    estimated_completion = Column(DateTime(timezone=True), nullable=True)
    
    # Additional workflow metadata
    agent_assignments = Column(JSON, nullable=False, default=dict)
    task_dependencies = Column(JSON, nullable=False, default=dict)
    error_log = Column(JSON, nullable=False, default=list)
    
    # Relationships
    request = relationship("ValidationRequestDB", back_populates="workflow_states")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_workflow_states_workflow_id', 'workflow_id'),
        Index('idx_workflow_states_request_id', 'request_id'),
        Index('idx_workflow_states_status', 'status'),
        Index('idx_workflow_states_last_activity', 'last_activity'),
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')", name='check_workflow_status'),
        CheckConstraint('progress >= 0 AND progress <= 1', name='check_progress'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'request_id': self.request_id,
            'status': self.status,
            'progress': self.progress,
            'active_agents': self.active_agents,
            'completed_tasks': self.completed_tasks,
            'pending_tasks': self.pending_tasks,
            'error_count': self.error_count,
            'last_activity': self.last_activity.isoformat(),
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'agent_assignments': self.agent_assignments,
            'task_dependencies': self.task_dependencies,
            'error_log': self.error_log,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class AgentStateDB(Base, TimestampMixin):
    """
    Database model for individual agent state tracking.
    
    Stores persistent state information for each agent to support
    learning and memory capabilities.
    """
    __tablename__ = 'agent_states'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(255), nullable=False, index=True)
    agent_type = Column(String(100), nullable=False, index=True)
    workflow_id = Column(String(36), nullable=False, index=True)
    state_data = Column(JSON, nullable=False, default=dict)
    memory_data = Column(JSON, nullable=False, default=dict)
    learning_data = Column(JSON, nullable=False, default=dict)
    performance_metrics = Column(JSON, nullable=False, default=dict)
    
    # Indexes for agent state queries
    __table_args__ = (
        Index('idx_agent_states_agent_id', 'agent_id'),
        Index('idx_agent_states_agent_type', 'agent_type'),
        Index('idx_agent_states_workflow_id', 'workflow_id'),
        UniqueConstraint('agent_id', 'workflow_id', name='uq_agent_workflow'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'workflow_id': self.workflow_id,
            'state_data': self.state_data,
            'memory_data': self.memory_data,
            'learning_data': self.learning_data,
            'performance_metrics': self.performance_metrics,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class ExternalDataSourceDB(Base, TimestampMixin):
    """
    Database model for tracking external data source usage and quality.
    
    Monitors external API usage, data quality, and availability for
    system optimization and fallback strategies.
    """
    __tablename__ = 'external_data_sources'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_name = Column(String(255), nullable=False, index=True)
    source_type = Column(String(100), nullable=False)
    endpoint_url = Column(String(1000), nullable=True)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    success_rate = Column(Float, nullable=False, default=1.0)
    average_response_time = Column(Float, nullable=True)
    data_quality_score = Column(Float, nullable=False, default=1.0)
    is_available = Column(Boolean, nullable=False, default=True)
    rate_limit_remaining = Column(Integer, nullable=True)
    rate_limit_reset = Column(DateTime(timezone=True), nullable=True)
    
    # Usage statistics
    total_requests = Column(Integer, nullable=False, default=0)
    successful_requests = Column(Integer, nullable=False, default=0)
    failed_requests = Column(Integer, nullable=False, default=0)
    
    # Configuration and metadata
    configuration = Column(JSON, nullable=False, default=dict)
    source_metadata = Column(JSON, nullable=False, default=dict)
    
    # Indexes for monitoring queries
    __table_args__ = (
        Index('idx_external_data_sources_source_name', 'source_name'),
        Index('idx_external_data_sources_source_type', 'source_type'),
        Index('idx_external_data_sources_is_available', 'is_available'),
        Index('idx_external_data_sources_last_accessed', 'last_accessed'),
        CheckConstraint('success_rate >= 0 AND success_rate <= 1', name='check_success_rate'),
        CheckConstraint('data_quality_score >= 0 AND data_quality_score <= 1', name='check_data_quality'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'source_name': self.source_name,
            'source_type': self.source_type,
            'endpoint_url': self.endpoint_url,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'success_rate': self.success_rate,
            'average_response_time': self.average_response_time,
            'data_quality_score': self.data_quality_score,
            'is_available': self.is_available,
            'rate_limit_remaining': self.rate_limit_remaining,
            'rate_limit_reset': self.rate_limit_reset.isoformat() if self.rate_limit_reset else None,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'configuration': self.configuration,
            'source_metadata': self.source_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
