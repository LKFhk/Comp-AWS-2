"""
Core data models for the RiskIntel360 platform.

This module contains the primary data structures used throughout the system,
including ValidationRequest, ValidationResult, and AgentMessage models.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict


class Priority(str, Enum):
    """Priority levels for validation requests and messages."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MessageType(str, Enum):
    """Types of messages exchanged between agents."""
    TASK_ASSIGNMENT = "task_assignment"
    DATA_SHARING = "data_sharing"
    STATUS_UPDATE = "status_update"
    COMPLETION_NOTICE = "completion_notice"
    ERROR_REPORT = "error_report"
    COORDINATION_REQUEST = "coordination_request"
    ANALYSIS_RESULT = "analysis_result"


class WorkflowStatus(str, Enum):
    """Status of validation workflows."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MaturityLevel(str, Enum):
    """Market maturity levels."""
    EMERGING = "emerging"
    GROWTH = "growth"
    MATURE = "mature"
    DECLINING = "declining"


class IntensityLevel(str, Enum):
    """Competitive intensity levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class ValidationRequest(BaseModel):
    """
    Represents a business validation request submitted by users.
    
    This model captures all necessary information to initiate a comprehensive
    business validation workflow across multiple AI agents.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique request identifier")
    user_id: str = Field(..., description="ID of the user submitting the request")
    business_concept: str = Field(..., min_length=10, max_length=2000, description="Description of the business concept to validate")
    target_market: str = Field(..., min_length=2, max_length=500, description="Target market or industry")
    analysis_scope: List[str] = Field(
        default=["market", "competitive", "financial", "risk", "customer"],
        description="Types of analysis to perform"
    )
    priority: Priority = Field(default=Priority.MEDIUM, description="Request priority level")
    deadline: Optional[datetime] = Field(None, description="Optional deadline for completion")
    custom_parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional custom parameters")
    status: Optional[WorkflowStatus] = Field(None, description="Current workflow status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Request creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    
    @field_validator('analysis_scope')
    @classmethod
    def validate_analysis_scope(cls, v):
        """Validate that analysis scope contains valid analysis types."""
        valid_scopes = {
            # Original analysis scopes
            "market", "competitive", "financial", "risk", "customer", "synthesis",
            # Enhanced fintech-specific analysis scopes
            "regulatory_compliance", "fraud_detection", "market_intelligence", 
            "risk_assessment", "kyc_verification"
        }
        invalid_scopes = set(v) - valid_scopes
        if invalid_scopes:
            raise ValueError(f"Invalid analysis scopes: {invalid_scopes}")
        return v
    
    @field_validator('deadline')
    @classmethod
    def validate_deadline(cls, v):
        """Ensure deadline is in the future if provided."""
        if v and v <= datetime.now(timezone.utc):
            raise ValueError("Deadline must be in the future")
        return v


class MarketSize(BaseModel):
    """Market size information."""
    total_addressable_market: Optional[float] = Field(None, description="TAM in USD")
    serviceable_addressable_market: Optional[float] = Field(None, description="SAM in USD")
    serviceable_obtainable_market: Optional[float] = Field(None, description="SOM in USD")
    currency: str = Field(default="USD", description="Currency for market size figures")
    year: int = Field(default_factory=lambda: datetime.now(timezone.utc).year, description="Year of market size data")


class Trend(BaseModel):
    """Market or industry trend information."""
    name: str = Field(..., description="Trend name or description")
    direction: str = Field(..., description="Trend direction (positive, negative, neutral)")
    strength: float = Field(..., ge=0, le=1, description="Trend strength (0-1)")
    timeframe: str = Field(..., description="Timeframe for the trend")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in trend analysis")


class Barrier(BaseModel):
    """Market entry barrier information."""
    type: str = Field(..., description="Type of barrier (regulatory, financial, technical, etc.)")
    description: str = Field(..., description="Detailed description of the barrier")
    severity: str = Field(..., description="Severity level (low, medium, high)")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Potential mitigation strategies")


class RegulatoryEnvironment(BaseModel):
    """Regulatory environment information."""
    jurisdiction: str = Field(..., description="Regulatory jurisdiction")
    complexity: str = Field(..., description="Regulatory complexity level")
    key_regulations: List[str] = Field(default_factory=list, description="Key applicable regulations")
    compliance_requirements: List[str] = Field(default_factory=list, description="Compliance requirements")
    regulatory_risk: str = Field(..., description="Overall regulatory risk level")


class MarketAnalysisResult(BaseModel):
    """Results from market research agent analysis."""
    market_size: Optional[MarketSize] = Field(None, description="Market size analysis")
    growth_trends: List[Trend] = Field(default_factory=list, description="Identified market trends")
    key_drivers: List[str] = Field(default_factory=list, description="Key market drivers")
    market_maturity: Optional[MaturityLevel] = Field(None, description="Market maturity level")
    entry_barriers: List[Barrier] = Field(default_factory=list, description="Market entry barriers")
    regulatory_environment: Optional[RegulatoryEnvironment] = Field(None, description="Regulatory environment")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in analysis results")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used in analysis")
    analysis_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Analysis completion time")


class Competitor(BaseModel):
    """Competitor information."""
    name: str = Field(..., description="Competitor name")
    market_share: Optional[float] = Field(None, ge=0, le=1, description="Market share (0-1)")
    strengths: List[str] = Field(default_factory=list, description="Competitor strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Competitor weaknesses")
    positioning: str = Field(..., description="Market positioning")
    threat_level: str = Field(..., description="Threat level (low, medium, high)")


class Advantage(BaseModel):
    """Competitive advantage information."""
    type: str = Field(..., description="Type of advantage")
    description: str = Field(..., description="Advantage description")
    sustainability: str = Field(..., description="Sustainability of advantage")
    impact: str = Field(..., description="Impact level")


class Threat(BaseModel):
    """Competitive threat information."""
    source: str = Field(..., description="Source of threat")
    description: str = Field(..., description="Threat description")
    probability: float = Field(..., ge=0, le=1, description="Probability of threat materializing")
    impact: str = Field(..., description="Potential impact level")


class CompetitiveAnalysisResult(BaseModel):
    """Results from competitive intelligence agent analysis."""
    direct_competitors: List[Competitor] = Field(default_factory=list, description="Direct competitors")
    indirect_competitors: List[Competitor] = Field(default_factory=list, description="Indirect competitors")
    competitive_intensity: Optional[IntensityLevel] = Field(None, description="Overall competitive intensity")
    competitive_advantages: List[Advantage] = Field(default_factory=list, description="Identified competitive advantages")
    threats: List[Threat] = Field(default_factory=list, description="Competitive threats")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in analysis results")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used in analysis")
    analysis_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Analysis completion time")


class FinancialProjection(BaseModel):
    """Financial projection data."""
    revenue_projection: Dict[str, float] = Field(default_factory=dict, description="Revenue projections by year")
    cost_structure: Dict[str, float] = Field(default_factory=dict, description="Cost structure breakdown")
    investment_required: float = Field(..., description="Total investment required")
    break_even_period: Optional[int] = Field(None, description="Break-even period in months")
    roi_projection: Optional[float] = Field(None, description="ROI projection")


class FinancialAnalysisResult(BaseModel):
    """Results from financial validation agent analysis."""
    financial_projections: Optional[FinancialProjection] = Field(None, description="Financial projections")
    viability_score: float = Field(..., ge=0, le=1, description="Financial viability score")
    key_assumptions: List[str] = Field(default_factory=list, description="Key financial assumptions")
    sensitivity_analysis: Dict[str, Any] = Field(default_factory=dict, description="Sensitivity analysis results")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in analysis results")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used in analysis")
    analysis_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Analysis completion time")


class RiskFactor(BaseModel):
    """Risk factor information."""
    category: str = Field(..., description="Risk category")
    description: str = Field(..., description="Risk description")
    probability: float = Field(..., ge=0, le=1, description="Risk probability")
    impact: str = Field(..., description="Risk impact level")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Mitigation strategies")


class RiskAnalysisResult(BaseModel):
    """Results from risk assessment agent analysis."""
    risk_factors: List[RiskFactor] = Field(default_factory=list, description="Identified risk factors")
    overall_risk_score: float = Field(..., ge=0, le=1, description="Overall risk score")
    risk_categories: Dict[str, float] = Field(default_factory=dict, description="Risk scores by category")
    mitigation_recommendations: List[str] = Field(default_factory=list, description="Risk mitigation recommendations")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in analysis results")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used in analysis")
    analysis_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Analysis completion time")


class CustomerSegment(BaseModel):
    """Customer segment information."""
    name: str = Field(..., description="Segment name")
    size: Optional[int] = Field(None, description="Segment size")
    characteristics: List[str] = Field(default_factory=list, description="Segment characteristics")
    needs: List[str] = Field(default_factory=list, description="Customer needs")
    pain_points: List[str] = Field(default_factory=list, description="Customer pain points")


class CustomerAnalysisResult(BaseModel):
    """Results from customer intelligence agent analysis."""
    customer_segments: List[CustomerSegment] = Field(default_factory=list, description="Identified customer segments")
    market_demand_score: float = Field(..., ge=0, le=1, description="Market demand score")
    sentiment_analysis: Dict[str, Any] = Field(default_factory=dict, description="Sentiment analysis results")
    customer_feedback: List[str] = Field(default_factory=list, description="Key customer feedback themes")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in analysis results")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used in analysis")
    analysis_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Analysis completion time")


class Recommendation(BaseModel):
    """Strategic recommendation."""
    category: str = Field(..., description="Recommendation category")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed recommendation description")
    priority: Priority = Field(..., description="Recommendation priority")
    implementation_steps: List[str] = Field(default_factory=list, description="Implementation steps")
    expected_impact: str = Field(..., description="Expected impact")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in recommendation")


class ValidationResult(BaseModel):
    """
    Complete validation result containing analysis from all agents.
    
    This model represents the final output of the multi-agent validation workflow,
    consolidating insights from all specialized agents into actionable recommendations.
    """
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True
    )
    
    request_id: str = Field(..., description="ID of the original validation request")
    overall_score: float = Field(..., ge=0, le=100, description="Overall business viability score (0-100)")
    confidence_level: float = Field(..., ge=0, le=1, description="Confidence in overall analysis (0-1)")
    
    # Agent-specific results
    market_analysis: Optional[MarketAnalysisResult] = Field(None, description="Market research results")
    competitive_analysis: Optional[CompetitiveAnalysisResult] = Field(None, description="Competitive intelligence results")
    financial_analysis: Optional[FinancialAnalysisResult] = Field(None, description="Financial validation results")
    risk_analysis: Optional[RiskAnalysisResult] = Field(None, description="Risk assessment results")
    customer_analysis: Optional[CustomerAnalysisResult] = Field(None, description="Customer intelligence results")
    
    # Synthesis results
    strategic_recommendations: List[Recommendation] = Field(default_factory=list, description="Strategic recommendations")
    key_insights: List[str] = Field(default_factory=list, description="Key insights from analysis")
    success_factors: List[str] = Field(default_factory=list, description="Critical success factors")
    
    # Metadata
    supporting_data: Dict[str, Any] = Field(default_factory=dict, description="Supporting data and evidence")
    data_quality_score: float = Field(..., ge=0, le=1, description="Overall data quality score")
    analysis_completeness: float = Field(..., ge=0, le=1, description="Analysis completeness score")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Result generation timestamp")
    processing_time_seconds: Optional[float] = Field(None, description="Total processing time in seconds")
    
    @field_validator('overall_score')
    @classmethod
    def validate_overall_score(cls, v):
        """Ensure overall score is within valid range."""
        if not 0 <= v <= 100:
            raise ValueError("Overall score must be between 0 and 100")
        return v


class AgentMessage(BaseModel):
    """
    Message structure for inter-agent communication.
    
    This model defines the protocol for agents to communicate with each other
    during the validation workflow, enabling coordination and data sharing.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique message identifier")
    sender_id: str = Field(..., description="ID of the sending agent")
    recipient_id: str = Field(..., description="ID of the receiving agent")
    message_type: MessageType = Field(..., description="Type of message")
    content: Dict[str, Any] = Field(..., description="Message content and data")
    priority: Priority = Field(default=Priority.MEDIUM, description="Message priority")
    correlation_id: str = Field(..., description="Correlation ID for request tracking")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Message timestamp")
    expires_at: Optional[datetime] = Field(None, description="Message expiration time")
    retry_count: int = Field(default=0, description="Number of delivery attempts")
    
    @field_validator('expires_at')
    @classmethod
    def validate_expiration(cls, v, info):
        """Ensure expiration time is after timestamp."""
        if v and info.data and 'timestamp' in info.data and v <= info.data['timestamp']:
            raise ValueError("Expiration time must be after timestamp")
        return v


class TaskDistribution(BaseModel):
    """Task distribution information for agent coordination."""
    workflow_id: str = Field(..., description="Workflow identifier")
    agent_assignments: Dict[str, List[str]] = Field(..., description="Agent task assignments")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Task dependencies")
    estimated_completion: datetime = Field(..., description="Estimated completion time")
    priority_order: List[str] = Field(..., description="Task execution priority order")


class WorkflowState(BaseModel):
    """Current state of a validation workflow."""
    workflow_id: str = Field(..., description="Workflow identifier")
    request_id: str = Field(..., description="Associated validation request ID")
    status: WorkflowStatus = Field(..., description="Current workflow status")
    progress: float = Field(..., ge=0, le=1, description="Completion progress (0-1)")
    active_agents: List[str] = Field(default_factory=list, description="Currently active agents")
    completed_tasks: List[str] = Field(default_factory=list, description="Completed tasks")
    pending_tasks: List[str] = Field(default_factory=list, description="Pending tasks")
    error_count: int = Field(default=0, description="Number of errors encountered")
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last activity timestamp")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
