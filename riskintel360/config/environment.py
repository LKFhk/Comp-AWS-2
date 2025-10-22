"""
Environment Configuration Manager for RiskIntel360 Platform
Handles environment-specific configuration switching between local Docker and AWS ECS.
"""

import os
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from riskintel360.config.settings import AppSettings, Environment

logger = logging.getLogger(__name__)


class DeploymentTarget(Enum):
    """Deployment target enumeration"""
    LOCAL_DOCKER = "local_docker"
    AWS_ECS = "aws_ecs"
    KUBERNETES = "kubernetes"


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration"""
    environment: Environment
    deployment_target: DeploymentTarget
    
    # Database configuration
    database_host: str
    database_port: int
    database_name: str
    database_user: str
    database_password: Optional[str]
    database_ssl_mode: str
    
    # Redis configuration
    redis_host: str
    redis_port: int
    redis_password: Optional[str]
    redis_ssl: bool
    
    # AWS configuration
    aws_region: Optional[str]
    aws_access_key_id: Optional[str]
    aws_secret_access_key: Optional[str]
    
    # Service discovery
    service_discovery_enabled: bool
    service_registry_url: Optional[str]
    
    # Monitoring and logging
    cloudwatch_enabled: bool
    log_aggregation_endpoint: Optional[str]
    metrics_endpoint: Optional[str]
    
    # Security
    encryption_at_rest: bool
    encryption_in_transit: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "environment": self.environment.value,
            "deployment_target": self.deployment_target.value,
            "database": {
                "host": self.database_host,
                "port": self.database_port,
                "name": self.database_name,
                "user": self.database_user,
                "password": self.database_password,
                "ssl_mode": self.database_ssl_mode,
            },
            "redis": {
                "host": self.redis_host,
                "port": self.redis_port,
                "password": self.redis_password,
                "ssl": self.redis_ssl,
            },
            "aws": {
                "region": self.aws_region,
                "access_key_id": self.aws_access_key_id,
                "secret_access_key": self.aws_secret_access_key,
            },
            "service_discovery": {
                "enabled": self.service_discovery_enabled,
                "registry_url": self.service_registry_url,
            },
            "monitoring": {
                "cloudwatch_enabled": self.cloudwatch_enabled,
                "log_aggregation_endpoint": self.log_aggregation_endpoint,
                "metrics_endpoint": self.metrics_endpoint,
            },
            "security": {
                "encryption_at_rest": self.encryption_at_rest,
                "encryption_in_transit": self.encryption_in_transit,
            },
        }


class EnvironmentManager:
    """Manages environment-specific configuration switching"""
    
    def __init__(self):
        self._current_config: Optional[EnvironmentConfig] = None
        self._environment = self._detect_environment()
        self._deployment_target = self._detect_deployment_target()
        
    def _detect_environment(self) -> Environment:
        """Detect current environment from environment variables"""
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        
        try:
            return Environment(env_name)
        except ValueError:
            logger.warning(f"Unknown environment '{env_name}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _detect_deployment_target(self) -> DeploymentTarget:
        """Detect deployment target from environment variables and context"""
        
        # Check for ECS metadata endpoint (indicates ECS deployment)
        if os.getenv("ECS_CONTAINER_METADATA_URI_V4") or os.getenv("ECS_CONTAINER_METADATA_URI"):
            return DeploymentTarget.AWS_ECS
        
        # Check for Kubernetes service account (indicates K8s deployment)
        if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount"):
            return DeploymentTarget.KUBERNETES
        
        # Check for explicit deployment target
        target = os.getenv("DEPLOYMENT_TARGET", "local_docker").lower()
        
        try:
            return DeploymentTarget(target)
        except ValueError:
            logger.warning(f"Unknown deployment target '{target}', defaulting to local_docker")
            return DeploymentTarget.LOCAL_DOCKER
    
    def get_config(self) -> EnvironmentConfig:
        """Get current environment configuration"""
        if self._current_config is None:
            self._current_config = self._build_config()
        
        return self._current_config
    
    def _build_config(self) -> EnvironmentConfig:
        """Build environment configuration based on current context"""
        
        if self._deployment_target == DeploymentTarget.LOCAL_DOCKER:
            return self._build_local_docker_config()
        elif self._deployment_target == DeploymentTarget.AWS_ECS:
            return self._build_aws_ecs_config()
        else:
            raise ValueError(f"Unsupported deployment target: {self._deployment_target}")
    
    def _build_local_docker_config(self) -> EnvironmentConfig:
        """Build configuration for local Docker deployment"""
        
        return EnvironmentConfig(
            environment=self._environment,
            deployment_target=DeploymentTarget.LOCAL_DOCKER,
            
            # Local PostgreSQL container
            database_host=os.getenv("POSTGRES_HOST", "postgres"),
            database_port=int(os.getenv("POSTGRES_PORT", "5432")),
            database_name=os.getenv("POSTGRES_DB", "RiskIntel360"),
            database_user=os.getenv("POSTGRES_USER", "RiskIntel360"),
            database_password=os.getenv("POSTGRES_PASSWORD", "RiskIntel360_password"),
            database_ssl_mode="disable",
            
            # Local Redis container
            redis_host=os.getenv("REDIS_HOST", "redis"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_password=os.getenv("REDIS_PASSWORD"),
            redis_ssl=False,
            
            # AWS configuration (for Bedrock access)
            aws_region=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            
            # Service discovery
            service_discovery_enabled=False,
            service_registry_url=None,
            
            # Monitoring
            cloudwatch_enabled=False,
            log_aggregation_endpoint=None,
            metrics_endpoint=None,
            
            # Security
            encryption_at_rest=False,
            encryption_in_transit=False,
        )
    
    def _build_aws_ecs_config(self) -> EnvironmentConfig:
        """Build configuration for AWS ECS deployment"""
        
        # Get AWS region from metadata or environment
        aws_region = self._get_aws_region()
        
        return EnvironmentConfig(
            environment=self._environment,
            deployment_target=DeploymentTarget.AWS_ECS,
            
            # Aurora Serverless
            database_host=os.getenv("AURORA_ENDPOINT", f"RiskIntel360-{self._environment.value}.cluster-xyz.{aws_region}.rds.amazonaws.com"),
            database_port=int(os.getenv("AURORA_PORT", "5432")),
            database_name=os.getenv("AURORA_DATABASE", "RiskIntel360"),
            database_user=os.getenv("AURORA_USERNAME", "RiskIntel360_user"),
            database_password=os.getenv("AURORA_PASSWORD"),  # Retrieved from Secrets Manager
            database_ssl_mode="require",
            
            # ElastiCache Redis
            redis_host=os.getenv("ELASTICACHE_ENDPOINT", f"RiskIntel360-{self._environment.value}.xyz.cache.amazonaws.com"),
            redis_port=int(os.getenv("ELASTICACHE_PORT", "6379")),
            redis_password=os.getenv("ELASTICACHE_AUTH_TOKEN"),
            redis_ssl=True,
            
            # AWS configuration (from IAM role)
            aws_region=aws_region,
            aws_access_key_id=None,  # Use IAM role
            aws_secret_access_key=None,  # Use IAM role
            
            # Service discovery
            service_discovery_enabled=True,
            service_registry_url=f"https://servicediscovery.{aws_region}.amazonaws.com",
            
            # Monitoring
            cloudwatch_enabled=True,
            log_aggregation_endpoint=f"https://logs.{aws_region}.amazonaws.com",
            metrics_endpoint=f"https://monitoring.{aws_region}.amazonaws.com",
            
            # Security
            encryption_at_rest=True,
            encryption_in_transit=True,
        )
    
    def _get_aws_region(self) -> str:
        """Get AWS region from various sources"""
        
        # Try environment variable first
        region = os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION")
        if region:
            return region
        
        # Try ECS metadata
        try:
            import requests
            metadata_uri = os.getenv("ECS_CONTAINER_METADATA_URI_V4")
            if metadata_uri:
                response = requests.get(f"{metadata_uri}/task", timeout=2)
                if response.status_code == 200:
                    task_metadata = response.json()
                    availability_zone = task_metadata.get("AvailabilityZone", "")
                    if availability_zone:
                        return availability_zone[:-1]  # Remove AZ suffix
        except Exception as e:
            logger.debug(f"Failed to get region from ECS metadata: {e}")
        
        # Try EC2 metadata
        try:
            import requests
            response = requests.get("http://169.254.169.254/latest/meta-data/placement/region", timeout=2)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logger.debug(f"Failed to get region from EC2 metadata: {e}")
        
        # Default fallback
        logger.warning("Could not determine AWS region, using us-east-1")
        return "us-east-1"
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        config = self.get_config()
        
        password_part = f":{config.database_password}" if config.database_password else ""
        ssl_part = f"?sslmode={config.database_ssl_mode}" if config.database_ssl_mode != "disable" else ""
        
        return f"postgresql://{config.database_user}{password_part}@{config.database_host}:{config.database_port}/{config.database_name}{ssl_part}"
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        config = self.get_config()
        
        scheme = "rediss" if config.redis_ssl else "redis"
        password_part = f":{config.redis_password}@" if config.redis_password else ""
        
        return f"{scheme}://{password_part}{config.redis_host}:{config.redis_port}/0"
    
    def is_local_development(self) -> bool:
        """Check if running in local development environment"""
        return self._deployment_target == DeploymentTarget.LOCAL_DOCKER
    
    def is_cloud_deployment(self) -> bool:
        """Check if running in cloud deployment"""
        return self._deployment_target in [DeploymentTarget.AWS_ECS, DeploymentTarget.KUBERNETES]
    
    def get_service_endpoints(self) -> Dict[str, str]:
        """Get service endpoints based on deployment target"""
        config = self.get_config()
        
        if self._deployment_target == DeploymentTarget.LOCAL_DOCKER:
            return {
                "api": "http://localhost:8000",
                "health": "http://localhost:8000/health",
                "metrics": "http://localhost:8000/metrics",
            }
        elif self._deployment_target == DeploymentTarget.AWS_ECS:
            # In ECS, services are accessed through load balancer or service discovery
            return {
                "api": f"https://api.RiskIntel360-{self._environment.value}.com",
                "health": f"https://api.RiskIntel360-{self._environment.value}.com/health",
                "metrics": f"https://api.RiskIntel360-{self._environment.value}.com/metrics",
            }
        else:
            return {}
    
    def validate_configuration(self) -> bool:
        """Validate current configuration"""
        config = self.get_config()
        
        # Check required database configuration
        if not all([config.database_host, config.database_name, config.database_user]):
            logger.error("Missing required database configuration")
            return False
        
        # Check required Redis configuration
        if not all([config.redis_host]):
            logger.error("Missing required Redis configuration")
            return False
        
        # Check AWS configuration for cloud deployments
        if self.is_cloud_deployment() and not config.aws_region:
            logger.error("Missing AWS region for cloud deployment")
            return False
        
        return True
    
    def log_configuration(self) -> None:
        """Log current configuration (without sensitive data)"""
        config = self.get_config()
        
        logger.info(f"Environment: {config.environment.value}")
        logger.info(f"Deployment Target: {config.deployment_target.value}")
        logger.info(f"Database Host: {config.database_host}")
        logger.info(f"Redis Host: {config.redis_host}")
        logger.info(f"AWS Region: {config.aws_region}")
        logger.info(f"CloudWatch Enabled: {config.cloudwatch_enabled}")
        logger.info(f"Service Discovery Enabled: {config.service_discovery_enabled}")


# Global environment manager instance
_environment_manager: Optional[EnvironmentManager] = None


def get_environment_manager() -> EnvironmentManager:
    """Get the global environment manager instance"""
    global _environment_manager
    
    if _environment_manager is None:
        _environment_manager = EnvironmentManager()
    
    return _environment_manager


def get_environment_config() -> EnvironmentConfig:
    """Get current environment configuration"""
    return get_environment_manager().get_config()


def is_local_development() -> bool:
    """Check if running in local development environment"""
    return get_environment_manager().is_local_development()


def is_cloud_deployment() -> bool:
    """Check if running in cloud deployment"""
    return get_environment_manager().is_cloud_deployment()
