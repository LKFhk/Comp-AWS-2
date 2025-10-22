"""
AWS Configuration Module for RiskIntel360 Platform
Handles AWS credentials, region settings, and service configurations.
"""

import os
import boto3
from typing import Optional, Dict, Any
from dataclasses import dataclass
from botocore.exceptions import NoCredentialsError, ClientError
import logging

logger = logging.getLogger(__name__)


@dataclass
class AWSConfig:
    """AWS Configuration settings"""
    region: str = "us-east-1"
    profile: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    
    # Service-specific configurations
    bedrock_region: str = "us-east-1"
    dynamodb_region: str = "us-east-1"
    aurora_region: str = "us-east-1"
    s3_region: str = "us-east-1"
    
    # Resource names and identifiers
    dynamodb_table_prefix: str = "RiskIntel360"
    s3_bucket_prefix: str = "RiskIntel360"
    aurora_cluster_name: str = "RiskIntel360-cluster"
    
    @classmethod
    def from_environment(cls) -> "AWSConfig":
        """Create AWS configuration from environment variables"""
        return cls(
            region=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            profile=os.getenv("AWS_PROFILE"),
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            session_token=os.getenv("AWS_SESSION_TOKEN"),
            bedrock_region=os.getenv("BEDROCK_REGION", "us-east-1"),
            dynamodb_region=os.getenv("DYNAMODB_REGION", "us-east-1"),
            aurora_region=os.getenv("AURORA_REGION", "us-east-1"),
            s3_region=os.getenv("S3_REGION", "us-east-1"),
            dynamodb_table_prefix=os.getenv("DYNAMODB_TABLE_PREFIX", "RiskIntel360"),
            s3_bucket_prefix=os.getenv("S3_BUCKET_PREFIX", "RiskIntel360"),
            aurora_cluster_name=os.getenv("AURORA_CLUSTER_NAME", "RiskIntel360-cluster"),
        )


class AWSClientManager:
    """Manages AWS service clients with proper configuration and error handling"""
    
    def __init__(self, config: AWSConfig):
        self.config = config
        self._clients: Dict[str, Any] = {}
        self._session: Optional[boto3.Session] = None
        
    def _get_session(self) -> boto3.Session:
        """Get or create boto3 session with proper credentials"""
        if self._session is None:
            session_kwargs = {}
            
            if self.config.profile:
                session_kwargs["profile_name"] = self.config.profile
            
            if self.config.access_key_id and self.config.secret_access_key:
                session_kwargs.update({
                    "aws_access_key_id": self.config.access_key_id,
                    "aws_secret_access_key": self.config.secret_access_key,
                })
                
                if self.config.session_token:
                    session_kwargs["aws_session_token"] = self.config.session_token
            
            self._session = boto3.Session(**session_kwargs)
            
        return self._session
    
    def get_client(self, service_name: str, region: Optional[str] = None) -> Any:
        """Get AWS service client with caching"""
        region = region or self.config.region
        client_key = f"{service_name}_{region}"
        
        if client_key not in self._clients:
            try:
                session = self._get_session()
                self._clients[client_key] = session.client(
                    service_name,
                    region_name=region
                )
                logger.info(f"Created AWS {service_name} client for region {region}")
            except NoCredentialsError:
                logger.error(f"No AWS credentials found for {service_name} client")
                raise
            except ClientError as e:
                logger.error(f"Failed to create {service_name} client: {e}")
                raise
                
        return self._clients[client_key]
    
    def get_bedrock_client(self):
        """Get Amazon Bedrock client"""
        return self.get_client("bedrock-runtime", self.config.bedrock_region)
    
    def get_dynamodb_client(self):
        """Get DynamoDB client"""
        return self.get_client("dynamodb", self.config.dynamodb_region)
    
    def get_dynamodb_resource(self):
        """Get DynamoDB resource"""
        session = self._get_session()
        return session.resource("dynamodb", region_name=self.config.dynamodb_region)
    
    def get_rds_client(self):
        """Get RDS client for Aurora"""
        return self.get_client("rds", self.config.aurora_region)
    
    def get_s3_client(self):
        """Get S3 client"""
        return self.get_client("s3", self.config.s3_region)
    
    def get_elasticache_client(self):
        """Get ElastiCache client"""
        return self.get_client("elasticache", self.config.region)
    
    def get_apigateway_client(self):
        """Get API Gateway client"""
        return self.get_client("apigateway", self.config.region)
    
    def get_cognito_client(self):
        """Get Cognito client"""
        return self.get_client("cognito-idp", self.config.region)
    
    def get_cloudwatch_client(self):
        """Get CloudWatch client"""
        return self.get_client("cloudwatch", self.config.region)
    
    def get_ecs_client(self):
        """Get ECS client"""
        return self.get_client("ecs", self.config.region)
    
    def validate_credentials(self) -> bool:
        """Validate AWS credentials by making a simple API call"""
        try:
            sts_client = self.get_client("sts")
            sts_client.get_caller_identity()
            logger.info("AWS credentials validated successfully")
            return True
        except Exception as e:
            logger.error(f"AWS credentials validation failed: {e}")
            return False


# Global AWS configuration and client manager instances
aws_config = AWSConfig.from_environment()
aws_client_manager = AWSClientManager(aws_config)


def get_aws_config() -> AWSConfig:
    """Get the global AWS configuration"""
    return aws_config


def get_aws_client_manager() -> AWSClientManager:
    """Get the global AWS client manager"""
    return aws_client_manager
