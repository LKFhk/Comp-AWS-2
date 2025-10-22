"""
Centralized API Configuration Management for RiskIntel360 Platform
Manages API settings, rate limits, feature flags, and service configurations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

from riskintel360.config.settings import get_settings

logger = logging.getLogger(__name__)


class FeatureFlag(str, Enum):
    """Feature flags for API functionality"""
    FINTECH_INTELLIGENCE = "fintech_intelligence"
    ADVANCED_FRAUD_DETECTION = "advanced_fraud_detection"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    MARKET_ANALYSIS = "market_analysis"
    KYC_VERIFICATION = "kyc_verification"
    COST_OPTIMIZATION = "cost_optimization"
    PERFORMANCE_MONITORING = "performance_monitoring"
    BUSINESS_VALUE_TRACKING = "business_value_tracking"
    REAL_TIME_ALERTS = "real_time_alerts"
    BULK_OPERATIONS = "bulk_operations"
    ASYNC_PROCESSING = "async_processing"
    ADVANCED_ANALYTICS = "advanced_analytics"


class ServiceTier(str, Enum):
    """Service tier levels"""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class RateLimitConfig(BaseModel):
    """Rate limit configuration"""
    requests_per_minute: int = Field(..., description="Requests per minute limit")
    requests_per_hour: int = Field(..., description="Requests per hour limit")
    requests_per_day: int = Field(..., description="Requests per day limit")
    burst_limit: int = Field(..., description="Burst request limit")
    window_seconds: int = Field(default=60, description="Rate limit window in seconds")


class EndpointConfig(BaseModel):
    """Configuration for individual API endpoints"""
    enabled: bool = Field(default=True, description="Whether endpoint is enabled")
    rate_limit: Optional[RateLimitConfig] = Field(None, description="Endpoint-specific rate limits")
    required_features: List[FeatureFlag] = Field(default_factory=list, description="Required feature flags")
    min_service_tier: ServiceTier = Field(default=ServiceTier.FREE, description="Minimum service tier required")
    cache_ttl_seconds: Optional[int] = Field(None, description="Cache TTL for responses")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    max_request_size_mb: int = Field(default=10, description="Maximum request size in MB")


class APIServiceConfig(BaseModel):
    """Configuration for API services"""
    name: str = Field(..., description="Service name")
    enabled: bool = Field(default=True, description="Whether service is enabled")
    base_url: Optional[str] = Field(None, description="Service base URL")
    timeout_seconds: int = Field(default=30, description="Service timeout")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    circuit_breaker_threshold: int = Field(default=5, description="Circuit breaker failure threshold")
    health_check_interval_seconds: int = Field(default=60, description="Health check interval")


class CentralizedAPIConfig:
    """Centralized API configuration manager"""
    
    def __init__(self):
        self.settings = get_settings()
        self._feature_flags: Dict[FeatureFlag, bool] = {}
        self._endpoint_configs: Dict[str, EndpointConfig] = {}
        self._service_configs: Dict[str, APIServiceConfig] = {}
        self._rate_limits: Dict[ServiceTier, RateLimitConfig] = {}
        self._initialize_default_config()
    
    def _initialize_default_config(self):
        """Initialize default configuration"""
        # Default feature flags
        self._feature_flags = {
            FeatureFlag.FINTECH_INTELLIGENCE: True,
            FeatureFlag.ADVANCED_FRAUD_DETECTION: True,
            FeatureFlag.REGULATORY_COMPLIANCE: True,
            FeatureFlag.MARKET_ANALYSIS: True,
            FeatureFlag.KYC_VERIFICATION: True,
            FeatureFlag.COST_OPTIMIZATION: True,
            FeatureFlag.PERFORMANCE_MONITORING: True,
            FeatureFlag.BUSINESS_VALUE_TRACKING: True,
            FeatureFlag.REAL_TIME_ALERTS: True,
            FeatureFlag.BULK_OPERATIONS: False,  # Disabled by default
            FeatureFlag.ASYNC_PROCESSING: True,
            FeatureFlag.ADVANCED_ANALYTICS: True,
        }
        
        # Default rate limits by service tier
        self._rate_limits = {
            ServiceTier.FREE: RateLimitConfig(
                requests_per_minute=10,
                requests_per_hour=100,
                requests_per_day=1000,
                burst_limit=20
            ),
            ServiceTier.BASIC: RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000,
                burst_limit=100
            ),
            ServiceTier.PROFESSIONAL: RateLimitConfig(
                requests_per_minute=300,
                requests_per_hour=5000,
                requests_per_day=50000,
                burst_limit=500
            ),
            ServiceTier.ENTERPRISE: RateLimitConfig(
                requests_per_minute=1000,
                requests_per_hour=20000,
                requests_per_day=200000,
                burst_limit=2000
            )
        }
        
        # Default endpoint configurations
        self._endpoint_configs = {
            "/api/v1/fintech/risk-analysis": EndpointConfig(
                enabled=True,
                required_features=[FeatureFlag.FINTECH_INTELLIGENCE],
                min_service_tier=ServiceTier.BASIC,
                cache_ttl_seconds=300,
                timeout_seconds=120,
                max_request_size_mb=5
            ),
            "/api/v1/fintech/fraud-detection": EndpointConfig(
                enabled=True,
                required_features=[FeatureFlag.ADVANCED_FRAUD_DETECTION],
                min_service_tier=ServiceTier.PROFESSIONAL,
                timeout_seconds=30,
                max_request_size_mb=20
            ),
            "/api/v1/fintech/compliance-check": EndpointConfig(
                enabled=True,
                required_features=[FeatureFlag.REGULATORY_COMPLIANCE],
                min_service_tier=ServiceTier.BASIC,
                cache_ttl_seconds=600,
                timeout_seconds=60
            ),
            "/api/v1/fintech/market-intelligence": EndpointConfig(
                enabled=True,
                required_features=[FeatureFlag.MARKET_ANALYSIS],
                min_service_tier=ServiceTier.BASIC,
                cache_ttl_seconds=180,
                timeout_seconds=45
            ),
            "/api/v1/fintech/kyc-verification": EndpointConfig(
                enabled=True,
                required_features=[FeatureFlag.KYC_VERIFICATION],
                min_service_tier=ServiceTier.PROFESSIONAL,
                timeout_seconds=90,
                max_request_size_mb=15
            ),
            "/api/v1/cost-optimization/*": EndpointConfig(
                enabled=True,
                required_features=[FeatureFlag.COST_OPTIMIZATION],
                min_service_tier=ServiceTier.BASIC,
                cache_ttl_seconds=300
            ),
            "/api/v1/performance/*": EndpointConfig(
                enabled=True,
                required_features=[FeatureFlag.PERFORMANCE_MONITORING],
                min_service_tier=ServiceTier.BASIC,
                cache_ttl_seconds=60
            )
        }
        
        # Default service configurations
        self._service_configs = {
            "bedrock_client": APIServiceConfig(
                name="Amazon Bedrock Client",
                enabled=True,
                timeout_seconds=60,
                retry_attempts=3,
                circuit_breaker_threshold=5
            ),
            "workflow_orchestrator": APIServiceConfig(
                name="Workflow Orchestrator",
                enabled=True,
                timeout_seconds=120,
                retry_attempts=2,
                circuit_breaker_threshold=3
            ),
            "ml_engine": APIServiceConfig(
                name="Unsupervised ML Engine",
                enabled=True,
                timeout_seconds=30,
                retry_attempts=2,
                circuit_breaker_threshold=5
            ),
            "external_data_integration": APIServiceConfig(
                name="External Data Integration",
                enabled=True,
                timeout_seconds=45,
                retry_attempts=3,
                circuit_breaker_threshold=10
            ),
            "performance_monitor": APIServiceConfig(
                name="Performance Monitor",
                enabled=True,
                timeout_seconds=15,
                retry_attempts=1,
                circuit_breaker_threshold=3
            )
        }
    
    def is_feature_enabled(self, feature: FeatureFlag) -> bool:
        """Check if a feature flag is enabled"""
        return self._feature_flags.get(feature, False)
    
    def enable_feature(self, feature: FeatureFlag):
        """Enable a feature flag"""
        self._feature_flags[feature] = True
        logger.info(f"Feature enabled: {feature.value}")
    
    def disable_feature(self, feature: FeatureFlag):
        """Disable a feature flag"""
        self._feature_flags[feature] = False
        logger.info(f"Feature disabled: {feature.value}")
    
    def get_endpoint_config(self, endpoint_path: str) -> Optional[EndpointConfig]:
        """Get configuration for a specific endpoint"""
        # Try exact match first
        if endpoint_path in self._endpoint_configs:
            return self._endpoint_configs[endpoint_path]
        
        # Try wildcard matches
        for pattern, config in self._endpoint_configs.items():
            if pattern.endswith("*") and endpoint_path.startswith(pattern[:-1]):
                return config
        
        return None
    
    def set_endpoint_config(self, endpoint_path: str, config: EndpointConfig):
        """Set configuration for a specific endpoint"""
        self._endpoint_configs[endpoint_path] = config
        logger.info(f"Endpoint configuration updated: {endpoint_path}")
    
    def get_rate_limit_config(self, service_tier: ServiceTier) -> RateLimitConfig:
        """Get rate limit configuration for a service tier"""
        return self._rate_limits.get(service_tier, self._rate_limits[ServiceTier.FREE])
    
    def get_service_config(self, service_name: str) -> Optional[APIServiceConfig]:
        """Get configuration for a service"""
        return self._service_configs.get(service_name)
    
    def set_service_config(self, service_name: str, config: APIServiceConfig):
        """Set configuration for a service"""
        self._service_configs[service_name] = config
        logger.info(f"Service configuration updated: {service_name}")
    
    def is_endpoint_enabled(self, endpoint_path: str, user_tier: ServiceTier = ServiceTier.FREE) -> bool:
        """Check if an endpoint is enabled for a user tier"""
        config = self.get_endpoint_config(endpoint_path)
        if not config:
            return True  # Default to enabled if no config
        
        if not config.enabled:
            return False
        
        # Check service tier requirement
        tier_order = [ServiceTier.FREE, ServiceTier.BASIC, ServiceTier.PROFESSIONAL, ServiceTier.ENTERPRISE]
        if tier_order.index(user_tier) < tier_order.index(config.min_service_tier):
            return False
        
        # Check required features
        for feature in config.required_features:
            if not self.is_feature_enabled(feature):
                return False
        
        return True
    
    def get_all_features(self) -> Dict[FeatureFlag, bool]:
        """Get all feature flags and their status"""
        return self._feature_flags.copy()
    
    def get_all_endpoint_configs(self) -> Dict[str, EndpointConfig]:
        """Get all endpoint configurations"""
        return self._endpoint_configs.copy()
    
    def get_all_service_configs(self) -> Dict[str, APIServiceConfig]:
        """Get all service configurations"""
        return self._service_configs.copy()
    
    def validate_configuration(self) -> bool:
        """Validate the current configuration"""
        try:
            # Validate feature flags
            for feature in FeatureFlag:
                if feature not in self._feature_flags:
                    logger.warning(f"Missing feature flag: {feature.value}")
            
            # Validate service configurations
            required_services = ["bedrock_client", "workflow_orchestrator"]
            for service in required_services:
                if service not in self._service_configs:
                    logger.error(f"Missing required service configuration: {service}")
                    return False
            
            logger.info("API configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def export_config(self) -> Dict[str, Any]:
        """Export current configuration"""
        return {
            "feature_flags": {flag.value: enabled for flag, enabled in self._feature_flags.items()},
            "endpoint_configs": {path: config.model_dump() for path, config in self._endpoint_configs.items()},
            "service_configs": {name: config.model_dump() for name, config in self._service_configs.items()},
            "rate_limits": {tier.value: config.model_dump() for tier, config in self._rate_limits.items()},
            "exported_at": datetime.utcnow().isoformat()
        }


# Global configuration instance
api_config = CentralizedAPIConfig()


def get_api_config() -> CentralizedAPIConfig:
    """Get the global API configuration instance"""
    return api_config


# Export configuration classes and functions
__all__ = [
    "FeatureFlag",
    "ServiceTier", 
    "RateLimitConfig",
    "EndpointConfig",
    "APIServiceConfig",
    "CentralizedAPIConfig",
    "api_config",
    "get_api_config"
]