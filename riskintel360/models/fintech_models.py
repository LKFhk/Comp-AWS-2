"""
Fintech Models for RiskIntel360
Data models specific to financial risk intelligence and compliance.
"""

from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uuid


class ComplianceStatus(Enum):
    """Compliance status enumeration"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"
    PENDING_ASSESSMENT = "pending_assessment"
    UNKNOWN = "unknown"


class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class FraudRiskLevel(Enum):
    """Fraud risk level enumeration"""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


class MarketTrend(Enum):
    """Market trend direction enumeration"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    VOLATILE = "volatile"


class DataSourceType(Enum):
    """Data source type enumeration"""
    SEC_EDGAR = "sec_edgar"
    FINRA = "finra"
    CFPB = "cfpb"
    FRED = "fred"
    TREASURY_GOV = "treasury_gov"
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    FINANCIAL_NEWS = "financial_news"
    INTERNAL = "internal"


class ComplianceAssessment(BaseModel):
    """Compliance assessment result"""
    model_config = ConfigDict(use_enum_values=True)
    
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique assessment identifier")
    regulation_id: str = Field(..., description="Regulation identifier")
    regulation_name: str = Field(..., description="Human-readable regulation name")
    compliance_status: ComplianceStatus = Field(..., description="Compliance status")
    risk_level: RiskLevel = Field(..., description="Associated risk level")
    requirements: List[str] = Field(default_factory=list, description="Compliance requirements")
    gaps: List[str] = Field(default_factory=list, description="Identified compliance gaps")
    remediation_plan: Dict[str, Any] = Field(default_factory=dict, description="Remediation plan details")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence in assessment")
    ai_reasoning: str = Field(..., description="AI reasoning for the assessment")
    data_sources: List[DataSourceType] = Field(default_factory=list, description="Data sources used")
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Assessment timestamp")
    expires_at: Optional[datetime] = Field(None, description="Assessment expiration")


class FraudDetectionResult(BaseModel):
    """Fraud detection analysis result"""
    model_config = ConfigDict(use_enum_values=True)
    
    detection_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique detection identifier")
    transaction_id: str = Field(..., description="Transaction identifier")
    fraud_probability: float = Field(..., ge=0.0, le=1.0, description="Fraud probability score")
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Anomaly score from ML models")
    risk_level: FraudRiskLevel = Field(..., description="Fraud risk level")
    detection_methods: List[str] = Field(default_factory=list, description="ML methods used for detection")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    recommended_action: str = Field(..., description="Recommended action")
    false_positive_likelihood: float = Field(..., ge=0.0, le=1.0, description="Likelihood of false positive")
    ml_explanation: str = Field(..., description="ML model explanation")
    llm_interpretation: str = Field(..., description="LLM interpretation of results")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Detection timestamp")
    model_version: str = Field("v1.0", description="ML model version used")


class MarketIntelligence(BaseModel):
    """Market intelligence analysis"""
    model_config = ConfigDict(use_enum_values=True)
    
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique analysis identifier")
    market_segment: str = Field(..., description="Market segment analyzed")
    trend_direction: MarketTrend = Field(..., description="Market trend direction")
    volatility_level: float = Field(..., ge=0.0, le=1.0, description="Market volatility level")
    key_drivers: List[str] = Field(default_factory=list, description="Key market drivers")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    opportunities: List[str] = Field(default_factory=list, description="Market opportunities")
    data_sources: List[DataSourceType] = Field(default_factory=list, description="Data sources used")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence score")
    ai_insights: str = Field(..., description="AI-generated insights")
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Analysis timestamp")
    valid_until: Optional[datetime] = Field(None, description="Analysis validity period")


class KYCVerificationResult(BaseModel):
    """KYC verification result"""
    model_config = ConfigDict(use_enum_values=True)
    
    verification_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique verification identifier")
    customer_id: str = Field(..., description="Customer identifier")
    verification_status: ComplianceStatus = Field(..., description="KYC verification status")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Customer risk score")
    risk_level: RiskLevel = Field(..., description="Customer risk level")
    identity_verified: bool = Field(..., description="Identity verification status")
    document_verification: Dict[str, bool] = Field(default_factory=dict, description="Document verification results")
    sanctions_check: bool = Field(..., description="Sanctions list check result")
    pep_check: bool = Field(..., description="Politically Exposed Person check result")
    adverse_media_check: bool = Field(..., description="Adverse media check result")
    verification_notes: str = Field("", description="Additional verification notes")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Verification confidence score")
    verified_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Verification timestamp")
    expires_at: Optional[datetime] = Field(None, description="Verification expiration")


class RiskAssessmentResult(BaseModel):
    """Comprehensive risk assessment result"""
    model_config = ConfigDict(use_enum_values=True)
    
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique assessment identifier")
    entity_id: str = Field(..., description="Entity being assessed")
    entity_type: str = Field(..., description="Type of entity (company, individual, etc.)")
    overall_risk_score: float = Field(..., ge=0.0, le=1.0, description="Overall risk score")
    overall_risk_level: RiskLevel = Field(..., description="Overall risk level")
    
    # Risk category scores
    credit_risk_score: float = Field(0.0, ge=0.0, le=1.0, description="Credit risk score")
    market_risk_score: float = Field(0.0, ge=0.0, le=1.0, description="Market risk score")
    operational_risk_score: float = Field(0.0, ge=0.0, le=1.0, description="Operational risk score")
    regulatory_risk_score: float = Field(0.0, ge=0.0, le=1.0, description="Regulatory risk score")
    fraud_risk_score: float = Field(0.0, ge=0.0, le=1.0, description="Fraud risk score")
    
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Risk mitigation strategies")
    recommendations: List[str] = Field(default_factory=list, description="Risk management recommendations")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Assessment confidence score")
    ai_analysis: str = Field(..., description="AI analysis and reasoning")
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Assessment timestamp")
    valid_until: Optional[datetime] = Field(None, description="Assessment validity period")


class FinancialAlert(BaseModel):
    """Financial alert model"""
    model_config = ConfigDict(use_enum_values=True)
    
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique alert identifier")
    alert_type: str = Field(..., description="Type of alert")
    severity: RiskLevel = Field(..., description="Alert severity level")
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")
    entity_id: str = Field(..., description="Related entity identifier")
    entity_type: str = Field(..., description="Type of related entity")
    triggered_by: str = Field(..., description="What triggered the alert")
    data_sources: List[DataSourceType] = Field(default_factory=list, description="Data sources involved")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Alert confidence score")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Alert creation timestamp")
    acknowledged: bool = Field(False, description="Whether alert has been acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="Who acknowledged the alert")
    acknowledged_at: Optional[datetime] = Field(None, description="When alert was acknowledged")
    resolved: bool = Field(False, description="Whether alert has been resolved")
    resolved_at: Optional[datetime] = Field(None, description="When alert was resolved")


class PublicDataSource(BaseModel):
    """Public data source information"""
    model_config = ConfigDict(use_enum_values=True)
    
    source_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique source identifier")
    source_type: DataSourceType = Field(..., description="Type of data source")
    source_name: str = Field(..., description="Human-readable source name")
    base_url: str = Field(..., description="Base URL for the data source")
    api_endpoint: Optional[str] = Field(None, description="API endpoint if applicable")
    is_free: bool = Field(True, description="Whether the data source is free")
    requires_api_key: bool = Field(False, description="Whether API key is required")
    rate_limit: Optional[int] = Field(None, description="Rate limit per hour")
    data_quality_score: float = Field(0.8, ge=0.0, le=1.0, description="Data quality score")
    reliability_score: float = Field(0.8, ge=0.0, le=1.0, description="Source reliability score")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last update timestamp")
    is_active: bool = Field(True, description="Whether source is currently active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional source metadata")


class WorkflowState(BaseModel):
    """Extended workflow state for RiskIntel360"""
    model_config = ConfigDict(use_enum_values=True)
    
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique workflow identifier")
    user_id: str = Field(..., description="User who initiated the workflow")
    workflow_type: str = Field("fintech_risk_analysis", description="Type of workflow")
    status: str = Field("created", description="Current workflow status")
    
    # Fintech-specific workflow state
    compliance_score: float = Field(0.0, ge=0.0, le=1.0, description="Overall compliance score")
    fraud_risk_level: FraudRiskLevel = Field(FraudRiskLevel.MINIMAL, description="Current fraud risk level")
    regulatory_alerts: List[FinancialAlert] = Field(default_factory=list, description="Regulatory alerts")
    market_conditions: Dict[str, Any] = Field(default_factory=dict, description="Current market conditions")
    public_data_quality: float = Field(0.0, ge=0.0, le=1.0, description="Public data quality score")
    
    # Workflow execution details
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Workflow start timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Workflow completion timestamp")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    
    # Agent coordination
    active_agents: List[str] = Field(default_factory=list, description="Currently active agent IDs")
    completed_agents: List[str] = Field(default_factory=list, description="Completed agent IDs")
    failed_agents: List[str] = Field(default_factory=list, description="Failed agent IDs")
    
    # Results and metrics
    results: Dict[str, Any] = Field(default_factory=dict, description="Workflow results")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Performance metrics")
    value_generated: float = Field(0.0, description="Estimated business value generated")
    cost_savings: float = Field(0.0, description="Estimated cost savings")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional workflow metadata")
