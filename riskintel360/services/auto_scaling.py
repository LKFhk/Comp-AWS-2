"""
AWS Auto-Scaling Service for RiskIntel360 Platform
Manages ECS Fargate auto-scaling based on demand (3-50 instances).
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from riskintel360.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ScalingMetrics:
    """Scaling metrics data structure"""
    cpu_utilization: float
    memory_utilization: float
    active_sessions: int
    request_rate: float
    response_time: float
    timestamp: datetime


@dataclass
class ScalingPolicy:
    """Auto-scaling policy configuration"""
    name: str
    metric_type: str
    target_value: float
    scale_out_cooldown: int = 120  # seconds
    scale_in_cooldown: int = 300   # seconds
    min_capacity: int = 3
    max_capacity: int = 50


class AutoScalingService:
    """ECS Fargate auto-scaling service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.environment = self.settings.environment.value
        
        # Get AWS region from settings or use default
        aws_region = getattr(self.settings, 'aws_region', 'us-east-1')
        
        # AWS clients with region
        self.ecs_client = boto3.client('ecs', region_name=aws_region)
        self.application_autoscaling_client = boto3.client('application-autoscaling', region_name=aws_region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=aws_region)
        
        # Service configuration
        self.cluster_name = f"RiskIntel360-{self.environment}"
        self.service_name = f"RiskIntel360-{self.environment}"
        self.resource_id = f"service/{self.cluster_name}/{self.service_name}"
        
        # Scaling policies
        self.scaling_policies = self._initialize_scaling_policies()
        
        # Metrics tracking
        self.metrics_history: List[ScalingMetrics] = []
        self.max_history_size = 100
    
    def _initialize_scaling_policies(self) -> List[ScalingPolicy]:
        """Initialize auto-scaling policies"""
        if self.environment == "production":
            return [
                ScalingPolicy(
                    name="cpu-scaling",
                    metric_type="CPUUtilization",
                    target_value=70.0,
                    scale_out_cooldown=120,
                    scale_in_cooldown=300,
                    min_capacity=3,
                    max_capacity=50
                ),
                ScalingPolicy(
                    name="memory-scaling",
                    metric_type="MemoryUtilization",
                    target_value=80.0,
                    scale_out_cooldown=120,
                    scale_in_cooldown=300,
                    min_capacity=3,
                    max_capacity=50
                ),
                ScalingPolicy(
                    name="request-rate-scaling",
                    metric_type="RequestRate",
                    target_value=100.0,
                    scale_out_cooldown=60,
                    scale_in_cooldown=180,
                    min_capacity=3,
                    max_capacity=50
                ),
                ScalingPolicy(
                    name="active-sessions-scaling",
                    metric_type="ActiveSessions",
                    target_value=20.0,
                    scale_out_cooldown=90,
                    scale_in_cooldown=240,
                    min_capacity=3,
                    max_capacity=50
                )
            ]
        else:
            return [
                ScalingPolicy(
                    name="cpu-scaling",
                    metric_type="CPUUtilization",
                    target_value=80.0,
                    scale_out_cooldown=180,
                    scale_in_cooldown=300,
                    min_capacity=1,
                    max_capacity=5
                ),
                ScalingPolicy(
                    name="memory-scaling",
                    metric_type="MemoryUtilization",
                    target_value=85.0,
                    scale_out_cooldown=180,
                    scale_in_cooldown=300,
                    min_capacity=1,
                    max_capacity=5
                )
            ]
    
    async def setup_auto_scaling(self) -> bool:
        """Setup auto-scaling for ECS service"""
        try:
            # Register scalable target
            await self._register_scalable_target()
            
            # Create scaling policies
            for policy in self.scaling_policies:
                await self._create_scaling_policy(policy)
            
            logger.info(f"Auto-scaling setup completed for {self.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup auto-scaling: {e}")
            return False
    
    async def _register_scalable_target(self) -> None:
        """Register ECS service as scalable target"""
        try:
            policy = self.scaling_policies[0]  # Use first policy for min/max capacity
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.application_autoscaling_client.register_scalable_target,
                {
                    'ServiceNamespace': 'ecs',
                    'ResourceId': self.resource_id,
                    'ScalableDimension': 'ecs:service:DesiredCount',
                    'MinCapacity': policy.min_capacity,
                    'MaxCapacity': policy.max_capacity,
                    'RoleARN': f'arn:aws:iam::{boto3.Session().get_credentials().access_key}:role/application-autoscaling-ecs-service-role'
                }
            )
            
            logger.info(f"Registered scalable target: {response}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationException':
                logger.info("Scalable target already registered")
            else:
                raise
    
    async def _create_scaling_policy(self, policy: ScalingPolicy) -> None:
        """Create auto-scaling policy"""
        try:
            policy_config = {
                'PolicyName': f"{self.service_name}-{policy.name}",
                'ServiceNamespace': 'ecs',
                'ResourceId': self.resource_id,
                'ScalableDimension': 'ecs:service:DesiredCount',
                'PolicyType': 'TargetTrackingScaling',
                'TargetTrackingScalingPolicyConfiguration': {
                    'TargetValue': policy.target_value,
                    'ScaleOutCooldown': policy.scale_out_cooldown,
                    'ScaleInCooldown': policy.scale_in_cooldown,
                }
            }
            
            # Configure metric specification based on policy type
            if policy.metric_type == "CPUUtilization":
                policy_config['TargetTrackingScalingPolicyConfiguration']['PredefinedMetricSpecification'] = {
                    'PredefinedMetricType': 'ECSServiceAverageCPUUtilization'
                }
            elif policy.metric_type == "MemoryUtilization":
                policy_config['TargetTrackingScalingPolicyConfiguration']['PredefinedMetricSpecification'] = {
                    'PredefinedMetricType': 'ECSServiceAverageMemoryUtilization'
                }
            else:
                # Custom metric
                policy_config['TargetTrackingScalingPolicyConfiguration']['CustomizedMetricSpecification'] = {
                    'MetricName': policy.metric_type,
                    'Namespace': 'RiskIntel360/Platform',
                    'Statistic': 'Average'
                }
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.application_autoscaling_client.put_scaling_policy,
                policy_config
            )
            
            logger.info(f"Created scaling policy {policy.name}: {response['PolicyARN']}")
            
        except ClientError as e:
            logger.error(f"Failed to create scaling policy {policy.name}: {e}")
            raise
    
    async def get_current_capacity(self) -> int:
        """Get current service capacity"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.ecs_client.describe_services,
                {
                    'cluster': self.cluster_name,
                    'services': [self.service_name]
                }
            )
            
            if response['services']:
                return response['services'][0]['desiredCount']
            return 0
            
        except ClientError as e:
            logger.error(f"Failed to get current capacity: {e}")
            return 0
    
    async def get_running_tasks(self) -> int:
        """Get number of running tasks"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.ecs_client.describe_services,
                {
                    'cluster': self.cluster_name,
                    'services': [self.service_name]
                }
            )
            
            if response['services']:
                return response['services'][0]['runningCount']
            return 0
            
        except ClientError as e:
            logger.error(f"Failed to get running tasks: {e}")
            return 0
    
    async def collect_metrics(self) -> ScalingMetrics:
        """Collect current scaling metrics"""
        try:
            # Get ECS service metrics
            cpu_utilization = await self._get_cloudwatch_metric(
                'AWS/ECS',
                'CPUUtilization',
                [
                    {'Name': 'ServiceName', 'Value': self.service_name},
                    {'Name': 'ClusterName', 'Value': self.cluster_name}
                ]
            )
            
            memory_utilization = await self._get_cloudwatch_metric(
                'AWS/ECS',
                'MemoryUtilization',
                [
                    {'Name': 'ServiceName', 'Value': self.service_name},
                    {'Name': 'ClusterName', 'Value': self.cluster_name}
                ]
            )
            
            # Get custom application metrics
            active_sessions = await self._get_cloudwatch_metric(
                'RiskIntel360/Platform',
                'ActiveSessions',
                []
            )
            
            request_rate = await self._get_cloudwatch_metric(
                'RiskIntel360/Platform',
                'RequestRate',
                []
            )
            
            response_time = await self._get_cloudwatch_metric(
                'RiskIntel360/Platform',
                'ResponseTime',
                []
            )
            
            metrics = ScalingMetrics(
                cpu_utilization=cpu_utilization or 0.0,
                memory_utilization=memory_utilization or 0.0,
                active_sessions=int(active_sessions or 0),
                request_rate=request_rate or 0.0,
                response_time=response_time or 0.0,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Store metrics history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return ScalingMetrics(0.0, 0.0, 0, 0.0, 0.0, datetime.now(timezone.utc))
    
    async def _get_cloudwatch_metric(
        self,
        namespace: str,
        metric_name: str,
        dimensions: List[Dict[str, str]]
    ) -> Optional[float]:
        """Get CloudWatch metric value"""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=5)
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.cloudwatch_client.get_metric_statistics,
                {
                    'Namespace': namespace,
                    'MetricName': metric_name,
                    'Dimensions': dimensions,
                    'StartTime': start_time,
                    'EndTime': end_time,
                    'Period': 300,  # 5 minutes
                    'Statistics': ['Average']
                }
            )
            
            if response['Datapoints']:
                # Return the most recent datapoint
                latest = max(response['Datapoints'], key=lambda x: x['Timestamp'])
                return latest['Average']
            
            return None
            
        except ClientError as e:
            logger.warning(f"Failed to get CloudWatch metric {metric_name}: {e}")
            return None
    
    async def publish_custom_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = 'Count',
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """Publish custom metric to CloudWatch"""
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.now(timezone.utc)
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.cloudwatch_client.put_metric_data,
                {
                    'Namespace': 'RiskIntel360/Platform',
                    'MetricData': [metric_data]
                }
            )
            
        except ClientError as e:
            logger.error(f"Failed to publish metric {metric_name}: {e}")
    
    async def get_scaling_activities(self) -> List[Dict[str, Any]]:
        """Get recent scaling activities"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.application_autoscaling_client.describe_scaling_activities,
                {
                    'ServiceNamespace': 'ecs',
                    'ResourceId': self.resource_id,
                    'ScalableDimension': 'ecs:service:DesiredCount',
                    'MaxResults': 50
                }
            )
            
            return response.get('ScalingActivities', [])
            
        except ClientError as e:
            logger.error(f"Failed to get scaling activities: {e}")
            return []
    
    async def update_scaling_policy(self, policy_name: str, target_value: float) -> bool:
        """Update scaling policy target value"""
        try:
            policy_arn = f"arn:aws:autoscaling::{boto3.Session().region_name}:scalingPolicy:{policy_name}"
            
            # Find the policy configuration
            policy = next((p for p in self.scaling_policies if p.name == policy_name), None)
            if not policy:
                logger.error(f"Policy {policy_name} not found")
                return False
            
            policy.target_value = target_value
            
            # Update the policy
            await self._create_scaling_policy(policy)
            
            logger.info(f"Updated scaling policy {policy_name} target value to {target_value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update scaling policy {policy_name}: {e}")
            return False
    
    async def manual_scale(self, desired_capacity: int) -> bool:
        """Manually scale the service to desired capacity"""
        try:
            # Validate capacity bounds
            min_capacity = min(p.min_capacity for p in self.scaling_policies)
            max_capacity = max(p.max_capacity for p in self.scaling_policies)
            
            if desired_capacity < min_capacity or desired_capacity > max_capacity:
                logger.error(f"Desired capacity {desired_capacity} outside bounds [{min_capacity}, {max_capacity}]")
                return False
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.ecs_client.update_service,
                {
                    'cluster': self.cluster_name,
                    'service': self.service_name,
                    'desiredCount': desired_capacity
                }
            )
            
            logger.info(f"Manually scaled service to {desired_capacity} instances")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to manually scale service: {e}")
            return False
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of recent metrics"""
        if not self.metrics_history:
            return {}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 metrics
        
        return {
            'avg_cpu_utilization': sum(m.cpu_utilization for m in recent_metrics) / len(recent_metrics),
            'avg_memory_utilization': sum(m.memory_utilization for m in recent_metrics) / len(recent_metrics),
            'avg_active_sessions': sum(m.active_sessions for m in recent_metrics) / len(recent_metrics),
            'avg_request_rate': sum(m.request_rate for m in recent_metrics) / len(recent_metrics),
            'avg_response_time': sum(m.response_time for m in recent_metrics) / len(recent_metrics),
            'latest_timestamp': recent_metrics[-1].timestamp.isoformat(),
            'metrics_count': len(self.metrics_history)
        }


# Global auto-scaling service instance
_auto_scaling_service: Optional[AutoScalingService] = None


def get_auto_scaling_service() -> AutoScalingService:
    """Get the global auto-scaling service instance"""
    global _auto_scaling_service
    if _auto_scaling_service is None:
        _auto_scaling_service = AutoScalingService()
    return _auto_scaling_service
