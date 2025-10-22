"""
Main CDK Stack for riskintel360 Platform Infrastructure
Enhanced for Fintech Data Processing and ML Capabilities
"""

from typing import Dict, Any
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_rds as rds,
    aws_elasticache as elasticache,
    aws_s3 as s3,
    aws_iam as iam,
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_bedrock as bedrock,
    aws_kms as kms,
    aws_ssm as ssm,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
    aws_sagemaker as sagemaker,
    RemovalPolicy,
    Duration,
)
from constructs import Construct


class RiskIntel360Stack(Stack):
    """Main infrastructure stack for riskintel360 Platform"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment: str = "development",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = environment
        self.is_production = environment == "production"
        
        # Create VPC for the application
        self.vpc = self._create_vpc()
        
        # Create DynamoDB tables
        self.dynamodb_tables = self._create_dynamodb_tables()
        
        # Create Aurora Serverless cluster
        self.aurora_cluster = self._create_aurora_cluster()
        
        # Create ElastiCache Redis cluster
        self.redis_cluster = self._create_redis_cluster()
        
        # Create S3 buckets
        self.s3_buckets = self._create_s3_buckets()
        
        # Create IAM roles and policies
        self.iam_roles = self._create_iam_roles()
        
        # Create Cognito User Pool for authentication
        self.cognito_resources = self._create_cognito_user_pool()
        
        # Create ECS cluster for AgentCore
        self.ecs_cluster = self._create_ecs_cluster()
        
        # Create API Gateway
        self.api_gateway = self._create_api_gateway()
        
        # Create CloudWatch resources
        self.cloudwatch_resources = self._create_cloudwatch_resources()
        
        # Create CloudTrail for audit logging
        self.cloudtrail = self._create_cloudtrail()
        
        # Create fintech-specific resources
        self.fintech_resources = self._create_fintech_resources()
        
        # Create ML infrastructure for fraud detection
        self.ml_resources = self._create_ml_infrastructure()
        
        # Create cost monitoring resources
        self.cost_monitoring = self._create_cost_monitoring()
        
        # Create competition demo resources
        self.demo_resources = self._create_demo_resources()
        
        # Output important resource information
        self._create_outputs()

    def _create_vpc(self) -> ec2.Vpc:
        """Create VPC with public and private subnets"""
        return ec2.Vpc(
            self,
            "riskintel360VPC",
            vpc_name=f"riskintel360-vpc-{self.env_name}",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=3,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="DatabaseSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )

    def _create_dynamodb_tables(self) -> Dict[str, dynamodb.Table]:
        """Create DynamoDB tables for agent states, sessions, and memory"""
        tables = {}
        
        # Agent States table
        tables["agent_states"] = dynamodb.Table(
            self,
            "AgentStatesTable",
            table_name=f"riskintel360-agent-states-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="agent_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="session_id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST if self.is_production 
                         else dynamodb.BillingMode.PROVISIONED,
            read_capacity=5 if not self.is_production else None,
            write_capacity=5 if not self.is_production else None,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production 
                          else RemovalPolicy.RETAIN,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=self.is_production
            ),
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )
        
        # Validation Sessions table
        tables["validation_sessions"] = dynamodb.Table(
            self,
            "ValidationSessionsTable",
            table_name=f"riskintel360-validation-sessions-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="session_id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST if self.is_production 
                         else dynamodb.BillingMode.PROVISIONED,
            read_capacity=5 if not self.is_production else None,
            write_capacity=5 if not self.is_production else None,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production 
                          else RemovalPolicy.RETAIN,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=self.is_production
            ),
        )
        
        # Agent Memory table
        tables["agent_memory"] = dynamodb.Table(
            self,
            "AgentMemoryTable",
            table_name=f"riskintel360-agent-memory-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="memory_key", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST if self.is_production 
                         else dynamodb.BillingMode.PROVISIONED,
            read_capacity=5 if not self.is_production else None,
            write_capacity=5 if not self.is_production else None,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production 
                          else RemovalPolicy.RETAIN,
            time_to_live_attribute="ttl",
        )
        
        # User Preferences table
        tables["user_preferences"] = dynamodb.Table(
            self,
            "UserPreferencesTable",
            table_name=f"riskintel360-user-preferences-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST if self.is_production 
                         else dynamodb.BillingMode.PROVISIONED,
            read_capacity=5 if not self.is_production else None,
            write_capacity=5 if not self.is_production else None,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production 
                          else RemovalPolicy.RETAIN,
        )
        
        # Audit Logs table
        tables["audit_logs"] = dynamodb.Table(
            self,
            "AuditLogsTable",
            table_name=f"riskintel360-audit-logs-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST if self.is_production 
                         else dynamodb.BillingMode.PROVISIONED,
            read_capacity=10 if not self.is_production else None,
            write_capacity=10 if not self.is_production else None,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production 
                          else RemovalPolicy.RETAIN,
            time_to_live_attribute="ttl",
        )
        
        # Add GSI for audit log queries
        tables["audit_logs"].add_global_secondary_index(
            index_name="user-tenant-index",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="tenant_id", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )
        
        tables["audit_logs"].add_global_secondary_index(
            index_name="tenant-timestamp-index",
            partition_key=dynamodb.Attribute(
                name="tenant_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )
        
        return tables

    def _create_aurora_cluster(self) -> rds.ServerlessCluster:
        """Create Aurora Serverless PostgreSQL cluster"""
        return rds.ServerlessCluster(
            self,
            "AuroraCluster",
            cluster_identifier=f"riskintel360-cluster-{self.env_name}",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_13_13
            ),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            default_database_name="riskintel360",
            scaling=rds.ServerlessScalingOptions(
                auto_pause=Duration.minutes(10) if not self.is_production else None,
                min_capacity=rds.AuroraCapacityUnit.ACU_2,
                max_capacity=rds.AuroraCapacityUnit.ACU_16 if self.is_production 
                           else rds.AuroraCapacityUnit.ACU_4,
            ),
            backup_retention=Duration.days(7) if self.is_production else Duration.days(1),
            removal_policy=RemovalPolicy.DESTROY if not self.is_production 
                          else RemovalPolicy.RETAIN,
        )

    def _create_redis_cluster(self) -> elasticache.CfnCacheCluster:
        """Create ElastiCache Redis cluster"""
        # Create subnet group for Redis
        subnet_group = elasticache.CfnSubnetGroup(
            self,
            "RedisSubnetGroup",
            description="Subnet group for riskintel360 Redis cluster",
            subnet_ids=[subnet.subnet_id for subnet in self.vpc.private_subnets],
            cache_subnet_group_name=f"riskintel360-redis-subnet-group-{self.env_name}",
        )
        
        # Create security group for Redis
        redis_security_group = ec2.SecurityGroup(
            self,
            "RedisSecurityGroup",
            vpc=self.vpc,
            description="Security group for riskintel360 Redis cluster",
            allow_all_outbound=False,
        )
        
        redis_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(6379),
            description="Allow Redis access from VPC",
        )
        
        return elasticache.CfnCacheCluster(
            self,
            "RedisCluster",
            cache_node_type="cache.t3.micro" if not self.is_production 
                           else "cache.r6g.large",
            engine="redis",
            num_cache_nodes=1,
            cluster_name=f"riskintel360-redis-{self.env_name}",
            cache_subnet_group_name=subnet_group.cache_subnet_group_name,
            vpc_security_group_ids=[redis_security_group.security_group_id],
        )

    def _create_s3_buckets(self) -> Dict[str, s3.Bucket]:
        """Create S3 buckets for data storage"""
        buckets = {}
        
        # Validation reports bucket
        buckets["validation_reports"] = s3.Bucket(
            self,
            "ValidationReportsBucket",
            bucket_name=f"riskintel360-validation-reports-{self.env_name}-{self.account}",
            versioned=self.is_production,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production 
                          else RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldReports",
                    enabled=True,
                    expiration=Duration.days(90) if not self.is_production 
                              else Duration.days(365),
                )
            ],
        )
        
        # Market data bucket
        buckets["market_data"] = s3.Bucket(
            self,
            "MarketDataBucket",
            bucket_name=f"riskintel360-market-data-{self.env_name}-{self.account}",
            versioned=self.is_production,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production 
                          else RemovalPolicy.RETAIN,
        )
        
        return buckets

    def _create_iam_roles(self) -> Dict[str, iam.Role]:
        """Create IAM roles for different components"""
        roles = {}
        
        # Agent execution role
        roles["agent_execution"] = iam.Role(
            self,
            "AgentExecutionRole",
            role_name=f"riskintel360AgentExecutionRole-{self.env_name}",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                ),
            ],
        )
        
        # Add permissions for Bedrock
        roles["agent_execution"].add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=["*"],
            )
        )
        
        # Add permissions for DynamoDB
        for table in self.dynamodb_tables.values():
            table.grant_read_write_data(roles["agent_execution"])
        
        # Add permissions for Aurora
        roles["agent_execution"].add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "rds-data:ExecuteStatement",
                    "rds-data:BatchExecuteStatement",
                    "rds-data:BeginTransaction",
                    "rds-data:CommitTransaction",
                    "rds-data:RollbackTransaction",
                ],
                resources=[self.aurora_cluster.cluster_arn],
            )
        )
        
        # Add permissions for S3
        for bucket in self.s3_buckets.values():
            bucket.grant_read_write(roles["agent_execution"])
        
        return roles

    def _create_cognito_user_pool(self) -> Dict[str, Any]:
        """Create Cognito User Pool and Client for authentication"""
        # Create User Pool
        user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=f"riskintel360-users-{self.env_name}",
            sign_in_aliases=cognito.SignInAliases(email=True, username=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production 
                          else RemovalPolicy.RETAIN,
            # Add custom attributes for tenant isolation
            custom_attributes={
                "tenant_id": cognito.StringAttribute(min_len=1, max_len=256, mutable=True)
            },
        )
        
        # Create User Pool Client
        user_pool_client = cognito.UserPoolClient(
            self,
            "UserPoolClient",
            user_pool=user_pool,
            user_pool_client_name=f"riskintel360-client-{self.env_name}",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                admin_user_password=True,
            ),
            generate_secret=True,
            access_token_validity=Duration.hours(1),
            id_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.days(30),
            prevent_user_existence_errors=True,
        )
        
        # Create User Pool Groups for RBAC
        admin_group = cognito.CfnUserPoolGroup(
            self,
            "AdminGroup",
            user_pool_id=user_pool.user_pool_id,
            group_name="admin",
            description="Administrator group with full access",
            precedence=1,
        )
        
        analyst_group = cognito.CfnUserPoolGroup(
            self,
            "AnalystGroup",
            user_pool_id=user_pool.user_pool_id,
            group_name="analyst",
            description="Business analyst group with read/write access to business data",
            precedence=2,
        )
        
        viewer_group = cognito.CfnUserPoolGroup(
            self,
            "ViewerGroup",
            user_pool_id=user_pool.user_pool_id,
            group_name="viewer",
            description="Viewer group with read-only access",
            precedence=3,
        )
        
        api_user_group = cognito.CfnUserPoolGroup(
            self,
            "ApiUserGroup",
            user_pool_id=user_pool.user_pool_id,
            group_name="api_user",
            description="API user group for programmatic access",
            precedence=4,
        )
        
        return {
            "user_pool": user_pool,
            "user_pool_client": user_pool_client,
            "groups": {
                "admin": admin_group,
                "analyst": analyst_group,
                "viewer": viewer_group,
                "api_user": api_user_group,
            }
        }

    def _create_ecs_cluster(self) -> ecs.Cluster:
        """Create ECS cluster for AgentCore runtime"""
        cluster = ecs.Cluster(
            self,
            "ECSCluster",
            cluster_name=f"riskintel360-agents-{self.env_name}",
            vpc=self.vpc,
            container_insights=self.is_production,
        )
        
        # Create ECR repository
        ecr_repository = self._create_ecr_repository()
        
        # Create ECS task definition
        task_definition = self._create_ecs_task_definition(ecr_repository)
        
        # Create ECS service
        service = self._create_ecs_service(cluster, task_definition)
        
        # Store references for outputs
        self.ecr_repository = ecr_repository
        self.ecs_task_definition = task_definition
        self.ecs_service = service
        
        return cluster

    def _create_api_gateway(self) -> apigateway.RestApi:
        """Create API Gateway for REST API"""
        return apigateway.RestApi(
            self,
            "APIGateway",
            rest_api_name=f"riskintel360-api-{self.env_name}",
            description=f"riskintel360 Platform API - {self.env_name}",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"],
            ),
            deploy_options=apigateway.StageOptions(
                stage_name=self.env_name,
                throttling_rate_limit=1000 if self.is_production else 100,
                throttling_burst_limit=2000 if self.is_production else 200,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
            ),
        )

    def _create_cloudwatch_resources(self) -> Dict[str, Any]:
        """Create CloudWatch resources for monitoring"""
        resources = {}
        
        # Log group for application logs
        resources["app_log_group"] = logs.LogGroup(
            self,
            "AppLogGroup",
            log_group_name=f"/aws/riskintel360/{self.env_name}/application",
            retention=logs.RetentionDays.ONE_WEEK if not self.is_production 
                     else logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production 
                          else RemovalPolicy.RETAIN,
        )
        
        # Dashboard
        resources["dashboard"] = cloudwatch.Dashboard(
            self,
            "Dashboard",
            dashboard_name=f"riskintel360-{self.env_name}",
        )
        
        return resources

    def _create_cloudtrail(self) -> Any:
        """Create CloudTrail for audit logging"""
        from aws_cdk import aws_cloudtrail as cloudtrail
        
        # Create S3 bucket for CloudTrail logs
        cloudtrail_bucket = s3.Bucket(
            self,
            "CloudTrailBucket",
            bucket_name=f"riskintel360-cloudtrail-{self.env_name}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production 
                          else RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldLogs",
                    enabled=True,
                    expiration=Duration.days(90) if not self.is_production 
                              else Duration.days(365),
                )
            ],
        )
        
        # Create CloudTrail
        trail = cloudtrail.Trail(
            self,
            "AuditTrail",
            trail_name=f"riskintel360-audit-trail-{self.env_name}",
            bucket=cloudtrail_bucket,
            include_global_service_events=True,
            is_multi_region_trail=self.is_production,
            enable_file_validation=True,
        )
        
        # Add event selectors for API Gateway and other services
        trail.add_event_selector(
            read_write_type=cloudtrail.ReadWriteType.ALL,
            include_management_events=True,
            data_resources=[
                cloudtrail.DataResource(
                    type="AWS::S3::Object",
                    values=[f"{bucket.bucket_arn}/*" for bucket in self.s3_buckets.values()]
                ),
                cloudtrail.DataResource(
                    type="AWS::DynamoDB::Table",
                    values=[table.table_arn for table in self.dynamodb_tables.values()]
                )
            ]
        )
        
        return trail

    def _create_ecr_repository(self):
        """Create ECR repository for Docker images"""
        from aws_cdk import aws_ecr as ecr
        
        return ecr.Repository(
            self,
            "ECRRepository",
            repository_name="riskintel360-platform",
            image_scan_on_push=True,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Keep last 10 images",
                    max_image_count=10,
                    rule_priority=1,
                )
            ],
            removal_policy=RemovalPolicy.DESTROY if not self.is_production 
                          else RemovalPolicy.RETAIN,
        )

    def _create_ecs_task_definition(self, ecr_repository):
        """Create ECS task definition"""
        # Create task execution role
        task_execution_role = iam.Role(
            self,
            "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                ),
            ],
        )
        
        # Add ECR permissions
        ecr_repository.grant_pull(task_execution_role)
        
        # Create task definition
        task_definition = ecs.FargateTaskDefinition(
            self,
            "TaskDefinition",
            family=f"riskintel360-{self.env_name}",
            cpu=512 if not self.is_production else 1024,
            memory_limit_mib=1024 if not self.is_production else 2048,
            task_role=self.iam_roles["agent_execution"],
            execution_role=task_execution_role,
        )
        
        # Add container
        container = task_definition.add_container(
            "riskintel360-app",
            image=ecs.ContainerImage.from_ecr_repository(ecr_repository, "latest"),
            environment={
                "ENVIRONMENT": self.env_name,
                "AWS_DEFAULT_REGION": self.region,
                "DATABASE_URL": f"postgresql://riskintel360:password@{self.aurora_cluster.cluster_endpoint.hostname}:5432/riskintel360",
                "REDIS_URL": f"redis://{self.redis_cluster.attr_redis_endpoint_address}:6379/0",
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="riskintel360",
                log_group=self.cloudwatch_resources["app_log_group"],
            ),
            health_check=ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                retries=3,
                start_period=Duration.seconds(60),
            ),
        )
        
        # Add port mapping
        container.add_port_mappings(
            ecs.PortMapping(
                container_port=8000,
                protocol=ecs.Protocol.TCP,
            )
        )
        
        return task_definition

    def _create_ecs_service(self, cluster, task_definition):
        """Create ECS service"""
        # Create security group for ECS service
        service_security_group = ec2.SecurityGroup(
            self,
            "ServiceSecurityGroup",
            vpc=self.vpc,
            description="Security group for riskintel360 ECS service",
            allow_all_outbound=True,
        )
        
        service_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(8000),
            description="Allow HTTP access from VPC",
        )
        
        # Create ECS service
        service = ecs.FargateService(
            self,
            "Service",
            cluster=cluster,
            task_definition=task_definition,
            service_name=f"riskintel360-service-{self.env_name}",
            desired_count=1 if not self.is_production else 2,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            security_groups=[service_security_group],
            assign_public_ip=False,
            enable_logging=True,
            circuit_breaker=ecs.DeploymentCircuitBreaker(
                rollback=True
            ),
            deployment_configuration=ecs.DeploymentConfiguration(
                maximum_percent=200,
                minimum_healthy_percent=50,
            ),
        )
        
        # Enable auto scaling
        scaling = service.auto_scale_task_count(
            min_capacity=1 if not self.is_production else 2,
            max_capacity=5 if not self.is_production else 20,
        )
        
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.minutes(5),
            scale_out_cooldown=Duration.minutes(2),
        )
        
        scaling.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=80,
            scale_in_cooldown=Duration.minutes(5),
            scale_out_cooldown=Duration.minutes(2),
        )
        
        return service

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs"""
        # VPC outputs
        cdk.CfnOutput(
            self,
            "VPCId",
            value=self.vpc.vpc_id,
            description="VPC ID",
        )
        
        # DynamoDB table outputs
        for name, table in self.dynamodb_tables.items():
            cdk.CfnOutput(
                self,
                f"{name.title()}TableName",
                value=table.table_name,
                description=f"{name.title()} DynamoDB table name",
            )
        
        # Aurora cluster output
        cdk.CfnOutput(
            self,
            "AuroraClusterEndpoint",
            value=self.aurora_cluster.cluster_endpoint.hostname,
            description="Aurora cluster endpoint",
        )
        
        # S3 bucket outputs
        for name, bucket in self.s3_buckets.items():
            cdk.CfnOutput(
                self,
                f"{name.title()}BucketName",
                value=bucket.bucket_name,
                description=f"{name.title()} S3 bucket name",
            )
        
        # Cognito User Pool outputs
        cdk.CfnOutput(
            self,
            "UserPoolId",
            value=self.cognito_resources["user_pool"].user_pool_id,
            description="Cognito User Pool ID",
        )
        
        cdk.CfnOutput(
            self,
            "UserPoolClientId",
            value=self.cognito_resources["user_pool_client"].user_pool_client_id,
            description="Cognito User Pool Client ID",
        )
        
        # ECS Cluster output
        cdk.CfnOutput(
            self,
            "ECSClusterName",
            value=self.ecs_cluster.cluster_name,
            description="ECS Cluster name",
        )
        
        # API Gateway output
        cdk.CfnOutput(
            self,
            "APIGatewayURL",
            value=self.api_gateway.url,
            description="API Gateway URL",
        )
        
        # ECR Repository output
        cdk.CfnOutput(
            self,
            "ECRRepositoryURI",
            value=self.ecr_repository.repository_uri,
            description="ECR Repository URI",
        )
        
        # ECS Service output
        cdk.CfnOutput(
            self,
            "ECSServiceName",
            value=self.ecs_service.service_name,
            description="ECS Service name",
        )
    def _create_fintech_resources(self) -> Dict[str, Any]:
        """Create fintech-specific infrastructure resources"""
        resources = {}
        
        # Create KMS key for fintech data encryption
        resources["fintech_kms_key"] = kms.Key(
            self,
            "FintechDataKey",
            description="KMS key for fintech data encryption",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production else RemovalPolicy.RETAIN,
        )
        
        # Create fintech data bucket with enhanced security
        resources["fintech_data_bucket"] = s3.Bucket(
            self,
            "FintechDataBucket",
            bucket_name=f"riskintel360-fintech-data-{self.env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=resources["fintech_kms_key"],
            removal_policy=RemovalPolicy.DESTROY if not self.is_production else RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="FintechDataLifecycle",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ],
                    expiration=Duration.days(2555) if self.is_production else Duration.days(365)  # 7 years for compliance
                )
            ],
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )
        
        # Create regulatory data table for compliance monitoring
        resources["regulatory_data_table"] = dynamodb.Table(
            self,
            "RegulatoryDataTable",
            table_name=f"riskintel360-regulatory-data-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="regulation_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="effective_date", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production else RemovalPolicy.RETAIN,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=self.is_production
            ),
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=resources["fintech_kms_key"],
        )
        
        # Add GSI for regulatory source queries
        resources["regulatory_data_table"].add_global_secondary_index(
            index_name="source-date-index",
            partition_key=dynamodb.Attribute(
                name="source", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="publication_date", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )
        
        # Create fraud detection results table
        resources["fraud_detection_table"] = dynamodb.Table(
            self,
            "FraudDetectionTable",
            table_name=f"riskintel360-fraud-detection-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="transaction_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="detection_timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production else RemovalPolicy.RETAIN,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=resources["fintech_kms_key"],
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            time_to_live_attribute="ttl",
        )
        
        # Create market data cache table
        resources["market_data_table"] = dynamodb.Table(
            self,
            "MarketDataTable",
            table_name=f"riskintel360-market-data-{self.env_name}",
            partition_key=dynamodb.Attribute(
                name="symbol", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if not self.is_production else RemovalPolicy.RETAIN,
            time_to_live_attribute="ttl",
        )
        
        # Create SSM parameters for fintech API keys
        resources["api_key_parameters"] = self._create_fintech_api_parameters(resources["fintech_kms_key"])
        
        return resources
    
    def _create_fintech_api_parameters(self, kms_key: kms.Key) -> Dict[str, ssm.StringParameter]:
        """Create SSM parameters for fintech API keys"""
        parameters = {}
        
        # Public data source API keys (free tier)
        api_keys = [
            "alpha-vantage-api-key",
            "yahoo-finance-api-key", 
            "fred-api-key",
            "sec-edgar-api-key",
            "treasury-api-key",
            "news-api-key"
        ]
        
        for key_name in api_keys:
            parameters[key_name] = ssm.StringParameter(
                self,
                f"FintechApiKey{key_name.replace('-', '').title()}",
                parameter_name=f"/riskintel360/{self.env_name}/fintech/api-keys/{key_name}",
                string_value="PLACEHOLDER_VALUE",  # To be updated manually
                description=f"API key for {key_name} fintech data source",
                type=ssm.ParameterType.SECURE_STRING,
                key_id=kms_key.key_id,
            )
        
        # Premium data source API keys (optional)
        premium_keys = [
            "bloomberg-api-key",
            "reuters-api-key",
            "sp-capital-iq-api-key",
            "refinitiv-api-key"
        ]
        
        for key_name in premium_keys:
            parameters[key_name] = ssm.StringParameter(
                self,
                f"PremiumApiKey{key_name.replace('-', '').title()}",
                parameter_name=f"/riskintel360/{self.env_name}/premium/api-keys/{key_name}",
                string_value="OPTIONAL_PLACEHOLDER",
                description=f"Premium API key for {key_name} (optional)",
                type=ssm.ParameterType.SECURE_STRING,
                key_id=kms_key.key_id,
            )
        
        return parameters
    
    def _create_ml_infrastructure(self) -> Dict[str, Any]:
        """Create ML infrastructure for fraud detection and risk assessment"""
        resources = {}
        
        # Create SageMaker execution role
        resources["sagemaker_role"] = iam.Role(
            self,
            "SageMakerExecutionRole",
            role_name=f"riskintel360-sagemaker-role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
            ],
        )
        
        # Grant access to fintech data bucket
        self.fintech_resources["fintech_data_bucket"].grant_read_write(resources["sagemaker_role"])
        
        # Create SageMaker model registry for fraud detection models
        resources["model_package_group"] = sagemaker.CfnModelPackageGroup(
            self,
            "FraudDetectionModelGroup",
            model_package_group_name=f"riskintel360-fraud-models-{self.env_name}",
            model_package_group_description="Model package group for fraud detection models",
        )
        
        # Create Lambda function for real-time ML inference
        resources["ml_inference_lambda"] = lambda_.Function(
            self,
            "MLInferenceLambda",
            function_name=f"riskintel360-ml-inference-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_inline("""
import json
import boto3
import numpy as np
from sklearn.ensemble import IsolationForest
import pickle
import base64

def lambda_handler(event, context):
    try:
        # Parse transaction data from event
        transaction_data = json.loads(event['body'])
        
        # Load pre-trained model (placeholder - would load from S3)
        # model = pickle.loads(base64.b64decode(model_data))
        
        # For demo, use simple anomaly detection
        isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        
        # Mock training data for demo
        normal_data = np.random.normal(100, 20, (1000, 5))
        isolation_forest.fit(normal_data)
        
        # Score the transaction
        transaction_array = np.array(transaction_data['features']).reshape(1, -1)
        anomaly_score = isolation_forest.decision_function(transaction_array)[0]
        is_anomaly = isolation_forest.predict(transaction_array)[0] == -1
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'transaction_id': transaction_data.get('transaction_id'),
                'anomaly_score': float(anomaly_score),
                'is_fraud': bool(is_anomaly),
                'confidence': abs(float(anomaly_score)),
                'model_version': 'v1.0'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
            """),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "ENVIRONMENT": self.env_name,
                "FINTECH_DATA_BUCKET": self.fintech_resources["fintech_data_bucket"].bucket_name,
            },
        )
        
        # Grant Lambda permissions to access DynamoDB and S3
        self.fintech_resources["fraud_detection_table"].grant_read_write_data(resources["ml_inference_lambda"])
        self.fintech_resources["fintech_data_bucket"].grant_read(resources["ml_inference_lambda"])
        
        return resources
    
    def _create_cost_monitoring(self) -> Dict[str, Any]:
        """Create cost monitoring and optimization resources"""
        resources = {}
        
        # Create CloudWatch dashboard for cost monitoring
        resources["cost_dashboard"] = cloudwatch.Dashboard(
            self,
            "CostMonitoringDashboard",
            dashboard_name=f"riskintel360-costs-{self.env_name}",
        )
        
        # Create cost anomaly detection
        resources["cost_anomaly_detector"] = cloudwatch.CfnAnomalyDetector(
            self,
            "CostAnomalyDetector",
            metric_name="EstimatedCharges",
            namespace="AWS/Billing",
            stat="Maximum",
            dimensions=[
                cloudwatch.CfnAnomalyDetector.DimensionProperty(
                    name="Currency",
                    value="USD"
                )
            ],
        )
        
        # Create cost alarm
        resources["cost_alarm"] = cloudwatch.Alarm(
            self,
            "CostAlarm",
            alarm_name=f"riskintel360-cost-alarm-{self.env_name}",
            alarm_description="Alert when costs exceed threshold",
            metric=cloudwatch.Metric(
                namespace="AWS/Billing",
                metric_name="EstimatedCharges",
                dimensions_map={"Currency": "USD"},
                statistic="Maximum",
            ),
            threshold=100 if not self.is_production else 1000,  # $100 dev, $1000 prod
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        
        # Create Lambda function for cost optimization
        resources["cost_optimizer_lambda"] = lambda_.Function(
            self,
            "CostOptimizerLambda",
            function_name=f"riskintel360-cost-optimizer-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_inline("""
import json
import boto3

def lambda_handler(event, context):
    try:
        # Initialize AWS clients
        ecs_client = boto3.client('ecs')
        cloudwatch = boto3.client('cloudwatch')
        
        # Get current ECS service metrics
        # Implement cost optimization logic here
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Cost optimization check completed',
                'recommendations': []
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
            """),
            timeout=Duration.minutes(5),
            memory_size=256,
        )
        
        # Create EventBridge rule for daily cost optimization
        resources["cost_optimization_rule"] = events.Rule(
            self,
            "CostOptimizationRule",
            rule_name=f"riskintel360-cost-optimization-{self.env_name}",
            description="Daily cost optimization check",
            schedule=events.Schedule.cron(hour="6", minute="0"),  # 6 AM UTC daily
        )
        
        resources["cost_optimization_rule"].add_target(
            targets.LambdaFunction(resources["cost_optimizer_lambda"])
        )
        
        return resources
    
    def _create_demo_resources(self) -> Dict[str, Any]:
        """Create resources specifically for competition demo"""
        resources = {}
        
        # Create demo data bucket
        resources["demo_data_bucket"] = s3.Bucket(
            self,
            "DemoDataBucket",
            bucket_name=f"riskintel360-demo-data-{self.env_name}-{self.account}",
            versioned=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,  # Always destroy demo resources
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DemoDataCleanup",
                    enabled=True,
                    expiration=Duration.days(30),  # Clean up demo data after 30 days
                )
            ],
        )
        
        # Create demo Lambda function for synthetic data generation
        resources["demo_data_generator"] = lambda_.Function(
            self,
            "DemoDataGenerator",
            function_name=f"riskintel360-demo-generator-{self.env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_inline("""
import json
import boto3
import random
import datetime
from decimal import Decimal

def lambda_handler(event, context):
    try:
        # Generate synthetic financial data for demo
        demo_data = {
            'transactions': generate_demo_transactions(),
            'market_data': generate_demo_market_data(),
            'regulatory_updates': generate_demo_regulatory_data(),
            'generated_at': datetime.datetime.utcnow().isoformat()
        }
        
        # Store in S3 for demo
        s3 = boto3.client('s3')
        bucket_name = event.get('bucket_name')
        
        if bucket_name:
            s3.put_object(
                Bucket=bucket_name,
                Key=f"demo-data/{datetime.datetime.utcnow().strftime('%Y-%m-%d')}/synthetic_data.json",
                Body=json.dumps(demo_data, default=str),
                ContentType='application/json'
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Demo data generated successfully',
                'records_generated': len(demo_data['transactions'])
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def generate_demo_transactions():
    transactions = []
    for i in range(1000):
        # Generate normal and anomalous transactions
        is_fraud = random.random() < 0.05  # 5% fraud rate
        
        if is_fraud:
            amount = random.uniform(5000, 50000)  # Large amounts
            location = random.choice(['Unknown', 'Foreign'])
        else:
            amount = random.uniform(10, 1000)  # Normal amounts
            location = random.choice(['Local', 'Domestic'])
        
        transactions.append({
            'transaction_id': f'TXN_{i:06d}',
            'amount': round(amount, 2),
            'location': location,
            'timestamp': (datetime.datetime.utcnow() - datetime.timedelta(minutes=random.randint(0, 1440))).isoformat(),
            'is_fraud': is_fraud
        })
    
    return transactions

def generate_demo_market_data():
    return {
        'SPY': {'price': 450.25, 'change': 2.15, 'volume': 50000000},
        'QQQ': {'price': 375.80, 'change': -1.25, 'volume': 30000000},
        'VIX': {'price': 18.45, 'change': 0.85, 'volume': 15000000}
    }

def generate_demo_regulatory_data():
    return [
        {
            'regulation_id': 'SEC-2024-001',
            'title': 'Enhanced Fintech Reporting Requirements',
            'effective_date': '2024-06-01',
            'impact': 'Medium',
            'source': 'SEC'
        }
    ]
            """),
            timeout=Duration.minutes(5),
            memory_size=512,
            environment={
                "DEMO_BUCKET": resources["demo_data_bucket"].bucket_name,
            },
        )
        
        # Grant Lambda permissions
        resources["demo_data_bucket"].grant_write(resources["demo_data_generator"])
        
        return resources