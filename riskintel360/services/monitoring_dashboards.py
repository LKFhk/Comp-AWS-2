"""
CloudWatch Dashboard Configurations for RiskIntel360 Platform
Defines dashboard layouts and metric configurations for comprehensive monitoring.
"""

import json
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

from riskintel360.config.settings import get_settings


class DashboardType(Enum):
    """Types of monitoring dashboards"""
    AGENT_PERFORMANCE = "agent_performance"
    SYSTEM_HEALTH = "system_health"
    BUSINESS_METRICS = "business_metrics"
    ERROR_MONITORING = "error_monitoring"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class MetricWidget:
    """CloudWatch metric widget configuration"""
    title: str
    metrics: List[List[str]]
    width: int = 12
    height: int = 6
    x: int = 0
    y: int = 0
    period: int = 300
    stat: str = "Average"
    region: str = "us-east-1"
    view: str = "timeSeries"


@dataclass
class TextWidget:
    """CloudWatch text widget configuration"""
    title: str
    markdown: str
    width: int = 12
    height: int = 3
    x: int = 0
    y: int = 0


class MonitoringDashboards:
    """CloudWatch dashboard configurations for RiskIntel360 platform"""
    
    def __init__(self):
        self.settings = get_settings()
        self.namespace = self.settings.monitoring.cloudwatch_namespace
    
    def get_agent_performance_dashboard(self) -> Dict[str, Any]:
        """Get agent performance monitoring dashboard"""
        widgets = [
            # Agent Response Times
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "OperationDuration", "Operation", "regulatory_compliance_analysis"],
                        [self.namespace, "OperationDuration", "Operation", "risk_assessment_analysis"],
                        [self.namespace, "OperationDuration", "Operation", "market_analysis_analysis"],
                        [self.namespace, "OperationDuration", "Operation", "customer_behavior_intelligence_analysis"],
                        [self.namespace, "OperationDuration", "Operation", "fraud_detection_analysis"],
                        [self.namespace, "OperationDuration", "Operation", "kyc_verification_analysis"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Agent Response Times (ms)",
                    "view": "timeSeries",
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 5000
                        }
                    }
                }
            },
            
            # Agent Success Rates
            {
                "type": "metric",
                "x": 12,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "OperationCount", "Operation", "regulatory_compliance_analysis", "Success", "True"],
                        [self.namespace, "OperationCount", "Operation", "risk_assessment_analysis", "Success", "True"],
                        [self.namespace, "OperationCount", "Operation", "market_analysis_analysis", "Success", "True"],
                        [self.namespace, "OperationCount", "Operation", "customer_behavior_intelligence_analysis", "Success", "True"],
                        [self.namespace, "OperationCount", "Operation", "fraud_detection_analysis", "Success", "True"],
                        [self.namespace, "OperationCount", "Operation", "kyc_verification_analysis", "Success", "True"]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Agent Success Count",
                    "view": "timeSeries"
                }
            },
            
            # Agent Error Rates
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "OperationErrors", "Operation", "regulatory_compliance_analysis"],
                        [self.namespace, "OperationErrors", "Operation", "risk_assessment_analysis"],
                        [self.namespace, "OperationErrors", "Operation", "market_analysis_analysis"],
                        [self.namespace, "OperationErrors", "Operation", "customer_behavior_intelligence_analysis"],
                        [self.namespace, "OperationErrors", "Operation", "fraud_detection_analysis"],
                        [self.namespace, "OperationErrors", "Operation", "kyc_verification_analysis"]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Agent Error Count",
                    "view": "timeSeries"
                }
            },
            
            # Agent Health Status
            {
                "type": "metric",
                "x": 12,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "HealthCheck", "Component", "regulatory_compliance_agent"],
                        [self.namespace, "HealthCheck", "Component", "risk_assessment_agent"],
                        [self.namespace, "HealthCheck", "Component", "market_analysis_agent"],
                        [self.namespace, "HealthCheck", "Component", "customer_behavior_intelligence_agent"],
                        [self.namespace, "HealthCheck", "Component", "fraud_detection_agent"],
                        [self.namespace, "HealthCheck", "Component", "kyc_verification_agent"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Agent Health Status (1=Healthy, 0=Unhealthy)",
                    "view": "timeSeries",
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 1
                        }
                    }
                }
            }
        ]
        
        return {
            "widgets": widgets
        }
    
    def get_system_health_dashboard(self) -> Dict[str, Any]:
        """Get system health monitoring dashboard"""
        widgets = [
            # System Overview
            {
                "type": "text",
                "x": 0,
                "y": 0,
                "width": 24,
                "height": 3,
                "properties": {
                    "markdown": "# RiskIntel360 Platform System Health\n\nMonitoring system health, performance, and availability metrics.\n\n**SLA Target**: 99.9% uptime, <5s response time"
                }
            },
            
            # Overall System Health
            {
                "type": "metric",
                "x": 0,
                "y": 3,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "SystemHealth", "System", "RiskIntel360"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Overall System Health",
                    "view": "singleValue",
                    "sparkline": True
                }
            },
            
            # Active Traces
            {
                "type": "metric",
                "x": 8,
                "y": 3,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "ActiveTraces", "System", "RiskIntel360"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Active Traces",
                    "view": "timeSeries"
                }
            },
            
            # Metrics Buffer Size
            {
                "type": "metric",
                "x": 16,
                "y": 3,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "MetricsBufferSize", "System", "RiskIntel360"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Metrics Buffer Size",
                    "view": "timeSeries"
                }
            },
            
            # Health Check Response Times
            {
                "type": "metric",
                "x": 0,
                "y": 9,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "HealthCheckDuration", "Component", "bedrock_client"],
                        [self.namespace, "HealthCheckDuration", "Component", "agentcore_client"],
                        [self.namespace, "HealthCheckDuration", "Component", "database"],
                        [self.namespace, "HealthCheckDuration", "Component", "redis"],
                        [self.namespace, "HealthCheckDuration", "Component", "external_apis"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Health Check Response Times (ms)",
                    "view": "timeSeries"
                }
            },
            
            # Component Health Status
            {
                "type": "metric",
                "x": 12,
                "y": 9,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "HealthCheck", "Component", "bedrock_client"],
                        [self.namespace, "HealthCheck", "Component", "agentcore_client"],
                        [self.namespace, "HealthCheck", "Component", "database"],
                        [self.namespace, "HealthCheck", "Component", "redis"],
                        [self.namespace, "HealthCheck", "Component", "external_apis"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Component Health Status",
                    "view": "timeSeries",
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 1
                        }
                    }
                }
            }
        ]
        
        return {
            "widgets": widgets
        }
    
    def get_business_metrics_dashboard(self) -> Dict[str, Any]:
        """Get business KPI monitoring dashboard"""
        widgets = [
            # Business KPIs Overview
            {
                "type": "text",
                "x": 0,
                "y": 0,
                "width": 24,
                "height": 3,
                "properties": {
                    "markdown": "# RiskIntel360 Platform Business Metrics\n\nKey Performance Indicators and business impact metrics.\n\n**Target**: 95% time reduction, 80% cost savings, <2 hour validation completion"
                }
            },
            
            # Validation Requests
            {
                "type": "metric",
                "x": 0,
                "y": 3,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "ValidationRequests", "Status", "Started"],
                        [self.namespace, "ValidationRequests", "Status", "Completed"],
                        [self.namespace, "ValidationRequests", "Status", "Failed"]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Validation Requests",
                    "view": "timeSeries"
                }
            },
            
            # Validation Completion Time
            {
                "type": "metric",
                "x": 6,
                "y": 3,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "ValidationCompletionTime", "Type", "EndToEnd"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Validation Completion Time (minutes)",
                    "view": "timeSeries",
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 120
                        }
                    }
                }
            },
            
            # Success Rate
            {
                "type": "metric",
                "x": 12,
                "y": 3,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "ValidationSuccessRate", "Period", "Hourly"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Validation Success Rate (%)",
                    "view": "singleValue",
                    "sparkline": True
                }
            },
            
            # Confidence Scores
            {
                "type": "metric",
                "x": 18,
                "y": 3,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "ConfidenceScore", "Agent", "regulatory_compliance"],
                        [self.namespace, "ConfidenceScore", "Agent", "risk_assessment"],
                        [self.namespace, "ConfidenceScore", "Agent", "market_analysis"],
                        [self.namespace, "ConfidenceScore", "Agent", "customer_behavior_intelligence"],
                        [self.namespace, "ConfidenceScore", "Agent", "fraud_detection"],
                        [self.namespace, "ConfidenceScore", "Agent", "kyc_verification"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Agent Confidence Scores",
                    "view": "timeSeries",
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 1
                        }
                    }
                }
            },
            
            # User Activity
            {
                "type": "metric",
                "x": 0,
                "y": 9,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "ActiveUsers", "Period", "Hourly"],
                        [self.namespace, "NewUsers", "Period", "Daily"],
                        [self.namespace, "UserSessions", "Type", "Active"]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "User Activity Metrics",
                    "view": "timeSeries"
                }
            },
            
            # Cost Savings Metrics
            {
                "type": "metric",
                "x": 12,
                "y": 9,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "CostSavings", "Type", "TimeReduction"],
                        [self.namespace, "CostSavings", "Type", "ResourceOptimization"],
                        [self.namespace, "CostSavings", "Type", "AutomationBenefit"]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Cost Savings Metrics ($)",
                    "view": "timeSeries"
                }
            }
        ]
        
        return {
            "widgets": widgets
        }
    
    def get_error_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get error monitoring and alerting dashboard"""
        widgets = [
            # Error Overview
            {
                "type": "text",
                "x": 0,
                "y": 0,
                "width": 24,
                "height": 3,
                "properties": {
                    "markdown": "# RiskIntel360 Platform Error Monitoring\n\nError tracking, alerting, and performance degradation detection.\n\n**Alert Thresholds**: >5% error rate, >5s response time, <95% availability"
                }
            },
            
            # Total Alerts
            {
                "type": "metric",
                "x": 0,
                "y": 3,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "AlertsCreated", "Severity", "critical"],
                        [self.namespace, "AlertsCreated", "Severity", "error"],
                        [self.namespace, "AlertsCreated", "Severity", "warning"],
                        [self.namespace, "AlertsCreated", "Severity", "info"]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Alerts by Severity",
                    "view": "timeSeries"
                }
            },
            
            # Error Rates by Component
            {
                "type": "metric",
                "x": 6,
                "y": 3,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "ErrorRate", "Component", "regulatory_compliance_agent"],
                        [self.namespace, "ErrorRate", "Component", "risk_assessment_agent"],
                        [self.namespace, "ErrorRate", "Component", "market_analysis_agent"],
                        [self.namespace, "ErrorRate", "Component", "customer_behavior_intelligence_agent"],
                        [self.namespace, "ErrorRate", "Component", "fraud_detection_agent"],
                        [self.namespace, "ErrorRate", "Component", "kyc_verification_agent"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Error Rate by Agent (%)",
                    "view": "timeSeries"
                }
            },
            
            # Performance Degradation
            {
                "type": "metric",
                "x": 12,
                "y": 3,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "PerformanceDegradation", "Type", "ResponseTime"],
                        [self.namespace, "PerformanceDegradation", "Type", "Throughput"],
                        [self.namespace, "PerformanceDegradation", "Type", "ErrorRate"]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Performance Degradation Events",
                    "view": "timeSeries"
                }
            },
            
            # Circuit Breaker Status
            {
                "type": "metric",
                "x": 18,
                "y": 3,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "CircuitBreakerStatus", "Component", "bedrock_client"],
                        [self.namespace, "CircuitBreakerStatus", "Component", "external_apis"],
                        [self.namespace, "CircuitBreakerStatus", "Component", "database"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Circuit Breaker Status",
                    "view": "timeSeries"
                }
            },
            
            # External API Errors
            {
                "type": "metric",
                "x": 0,
                "y": 9,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "ExternalAPIErrors", "API", "alpha_vantage"],
                        [self.namespace, "ExternalAPIErrors", "API", "news_api"],
                        [self.namespace, "ExternalAPIErrors", "API", "crunchbase"],
                        [self.namespace, "ExternalAPIErrors", "API", "yahoo_finance"]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "External API Errors",
                    "view": "timeSeries"
                }
            },
            
            # Recovery Metrics
            {
                "type": "metric",
                "x": 12,
                "y": 9,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [self.namespace, "RecoveryTime", "Type", "AutoRecovery"],
                        [self.namespace, "RecoveryTime", "Type", "ManualIntervention"],
                        [self.namespace, "RecoverySuccess", "Type", "Automatic"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Recovery Metrics",
                    "view": "timeSeries"
                }
            }
        ]
        
        return {
            "widgets": widgets
        }
    
    def get_infrastructure_dashboard(self) -> Dict[str, Any]:
        """Get infrastructure monitoring dashboard"""
        widgets = [
            # Infrastructure Overview
            {
                "type": "text",
                "x": 0,
                "y": 0,
                "width": 24,
                "height": 3,
                "properties": {
                    "markdown": "# RiskIntel360 Platform Infrastructure\n\nAWS infrastructure monitoring including ECS, DynamoDB, Aurora, and ElastiCache.\n\n**Auto-scaling**: 3-50 ECS instances based on demand"
                }
            },
            
            # ECS Metrics
            {
                "type": "metric",
                "x": 0,
                "y": 3,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/ECS", "CPUUtilization", "ServiceName", "RiskIntel360-service"],
                        ["AWS/ECS", "MemoryUtilization", "ServiceName", "RiskIntel360-service"],
                        ["AWS/ECS", "RunningTaskCount", "ServiceName", "RiskIntel360-service"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "ECS Service Metrics",
                    "view": "timeSeries"
                }
            },
            
            # DynamoDB Metrics
            {
                "type": "metric",
                "x": 8,
                "y": 3,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "RiskIntel360-agent-states"],
                        ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", "RiskIntel360-agent-states"],
                        ["AWS/DynamoDB", "ThrottledRequests", "TableName", "RiskIntel360-agent-states"]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "DynamoDB Metrics",
                    "view": "timeSeries"
                }
            },
            
            # ElastiCache Metrics
            {
                "type": "metric",
                "x": 16,
                "y": 3,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/ElastiCache", "CPUUtilization", "CacheClusterId", "RiskIntel360-redis"],
                        ["AWS/ElastiCache", "CacheHitRate", "CacheClusterId", "RiskIntel360-redis"],
                        ["AWS/ElastiCache", "NetworkBytesIn", "CacheClusterId", "RiskIntel360-redis"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "ElastiCache Metrics",
                    "view": "timeSeries"
                }
            },
            
            # Aurora Metrics
            {
                "type": "metric",
                "x": 0,
                "y": 9,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/RDS", "CPUUtilization", "DBClusterIdentifier", "RiskIntel360-cluster"],
                        ["AWS/RDS", "DatabaseConnections", "DBClusterIdentifier", "RiskIntel360-cluster"],
                        ["AWS/RDS", "ReadLatency", "DBClusterIdentifier", "RiskIntel360-cluster"],
                        ["AWS/RDS", "WriteLatency", "DBClusterIdentifier", "RiskIntel360-cluster"]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Aurora Serverless Metrics",
                    "view": "timeSeries"
                }
            },
            
            # API Gateway Metrics
            {
                "type": "metric",
                "x": 12,
                "y": 9,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/ApiGateway", "Count", "ApiName", "RiskIntel360-api"],
                        ["AWS/ApiGateway", "Latency", "ApiName", "RiskIntel360-api"],
                        ["AWS/ApiGateway", "4XXError", "ApiName", "RiskIntel360-api"],
                        ["AWS/ApiGateway", "5XXError", "ApiName", "RiskIntel360-api"]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "API Gateway Metrics",
                    "view": "timeSeries"
                }
            }
        ]
        
        return {
            "widgets": widgets
        }
    
    def get_all_dashboards(self) -> Dict[DashboardType, Dict[str, Any]]:
        """Get all dashboard configurations"""
        return {
            DashboardType.AGENT_PERFORMANCE: self.get_agent_performance_dashboard(),
            DashboardType.SYSTEM_HEALTH: self.get_system_health_dashboard(),
            DashboardType.BUSINESS_METRICS: self.get_business_metrics_dashboard(),
            DashboardType.ERROR_MONITORING: self.get_error_monitoring_dashboard(),
            DashboardType.INFRASTRUCTURE: self.get_infrastructure_dashboard()
        }
    
    def get_dashboard_names(self) -> Dict[DashboardType, str]:
        """Get dashboard names for CloudWatch"""
        return {
            DashboardType.AGENT_PERFORMANCE: "RiskIntel360-Agent-Performance",
            DashboardType.SYSTEM_HEALTH: "RiskIntel360-System-Health",
            DashboardType.BUSINESS_METRICS: "RiskIntel360-Business-Metrics",
            DashboardType.ERROR_MONITORING: "RiskIntel360-Error-Monitoring",
            DashboardType.INFRASTRUCTURE: "RiskIntel360-Infrastructure"
        }
