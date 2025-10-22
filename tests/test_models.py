"""
Unit tests for RiskIntel360 Platform data models.

Tests cover Pydantic model validation, serialization, and database operations.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import json
import uuid

from riskintel360.models import (
    ValidationRequest, ValidationResult, AgentMessage, WorkflowState,
    Priority, MessageType, WorkflowStatus, MaturityLevel, IntensityLevel,
    MarketSize, Trend, Barrier, RegulatoryEnvironment, MarketAnalysisResult,
    Competitor, Advantage, Threat, CompetitiveAnalysisResult,
    FinancialProjection, FinancialAnalysisResult,
    RiskFactor, RiskAnalysisResult,
    CustomerSegment, CustomerAnalysisResult,
    Recommendation,
    ValidationRequestDB, ValidationResultDB, AgentMessageDB, WorkflowStateDB,
    PostgreSQLAdapter, HybridDataManager
)


class TestValidationRequest:
    """Test ValidationRequest Pydantic model."""
    
    def test_validation_request_creation(self):
        """Test creating a valid ValidationRequest."""
        request = ValidationRequest(
            user_id="user123",
            business_concept="AI-powered fitness app for seniors",
            target_market="Senior fitness market in North America",
            analysis_scope=["market", "competitive", "financial"],
            priority=Priority.HIGH
        )
        
        assert request.user_id == "user123"
        assert request.business_concept == "AI-powered fitness app for seniors"
        assert request.target_market == "Senior fitness market in North America"
        assert request.analysis_scope == ["market", "competitive", "financial"]
        assert request.priority == Priority.HIGH
        assert request.id is not None
        assert isinstance(request.created_at, datetime)
        assert isinstance(request.updated_at, datetime)
    
    def test_validation_request_default_values(self):
        """Test ValidationRequest with default values."""
        request = ValidationRequest(
            user_id="user123",
            business_concept="Test business concept",
            target_market="Test market"
        )
        
        assert request.priority == Priority.MEDIUM
        assert request.analysis_scope == ["market", "competitive", "financial", "risk", "customer"]
        assert request.custom_parameters == {}
        assert request.deadline is None
    
    def test_validation_request_invalid_analysis_scope(self):
        """Test ValidationRequest with invalid analysis scope."""
        with pytest.raises(ValueError, match="Invalid analysis scopes"):
            ValidationRequest(
                user_id="user123",
                business_concept="Test business concept",
                target_market="Test market",
                analysis_scope=["invalid_scope", "market"]
            )
    
    def test_validation_request_past_deadline(self):
        """Test ValidationRequest with past deadline."""
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        
        with pytest.raises(ValueError, match="Deadline must be in the future"):
            ValidationRequest(
                user_id="user123",
                business_concept="Test business concept",
                target_market="Test market",
                deadline=past_date
            )
    
    def test_validation_request_serialization(self):
        """Test ValidationRequest JSON serialization."""
        request = ValidationRequest(
            user_id="user123",
            business_concept="Test business concept",
            target_market="Test market"
        )
        
        # Test dict conversion
        request_dict = request.model_dump()
        assert isinstance(request_dict, dict)
        assert request_dict["user_id"] == "user123"
        
        # Test JSON serialization
        json_str = request.model_dump_json()
        assert isinstance(json_str, str)
        
        # Test deserialization
        parsed_request = ValidationRequest.model_validate_json(json_str)
        assert parsed_request.user_id == request.user_id
        assert parsed_request.business_concept == request.business_concept


class TestValidationResult:
    """Test ValidationResult Pydantic model."""
    
    def test_validation_result_creation(self):
        """Test creating a valid ValidationResult."""
        result = ValidationResult(
            request_id="req123",
            overall_score=85.5,
            confidence_level=0.9,
            data_quality_score=0.95,
            analysis_completeness=0.88
        )
        
        assert result.request_id == "req123"
        assert result.overall_score == 85.5
        assert result.confidence_level == 0.9
        assert result.data_quality_score == 0.95
        assert result.analysis_completeness == 0.88
        assert isinstance(result.generated_at, datetime)
    
    def test_validation_result_with_analysis(self):
        """Test ValidationResult with analysis components."""
        market_analysis = MarketAnalysisResult(
            confidence_score=0.85,
            market_size=MarketSize(
                total_addressable_market=1000000000.0,
                serviceable_addressable_market=100000000.0,
                serviceable_obtainable_market=10000000.0
            ),
            growth_trends=[
                Trend(
                    name="Digital health adoption",
                    direction="positive",
                    strength=0.8,
                    timeframe="2024-2026",
                    confidence=0.9
                )
            ]
        )
        
        result = ValidationResult(
            request_id="req123",
            overall_score=85.5,
            confidence_level=0.9,
            data_quality_score=0.95,
            analysis_completeness=0.88,
            market_analysis=market_analysis
        )
        
        assert result.market_analysis is not None
        assert result.market_analysis.confidence_score == 0.85
        assert result.market_analysis.market_size.total_addressable_market == 1000000000.0
    
    def test_validation_result_invalid_score(self):
        """Test ValidationResult with invalid overall score."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="Input should be less than or equal to 100"):
            ValidationResult(
                request_id="req123",
                overall_score=150.0,  # Invalid: > 100
                confidence_level=0.9,
                data_quality_score=0.95,
                analysis_completeness=0.88
            )


class TestAgentMessage:
    """Test AgentMessage Pydantic model."""
    
    def test_agent_message_creation(self):
        """Test creating a valid AgentMessage."""
        message = AgentMessage(
            sender_id="market_analysis_agent",
            recipient_id="synthesis_agent",
            message_type=MessageType.DATA_SHARING,
            content={"market_data": {"size": 1000000}},
            correlation_id="corr123"
        )
        
        assert message.sender_id == "market_analysis_agent"
        assert message.recipient_id == "synthesis_agent"
        assert message.message_type == MessageType.DATA_SHARING
        assert message.content == {"market_data": {"size": 1000000}}
        assert message.correlation_id == "corr123"
        assert message.priority == Priority.MEDIUM
        assert isinstance(message.timestamp, datetime)
    
    def test_agent_message_expiration_validation(self):
        """Test AgentMessage with invalid expiration time."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        with pytest.raises(ValueError, match="Expiration time must be after timestamp"):
            AgentMessage(
                sender_id="agent1",
                recipient_id="agent2",
                message_type=MessageType.STATUS_UPDATE,
                content={"status": "completed"},
                correlation_id="corr123",
                expires_at=past_time
            )


class TestWorkflowState:
    """Test WorkflowState Pydantic model."""
    
    def test_workflow_state_creation(self):
        """Test creating a valid WorkflowState."""
        state = WorkflowState(
            workflow_id="workflow123",
            request_id="req123",
            status=WorkflowStatus.IN_PROGRESS,
            progress=0.5,
            active_agents=["market_analysis", "regulatory_compliance"],
            completed_tasks=["task1", "task2"],
            pending_tasks=["task3", "task4"]
        )
        
        assert state.workflow_id == "workflow123"
        assert state.request_id == "req123"
        assert state.status == WorkflowStatus.IN_PROGRESS
        assert state.progress == 0.5
        assert state.active_agents == ["market_analysis", "regulatory_compliance"]
        assert state.completed_tasks == ["task1", "task2"]
        assert state.pending_tasks == ["task3", "task4"]


class TestAnalysisResultModels:
    """Test analysis result models."""
    
    def test_market_analysis_result(self):
        """Test MarketAnalysisResult model."""
        result = MarketAnalysisResult(
            confidence_score=0.85,
            market_size=MarketSize(
                total_addressable_market=1000000000.0,
                serviceable_addressable_market=100000000.0
            ),
            growth_trends=[
                Trend(
                    name="AI adoption",
                    direction="positive",
                    strength=0.9,
                    timeframe="2024-2026",
                    confidence=0.85
                )
            ],
            market_maturity=MaturityLevel.GROWTH,
            entry_barriers=[
                Barrier(
                    type="regulatory",
                    description="FDA approval required",
                    severity="high",
                    mitigation_strategies=["Early FDA engagement", "Regulatory consulting"]
                )
            ]
        )
        
        assert result.confidence_score == 0.85
        assert result.market_maturity == MaturityLevel.GROWTH
        assert len(result.growth_trends) == 1
        assert len(result.entry_barriers) == 1
    
    def test_competitive_analysis_result(self):
        """Test CompetitiveAnalysisResult model."""
        result = CompetitiveAnalysisResult(
            confidence_score=0.8,
            direct_competitors=[
                Competitor(
                    name="FitnessPal Senior",
                    market_share=0.15,
                    strengths=["Brand recognition", "Large user base"],
                    weaknesses=["Poor senior UX", "Limited AI features"],
                    positioning="Mass market fitness",
                    threat_level="medium"
                )
            ],
            competitive_intensity=IntensityLevel.MODERATE,
            competitive_advantages=[
                Advantage(
                    type="technology",
                    description="Advanced AI personalization",
                    sustainability="high",
                    impact="significant"
                )
            ]
        )
        
        assert result.confidence_score == 0.8
        assert result.competitive_intensity == IntensityLevel.MODERATE
        assert len(result.direct_competitors) == 1
        assert len(result.competitive_advantages) == 1


class TestDatabaseModels:
    """Test SQLAlchemy database models."""
    
    def test_validation_request_db_creation(self):
        """Test creating ValidationRequestDB instance."""
        db_request = ValidationRequestDB(
            user_id="user123",
            business_concept="Test business concept",
            target_market="Test market",
            analysis_scope=["market", "competitive"],
            priority="high"
        )
        
        assert db_request.user_id == "user123"
        assert db_request.business_concept == "Test business concept"
        assert db_request.analysis_scope == ["market", "competitive"]
        assert db_request.priority == "high"
    
    def test_validation_request_db_to_dict(self):
        """Test ValidationRequestDB to_dict method."""
        db_request = ValidationRequestDB(
            id="req123",
            user_id="user123",
            business_concept="Test business concept",
            target_market="Test market",
            analysis_scope=["market"],
            priority="medium"
        )
        
        result_dict = db_request.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["id"] == "req123"
        assert result_dict["user_id"] == "user123"
        assert result_dict["analysis_scope"] == ["market"]
    
    def test_validation_request_db_invalid_scope(self):
        """Test ValidationRequestDB with invalid analysis scope."""
        db_request = ValidationRequestDB(
            user_id="user123",
            business_concept="Test business concept",
            target_market="Test market"
        )
        
        with pytest.raises(ValueError, match="Invalid analysis scopes"):
            db_request.analysis_scope = ["invalid_scope"]
    
    def test_agent_message_db_creation(self):
        """Test creating AgentMessageDB instance."""
        db_message = AgentMessageDB(
            sender_id="agent1",
            recipient_id="agent2",
            message_type="data_sharing",
            content={"data": "test"},
            correlation_id="corr123"
        )
        
        assert db_message.sender_id == "agent1"
        assert db_message.recipient_id == "agent2"
        assert db_message.message_type == "data_sharing"
        assert db_message.content == {"data": "test"}
        # SQLAlchemy defaults are applied when saved to DB, not in memory
        # So we check if the field exists and can be set
        assert hasattr(db_message, 'delivered')
        assert hasattr(db_message, 'processed')
        
        # Test explicit setting
        db_message.delivered = False
        db_message.processed = False
        assert db_message.delivered is False
        assert db_message.processed is False


@pytest.mark.asyncio
class TestDataAccessAdapters:
    """Test data access adapters."""
    
    @pytest.fixture
    def sample_validation_request(self):
        """Create a sample ValidationRequest for testing."""
        return ValidationRequest(
            user_id="test_user",
            business_concept="Test AI fitness app",
            target_market="Senior fitness market",
            analysis_scope=["market", "competitive"],
            priority=Priority.HIGH
        )
    
    @pytest.fixture
    def sample_agent_message(self):
        """Create a sample AgentMessage for testing."""
        return AgentMessage(
            sender_id="market_agent",
            recipient_id="synthesis_agent",
            message_type=MessageType.DATA_SHARING,
            content={"market_size": 1000000},
            correlation_id="test_correlation"
        )
    
    async def test_hybrid_data_manager_initialization(self):
        """Test HybridDataManager initialization."""
        manager = HybridDataManager()
        assert manager.adapter is not None
        
        # Should use PostgreSQL adapter in test environment
        assert isinstance(manager.adapter, PostgreSQLAdapter)
    
    async def test_validation_request_operations(self, sample_validation_request):
        """Test validation request CRUD operations."""
        manager = HybridDataManager()
        
        # Note: This test would require a test database setup
        # For now, we'll test the model validation
        request_dict = sample_validation_request.model_dump()
        assert request_dict["user_id"] == "test_user"
        assert request_dict["business_concept"] == "Test AI fitness app"
    
    async def test_agent_message_operations(self, sample_agent_message):
        """Test agent message operations."""
        manager = HybridDataManager()
        
        # Test message serialization
        message_dict = sample_agent_message.model_dump()
        assert message_dict["sender_id"] == "market_agent"
        assert message_dict["recipient_id"] == "synthesis_agent"
        assert message_dict["content"] == {"market_size": 1000000}


class TestModelValidation:
    """Test model validation and edge cases."""
    
    def test_priority_enum_validation(self):
        """Test Priority enum validation."""
        # Valid priorities
        assert Priority.LOW == "low"
        assert Priority.MEDIUM == "medium"
        assert Priority.HIGH == "high"
        assert Priority.URGENT == "urgent"
        
        # Test in ValidationRequest
        request = ValidationRequest(
            user_id="user123",
            business_concept="Test concept",
            target_market="Test market",
            priority=Priority.URGENT
        )
        assert request.priority == Priority.URGENT
    
    def test_message_type_enum_validation(self):
        """Test MessageType enum validation."""
        # Valid message types
        assert MessageType.TASK_ASSIGNMENT == "task_assignment"
        assert MessageType.DATA_SHARING == "data_sharing"
        assert MessageType.STATUS_UPDATE == "status_update"
        assert MessageType.COMPLETION_NOTICE == "completion_notice"
        assert MessageType.ERROR_REPORT == "error_report"
        assert MessageType.COORDINATION_REQUEST == "coordination_request"
    
    def test_workflow_status_enum_validation(self):
        """Test WorkflowStatus enum validation."""
        # Valid workflow statuses
        assert WorkflowStatus.PENDING == "pending"
        assert WorkflowStatus.IN_PROGRESS == "in_progress"
        assert WorkflowStatus.COMPLETED == "completed"
        assert WorkflowStatus.FAILED == "failed"
        assert WorkflowStatus.CANCELLED == "cancelled"
    
    def test_model_field_validation(self):
        """Test various field validations."""
        # Test minimum length validation
        with pytest.raises(ValueError):
            ValidationRequest(
                user_id="user123",
                business_concept="short",  # Too short (min 10 chars)
                target_market="Test market"
            )
        
        # Test maximum length validation
        long_concept = "x" * 2001  # Too long (max 2000 chars)
        with pytest.raises(ValueError):
            ValidationRequest(
                user_id="user123",
                business_concept=long_concept,
                target_market="Test market"
            )
    
    def test_confidence_score_validation(self):
        """Test confidence score validation (0-1 range)."""
        # Valid confidence score
        result = MarketAnalysisResult(confidence_score=0.85)
        assert result.confidence_score == 0.85
        
        # Invalid confidence scores
        with pytest.raises(ValueError):
            MarketAnalysisResult(confidence_score=1.5)  # > 1
        
        with pytest.raises(ValueError):
            MarketAnalysisResult(confidence_score=-0.1)  # < 0


if __name__ == "__main__":
    pytest.main([__file__])
