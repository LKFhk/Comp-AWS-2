"""
RiskIntel360 Platform Data Models

This package contains all data models, database schemas, and data access layers
for the RiskIntel360 multi-agent financial intelligence platform.
"""

from .core import (
    # Enums
    Priority,
    MessageType,
    WorkflowStatus,
    MaturityLevel,
    IntensityLevel,
    
    # Core Models
    ValidationRequest,
    ValidationResult,
    AgentMessage,
    WorkflowState,
    TaskDistribution,
    
    # Analysis Result Models
    MarketSize,
    Trend,
    Barrier,
    RegulatoryEnvironment,
    MarketAnalysisResult,
    Competitor,
    Advantage,
    Threat,
    CompetitiveAnalysisResult,
    FinancialProjection,
    FinancialAnalysisResult,
    RiskFactor,
    RiskAnalysisResult,
    CustomerSegment,
    CustomerAnalysisResult,
    Recommendation,
)

from .database import (
    # SQLAlchemy Base
    Base,
    TimestampMixin,
    
    # Database Models
    ValidationRequestDB,
    ValidationResultDB,
    AgentMessageDB,
    WorkflowStateDB,
    AgentStateDB,
    ExternalDataSourceDB,
)

from .adapters import (
    # Abstract Base
    DataAccessAdapter,
    
    # Concrete Adapters
    PostgreSQLAdapter,
    DynamoDBAdapter,
    HybridDataManager,
    
    # Global Instance
    data_manager,
)

from .fintech_models import (
    # Fintech Enums
    ComplianceStatus,
    RiskLevel,
    FraudRiskLevel,
    MarketTrend,
    DataSourceType,
    
    # Fintech Models
    ComplianceAssessment,
    FraudDetectionResult,
    MarketIntelligence,
    KYCVerificationResult,
    RiskAssessmentResult,
    FinancialAlert,
    PublicDataSource,
    WorkflowState as FinTechWorkflowState,
)

__all__ = [
    # Enums
    'Priority',
    'MessageType',
    'WorkflowStatus',
    'MaturityLevel',
    'IntensityLevel',
    
    # Core Models
    'ValidationRequest',
    'ValidationResult',
    'AgentMessage',
    'WorkflowState',
    'TaskDistribution',
    
    # Analysis Result Models
    'MarketSize',
    'Trend',
    'Barrier',
    'RegulatoryEnvironment',
    'MarketAnalysisResult',
    'Competitor',
    'Advantage',
    'Threat',
    'CompetitiveAnalysisResult',
    'FinancialProjection',
    'FinancialAnalysisResult',
    'RiskFactor',
    'RiskAnalysisResult',
    'CustomerSegment',
    'CustomerAnalysisResult',
    'Recommendation',
    
    # Database Models
    'Base',
    'TimestampMixin',
    'ValidationRequestDB',
    'ValidationResultDB',
    'AgentMessageDB',
    'WorkflowStateDB',
    'AgentStateDB',
    'ExternalDataSourceDB',
    
    # Data Access
    'DataAccessAdapter',
    'PostgreSQLAdapter',
    'DynamoDBAdapter',
    'HybridDataManager',
    'data_manager',
    
    # Fintech Enums
    'ComplianceStatus',
    'RiskLevel',
    'FraudRiskLevel',
    'MarketTrend',
    'DataSourceType',
    
    # Fintech Models
    'ComplianceAssessment',
    'FraudDetectionResult',
    'MarketIntelligence',
    'KYCVerificationResult',
    'RiskAssessmentResult',
    'FinancialAlert',
    'PublicDataSource',
    'FinTechWorkflowState',
]
