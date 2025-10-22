"""
Infrastructure tests for CDK deployments
Tests the fintech-enhanced infrastructure components
"""

import pytest
import aws_cdk as cdk
from aws_cdk import assertions
from infrastructure.stacks.riskintel360_stack import RiskIntel360Stack


class TestCDKDeployment:
    """Test CDK infrastructure deployment"""
    
    @pytest.fixture
    def app(self):
        """Create CDK app for testing"""
        return cdk.App()
    
    @pytest.fixture
    def development_stack(self, app):
        """Create development stack for testing"""
        return RiskIntel360Stack(
            app,
            "TestRiskIntel360Stack-development",
            environment="development",
            env=cdk.Environment(account="123456789012", region="us-east-1"),
        )
    
    @pytest.fixture
    def production_stack(self, app):
        """Create production stack for testing"""
        return RiskIntel360Stack(
            app,
            "TestRiskIntel360Stack-production", 
            environment="production",
            env=cdk.Environment(account="123456789012", region="us-east-1"),
        )
    
    def test_vpc_creation(self, development_stack):
        """Test VPC is created with correct configuration"""
        template = assertions.Template.from_stack(development_stack)
        
        # Verify VPC exists
        template.has_resource_properties("AWS::EC2::VPC", {
            "CidrBlock": "10.0.0.0/16",
            "EnableDnsHostnames": True,
            "EnableDnsSupport": True,
        })
        
        # Verify subnets are created
        template.resource_count_is("AWS::EC2::Subnet", 9)  # 3 AZs x 3 subnet types
    
    def test_fintech_dynamodb_tables(self, development_stack):
        """Test fintech-specific DynamoDB tables are created"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test regulatory data table
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": assertions.Match.string_like_regexp(r".*regulatory-data.*"),
            "AttributeDefinitions": [
                {"AttributeName": "regulation_id", "AttributeType": "S"},
                {"AttributeName": "effective_date", "AttributeType": "S"},
                {"AttributeName": "source", "AttributeType": "S"},
                {"AttributeName": "publication_date", "AttributeType": "S"},
            ],
        })
        
        # Test fraud detection table
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": assertions.Match.string_like_regexp(r".*fraud-detection.*"),
            "AttributeDefinitions": [
                {"AttributeName": "transaction_id", "AttributeType": "S"},
                {"AttributeName": "detection_timestamp", "AttributeType": "S"},
            ],
            "StreamSpecification": {"StreamViewType": "NEW_AND_OLD_IMAGES"},
        })
        
        # Test market data table
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "TableName": assertions.Match.string_like_regexp(r".*market-data.*"),
            "AttributeDefinitions": [
                {"AttributeName": "symbol", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
        })
    
    def test_fintech_s3_buckets(self, development_stack):
        """Test fintech data buckets are created with proper security"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test fintech data bucket with KMS encryption
        template.has_resource_properties("AWS::S3::Bucket", {
            "BucketName": assertions.Match.string_like_regexp(r".*fintech-data.*"),
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [
                    {
                        "ServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "aws:kms"
                        }
                    }
                ]
            },
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            },
        })
        
        # Test demo data bucket
        template.has_resource_properties("AWS::S3::Bucket", {
            "BucketName": assertions.Match.string_like_regexp(r".*demo-data.*"),
        })
    
    def test_kms_key_creation(self, development_stack):
        """Test KMS key for fintech data encryption"""
        template = assertions.Template.from_stack(development_stack)
        
        template.has_resource_properties("AWS::KMS::Key", {
            "Description": "KMS key for fintech data encryption",
            "EnableKeyRotation": True,
        })
    
    def test_ssm_parameters_for_api_keys(self, development_stack):
        """Test SSM parameters for fintech API keys"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test public API key parameters
        public_api_keys = [
            "alpha-vantage-api-key",
            "yahoo-finance-api-key",
            "fred-api-key",
            "sec-edgar-api-key",
            "treasury-api-key",
            "news-api-key"
        ]
        
        for key_name in public_api_keys:
            template.has_resource_properties("AWS::SSM::Parameter", {
                "Name": f"/riskintel360/development/fintech/api-keys/{key_name}",
                "Type": "SecureString",
            })
        
        # Test premium API key parameters
        premium_api_keys = [
            "bloomberg-api-key",
            "reuters-api-key", 
            "sp-capital-iq-api-key",
            "refinitiv-api-key"
        ]
        
        for key_name in premium_api_keys:
            template.has_resource_properties("AWS::SSM::Parameter", {
                "Name": f"/riskintel360/development/premium/api-keys/{key_name}",
                "Type": "SecureString",
            })
    
    def test_ml_infrastructure(self, development_stack):
        """Test ML infrastructure components"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test SageMaker execution role
        template.has_resource_properties("AWS::IAM::Role", {
            "RoleName": assertions.Match.string_like_regexp(r".*sagemaker-role.*"),
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "sagemaker.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ]
            },
        })
        
        # Test SageMaker model package group
        template.has_resource_properties("AWS::SageMaker::ModelPackageGroup", {
            "ModelPackageGroupName": assertions.Match.string_like_regexp(r".*fraud-models.*"),
        })
        
        # Test ML inference Lambda function
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": assertions.Match.string_like_regexp(r".*ml-inference.*"),
            "Runtime": "python3.11",
            "Timeout": 30,
            "MemorySize": 512,
        })
    
    def test_cost_monitoring_resources(self, development_stack):
        """Test cost monitoring and optimization resources"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test cost dashboard
        template.has_resource_properties("AWS::CloudWatch::Dashboard", {
            "DashboardName": assertions.Match.string_like_regexp(r".*costs.*"),
        })
        
        # Test cost anomaly detector
        template.has_resource_properties("AWS::CloudWatch::AnomalyDetector", {
            "MetricName": "EstimatedCharges",
            "Namespace": "AWS/Billing",
            "Stat": "Maximum",
        })
        
        # Test cost alarm
        template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "AlarmName": assertions.Match.string_like_regexp(r".*cost-alarm.*"),
            "MetricName": "EstimatedCharges",
            "Threshold": 100,  # Development threshold
        })
        
        # Test cost optimizer Lambda
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": assertions.Match.string_like_regexp(r".*cost-optimizer.*"),
        })
        
        # Test EventBridge rule for cost optimization
        template.has_resource_properties("AWS::Events::Rule", {
            "RuleName": assertions.Match.string_like_regexp(r".*cost-optimization.*"),
            "ScheduleExpression": "cron(0 6 * * ? *)",
        })
    
    def test_demo_resources(self, development_stack):
        """Test competition demo resources"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test demo data bucket
        template.has_resource_properties("AWS::S3::Bucket", {
            "BucketName": assertions.Match.string_like_regexp(r".*demo-data.*"),
        })
        
        # Test demo data generator Lambda
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": assertions.Match.string_like_regexp(r".*demo-generator.*"),
        })
    
    def test_ecs_cluster_configuration(self, development_stack):
        """Test ECS cluster for agent runtime"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test ECS cluster
        template.has_resource_properties("AWS::ECS::Cluster", {
            "ClusterName": assertions.Match.string_like_regexp(r".*agents.*"),
        })
        
        # Test ECR repository
        template.has_resource_properties("AWS::ECR::Repository", {
            "RepositoryName": "riskintel360-platform",
            "ImageScanningConfiguration": {"ScanOnPush": True},
        })
        
        # Test ECS task definition
        template.has_resource_properties("AWS::ECS::TaskDefinition", {
            "Family": assertions.Match.string_like_regexp(r".*development.*"),
            "RequiresCompatibilities": ["FARGATE"],
            "Cpu": "512",
            "Memory": "1024",
        })
        
        # Test ECS service
        template.has_resource_properties("AWS::ECS::Service", {
            "ServiceName": assertions.Match.string_like_regexp(r".*service.*"),
            "DesiredCount": 1,  # Development count
        })
    
    def test_production_vs_development_differences(self, development_stack, production_stack):
        """Test differences between production and development stacks"""
        dev_template = assertions.Template.from_stack(development_stack)
        prod_template = assertions.Template.from_stack(production_stack)
        
        # Test cost alarm thresholds
        dev_template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "Threshold": 100,  # Development threshold
        })
        
        prod_template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "Threshold": 1000,  # Production threshold
        })
        
        # Test ECS service desired count
        dev_template.has_resource_properties("AWS::ECS::Service", {
            "DesiredCount": 1,  # Development count
        })
        
        prod_template.has_resource_properties("AWS::ECS::Service", {
            "DesiredCount": 2,  # Production count
        })
    
    def test_iam_permissions(self, development_stack):
        """Test IAM roles and permissions for fintech operations"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test agent execution role has Bedrock permissions
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    {
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                            "bedrock:InvokeModelWithResponseStream",
                        ],
                        "Resource": "*",
                    }
                ])
            }
        })
    
    def test_security_groups(self, development_stack):
        """Test security group configurations"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test Redis security group
        template.has_resource_properties("AWS::EC2::SecurityGroup", {
            "GroupDescription": "Security group for riskintel360 Redis cluster",
            "SecurityGroupIngress": [
                {
                    "IpProtocol": "tcp",
                    "FromPort": 6379,
                    "ToPort": 6379,
                    "CidrIp": "10.0.0.0/16",
                }
            ],
        })
        
        # Test ECS service security group
        template.has_resource_properties("AWS::EC2::SecurityGroup", {
            "GroupDescription": "Security group for riskintel360 ECS service",
            "SecurityGroupIngress": [
                {
                    "IpProtocol": "tcp",
                    "FromPort": 8000,
                    "ToPort": 8000,
                    "CidrIp": "10.0.0.0/16",
                }
            ],
        })
    
    def test_cloudwatch_resources(self, development_stack):
        """Test CloudWatch monitoring resources"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test application log group
        template.has_resource_properties("AWS::Logs::LogGroup", {
            "LogGroupName": "/aws/riskintel360/development/application",
        })
        
        # Test dashboard
        template.has_resource_properties("AWS::CloudWatch::Dashboard", {
            "DashboardName": "riskintel360-development",
        })
    
    def test_cloudtrail_audit_logging(self, development_stack):
        """Test CloudTrail configuration for audit logging"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test CloudTrail
        template.has_resource_properties("AWS::CloudTrail::Trail", {
            "TrailName": assertions.Match.string_like_regexp(r".*audit-trail.*"),
            "IncludeGlobalServiceEvents": True,
            "EnableLogFileValidation": True,
        })
        
        # Test CloudTrail S3 bucket
        template.has_resource_properties("AWS::S3::Bucket", {
            "BucketName": assertions.Match.string_like_regexp(r".*cloudtrail.*"),
        })


class TestInfrastructureValidation:
    """Test infrastructure validation and compliance"""
    
    def test_resource_naming_convention(self, development_stack):
        """Test resource naming follows conventions"""
        template = assertions.Template.from_stack(development_stack)
        
        # All DynamoDB tables should include environment in name
        dynamodb_tables = template.find_resources("AWS::DynamoDB::Table")
        for logical_id, properties in dynamodb_tables.items():
            table_name = properties["Properties"]["TableName"]
            assert "development" in table_name, f"Table {table_name} missing environment"
    
    def test_encryption_at_rest(self, development_stack):
        """Test encryption at rest for sensitive resources"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test DynamoDB encryption
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "SSESpecification": {
                "SSEEnabled": True,
                "KMSMasterKeyId": assertions.Match.any_value(),
            }
        })
        
        # Test S3 encryption
        template.has_resource_properties("AWS::S3::Bucket", {
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": assertions.Match.any_value()
            }
        })
    
    def test_backup_and_retention_policies(self, development_stack):
        """Test backup and data retention policies"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test S3 lifecycle rules
        template.has_resource_properties("AWS::S3::Bucket", {
            "LifecycleConfiguration": {
                "Rules": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Status": "Enabled",
                    })
                ])
            }
        })
        
        # Test DynamoDB point-in-time recovery for production-like tables
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "PointInTimeRecoverySpecification": {
                "PointInTimeRecoveryEnabled": assertions.Match.any_value()
            }
        })
    
    def test_auto_scaling_configuration(self, development_stack):
        """Test auto-scaling configuration for ECS"""
        template = assertions.Template.from_stack(development_stack)
        
        # Test ECS service auto-scaling target
        template.has_resource_properties("AWS::ApplicationAutoScaling::ScalableTarget", {
            "ServiceNamespace": "ecs",
            "ScalableDimension": "ecs:service:DesiredCount",
            "MinCapacity": 1,
            "MaxCapacity": 5,
        })
        
        # Test CPU-based scaling policy
        template.has_resource_properties("AWS::ApplicationAutoScaling::ScalingPolicy", {
            "PolicyType": "TargetTrackingScaling",
            "TargetTrackingScalingPolicyConfiguration": {
                "TargetValue": 70.0,
                "PredefinedMetricSpecification": {
                    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
                }
            }
        })
        
        # Test memory-based scaling policy
        template.has_resource_properties("AWS::ApplicationAutoScaling::ScalingPolicy", {
            "PolicyType": "TargetTrackingScaling", 
            "TargetTrackingScalingPolicyConfiguration": {
                "TargetValue": 80.0,
                "PredefinedMetricSpecification": {
                    "PredefinedMetricType": "ECSServiceAverageMemoryUtilization"
                }
            }
        })
