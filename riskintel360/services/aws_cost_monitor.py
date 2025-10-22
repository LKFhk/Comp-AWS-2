"""
AWS Cost Optimization Monitoring Service

This service tracks AWS costs across all services used by RiskIntel360,
monitors public vs premium data usage costs, and provides optimization recommendations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class CostAlertLevel(Enum):
    """Cost alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ServiceCategory(Enum):
    """AWS service categories for cost tracking"""
    AI_ML = "ai_ml"  # Bedrock Nova, SageMaker
    COMPUTE = "compute"  # ECS, Lambda
    STORAGE = "storage"  # S3, EBS
    MONITORING = "monitoring"  # CloudWatch, X-Ray
    DATA = "data"  # DynamoDB, Aurora
    NETWORKING = "networking"  # API Gateway, VPC


@dataclass
class CostMetric:
    """Individual cost metric"""
    service_name: str
    category: ServiceCategory
    current_cost: float
    projected_monthly_cost: float
    usage_hours: float
    cost_per_hour: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CostAlert:
    """Cost alert notification"""
    alert_id: str
    level: CostAlertLevel
    service_name: str
    message: str
    current_cost: float
    threshold: float
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CostOptimizationRecommendation:
    """Cost optimization recommendation"""
    recommendation_id: str
    service_name: str
    category: ServiceCategory
    description: str
    potential_savings: float
    implementation_effort: str  # "low", "medium", "high"
    priority: int  # 1-5, 1 being highest
    action_items: List[str] = field(default_factory=list)


class AWSCostMonitor:
    """
    AWS Cost Optimization Monitoring Service
    
    Tracks costs across all AWS services, monitors usage patterns,
    and provides optimization recommendations for RiskIntel360.
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.cost_explorer = None
        self.cloudwatch = None
        self.pricing = None
        
        # Cost thresholds (USD)
        self.cost_thresholds = {
            "bedrock": {"warning": 100.0, "critical": 500.0, "emergency": 1000.0},
            "ecs": {"warning": 50.0, "critical": 200.0, "emergency": 500.0},
            "s3": {"warning": 20.0, "critical": 100.0, "emergency": 300.0},
            "cloudwatch": {"warning": 30.0, "critical": 150.0, "emergency": 400.0},
            "api_gateway": {"warning": 25.0, "critical": 100.0, "emergency": 250.0},
            "total_monthly": {"warning": 300.0, "critical": 1000.0, "emergency": 2500.0}
        }
        
        # Public vs premium data cost tracking
        self.data_cost_targets = {
            "public_data_percentage": 0.8,  # 80% public data target
            "premium_data_budget": 200.0,   # Monthly premium data budget
            "cost_reduction_target": 0.8    # 80% cost reduction target
        }
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AWS clients"""
        try:
            self.cost_explorer = boto3.client('ce', region_name=self.region)
            self.cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            self.pricing = boto3.client('pricing', region_name='us-east-1')  # Pricing API only in us-east-1
            logger.info("AWS cost monitoring clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise
    
    async def get_current_costs(self, days_back: int = 7) -> Dict[str, CostMetric]:
        """
        Get current costs for all AWS services
        
        Args:
            days_back: Number of days to look back for cost data
            
        Returns:
            Dictionary of service costs
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Get cost and usage data
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self._get_cost_and_usage,
                start_date.isoformat(),
                end_date.isoformat()
            )
            
            costs = {}
            
            if 'ResultsByTime' in response:
                for result in response['ResultsByTime']:
                    if 'Groups' in result:
                        for group in result['Groups']:
                            service_name = group['Keys'][0] if group['Keys'] else 'Unknown'
                            amount = float(group['Metrics']['BlendedCost']['Amount'])
                            
                            # Categorize service
                            category = self._categorize_service(service_name)
                            
                            # Calculate projections
                            daily_cost = amount / days_back
                            monthly_projection = daily_cost * 30
                            
                            costs[service_name] = CostMetric(
                                service_name=service_name,
                                category=category,
                                current_cost=amount,
                                projected_monthly_cost=monthly_projection,
                                usage_hours=days_back * 24,
                                cost_per_hour=amount / (days_back * 24) if days_back > 0 else 0
                            )
            
            logger.info(f"Retrieved cost data for {len(costs)} services")
            return costs
            
        except Exception as e:
            logger.error(f"Failed to get current costs: {e}")
            return {}
    
    def _get_cost_and_usage(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get cost and usage data from AWS Cost Explorer"""
        return self.cost_explorer.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='DAILY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
    
    def _categorize_service(self, service_name: str) -> ServiceCategory:
        """Categorize AWS service by type"""
        service_mappings = {
            'Amazon Bedrock': ServiceCategory.AI_ML,
            'Amazon SageMaker': ServiceCategory.AI_ML,
            'Amazon Elastic Container Service': ServiceCategory.COMPUTE,
            'AWS Lambda': ServiceCategory.COMPUTE,
            'Amazon Simple Storage Service': ServiceCategory.STORAGE,
            'Amazon Elastic Block Store': ServiceCategory.STORAGE,
            'Amazon CloudWatch': ServiceCategory.MONITORING,
            'AWS X-Ray': ServiceCategory.MONITORING,
            'Amazon DynamoDB': ServiceCategory.DATA,
            'Amazon Aurora': ServiceCategory.DATA,
            'Amazon API Gateway': ServiceCategory.NETWORKING,
            'Amazon Virtual Private Cloud': ServiceCategory.NETWORKING
        }
        
        for service_key, category in service_mappings.items():
            if service_key.lower() in service_name.lower():
                return category
        
        return ServiceCategory.COMPUTE  # Default category
    
    async def monitor_public_vs_premium_data_costs(self) -> Dict[str, Any]:
        """
        Monitor public data usage vs premium data costs
        
        Returns:
            Analysis of data source cost efficiency
        """
        try:
            # Simulate data source cost tracking (would integrate with actual usage metrics)
            public_data_sources = [
                "SEC EDGAR", "FINRA", "CFPB", "FRED", "Treasury.gov", "Yahoo Finance"
            ]
            
            premium_data_sources = [
                "Bloomberg API", "Reuters", "S&P Capital IQ", "Refinitiv"
            ]
            
            # Get CloudWatch metrics for data source usage
            public_usage_cost = await self._get_data_source_costs(public_data_sources)
            premium_usage_cost = await self._get_data_source_costs(premium_data_sources)
            
            total_data_cost = public_usage_cost + premium_usage_cost
            public_percentage = public_usage_cost / total_data_cost if total_data_cost > 0 else 1.0
            
            cost_reduction_achieved = 1.0 - (total_data_cost / self._estimate_traditional_data_costs())
            
            analysis = {
                "public_data_cost": public_usage_cost,
                "premium_data_cost": premium_usage_cost,
                "total_data_cost": total_data_cost,
                "public_data_percentage": public_percentage,
                "cost_reduction_achieved": cost_reduction_achieved,
                "target_public_percentage": self.data_cost_targets["public_data_percentage"],
                "target_cost_reduction": self.data_cost_targets["cost_reduction_target"],
                "meets_public_data_target": public_percentage >= self.data_cost_targets["public_data_percentage"],
                "meets_cost_reduction_target": cost_reduction_achieved >= self.data_cost_targets["cost_reduction_target"],
                "recommendations": []
            }
            
            # Generate recommendations
            if not analysis["meets_public_data_target"]:
                analysis["recommendations"].append(
                    f"Increase public data usage to {self.data_cost_targets['public_data_percentage']*100}% "
                    f"(currently {public_percentage*100:.1f}%)"
                )
            
            if not analysis["meets_cost_reduction_target"]:
                analysis["recommendations"].append(
                    f"Optimize data sources to achieve {self.data_cost_targets['cost_reduction_target']*100}% "
                    f"cost reduction (currently {cost_reduction_achieved*100:.1f}%)"
                )
            
            logger.info(f"Data cost analysis: {public_percentage*100:.1f}% public data usage")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to monitor data costs: {e}")
            return {}
    
    async def _get_data_source_costs(self, data_sources: List[str]) -> float:
        """Get estimated costs for data sources"""
        # This would integrate with actual usage metrics
        # For now, return simulated costs based on data source type
        base_cost_per_source = 10.0  # Base monthly cost per data source
        
        cost_multipliers = {
            "Bloomberg API": 50.0,
            "Reuters": 40.0,
            "S&P Capital IQ": 45.0,
            "Refinitiv": 35.0
        }
        
        total_cost = 0.0
        for source in data_sources:
            multiplier = cost_multipliers.get(source, 1.0)
            total_cost += base_cost_per_source * multiplier
        
        return total_cost
    
    def _estimate_traditional_data_costs(self) -> float:
        """Estimate traditional financial data costs without public-first approach"""
        # Traditional enterprise financial data costs
        return 5000.0  # Monthly cost for traditional data subscriptions
    
    async def get_cost_dashboard_data(self) -> Dict[str, Any]:
        """
        Get complete cost dashboard data
        
        Returns:
            Complete dashboard data for cost optimization
        """
        try:
            # Get all cost data components
            current_costs = await self.get_current_costs()
            data_analysis = await self.monitor_public_vs_premium_data_costs()
            efficiency_metrics = await self.track_auto_scaling_efficiency()
            alerts = await self.generate_cost_alerts(current_costs)
            recommendations = await self.generate_optimization_recommendations(current_costs, efficiency_metrics)
            cost_trends = await self._get_cost_trends()
            
            # Calculate summary metrics
            total_current_cost = sum(cost.current_cost for cost in current_costs.values())
            total_projected_monthly_cost = sum(cost.projected_monthly_cost for cost in current_costs.values())
            
            # Calculate potential savings from recommendations
            potential_monthly_savings = sum(rec.potential_savings for rec in recommendations)
            cost_reduction_percentage = (potential_monthly_savings / total_projected_monthly_cost * 100) if total_projected_monthly_cost > 0 else 0
            
            # Count high priority recommendations
            high_priority_recommendations = len([r for r in recommendations if r.priority <= 2])
            
            summary = {
                "total_current_cost": total_current_cost,
                "total_projected_monthly_cost": total_projected_monthly_cost,
                "potential_monthly_savings": potential_monthly_savings,
                "cost_reduction_percentage": cost_reduction_percentage,
                "active_alerts_count": len(alerts),
                "high_priority_recommendations": high_priority_recommendations,
                "last_updated": datetime.now().isoformat()
            }
            
            return {
                "summary": summary,
                "current_costs": current_costs,
                "data_cost_analysis": data_analysis,
                "efficiency_metrics": efficiency_metrics,
                "alerts": alerts,
                "recommendations": recommendations,
                "cost_trends": cost_trends,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get cost dashboard data: {e}")
            return {
                "summary": {},
                "current_costs": {},
                "data_cost_analysis": {},
                "efficiency_metrics": {},
                "alerts": [],
                "recommendations": [],
                "cost_trends": {},
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def _get_cost_trends(self, days: int = 30) -> Dict[str, List[float]]:
        """
        Get cost trends for the specified number of days
        
        Args:
            days: Number of days to get trends for
            
        Returns:
            Dictionary of service cost trends
        """
        try:
            trends = {}
            
            # Get historical cost data for each day
            for day_offset in range(days):
                date = datetime.now().date() - timedelta(days=day_offset)
                
                # For now, simulate trend data (would integrate with actual Cost Explorer historical data)
                if "total" not in trends:
                    trends["total"] = []
                
                # Simulate realistic cost trends with some variation
                base_cost = 100.0
                daily_variation = day_offset * 2.5 + (day_offset % 7) * 1.5  # Weekly pattern
                trends["total"].append(base_cost + daily_variation)
            
            # Reverse to get chronological order (oldest to newest)
            for service in trends:
                trends[service].reverse()
            
            # Add individual service trends
            service_trends = {
                "bedrock": [t * 0.4 for t in trends["total"]],
                "ecs": [t * 0.3 for t in trends["total"]],
                "s3": [t * 0.2 for t in trends["total"]],
                "cloudwatch": [t * 0.1 for t in trends["total"]]
            }
            
            trends.update(service_trends)
            
            logger.info(f"Generated cost trends for {days} days")
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get cost trends: {e}")
            return {"total": [0.0] * days}
    
    async def track_auto_scaling_efficiency(self) -> Dict[str, Any]:
        """
        Track ECS auto-scaling efficiency and resource utilization
        
        Returns:
            Auto-scaling efficiency metrics
        """
        try:
            # Get ECS cluster metrics
            cluster_metrics = await self._get_ecs_cluster_metrics()
            
            # Calculate efficiency metrics
            efficiency_analysis = {
                "average_cpu_utilization": cluster_metrics.get("avg_cpu", 0),
                "average_memory_utilization": cluster_metrics.get("avg_memory", 0),
                "scaling_events_count": cluster_metrics.get("scaling_events", 0),
                "cost_per_task": cluster_metrics.get("cost_per_task", 0),
                "efficiency_score": 0,
                "recommendations": []
            }
            
            # Calculate efficiency score (0-100)
            cpu_efficiency = min(efficiency_analysis["average_cpu_utilization"] / 70, 1.0)  # Target 70% CPU
            memory_efficiency = min(efficiency_analysis["average_memory_utilization"] / 80, 1.0)  # Target 80% memory
            efficiency_analysis["efficiency_score"] = (cpu_efficiency + memory_efficiency) / 2 * 100
            
            # Generate recommendations
            if efficiency_analysis["average_cpu_utilization"] < 50:
                efficiency_analysis["recommendations"].append(
                    "Consider reducing instance sizes - CPU utilization is low"
                )
            
            if efficiency_analysis["average_memory_utilization"] < 60:
                efficiency_analysis["recommendations"].append(
                    "Consider optimizing memory allocation - memory utilization is low"
                )
            
            if efficiency_analysis["scaling_events_count"] > 20:
                efficiency_analysis["recommendations"].append(
                    "High scaling frequency detected - consider adjusting scaling policies"
                )
            
            logger.info(f"Auto-scaling efficiency score: {efficiency_analysis['efficiency_score']:.1f}")
            return efficiency_analysis
            
        except Exception as e:
            logger.error(f"Failed to track auto-scaling efficiency: {e}")
            return {}
    
    async def _get_ecs_cluster_metrics(self) -> Dict[str, float]:
        """Get ECS cluster performance metrics"""
        try:
            # Get CloudWatch metrics for ECS
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            metrics = {}
            
            # CPU Utilization
            cpu_response = await asyncio.get_event_loop().run_in_executor(
                None,
                self._get_cloudwatch_metric,
                'AWS/ECS',
                'CPUUtilization',
                start_time,
                end_time
            )
            
            if cpu_response and 'Datapoints' in cpu_response:
                cpu_values = [dp['Average'] for dp in cpu_response['Datapoints']]
                metrics['avg_cpu'] = sum(cpu_values) / len(cpu_values) if cpu_values else 0
            
            # Memory Utilization
            memory_response = await asyncio.get_event_loop().run_in_executor(
                None,
                self._get_cloudwatch_metric,
                'AWS/ECS',
                'MemoryUtilization',
                start_time,
                end_time
            )
            
            if memory_response and 'Datapoints' in memory_response:
                memory_values = [dp['Average'] for dp in memory_response['Datapoints']]
                metrics['avg_memory'] = sum(memory_values) / len(memory_values) if memory_values else 0
            
            # Simulate other metrics
            metrics['scaling_events'] = 5  # Would get from auto-scaling events
            metrics['cost_per_task'] = 0.05  # Would calculate from actual costs
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get ECS metrics: {e}")
            return {}
    
    def _get_cloudwatch_metric(self, namespace: str, metric_name: str, 
                              start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get CloudWatch metric data"""
        return self.cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,  # 1 hour periods
            Statistics=['Average']
        )
    
    async def generate_cost_alerts(self, current_costs: Dict[str, CostMetric]) -> List[CostAlert]:
        """
        Generate cost alerts based on thresholds
        
        Args:
            current_costs: Current cost metrics
            
        Returns:
            List of cost alerts
        """
        alerts = []
        
        try:
            total_monthly_cost = sum(cost.projected_monthly_cost for cost in current_costs.values())
            
            # Check total monthly cost
            total_thresholds = self.cost_thresholds["total_monthly"]
            if total_monthly_cost >= total_thresholds["emergency"]:
                alerts.append(CostAlert(
                    alert_id=f"total_cost_emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    level=CostAlertLevel.EMERGENCY,
                    service_name="Total",
                    message=f"Emergency: Total monthly cost projection ${total_monthly_cost:.2f} exceeds emergency threshold ${total_thresholds['emergency']:.2f}",
                    current_cost=total_monthly_cost,
                    threshold=total_thresholds["emergency"],
                    recommendations=[
                        "Immediately review and reduce resource usage",
                        "Consider scaling down non-critical services",
                        "Implement aggressive cost optimization measures"
                    ]
                ))
            elif total_monthly_cost >= total_thresholds["critical"]:
                alerts.append(CostAlert(
                    alert_id=f"total_cost_critical_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    level=CostAlertLevel.CRITICAL,
                    service_name="Total",
                    message=f"Critical: Total monthly cost projection ${total_monthly_cost:.2f} exceeds critical threshold ${total_thresholds['critical']:.2f}",
                    current_cost=total_monthly_cost,
                    threshold=total_thresholds["critical"],
                    recommendations=[
                        "Review resource usage and optimize immediately",
                        "Consider implementing cost controls",
                        "Evaluate service necessity and usage patterns"
                    ]
                ))
            elif total_monthly_cost >= total_thresholds["warning"]:
                alerts.append(CostAlert(
                    alert_id=f"total_cost_warning_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    level=CostAlertLevel.WARNING,
                    service_name="Total",
                    message=f"Warning: Total monthly cost projection ${total_monthly_cost:.2f} exceeds warning threshold ${total_thresholds['warning']:.2f}",
                    current_cost=total_monthly_cost,
                    threshold=total_thresholds["warning"],
                    recommendations=[
                        "Monitor usage patterns closely",
                        "Consider cost optimization opportunities",
                        "Review upcoming usage projections"
                    ]
                ))
            
            # Check individual service costs
            for service_name, cost_metric in current_costs.items():
                service_key = self._get_service_threshold_key(service_name)
                if service_key in self.cost_thresholds:
                    thresholds = self.cost_thresholds[service_key]
                    monthly_cost = cost_metric.projected_monthly_cost
                    
                    if monthly_cost >= thresholds["emergency"]:
                        level = CostAlertLevel.EMERGENCY
                        threshold = thresholds["emergency"]
                    elif monthly_cost >= thresholds["critical"]:
                        level = CostAlertLevel.CRITICAL
                        threshold = thresholds["critical"]
                    elif monthly_cost >= thresholds["warning"]:
                        level = CostAlertLevel.WARNING
                        threshold = thresholds["warning"]
                    else:
                        continue
                    
                    alerts.append(CostAlert(
                        alert_id=f"{service_key}_{level.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        level=level,
                        service_name=service_name,
                        message=f"{level.value.title()}: {service_name} monthly cost projection ${monthly_cost:.2f} exceeds {level.value} threshold ${threshold:.2f}",
                        current_cost=monthly_cost,
                        threshold=threshold,
                        recommendations=self._get_service_recommendations(service_name, level)
                    ))
            
            logger.info(f"Generated {len(alerts)} cost alerts")
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to generate cost alerts: {e}")
            return []
    
    def _get_service_threshold_key(self, service_name: str) -> str:
        """Map service name to threshold key"""
        mappings = {
            'Amazon Bedrock': 'bedrock',
            'Amazon Elastic Container Service': 'ecs',
            'Amazon Simple Storage Service': 's3',
            'Amazon CloudWatch': 'cloudwatch',
            'Amazon API Gateway': 'api_gateway'
        }
        
        for service_key, threshold_key in mappings.items():
            if service_key.lower() in service_name.lower():
                return threshold_key
        
        return 'ecs'  # Default
    
    def _get_service_recommendations(self, service_name: str, level: CostAlertLevel) -> List[str]:
        """Get service-specific cost optimization recommendations"""
        base_recommendations = {
            'Amazon Bedrock': [
                "Optimize prompt lengths and reduce token usage",
                "Use Claude-3 Haiku for simple tasks instead of Opus",
                "Implement request caching to reduce API calls",
                "Review and optimize model selection for each use case"
            ],
            'Amazon Elastic Container Service': [
                "Review task definitions and right-size containers",
                "Implement auto-scaling policies to match demand",
                "Consider using Spot instances for non-critical workloads",
                "Optimize container resource allocation"
            ],
            'Amazon Simple Storage Service': [
                "Implement lifecycle policies for old data",
                "Use appropriate storage classes (IA, Glacier)",
                "Review and clean up unused objects",
                "Optimize data compression and deduplication"
            ],
            'Amazon CloudWatch': [
                "Review log retention policies",
                "Optimize custom metrics and reduce frequency",
                "Use log filtering to reduce ingestion costs",
                "Consider log aggregation strategies"
            ]
        }
        
        service_key = next((key for key in base_recommendations.keys() 
                           if key.lower() in service_name.lower()), None)
        
        if service_key:
            recommendations = base_recommendations[service_key].copy()
            
            if level == CostAlertLevel.EMERGENCY:
                recommendations.insert(0, "IMMEDIATE ACTION REQUIRED: Scale down resources now")
            elif level == CostAlertLevel.CRITICAL:
                recommendations.insert(0, "Urgent: Implement cost controls within 24 hours")
            
            return recommendations
        
        return ["Review service usage and optimize resource allocation"]
    
    async def generate_optimization_recommendations(self, 
                                                 current_costs: Dict[str, CostMetric],
                                                 efficiency_metrics: Dict[str, Any]) -> List[CostOptimizationRecommendation]:
        """
        Generate comprehensive cost optimization recommendations
        
        Args:
            current_costs: Current cost metrics
            efficiency_metrics: Auto-scaling efficiency metrics
            
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        try:
            # Analyze costs by category
            category_costs = {}
            for cost_metric in current_costs.values():
                category = cost_metric.category
                if category not in category_costs:
                    category_costs[category] = 0
                category_costs[category] += cost_metric.projected_monthly_cost
            
            # Generate category-specific recommendations
            for category, total_cost in category_costs.items():
                if total_cost > 100:  # Focus on significant costs
                    recommendations.extend(
                        self._generate_category_recommendations(category, total_cost)
                    )
            
            # Generate efficiency-based recommendations
            if efficiency_metrics:
                efficiency_score = efficiency_metrics.get("efficiency_score", 0)
                if efficiency_score < 70:
                    recommendations.append(CostOptimizationRecommendation(
                        recommendation_id=f"efficiency_improvement_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        service_name="ECS Auto-scaling",
                        category=ServiceCategory.COMPUTE,
                        description=f"Improve auto-scaling efficiency (current score: {efficiency_score:.1f})",
                        potential_savings=total_cost * 0.2,  # Estimate 20% savings
                        implementation_effort="medium",
                        priority=2,
                        action_items=[
                            "Adjust auto-scaling policies for better resource utilization",
                            "Optimize container resource requests and limits",
                            "Implement predictive scaling based on usage patterns"
                        ]
                    ))
            
            # Sort recommendations by priority and potential savings
            recommendations.sort(key=lambda x: (x.priority, -x.potential_savings))
            
            logger.info(f"Generated {len(recommendations)} optimization recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate optimization recommendations: {e}")
            return []
    
    def _generate_category_recommendations(self, category: ServiceCategory, 
                                        total_cost: float) -> List[CostOptimizationRecommendation]:
        """Generate recommendations for specific service category"""
        recommendations = []
        
        if category == ServiceCategory.AI_ML:
            recommendations.append(CostOptimizationRecommendation(
                recommendation_id=f"ai_ml_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                service_name="AI/ML Services",
                category=category,
                description="Optimize AI/ML service usage and model selection",
                potential_savings=total_cost * 0.3,  # Estimate 30% savings
                implementation_effort="low",
                priority=1,
                action_items=[
                    "Use appropriate Claude-3 model variants for different tasks",
                    "Implement request batching and caching",
                    "Optimize prompt engineering to reduce token usage",
                    "Monitor and optimize model inference patterns"
                ]
            ))
        
        elif category == ServiceCategory.COMPUTE:
            recommendations.append(CostOptimizationRecommendation(
                recommendation_id=f"compute_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                service_name="Compute Services",
                category=category,
                description="Optimize compute resource allocation and scaling",
                potential_savings=total_cost * 0.25,  # Estimate 25% savings
                implementation_effort="medium",
                priority=2,
                action_items=[
                    "Right-size ECS tasks based on actual usage",
                    "Implement more aggressive auto-scaling policies",
                    "Consider using Spot instances for batch workloads",
                    "Optimize container startup and shutdown times"
                ]
            ))
        
        elif category == ServiceCategory.STORAGE:
            recommendations.append(CostOptimizationRecommendation(
                recommendation_id=f"storage_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                service_name="Storage Services",
                category=category,
                description="Optimize storage costs through lifecycle management",
                potential_savings=total_cost * 0.4,  # Estimate 40% savings
                implementation_effort="low",
                priority=1,
                action_items=[
                    "Implement S3 lifecycle policies for data archival",
                    "Use appropriate storage classes (Standard-IA, Glacier)",
                    "Enable S3 compression and deduplication",
                    "Clean up unused and temporary files regularly"
                ]
            ))
        
        return recommendations
    
    async def get_cost_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive cost dashboard data
        
        Returns:
            Dashboard data including costs, alerts, and recommendations
        """
        try:
            # Get current costs
            current_costs = await self.get_current_costs()
            
            # Monitor data costs
            data_cost_analysis = await self.monitor_public_vs_premium_data_costs()
            
            # Track auto-scaling efficiency
            efficiency_metrics = await self.track_auto_scaling_efficiency()
            
            # Generate alerts
            alerts = await self.generate_cost_alerts(current_costs)
            
            # Generate recommendations
            recommendations = await self.generate_optimization_recommendations(
                current_costs, efficiency_metrics
            )
            
            # Calculate summary metrics
            total_current_cost = sum(cost.current_cost for cost in current_costs.values())
            total_projected_cost = sum(cost.projected_monthly_cost for cost in current_costs.values())
            potential_savings = sum(rec.potential_savings for rec in recommendations)
            
            dashboard_data = {
                "summary": {
                    "total_current_cost": total_current_cost,
                    "total_projected_monthly_cost": total_projected_cost,
                    "potential_monthly_savings": potential_savings,
                    "cost_reduction_percentage": (potential_savings / total_projected_cost * 100) if total_projected_cost > 0 else 0,
                    "active_alerts_count": len(alerts),
                    "high_priority_recommendations": len([r for r in recommendations if r.priority <= 2])
                },
                "current_costs": current_costs,
                "data_cost_analysis": data_cost_analysis,
                "efficiency_metrics": efficiency_metrics,
                "alerts": alerts,
                "recommendations": recommendations,
                "cost_trends": await self._get_cost_trends(),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Generated cost dashboard data with {len(current_costs)} services")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get cost dashboard data: {e}")
            return {}
    
    async def _get_cost_trends(self) -> Dict[str, List[float]]:
        """Get cost trends over the last 30 days"""
        try:
            # Simulate cost trends (would get from actual Cost Explorer data)
            days = 30
            trends = {}
            
            services = ["bedrock", "ecs", "s3", "cloudwatch", "total"]
            
            for service in services:
                # Generate realistic trend data
                base_cost = 50 if service != "total" else 200
                daily_costs = []
                
                for day in range(days):
                    # Add some realistic variation
                    variation = 1 + (day % 7) * 0.1 - 0.3  # Weekly pattern
                    noise = 1 + (hash(f"{service}_{day}") % 20 - 10) / 100  # Random noise
                    daily_cost = base_cost * variation * noise
                    daily_costs.append(max(0, daily_cost))
                
                trends[service] = daily_costs
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get cost trends: {e}")
            return {}


# Singleton instance
_cost_monitor_instance = None

def get_cost_monitor() -> AWSCostMonitor:
    """Get singleton cost monitor instance"""
    global _cost_monitor_instance
    if _cost_monitor_instance is None:
        _cost_monitor_instance = AWSCostMonitor()
    return _cost_monitor_instance