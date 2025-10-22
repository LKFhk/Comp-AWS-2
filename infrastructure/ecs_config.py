"""
AWS ECS Configuration for riskintel360 Platform
Task definitions and service configurations for auto-scaling agent deployment.
"""

import json
from typing import Dict, List, Any, Optional
from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_logs as logs,
    aws_iam as iam,
    aws_applicationautoscaling as appscaling,
    aws_cloudwatch as cloudwatch,
    Duration,
    RemovalPolicy,
)
from constructs import Construct


class ECSAgentCluster(Construct):
    """ECS cluster configuration for riskintel360 agents"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        environment: str = "development",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.environment = environment
        self.vpc = vpc
        
        # Create ECS cluster
        self.cluster = ecs.Cluster(
            self,
            "riskintel360Cluster",
            cluster_name=f"riskintel360-{environment}",
            vpc=vpc,
            container_insights=True,
        )
        
        # Create task execution role
        self.execution_role = self._create_execution_role()
        
        # Create task role
        self.task_role = self._create_task_role()
        
        # Create log group
        self.log_group = logs.LogGroup(
            self,
            "AgentLogGroup",
            log_group_name=f"/ecs/riskintel360-{environment}",
            retention=logs.RetentionDays.ONE_WEEK if environment == "development" else logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY if environment == "development" else RemovalPolicy.RETAIN,
        )
        
        # Create task definition
        self.task_definition = self._create_task_definition()
        
        # Create service
        self.service = self._create_service()
        
        # Setup auto-scaling
        self._setup_auto_scaling()
    
    def _create_execution_role(self) -> iam.Role:
        """Create ECS task execution role"""
        role = iam.Role(
            self,
            "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ],
        )
        
        # Add permissions for Secrets Manager and Parameter Store
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:GetParametersByPath",
                ],
                resources=["*"],
            )
        )
        
        return role
    
    def _create_task_role(self) -> iam.Role:
        """Create ECS task role with necessary permissions"""
        role = iam.Role(
            self,
            "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        
        # Add Bedrock permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:GetFoundationModel",
                    "bedrock:ListFoundationModels",
                ],
                resources=["*"],
            )
        )
        
        # Add DynamoDB permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                ],
                resources=[f"arn:aws:dynamodb:*:*:table/riskintel360-{self.environment}-*"],
            )
        )
        
        # Add S3 permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                ],
                resources=[f"arn:aws:s3:::riskintel360-{self.environment}-*/*"],
            )
        )
        
        # Add CloudWatch permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["*"],
            )
        )
        
        return role
    
    def _create_task_definition(self) -> ecs.FargateTaskDefinition:
        """Create ECS task definition"""
        
        # CPU and memory configurations based on environment
        if self.environment == "production":
            cpu = 1024  # 1 vCPU
            memory_limit_mib = 2048  # 2 GB
        else:
            cpu = 512   # 0.5 vCPU
            memory_limit_mib = 1024  # 1 GB
        
        task_def = ecs.FargateTaskDefinition(
            self,
            "AgentTaskDefinition",
            family=f"riskintel360-{self.environment}",
            cpu=cpu,
            memory_limit_mib=memory_limit_mib,
            execution_role=self.execution_role,
            task_role=self.task_role,
        )
        
        # Environment variables
        environment_vars = {
            "ENVIRONMENT": self.environment,
            "AWS_DEFAULT_REGION": Stack.of(self).region,
            "LOG_LEVEL": "INFO" if self.environment == "production" else "DEBUG",
            "PYTHONUNBUFFERED": "1",
        }
        
        # Container definition
        container = task_def.add_container(
            "riskintel360Agent",
            image=ecs.ContainerImage.from_registry(f"riskintel360-platform:{self.environment}"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="agent",
                log_group=self.log_group,
            ),
            environment=environment_vars,
            health_check=ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                retries=3,
                start_period=Duration.seconds(60),
            ),
        )
        
        # Port mapping
        container.add_port_mappings(
            ecs.PortMapping(
                container_port=8000,
                protocol=ecs.Protocol.TCP,
            )
        )
        
        return task_def
    
    def _create_service(self) -> ecs.FargateService:
        """Create ECS service"""
        
        # Service configuration based on environment
        if self.environment == "production":
            desired_count = 3
            max_healthy_percent = 200
            min_healthy_percent = 50
        else:
            desired_count = 1
            max_healthy_percent = 200
            min_healthy_percent = 0
        
        service = ecs.FargateService(
            self,
            "AgentService",
            service_name=f"riskintel360-{self.environment}",
            cluster=self.cluster,
            task_definition=self.task_definition,
            desired_count=desired_count,
            deployment_configuration=ecs.DeploymentConfiguration(
                maximum_percent=max_healthy_percent,
                minimum_healthy_percent=min_healthy_percent,
            ),
            health_check_grace_period=Duration.seconds(60),
            enable_logging=True,
        )
        
        return service
    
    def _setup_auto_scaling(self) -> None:
        """Setup auto-scaling for the ECS service"""
        
        # Auto-scaling configuration
        min_capacity = 3 if self.environment == "production" else 1
        max_capacity = 50 if self.environment == "production" else 5
        
        # Create scalable target
        scalable_target = self.service.auto_scale_task_count(
            min_capacity=min_capacity,
            max_capacity=max_capacity,
        )
        
        # CPU-based scaling
        scalable_target.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.minutes(5),
            scale_out_cooldown=Duration.minutes(2),
        )
        
        # Memory-based scaling
        scalable_target.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=80,
            scale_in_cooldown=Duration.minutes(5),
            scale_out_cooldown=Duration.minutes(2),
        )
        
        # Custom metric scaling (request count)
        if self.environment == "production":
            scalable_target.scale_on_metric(
                "RequestCountScaling",
                metric=cloudwatch.Metric(
                    namespace="riskintel360/Platform",
                    metric_name="ActiveSessions",
                    statistic="Average",
                ),
                scaling_steps=[
                    appscaling.ScalingInterval(upper=10, change=-1),
                    appscaling.ScalingInterval(lower=20, upper=30, change=0),
                    appscaling.ScalingInterval(lower=30, upper=50, change=+1),
                    appscaling.ScalingInterval(lower=50, change=+2),
                ],
                adjustment_type=appscaling.AdjustmentType.CHANGE_IN_CAPACITY,
            )


def generate_task_definition_json(environment: str = "development") -> Dict[str, Any]:
    """Generate ECS task definition JSON for standalone deployment"""
    
    # Base configuration
    if environment == "production":
        cpu = "1024"
        memory = "2048"
        log_level = "INFO"
    else:
        cpu = "512"
        memory = "1024"
        log_level = "DEBUG"
    
    task_definition = {
        "family": f"riskintel360-{environment}",
        "networkMode": "awsvpc",
        "requiresCompatibilities": ["FARGATE"],
        "cpu": cpu,
        "memory": memory,
        "executionRoleArn": f"arn:aws:iam::{{AWS_ACCOUNT_ID}}:role/riskintel360-{environment}-execution-role",
        "taskRoleArn": f"arn:aws:iam::{{AWS_ACCOUNT_ID}}:role/riskintel360-{environment}-task-role",
        "containerDefinitions": [
            {
                "name": "riskintel360-agent",
                "image": f"{{AWS_ACCOUNT_ID}}.dkr.ecr.{{AWS_REGION}}.amazonaws.com/riskintel360-platform:{environment}",
                "essential": True,
                "portMappings": [
                    {
                        "containerPort": 8000,
                        "protocol": "tcp"
                    }
                ],
                "environment": [
                    {"name": "ENVIRONMENT", "value": environment},
                    {"name": "LOG_LEVEL", "value": log_level},
                    {"name": "PYTHONUNBUFFERED", "value": "1"},
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": f"/ecs/riskintel360-{environment}",
                        "awslogs-region": "{{AWS_REGION}}",
                        "awslogs-stream-prefix": "agent"
                    }
                },
                "healthCheck": {
                    "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                    "interval": 30,
                    "timeout": 5,
                    "retries": 3,
                    "startPeriod": 60
                },
                "stopTimeout": 30,
            }
        ]
    }
    
    return task_definition


def generate_service_definition_json(environment: str = "development") -> Dict[str, Any]:
    """Generate ECS service definition JSON for standalone deployment"""
    
    # Service configuration
    if environment == "production":
        desired_count = 3
        max_percent = 200
        min_percent = 50
    else:
        desired_count = 1
        max_percent = 200
        min_percent = 0
    
    service_definition = {
        "serviceName": f"riskintel360-{environment}",
        "cluster": f"riskintel360-{environment}",
        "taskDefinition": f"riskintel360-{environment}",
        "desiredCount": desired_count,
        "launchType": "FARGATE",
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "subnets": ["{{SUBNET_ID_1}}", "{{SUBNET_ID_2}}"],
                "securityGroups": ["{{SECURITY_GROUP_ID}}"],
                "assignPublicIp": "ENABLED" if environment == "development" else "DISABLED"
            }
        },
        "deploymentConfiguration": {
            "maximumPercent": max_percent,
            "minimumHealthyPercent": min_percent,
            "deploymentCircuitBreaker": {
                "enable": True,
                "rollback": True
            }
        },
        "healthCheckGracePeriodSeconds": 60,
        "enableExecuteCommand": environment == "development",
    }
    
    return service_definition


# Export task and service definitions as JSON files
if __name__ == "__main__":
    import os
    
    # Create output directory
    os.makedirs("ecs-definitions", exist_ok=True)
    
    # Generate definitions for both environments
    for env in ["development", "production"]:
        # Task definition
        task_def = generate_task_definition_json(env)
        with open(f"ecs-definitions/task-definition-{env}.json", "w") as f:
            json.dump(task_def, f, indent=2)
        
        # Service definition
        service_def = generate_service_definition_json(env)
        with open(f"ecs-definitions/service-definition-{env}.json", "w") as f:
            json.dump(service_def, f, indent=2)
    
    print("ECS definitions generated successfully!")
