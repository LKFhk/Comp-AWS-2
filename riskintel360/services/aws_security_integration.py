"""
AWS Security Integration Service
Integrates with AWS IAM, KMS, CloudTrail, and other security services.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from riskintel360.config.settings import get_settings
from riskintel360.auth.models import SecurityContext, AuditAction, ResourceType

logger = logging.getLogger(__name__)


@dataclass
class IAMPolicy:
    """IAM policy definition"""
    name: str
    description: str
    policy_document: Dict[str, Any]
    attached_roles: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class KMSKeyInfo:
    """KMS key information"""
    key_id: str
    key_arn: str
    alias: str
    description: str
    key_usage: str
    key_state: str
    creation_date: datetime
    deletion_date: Optional[datetime]


@dataclass
class CloudTrailEvent:
    """CloudTrail event information"""
    event_id: str
    event_name: str
    event_source: str
    event_time: datetime
    user_identity: Dict[str, Any]
    source_ip_address: str
    user_agent: str
    resources: List[Dict[str, Any]]
    request_parameters: Dict[str, Any]
    response_elements: Dict[str, Any]


class AWSSecurityIntegration:
    """AWS security services integration"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize AWS clients
        self._iam_client = None
        self._kms_client = None
        self._cloudtrail_client = None
        self._sts_client = None
        self._organizations_client = None
        
        # Security configuration
        self._security_policies = {}
        self._kms_keys = {}
        self._cloudtrail_trails = {}
        
        # Initialize clients
        self._initialize_aws_clients()
    
    def _initialize_aws_clients(self) -> None:
        """Initialize AWS security service clients"""
        try:
            # IAM for identity and access management
            self._iam_client = boto3.client('iam')
            
            # KMS for key management
            self._kms_client = boto3.client('kms')
            
            # CloudTrail for audit logging
            self._cloudtrail_client = boto3.client('cloudtrail')
            
            # STS for security token service
            self._sts_client = boto3.client('sts')
            
            # Organizations for multi-account management
            try:
                self._organizations_client = boto3.client('organizations')
            except Exception:
                # Organizations might not be available in all accounts
                logger.info("AWS Organizations client not available")
            
            logger.info("AWS security clients initialized successfully")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found - security integration disabled")
        except Exception as e:
            logger.error(f"Failed to initialize AWS security clients: {e}")
    
    async def setup_iam_security_policies(self) -> Dict[str, Any]:
        """Setup IAM security policies for RiskIntel360"""
        if not self._iam_client:
            return {"error": "IAM client not available"}
        
        try:
            # Define security policies for different roles
            security_policies = {
                "RiskIntel360AdminPolicy": {
                    "description": "Full administrative access to RiskIntel360 resources",
                    "policy_document": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "bedrock:*",
                                    "kms:*",
                                    "dynamodb:*",
                                    "s3:*",
                                    "cloudwatch:*",
                                    "cloudtrail:*",
                                    "iam:ListRoles",
                                    "iam:PassRole"
                                ],
                                "Resource": "*",
                                "Condition": {
                                    "StringEquals": {
                                        "aws:RequestedRegion": [
                                            "us-east-1",
                                            "us-west-2"
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                },
                "RiskIntel360AnalystPolicy": {
                    "description": "Analyst access to RiskIntel360 resources",
                    "policy_document": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "bedrock:InvokeModel",
                                    "bedrock:ListFoundationModels",
                                    "dynamodb:GetItem",
                                    "dynamodb:PutItem",
                                    "dynamodb:Query",
                                    "dynamodb:Scan",
                                    "s3:GetObject",
                                    "s3:PutObject",
                                    "cloudwatch:GetMetricStatistics",
                                    "cloudwatch:ListMetrics"
                                ],
                                "Resource": [
                                    f"arn:aws:dynamodb:*:*:table/riskintel360-*",
                                    f"arn:aws:s3:::riskintel360-*/*",
                                    f"arn:aws:bedrock:*:*:foundation-model/*"
                                ]
                            }
                        ]
                    }
                },
                "RiskIntel360ViewerPolicy": {
                    "description": "Read-only access to RiskIntel360 resources",
                    "policy_document": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "dynamodb:GetItem",
                                    "dynamodb:Query",
                                    "s3:GetObject",
                                    "cloudwatch:GetMetricStatistics",
                                    "cloudwatch:ListMetrics"
                                ],
                                "Resource": [
                                    f"arn:aws:dynamodb:*:*:table/riskintel360-*",
                                    f"arn:aws:s3:::riskintel360-*/*"
                                ]
                            }
                        ]
                    }
                }
            }
            
            # Create or update policies
            created_policies = {}
            for policy_name, policy_config in security_policies.items():
                try:
                    # Check if policy exists
                    try:
                        response = self._iam_client.get_policy(
                            PolicyArn=f"arn:aws:iam::{self._get_account_id()}:policy/{policy_name}"
                        )
                        # Policy exists, update it
                        policy_arn = response['Policy']['Arn']
                        
                        # Create new policy version
                        self._iam_client.create_policy_version(
                            PolicyArn=policy_arn,
                            PolicyDocument=json.dumps(policy_config['policy_document']),
                            SetAsDefault=True
                        )
                        
                        logger.info(f"Updated IAM policy: {policy_name}")
                        
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'NoSuchEntity':
                            # Policy doesn't exist, create it
                            response = self._iam_client.create_policy(
                                PolicyName=policy_name,
                                PolicyDocument=json.dumps(policy_config['policy_document']),
                                Description=policy_config['description']
                            )
                            
                            policy_arn = response['Policy']['Arn']
                            logger.info(f"Created IAM policy: {policy_name}")
                        else:
                            raise
                    
                    created_policies[policy_name] = {
                        "policy_arn": policy_arn,
                        "description": policy_config['description'],
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to create/update policy {policy_name}: {e}")
                    created_policies[policy_name] = {"error": str(e)}
            
            return {
                "success": True,
                "policies_created": len([p for p in created_policies.values() if "error" not in p]),
                "policies": created_policies
            }
            
        except Exception as e:
            logger.error(f"Failed to setup IAM security policies: {e}")
            return {"error": str(e)}
    
    async def setup_kms_encryption_keys(self) -> Dict[str, Any]:
        """Setup KMS encryption keys for different data classifications"""
        if not self._kms_client:
            return {"error": "KMS client not available"}
        
        try:
            # Define encryption keys for different data classifications
            key_configurations = {
                "riskintel360-confidential": {
                    "description": "RiskIntel360 confidential data encryption key",
                    "usage": "ENCRYPT_DECRYPT",
                    "key_spec": "SYMMETRIC_DEFAULT",
                    "policy": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Sid": "Enable IAM User Permissions",
                                "Effect": "Allow",
                                "Principal": {
                                    "AWS": f"arn:aws:iam::{self._get_account_id()}:root"
                                },
                                "Action": "kms:*",
                                "Resource": "*"
                            },
                            {
                                "Sid": "Allow RiskIntel360 Service Access",
                                "Effect": "Allow",
                                "Principal": {
                                    "AWS": f"arn:aws:iam::{self._get_account_id()}:role/RiskIntel360ServiceRole"
                                },
                                "Action": [
                                    "kms:Encrypt",
                                    "kms:Decrypt",
                                    "kms:ReEncrypt*",
                                    "kms:GenerateDataKey*",
                                    "kms:DescribeKey"
                                ],
                                "Resource": "*"
                            }
                        ]
                    }
                },
                "riskintel360-restricted": {
                    "description": "RiskIntel360 restricted data encryption key",
                    "usage": "ENCRYPT_DECRYPT",
                    "key_spec": "SYMMETRIC_DEFAULT",
                    "policy": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Sid": "Enable IAM User Permissions",
                                "Effect": "Allow",
                                "Principal": {
                                    "AWS": f"arn:aws:iam::{self._get_account_id()}:root"
                                },
                                "Action": "kms:*",
                                "Resource": "*"
                            }
                        ]
                    }
                }
            }
            
            created_keys = {}
            for key_name, key_config in key_configurations.items():
                try:
                    # Check if key alias already exists
                    alias_name = f"alias/{key_name}-{self.settings.environment.value}"
                    
                    try:
                        response = self._kms_client.describe_key(KeyId=alias_name)
                        # Key exists
                        key_id = response['KeyMetadata']['KeyId']
                        logger.info(f"KMS key already exists: {alias_name}")
                        
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'NotFoundException':
                            # Create new key
                            response = self._kms_client.create_key(
                                Description=key_config['description'],
                                KeyUsage=key_config['usage'],
                                KeySpec=key_config['key_spec'],
                                Policy=json.dumps(key_config['policy']),
                                Tags=[
                                    {'TagKey': 'Service', 'TagValue': 'RiskIntel360'},
                                    {'TagKey': 'Environment', 'TagValue': self.settings.environment.value},
                                    {'TagKey': 'DataClassification', 'TagValue': key_name.split('-')[-1]}
                                ]
                            )
                            
                            key_id = response['KeyMetadata']['KeyId']
                            
                            # Create alias
                            self._kms_client.create_alias(
                                AliasName=alias_name,
                                TargetKeyId=key_id
                            )
                            
                            logger.info(f"Created KMS key: {alias_name}")
                        else:
                            raise
                    
                    created_keys[key_name] = {
                        "key_id": key_id,
                        "alias": alias_name,
                        "description": key_config['description'],
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to create/verify KMS key {key_name}: {e}")
                    created_keys[key_name] = {"error": str(e)}
            
            return {
                "success": True,
                "keys_created": len([k for k in created_keys.values() if "error" not in k]),
                "keys": created_keys
            }
            
        except Exception as e:
            logger.error(f"Failed to setup KMS encryption keys: {e}")
            return {"error": str(e)}
    
    async def setup_cloudtrail_logging(self) -> Dict[str, Any]:
        """Setup CloudTrail logging for audit trails"""
        if not self._cloudtrail_client:
            return {"error": "CloudTrail client not available"}
        
        try:
            trail_name = f"riskintel360-audit-trail-{self.settings.environment.value}"
            s3_bucket_name = f"riskintel360-cloudtrail-{self.settings.environment.value}-{self._get_account_id()}"
            
            # Check if trail exists
            try:
                response = self._cloudtrail_client.describe_trails(
                    trailNameList=[trail_name]
                )
                
                if response['trailList']:
                    logger.info(f"CloudTrail already exists: {trail_name}")
                    trail_arn = response['trailList'][0]['TrailARN']
                else:
                    raise ClientError({'Error': {'Code': 'TrailNotFoundException'}}, 'DescribeTrails')
                    
            except ClientError as e:
                if e.response['Error']['Code'] == 'TrailNotFoundException':
                    # Create S3 bucket for CloudTrail logs
                    s3_client = boto3.client('s3')
                    
                    try:
                        # Create bucket
                        if self.settings.aws_region == 'us-east-1':
                            s3_client.create_bucket(Bucket=s3_bucket_name)
                        else:
                            s3_client.create_bucket(
                                Bucket=s3_bucket_name,
                                CreateBucketConfiguration={'LocationConstraint': self.settings.aws_region}
                            )
                        
                        # Set bucket policy for CloudTrail
                        bucket_policy = {
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Sid": "AWSCloudTrailAclCheck",
                                    "Effect": "Allow",
                                    "Principal": {"Service": "cloudtrail.amazonaws.com"},
                                    "Action": "s3:GetBucketAcl",
                                    "Resource": f"arn:aws:s3:::{s3_bucket_name}"
                                },
                                {
                                    "Sid": "AWSCloudTrailWrite",
                                    "Effect": "Allow",
                                    "Principal": {"Service": "cloudtrail.amazonaws.com"},
                                    "Action": "s3:PutObject",
                                    "Resource": f"arn:aws:s3:::{s3_bucket_name}/*",
                                    "Condition": {
                                        "StringEquals": {
                                            "s3:x-amz-acl": "bucket-owner-full-control"
                                        }
                                    }
                                }
                            ]
                        }
                        
                        s3_client.put_bucket_policy(
                            Bucket=s3_bucket_name,
                            Policy=json.dumps(bucket_policy)
                        )
                        
                        logger.info(f"Created S3 bucket for CloudTrail: {s3_bucket_name}")
                        
                    except ClientError as s3_error:
                        if s3_error.response['Error']['Code'] != 'BucketAlreadyExists':
                            raise
                    
                    # Create CloudTrail
                    response = self._cloudtrail_client.create_trail(
                        Name=trail_name,
                        S3BucketName=s3_bucket_name,
                        IncludeGlobalServiceEvents=True,
                        IsMultiRegionTrail=True,
                        EnableLogFileValidation=True,
                        EventSelectors=[
                            {
                                'ReadWriteType': 'All',
                                'IncludeManagementEvents': True,
                                'DataResources': [
                                    {
                                        'Type': 'AWS::S3::Object',
                                        'Values': [f'arn:aws:s3:::riskintel360-*/*']
                                    },
                                    {
                                        'Type': 'AWS::DynamoDB::Table',
                                        'Values': [f'arn:aws:dynamodb:*:*:table/riskintel360-*']
                                    }
                                ]
                            }
                        ],
                        Tags=[
                            {'Key': 'Service', 'Value': 'RiskIntel360'},
                            {'Key': 'Environment', 'Value': self.settings.environment.value}
                        ]
                    )
                    
                    trail_arn = response['TrailARN']
                    
                    # Start logging
                    self._cloudtrail_client.start_logging(Name=trail_name)
                    
                    logger.info(f"Created and started CloudTrail: {trail_name}")
                else:
                    raise
            
            return {
                "success": True,
                "trail_name": trail_name,
                "trail_arn": trail_arn,
                "s3_bucket": s3_bucket_name,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to setup CloudTrail logging: {e}")
            return {"error": str(e)}
    
    async def get_security_compliance_status(self) -> Dict[str, Any]:
        """Get comprehensive security compliance status"""
        try:
            status = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "account_id": self._get_account_id(),
                "region": self.settings.aws_region,
                "environment": self.settings.environment.value,
                "iam_compliance": await self._check_iam_compliance(),
                "kms_compliance": await self._check_kms_compliance(),
                "cloudtrail_compliance": await self._check_cloudtrail_compliance(),
                "overall_compliance_score": 0.0
            }
            
            # Calculate overall compliance score
            compliance_scores = []
            for service, compliance in status.items():
                if isinstance(compliance, dict) and "compliance_score" in compliance:
                    compliance_scores.append(compliance["compliance_score"])
            
            if compliance_scores:
                status["overall_compliance_score"] = sum(compliance_scores) / len(compliance_scores)
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get security compliance status: {e}")
            return {"error": str(e)}
    
    async def _check_iam_compliance(self) -> Dict[str, Any]:
        """Check IAM compliance status"""
        if not self._iam_client:
            return {"error": "IAM client not available"}
        
        try:
            compliance_checks = {
                "mfa_enabled": False,
                "password_policy_compliant": False,
                "unused_access_keys": 0,
                "overprivileged_users": 0,
                "compliance_score": 0.0
            }
            
            # Check MFA enforcement
            try:
                response = self._iam_client.get_account_summary()
                account_summary = response['SummaryMap']
                
                if account_summary.get('AccountMFAEnabled', 0) > 0:
                    compliance_checks["mfa_enabled"] = True
                    
            except Exception as e:
                logger.warning(f"Could not check MFA status: {e}")
            
            # Check password policy
            try:
                response = self._iam_client.get_account_password_policy()
                policy = response['PasswordPolicy']
                
                # Check if password policy meets security requirements
                requirements_met = (
                    policy.get('MinimumPasswordLength', 0) >= 12 and
                    policy.get('RequireUppercaseCharacters', False) and
                    policy.get('RequireLowercaseCharacters', False) and
                    policy.get('RequireNumbers', False) and
                    policy.get('RequireSymbols', False)
                )
                
                compliance_checks["password_policy_compliant"] = requirements_met
                
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchEntity':
                    logger.warning(f"Could not check password policy: {e}")
            
            # Calculate compliance score
            score_factors = [
                compliance_checks["mfa_enabled"],
                compliance_checks["password_policy_compliant"],
                compliance_checks["unused_access_keys"] == 0,
                compliance_checks["overprivileged_users"] == 0
            ]
            
            compliance_checks["compliance_score"] = sum(score_factors) / len(score_factors)
            
            return compliance_checks
            
        except Exception as e:
            logger.error(f"IAM compliance check failed: {e}")
            return {"error": str(e)}
    
    async def _check_kms_compliance(self) -> Dict[str, Any]:
        """Check KMS compliance status"""
        if not self._kms_client:
            return {"error": "KMS client not available"}
        
        try:
            compliance_checks = {
                "keys_encrypted": 0,
                "key_rotation_enabled": 0,
                "unused_keys": 0,
                "compliance_score": 0.0
            }
            
            # List KMS keys
            response = self._kms_client.list_keys()
            keys = response['Keys']
            
            for key in keys:
                key_id = key['KeyId']
                
                try:
                    # Get key details
                    key_response = self._kms_client.describe_key(KeyId=key_id)
                    key_metadata = key_response['KeyMetadata']
                    
                    if key_metadata['KeyUsage'] == 'ENCRYPT_DECRYPT':
                        compliance_checks["keys_encrypted"] += 1
                        
                        # Check key rotation
                        try:
                            rotation_response = self._kms_client.get_key_rotation_status(KeyId=key_id)
                            if rotation_response['KeyRotationEnabled']:
                                compliance_checks["key_rotation_enabled"] += 1
                        except ClientError:
                            # Key rotation might not be supported for all key types
                            pass
                            
                except ClientError as e:
                    if e.response['Error']['Code'] == 'AccessDeniedException':
                        # Skip keys we don't have access to
                        continue
                    else:
                        logger.warning(f"Could not check key {key_id}: {e}")
            
            # Calculate compliance score
            if compliance_checks["keys_encrypted"] > 0:
                rotation_ratio = compliance_checks["key_rotation_enabled"] / compliance_checks["keys_encrypted"]
                compliance_checks["compliance_score"] = rotation_ratio
            
            return compliance_checks
            
        except Exception as e:
            logger.error(f"KMS compliance check failed: {e}")
            return {"error": str(e)}
    
    async def _check_cloudtrail_compliance(self) -> Dict[str, Any]:
        """Check CloudTrail compliance status"""
        if not self._cloudtrail_client:
            return {"error": "CloudTrail client not available"}
        
        try:
            compliance_checks = {
                "trails_active": 0,
                "log_file_validation_enabled": 0,
                "multi_region_enabled": 0,
                "compliance_score": 0.0
            }
            
            # List CloudTrail trails
            response = self._cloudtrail_client.describe_trails()
            trails = response['trailList']
            
            for trail in trails:
                trail_name = trail['Name']
                
                # Check if trail is logging
                try:
                    status_response = self._cloudtrail_client.get_trail_status(Name=trail_name)
                    if status_response['IsLogging']:
                        compliance_checks["trails_active"] += 1
                        
                        # Check log file validation
                        if trail.get('LogFileValidationEnabled', False):
                            compliance_checks["log_file_validation_enabled"] += 1
                        
                        # Check multi-region
                        if trail.get('IsMultiRegionTrail', False):
                            compliance_checks["multi_region_enabled"] += 1
                            
                except ClientError as e:
                    logger.warning(f"Could not check trail status {trail_name}: {e}")
            
            # Calculate compliance score
            if compliance_checks["trails_active"] > 0:
                validation_ratio = compliance_checks["log_file_validation_enabled"] / compliance_checks["trails_active"]
                multiregion_ratio = compliance_checks["multi_region_enabled"] / compliance_checks["trails_active"]
                compliance_checks["compliance_score"] = (validation_ratio + multiregion_ratio) / 2
            
            return compliance_checks
            
        except Exception as e:
            logger.error(f"CloudTrail compliance check failed: {e}")
            return {"error": str(e)}
    
    def _get_account_id(self) -> str:
        """Get AWS account ID"""
        try:
            if self._sts_client:
                response = self._sts_client.get_caller_identity()
                return response['Account']
            else:
                return "unknown"
        except Exception:
            return "unknown"
    
    async def get_cloudtrail_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_name: Optional[str] = None,
        user_name: Optional[str] = None,
        limit: int = 50
    ) -> List[CloudTrailEvent]:
        """Get CloudTrail events for audit purposes"""
        if not self._cloudtrail_client:
            return []
        
        try:
            # Set default time range (last 24 hours)
            if not end_time:
                end_time = datetime.now(timezone.utc)
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            # Build lookup attributes
            lookup_attributes = []
            if event_name:
                lookup_attributes.append({
                    'AttributeKey': 'EventName',
                    'AttributeValue': event_name
                })
            if user_name:
                lookup_attributes.append({
                    'AttributeKey': 'Username',
                    'AttributeValue': user_name
                })
            
            # Lookup events
            kwargs = {
                'StartTime': start_time,
                'EndTime': end_time,
                'MaxItems': limit
            }
            
            if lookup_attributes:
                kwargs['LookupAttributes'] = lookup_attributes
            
            response = self._cloudtrail_client.lookup_events(**kwargs)
            
            # Convert to CloudTrailEvent objects
            events = []
            for event in response['Events']:
                cloudtrail_event = CloudTrailEvent(
                    event_id=event['EventId'],
                    event_name=event['EventName'],
                    event_source=event.get('EventSource', ''),
                    event_time=event['EventTime'],
                    user_identity=event.get('UserIdentity', {}),
                    source_ip_address=event.get('SourceIPAddress', ''),
                    user_agent=event.get('UserAgent', ''),
                    resources=event.get('Resources', []),
                    request_parameters=event.get('RequestParameters', {}),
                    response_elements=event.get('ResponseElements', {})
                )
                events.append(cloudtrail_event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get CloudTrail events: {e}")
            return []


# Global AWS security integration instance
aws_security_integration = AWSSecurityIntegration()
# Aliases for backward compatibility with tests
AWSSecurityManager = AWSSecurityIntegration


class IAMRoleManager:
    """IAM role management service"""
    
    def __init__(self):
        try:
            self.iam_client = boto3.client('iam')
        except Exception:
            self.iam_client = None
        logger.info("IAMRoleManager initialized")
    
    def create_role(self, role_name: str, assume_role_policy: Dict[str, Any]) -> Dict[str, Any]:
        """Create IAM role"""
        if not self.iam_client:
            return {"success": False, "error": "IAM client not available"}
        
        try:
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy)
            )
            return {"success": True, "role_arn": response['Role']['Arn']}
        except Exception as e:
            return {"success": False, "error": str(e)}


class KMSEncryptionService:
    """KMS encryption service"""
    
    def __init__(self):
        try:
            self.kms_client = boto3.client('kms')
        except Exception:
            self.kms_client = None
        logger.info("KMSEncryptionService initialized")
    
    def encrypt_data(self, key_id: str, plaintext: str) -> Dict[str, Any]:
        """Encrypt data using KMS"""
        if not self.kms_client:
            return {"success": False, "error": "KMS client not available"}
        
        try:
            response = self.kms_client.encrypt(
                KeyId=key_id,
                Plaintext=plaintext
            )
            return {"success": True, "ciphertext": response['CiphertextBlob']}
        except Exception as e:
            return {"success": False, "error": str(e)}


class CloudTrailMonitor:
    """CloudTrail monitoring service"""
    
    def __init__(self):
        try:
            self.cloudtrail_client = boto3.client('cloudtrail')
        except Exception:
            self.cloudtrail_client = None
        logger.info("CloudTrailMonitor initialized")
    
    def get_events(self, start_time: datetime, end_time: datetime) -> List[CloudTrailEvent]:
        """Get CloudTrail events"""
        if not self.cloudtrail_client:
            return []
        
        try:
            response = self.cloudtrail_client.lookup_events(
                StartTime=start_time,
                EndTime=end_time
            )
            return [CloudTrailEvent(
                event_id=event.get('EventId', ''),
                event_name=event.get('EventName', ''),
                event_source=event.get('EventSource', ''),
                event_time=event.get('EventTime', datetime.now()),
                user_identity=event.get('UserIdentity', {}),
                source_ip_address=event.get('SourceIPAddress', ''),
                user_agent=event.get('UserAgent', ''),
                resources=event.get('Resources', []),
                request_parameters=event.get('RequestParameters', {}),
                response_elements=event.get('ResponseElements', {})
            ) for event in response.get('Events', [])]
        except Exception as e:
            logger.error(f"Failed to get CloudTrail events: {e}")
            return []


class SecurityGroupManager:
    """Security group management service"""
    
    def __init__(self):
        try:
            self.ec2_client = boto3.client('ec2')
        except Exception:
            self.ec2_client = None
        logger.info("SecurityGroupManager initialized")
    
    def create_security_group(self, group_name: str, description: str, vpc_id: str) -> Dict[str, Any]:
        """Create security group"""
        if not self.ec2_client:
            return {"success": False, "error": "EC2 client not available"}
        
        try:
            response = self.ec2_client.create_security_group(
                GroupName=group_name,
                Description=description,
                VpcId=vpc_id
            )
            return {"success": True, "group_id": response['GroupId']}
        except Exception as e:
            return {"success": False, "error": str(e)}