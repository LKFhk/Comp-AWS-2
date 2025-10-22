"""
Application Settings Module for RiskIntel360 Platform
Handles environment-specific configuration and application settings.
"""

import os
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Application environment types"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


def _parse_cors_origins(cors_origins_str: str, environment: Environment) -> List[str]:
    """Parse CORS origins based on environment"""
    if environment == Environment.PRODUCTION:
        # In production, never allow all origins
        if cors_origins_str == "*":
            return ["https://RiskIntel360.com", "https://app.RiskIntel360.com"]
        else:
            return [origin.strip() for origin in cors_origins_str.split(",")]
    elif environment == Environment.STAGING:
        # In staging, allow specific staging domains
        if cors_origins_str == "*":
            return ["https://staging.RiskIntel360.com", "http://localhost:3000"]
        else:
            return [origin.strip() for origin in cors_origins_str.split(",")]
    else:
        # In development/testing, allow localhost and specified origins
        if cors_origins_str == "*":
            return [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
            ]
        else:
            return [origin.strip() for origin in cors_origins_str.split(",")]


@dataclass
class DatabaseSettings:
    """Database configuration settings"""

    # DynamoDB settings
    dynamodb_table_prefix: str = "RiskIntel360"
    dynamodb_read_capacity: int = 5
    dynamodb_write_capacity: int = 5

    # Aurora settings
    aurora_cluster_name: str = "RiskIntel360-cluster"
    aurora_database_name: str = "RiskIntel360"
    aurora_username: str = "RiskIntel360_user"
    aurora_password: Optional[str] = None
    aurora_port: int = 5432

    # Redis settings
    redis_cluster_name: str = "RiskIntel360-redis"
    redis_port: int = 6379
    redis_ttl_seconds: int = 3600


@dataclass
class APISettings:
    """API configuration settings"""

    host: str = "0.0.0.0"
    port: int = 8000
    base_url: str = "http://localhost:8000"
    debug: bool = False
    reload: bool = False
    workers: int = 1

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    # CORS settings
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_methods: List[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE"]
    )
    cors_headers: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class AgentSettings:
    """AI Agent configuration settings"""

    # Model configurations
    market_research_model: str = "anthropic.claude-3-haiku-20240307-v1:0"
    competitive_intel_model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    financial_validation_model: str = "anthropic.claude-3-opus-20240229-v1:0"
    risk_assessment_model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    customer_intel_model: str = "anthropic.claude-3-haiku-20240307-v1:0"
    synthesis_model: str = "anthropic.claude-3-opus-20240229-v1:0"

    # Agent runtime settings
    max_concurrent_agents: int = 50
    min_concurrent_agents: int = 3
    agent_timeout_seconds: int = 300
    workflow_timeout_seconds: int = 7200  # 2 hours

    # Memory settings
    memory_retention_days: int = 30
    max_memory_size_mb: int = 100


@dataclass
class ExternalAPISettings:
    """External API configuration settings"""

    # Market data APIs
    alpha_vantage_api_key: Optional[str] = None
    yahoo_finance_enabled: bool = True

    # News and social APIs
    news_api_key: Optional[str] = None
    twitter_api_key: Optional[str] = None
    reddit_api_key: Optional[str] = None

    # Competitive intelligence APIs
    crunchbase_api_key: Optional[str] = None
    pitchbook_api_key: Optional[str] = None

    # Rate limiting for external APIs
    api_rate_limit_requests: int = 60
    api_rate_limit_window: int = 60
    api_timeout_seconds: int = 30


@dataclass
class SecuritySettings:
    """Security configuration settings"""

    # JWT settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # OAuth settings
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_redirect_uri: str = "http://localhost:8000/auth/callback"
    oauth_region: str = "us-east-1"

    # Cognito settings
    cognito_user_pool_id: Optional[str] = None
    cognito_user_pool_client_id: Optional[str] = None
    cognito_region: str = "us-east-1"

    # Encryption settings
    encryption_key: Optional[str] = None

    # HTTPS settings
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None

    # Multi-tenant settings
    multi_tenant_enabled: bool = True
    default_tenant_id: str = "default"

    # Audit settings
    audit_enabled: bool = True
    audit_retention_days: int = 90


@dataclass
class LoggingSettings:
    """Logging configuration settings"""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 10
    backup_count: int = 5

    # Structured logging
    structured_logging: bool = True
    log_requests: bool = True
    log_responses: bool = False


@dataclass
class MonitoringSettings:
    """Monitoring and observability settings"""

    # CloudWatch settings
    cloudwatch_enabled: bool = True
    cloudwatch_namespace: str = "RiskIntel360/Platform"

    # Metrics settings
    metrics_enabled: bool = True
    custom_metrics_enabled: bool = True

    # Health check settings
    health_check_interval: int = 30
    health_check_timeout: int = 5


@dataclass
class AppSettings:
    """Main application settings"""

    # Environment
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False

    # Application info
    app_name: str = "RiskIntel360 Platform"
    app_version: str = "0.1.0"
    
    # AWS settings
    aws_region: str = "us-east-1"

    # Component settings
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    api: APISettings = field(default_factory=APISettings)
    agents: AgentSettings = field(default_factory=AgentSettings)
    external_apis: ExternalAPISettings = field(default_factory=ExternalAPISettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    monitoring: MonitoringSettings = field(default_factory=MonitoringSettings)

    @classmethod
    def from_environment(cls) -> "AppSettings":
        """Create application settings from environment variables"""
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        environment = Environment(env_name)

        # Database settings
        database = DatabaseSettings(
            dynamodb_table_prefix=os.getenv("DYNAMODB_TABLE_PREFIX", "RiskIntel360"),
            dynamodb_read_capacity=int(os.getenv("DYNAMODB_READ_CAPACITY", "5")),
            dynamodb_write_capacity=int(os.getenv("DYNAMODB_WRITE_CAPACITY", "5")),
            aurora_cluster_name=os.getenv("AURORA_CLUSTER_NAME", "RiskIntel360-cluster"),
            aurora_database_name=os.getenv("AURORA_DATABASE_NAME", "RiskIntel360"),
            aurora_username=os.getenv("AURORA_USERNAME", "RiskIntel360_user"),
            aurora_password=os.getenv("AURORA_PASSWORD"),
            aurora_port=int(os.getenv("AURORA_PORT", "5432")),
            redis_cluster_name=os.getenv("REDIS_CLUSTER_NAME", "RiskIntel360-redis"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_ttl_seconds=int(os.getenv("REDIS_TTL_SECONDS", "3600")),
        )

        # API settings
        api = APISettings(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            base_url=os.getenv(
                "API_BASE_URL", f"http://localhost:{os.getenv('API_PORT', '8000')}"
            ),
            debug=os.getenv("API_DEBUG", "false").lower() == "true",
            reload=os.getenv("API_RELOAD", "false").lower() == "true",
            workers=int(os.getenv("API_WORKERS", "1")),
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
            cors_origins=_parse_cors_origins(
                os.getenv("CORS_ORIGINS", "*"), environment
            ),
            cors_methods=os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE").split(","),
            cors_headers=(
                os.getenv("CORS_HEADERS", "*").split(",")
                if os.getenv("CORS_HEADERS") != "*"
                else ["*"]
            ),
        )

        # Agent settings
        agents = AgentSettings(
            market_research_model=os.getenv(
                "MARKET_RESEARCH_MODEL", "anthropic.claude-3-haiku-20240307-v1:0"
            ),
            competitive_intel_model=os.getenv(
                "COMPETITIVE_INTEL_MODEL", "anthropic.claude-3-5-sonnet-20241022-v2:0"
            ),
            financial_validation_model=os.getenv(
                "FINANCIAL_VALIDATION_MODEL", "anthropic.claude-3-opus-20240229-v1:0"
            ),
            risk_assessment_model=os.getenv(
                "RISK_ASSESSMENT_MODEL", "anthropic.claude-3-5-sonnet-20241022-v2:0"
            ),
            customer_intel_model=os.getenv(
                "CUSTOMER_INTEL_MODEL", "anthropic.claude-3-haiku-20240307-v1:0"
            ),
            synthesis_model=os.getenv(
                "SYNTHESIS_MODEL", "anthropic.claude-3-opus-20240229-v1:0"
            ),
            max_concurrent_agents=int(os.getenv("MAX_CONCURRENT_AGENTS", "50")),
            min_concurrent_agents=int(os.getenv("MIN_CONCURRENT_AGENTS", "3")),
            agent_timeout_seconds=int(os.getenv("AGENT_TIMEOUT_SECONDS", "300")),
            workflow_timeout_seconds=int(os.getenv("WORKFLOW_TIMEOUT_SECONDS", "7200")),
            memory_retention_days=int(os.getenv("MEMORY_RETENTION_DAYS", "30")),
            max_memory_size_mb=int(os.getenv("MAX_MEMORY_SIZE_MB", "100")),
        )

        # External API settings
        external_apis = ExternalAPISettings(
            alpha_vantage_api_key=os.getenv("ALPHA_VANTAGE_API_KEY"),
            yahoo_finance_enabled=os.getenv("YAHOO_FINANCE_ENABLED", "true").lower()
            == "true",
            news_api_key=os.getenv("NEWS_API_KEY"),
            twitter_api_key=os.getenv("TWITTER_API_KEY"),
            reddit_api_key=os.getenv("REDDIT_API_KEY"),
            crunchbase_api_key=os.getenv("CRUNCHBASE_API_KEY"),
            pitchbook_api_key=os.getenv("PITCHBOOK_API_KEY"),
            api_rate_limit_requests=int(os.getenv("API_RATE_LIMIT_REQUESTS", "60")),
            api_rate_limit_window=int(os.getenv("API_RATE_LIMIT_WINDOW", "60")),
            api_timeout_seconds=int(os.getenv("API_TIMEOUT_SECONDS", "30")),
        )

        # Security settings
        security = SecuritySettings(
            jwt_secret_key=os.getenv(
                "JWT_SECRET_KEY", "your-secret-key-change-in-production"
            ),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
            oauth_client_id=os.getenv("OAUTH_CLIENT_ID"),
            oauth_client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
            oauth_redirect_uri=os.getenv(
                "OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback"
            ),
            oauth_region=os.getenv("OAUTH_REGION", "us-east-1"),
            cognito_user_pool_id=os.getenv("COGNITO_USER_POOL_ID"),
            cognito_user_pool_client_id=os.getenv("COGNITO_USER_POOL_CLIENT_ID"),
            cognito_region=os.getenv("COGNITO_REGION", "us-east-1"),
            encryption_key=os.getenv("ENCRYPTION_KEY"),
            ssl_enabled=os.getenv("SSL_ENABLED", "false").lower() == "true",
            ssl_cert_path=os.getenv("SSL_CERT_PATH"),
            ssl_key_path=os.getenv("SSL_KEY_PATH"),
            multi_tenant_enabled=os.getenv("MULTI_TENANT_ENABLED", "true").lower()
            == "true",
            default_tenant_id=os.getenv("DEFAULT_TENANT_ID", "default"),
            audit_enabled=os.getenv("AUDIT_ENABLED", "true").lower() == "true",
            audit_retention_days=int(os.getenv("AUDIT_RETENTION_DAYS", "90")),
        )

        # Logging settings
        logging_settings = LoggingSettings(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv(
                "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            file_path=os.getenv("LOG_FILE_PATH"),
            max_file_size_mb=int(os.getenv("LOG_MAX_FILE_SIZE_MB", "10")),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
            structured_logging=os.getenv("STRUCTURED_LOGGING", "true").lower()
            == "true",
            log_requests=os.getenv("LOG_REQUESTS", "true").lower() == "true",
            log_responses=os.getenv("LOG_RESPONSES", "false").lower() == "true",
        )

        # Monitoring settings
        monitoring = MonitoringSettings(
            cloudwatch_enabled=os.getenv("CLOUDWATCH_ENABLED", "true").lower()
            == "true",
            cloudwatch_namespace=os.getenv(
                "CLOUDWATCH_NAMESPACE", "RiskIntel360/Platform"
            ),
            metrics_enabled=os.getenv("METRICS_ENABLED", "true").lower() == "true",
            custom_metrics_enabled=os.getenv("CUSTOM_METRICS_ENABLED", "true").lower()
            == "true",
            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
            health_check_timeout=int(os.getenv("HEALTH_CHECK_TIMEOUT", "5")),
        )

        return cls(
            environment=environment,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            app_name=os.getenv("APP_NAME", "RiskIntel360 Platform"),
            app_version=os.getenv("APP_VERSION", "0.1.0"),
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            database=database,
            api=api,
            agents=agents,
            external_apis=external_apis,
            security=security,
            logging=logging_settings,
            monitoring=monitoring,
        )


# Global settings instance
settings = AppSettings.from_environment()


def get_settings() -> AppSettings:
    """Get the global application settings"""
    return settings
