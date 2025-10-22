"""
Cost Optimization Dashboard Service

Provides dashboard functionality for AWS cost monitoring and optimization
with real-time updates and interactive visualizations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json

from .aws_cost_monitor import AWSCostMonitor, CostAlert, CostOptimizationRecommendation, CostAlertLevel

logger = logging.getLogger(__name__)


@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    widget_id: str
    title: str
    widget_type: str  # "metric", "chart", "table", "alert"
    data: Dict[str, Any]
    refresh_interval: int = 300  # 5 minutes default
    priority: int = 1


@dataclass
class CostDashboardConfig:
    """Cost dashboard configuration"""
    refresh_interval: int = 300  # 5 minutes
    alert_retention_days: int = 30
    recommendation_limit: int = 10
    enable_real_time_alerts: bool = True
    cost_threshold_multiplier: float = 1.0


class CostOptimizationDashboard:
    """
    Cost Optimization Dashboard Service
    
    Provides comprehensive dashboard functionality for AWS cost monitoring,
    optimization recommendations, and real-time alerting.
    """
    
    def __init__(self, config: Optional[CostDashboardConfig] = None):
        self.config = config or CostDashboardConfig()
        self.cost_monitor = AWSCostMonitor()
        self.dashboard_cache = {}
        self.last_refresh = None
        
        # Dashboard widgets configuration
        self.widget_configs = {
            "cost_summary": {
                "title": "Cost Summary",
                "type": "metric",
                "priority": 1
            },
            "cost_trends": {
                "title": "Cost Trends (30 Days)",
                "type": "chart",
                "priority": 2
            },
            "service_breakdown": {
                "title": "Service Cost Breakdown",
                "type": "chart",
                "priority": 3
            },
            "data_cost_analysis": {
                "title": "Public vs Premium Data Costs",
                "type": "metric",
                "priority": 4
            },
            "efficiency_metrics": {
                "title": "Auto-scaling Efficiency",
                "type": "metric",
                "priority": 5
            },
            "active_alerts": {
                "title": "Active Cost Alerts",
                "type": "alert",
                "priority": 6
            },
            "optimization_recommendations": {
                "title": "Cost Optimization Recommendations",
                "type": "table",
                "priority": 7
            }
        }
    
    async def get_dashboard_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get complete dashboard data
        
        Args:
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            Complete dashboard data
        """
        try:
            # Check if we need to refresh
            if not force_refresh and self._is_cache_valid():
                logger.info("Returning cached dashboard data")
                return self.dashboard_cache
            
            logger.info("Refreshing dashboard data")
            
            # Get fresh data from cost monitor
            dashboard_data = await self.cost_monitor.get_cost_dashboard_data()
            
            # Process data for dashboard widgets
            processed_data = await self._process_dashboard_data(dashboard_data)
            
            # Update cache
            self.dashboard_cache = processed_data
            self.last_refresh = datetime.now()
            
            logger.info("Dashboard data refreshed successfully")
            return processed_data
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            # Return cached data if available, otherwise empty dashboard
            return self.dashboard_cache if self.dashboard_cache else self._get_empty_dashboard()
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self.last_refresh or not self.dashboard_cache:
            return False
        
        cache_age = (datetime.now() - self.last_refresh).total_seconds()
        return cache_age < self.config.refresh_interval
    
    async def _process_dashboard_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw cost data for dashboard display"""
        try:
            widgets = {}
            
            # Cost Summary Widget
            widgets["cost_summary"] = await self._create_cost_summary_widget(raw_data)
            
            # Cost Trends Widget
            widgets["cost_trends"] = await self._create_cost_trends_widget(raw_data)
            
            # Service Breakdown Widget
            widgets["service_breakdown"] = await self._create_service_breakdown_widget(raw_data)
            
            # Data Cost Analysis Widget
            widgets["data_cost_analysis"] = await self._create_data_cost_widget(raw_data)
            
            # Efficiency Metrics Widget
            widgets["efficiency_metrics"] = await self._create_efficiency_widget(raw_data)
            
            # Active Alerts Widget
            widgets["active_alerts"] = await self._create_alerts_widget(raw_data)
            
            # Optimization Recommendations Widget
            widgets["optimization_recommendations"] = await self._create_recommendations_widget(raw_data)
            
            return {
                "widgets": widgets,
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "refresh_interval": self.config.refresh_interval,
                    "data_quality": self._assess_data_quality(raw_data)
                },
                "summary": raw_data.get("summary", {}),
                "raw_data": raw_data  # Include for debugging
            }
            
        except Exception as e:
            logger.error(f"Failed to process dashboard data: {e}")
            return self._get_empty_dashboard()
    
    async def _create_cost_summary_widget(self, data: Dict[str, Any]) -> DashboardWidget:
        """Create cost summary widget"""
        summary = data.get("summary", {})
        
        widget_data = {
            "metrics": [
                {
                    "label": "Current Monthly Projection",
                    "value": summary.get("total_projected_monthly_cost", 0),
                    "format": "currency",
                    "trend": "up" if summary.get("total_projected_monthly_cost", 0) > 500 else "stable"
                },
                {
                    "label": "Potential Monthly Savings",
                    "value": summary.get("potential_monthly_savings", 0),
                    "format": "currency",
                    "trend": "up"
                },
                {
                    "label": "Cost Reduction Opportunity",
                    "value": summary.get("cost_reduction_percentage", 0),
                    "format": "percentage",
                    "trend": "up"
                },
                {
                    "label": "Active Alerts",
                    "value": summary.get("active_alerts_count", 0),
                    "format": "number",
                    "trend": "down" if summary.get("active_alerts_count", 0) == 0 else "up"
                }
            ],
            "status": self._get_cost_status(summary),
            "last_updated": datetime.now().isoformat()
        }
        
        return DashboardWidget(
            widget_id="cost_summary",
            title="Cost Summary",
            widget_type="metric",
            data=widget_data,
            priority=1
        )
    
    async def _create_cost_trends_widget(self, data: Dict[str, Any]) -> DashboardWidget:
        """Create cost trends chart widget"""
        trends = data.get("cost_trends", {})
        
        # Prepare chart data
        chart_data = {
            "labels": [f"Day {i+1}" for i in range(30)],  # Last 30 days
            "datasets": []
        }
        
        colors = {
            "total": "#3B82F6",
            "bedrock": "#EF4444", 
            "ecs": "#10B981",
            "s3": "#F59E0B",
            "cloudwatch": "#8B5CF6"
        }
        
        for service, daily_costs in trends.items():
            if service in colors:
                chart_data["datasets"].append({
                    "label": service.title(),
                    "data": daily_costs,
                    "borderColor": colors[service],
                    "backgroundColor": colors[service] + "20",  # Add transparency
                    "fill": False
                })
        
        widget_data = {
            "chart_type": "line",
            "chart_data": chart_data,
            "options": {
                "responsive": True,
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "title": {
                            "display": True,
                            "text": "Cost (USD)"
                        }
                    }
                }
            }
        }
        
        return DashboardWidget(
            widget_id="cost_trends",
            title="Cost Trends (30 Days)",
            widget_type="chart",
            data=widget_data,
            priority=2
        )
    
    async def _create_service_breakdown_widget(self, data: Dict[str, Any]) -> DashboardWidget:
        """Create service cost breakdown widget"""
        current_costs = data.get("current_costs", {})
        
        # Prepare pie chart data
        labels = []
        values = []
        colors = ["#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#6B7280"]
        
        for i, (service_name, cost_metric) in enumerate(current_costs.items()):
            labels.append(service_name.replace("Amazon ", "").replace("AWS ", ""))
            values.append(cost_metric.projected_monthly_cost)
        
        chart_data = {
            "labels": labels,
            "datasets": [{
                "data": values,
                "backgroundColor": colors[:len(labels)],
                "borderWidth": 2
            }]
        }
        
        widget_data = {
            "chart_type": "doughnut",
            "chart_data": chart_data,
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {
                        "position": "right"
                    }
                }
            },
            "total_cost": sum(values)
        }
        
        return DashboardWidget(
            widget_id="service_breakdown",
            title="Service Cost Breakdown",
            widget_type="chart",
            data=widget_data,
            priority=3
        )
    
    async def _create_data_cost_widget(self, data: Dict[str, Any]) -> DashboardWidget:
        """Create data cost analysis widget"""
        data_analysis = data.get("data_cost_analysis", {})
        
        widget_data = {
            "metrics": [
                {
                    "label": "Public Data Usage",
                    "value": data_analysis.get("public_data_percentage", 0) * 100,
                    "format": "percentage",
                    "target": 80,
                    "status": "success" if data_analysis.get("meets_public_data_target", False) else "warning"
                },
                {
                    "label": "Cost Reduction Achieved",
                    "value": data_analysis.get("cost_reduction_achieved", 0) * 100,
                    "format": "percentage",
                    "target": 80,
                    "status": "success" if data_analysis.get("meets_cost_reduction_target", False) else "warning"
                },
                {
                    "label": "Public Data Cost",
                    "value": data_analysis.get("public_data_cost", 0),
                    "format": "currency"
                },
                {
                    "label": "Premium Data Cost",
                    "value": data_analysis.get("premium_data_cost", 0),
                    "format": "currency"
                }
            ],
            "recommendations": data_analysis.get("recommendations", []),
            "status": "success" if (data_analysis.get("meets_public_data_target", False) and 
                                  data_analysis.get("meets_cost_reduction_target", False)) else "warning"
        }
        
        return DashboardWidget(
            widget_id="data_cost_analysis",
            title="Public vs Premium Data Costs",
            widget_type="metric",
            data=widget_data,
            priority=4
        )
    
    async def _create_efficiency_widget(self, data: Dict[str, Any]) -> DashboardWidget:
        """Create auto-scaling efficiency widget"""
        efficiency = data.get("efficiency_metrics", {})
        
        widget_data = {
            "metrics": [
                {
                    "label": "Efficiency Score",
                    "value": efficiency.get("efficiency_score", 0),
                    "format": "number",
                    "suffix": "/100",
                    "status": "success" if efficiency.get("efficiency_score", 0) >= 70 else "warning"
                },
                {
                    "label": "Average CPU Utilization",
                    "value": efficiency.get("average_cpu_utilization", 0),
                    "format": "percentage",
                    "target": 70
                },
                {
                    "label": "Average Memory Utilization",
                    "value": efficiency.get("average_memory_utilization", 0),
                    "format": "percentage",
                    "target": 80
                },
                {
                    "label": "Scaling Events (24h)",
                    "value": efficiency.get("scaling_events_count", 0),
                    "format": "number"
                }
            ],
            "recommendations": efficiency.get("recommendations", [])
        }
        
        return DashboardWidget(
            widget_id="efficiency_metrics",
            title="Auto-scaling Efficiency",
            widget_type="metric",
            data=widget_data,
            priority=5
        )
    
    async def _create_alerts_widget(self, data: Dict[str, Any]) -> DashboardWidget:
        """Create active alerts widget"""
        alerts = data.get("alerts", [])
        
        # Group alerts by severity
        alert_groups = {
            "emergency": [],
            "critical": [],
            "warning": [],
            "info": []
        }
        
        for alert in alerts:
            level = alert.level.value if hasattr(alert, 'level') else alert.get('level', 'info')
            if level in alert_groups:
                alert_groups[level].append({
                    "id": alert.alert_id if hasattr(alert, 'alert_id') else alert.get('alert_id'),
                    "service": alert.service_name if hasattr(alert, 'service_name') else alert.get('service_name'),
                    "message": alert.message if hasattr(alert, 'message') else alert.get('message'),
                    "cost": alert.current_cost if hasattr(alert, 'current_cost') else alert.get('current_cost'),
                    "threshold": alert.threshold if hasattr(alert, 'threshold') else alert.get('threshold'),
                    "timestamp": alert.timestamp.isoformat() if hasattr(alert, 'timestamp') else alert.get('timestamp')
                })
        
        widget_data = {
            "alert_groups": alert_groups,
            "total_alerts": len(alerts),
            "severity_counts": {level: len(group) for level, group in alert_groups.items()},
            "most_severe": self._get_most_severe_level(alert_groups)
        }
        
        return DashboardWidget(
            widget_id="active_alerts",
            title="Active Cost Alerts",
            widget_type="alert",
            data=widget_data,
            priority=6
        )
    
    async def _create_recommendations_widget(self, data: Dict[str, Any]) -> DashboardWidget:
        """Create optimization recommendations widget"""
        recommendations = data.get("recommendations", [])
        
        # Process recommendations for table display
        table_data = []
        for rec in recommendations[:self.config.recommendation_limit]:
            table_data.append({
                "id": rec.recommendation_id if hasattr(rec, 'recommendation_id') else rec.get('recommendation_id'),
                "service": rec.service_name if hasattr(rec, 'service_name') else rec.get('service_name'),
                "description": rec.description if hasattr(rec, 'description') else rec.get('description'),
                "potential_savings": rec.potential_savings if hasattr(rec, 'potential_savings') else rec.get('potential_savings'),
                "effort": rec.implementation_effort if hasattr(rec, 'implementation_effort') else rec.get('implementation_effort'),
                "priority": rec.priority if hasattr(rec, 'priority') else rec.get('priority'),
                "action_items": rec.action_items if hasattr(rec, 'action_items') else rec.get('action_items', [])
            })
        
        # Calculate total potential savings
        total_savings = sum(item["potential_savings"] for item in table_data)
        
        widget_data = {
            "recommendations": table_data,
            "total_recommendations": len(recommendations),
            "total_potential_savings": total_savings,
            "high_priority_count": len([r for r in table_data if r["priority"] <= 2]),
            "columns": [
                {"key": "service", "label": "Service", "sortable": True},
                {"key": "description", "label": "Recommendation", "sortable": False},
                {"key": "potential_savings", "label": "Savings", "sortable": True, "format": "currency"},
                {"key": "effort", "label": "Effort", "sortable": True},
                {"key": "priority", "label": "Priority", "sortable": True}
            ]
        }
        
        return DashboardWidget(
            widget_id="optimization_recommendations",
            title="Cost Optimization Recommendations",
            widget_type="table",
            data=widget_data,
            priority=7
        )
    
    def _get_cost_status(self, summary: Dict[str, Any]) -> str:
        """Determine overall cost status"""
        projected_cost = summary.get("total_projected_monthly_cost", 0)
        alert_count = summary.get("active_alerts_count", 0)
        
        if alert_count > 0:
            return "warning"
        elif projected_cost > 1000:
            return "warning"
        elif projected_cost > 500:
            return "info"
        else:
            return "success"
    
    def _get_most_severe_level(self, alert_groups: Dict[str, List]) -> str:
        """Get the most severe alert level"""
        if alert_groups["emergency"]:
            return "emergency"
        elif alert_groups["critical"]:
            return "critical"
        elif alert_groups["warning"]:
            return "warning"
        elif alert_groups["info"]:
            return "info"
        else:
            return "none"
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of dashboard data"""
        quality_score = 100
        issues = []
        
        # Check for missing data
        if not data.get("current_costs"):
            quality_score -= 30
            issues.append("Missing current cost data")
        
        if not data.get("cost_trends"):
            quality_score -= 20
            issues.append("Missing cost trend data")
        
        if not data.get("efficiency_metrics"):
            quality_score -= 15
            issues.append("Missing efficiency metrics")
        
        # Check data freshness
        timestamp = data.get("timestamp")
        if timestamp:
            try:
                data_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                age_minutes = (datetime.now() - data_time.replace(tzinfo=None)).total_seconds() / 60
                if age_minutes > 30:
                    quality_score -= 10
                    issues.append("Data is more than 30 minutes old")
            except:
                quality_score -= 5
                issues.append("Invalid timestamp format")
        
        return {
            "score": max(0, quality_score),
            "status": "good" if quality_score >= 80 else "fair" if quality_score >= 60 else "poor",
            "issues": issues
        }
    
    def _get_empty_dashboard(self) -> Dict[str, Any]:
        """Get empty dashboard structure"""
        return {
            "widgets": {},
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "refresh_interval": self.config.refresh_interval,
                "data_quality": {"score": 0, "status": "poor", "issues": ["No data available"]}
            },
            "summary": {},
            "error": "Failed to load dashboard data"
        }
    
    async def get_widget_data(self, widget_id: str) -> Optional[DashboardWidget]:
        """Get data for a specific widget"""
        try:
            dashboard_data = await self.get_dashboard_data()
            return dashboard_data.get("widgets", {}).get(widget_id)
        except Exception as e:
            logger.error(f"Failed to get widget data for {widget_id}: {e}")
            return None
    
    async def refresh_widget(self, widget_id: str) -> Optional[DashboardWidget]:
        """Refresh a specific widget"""
        try:
            # Force refresh of dashboard data
            dashboard_data = await self.get_dashboard_data(force_refresh=True)
            return dashboard_data.get("widgets", {}).get(widget_id)
        except Exception as e:
            logger.error(f"Failed to refresh widget {widget_id}: {e}")
            return None
    
    async def export_dashboard_data(self, format: str = "json") -> str:
        """Export dashboard data in specified format"""
        try:
            dashboard_data = await self.get_dashboard_data()
            
            if format.lower() == "json":
                return json.dumps(dashboard_data, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export dashboard data: {e}")
            return ""


# Singleton instance
_dashboard_instance = None

def get_cost_dashboard() -> CostOptimizationDashboard:
    """Get singleton cost dashboard instance"""
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = CostOptimizationDashboard()
    return _dashboard_instance