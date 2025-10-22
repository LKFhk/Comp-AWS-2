"""
Cost Optimization API Endpoints

Provides REST API endpoints for AWS cost monitoring, optimization,
and dashboard functionality.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..services.aws_cost_monitor import get_cost_monitor, CostAlertLevel
from ..services.cost_optimization_dashboard import get_cost_dashboard
from ..auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/cost-optimization", tags=["cost-optimization"])


# Request/Response Models
class CostSummaryResponse(BaseModel):
    """Cost summary response model"""
    total_current_cost: float = Field(..., description="Total current cost")
    total_projected_monthly_cost: float = Field(..., description="Projected monthly cost")
    potential_monthly_savings: float = Field(..., description="Potential monthly savings")
    cost_reduction_percentage: float = Field(..., description="Cost reduction percentage")
    active_alerts_count: int = Field(..., description="Number of active alerts")
    high_priority_recommendations: int = Field(..., description="High priority recommendations count")
    last_updated: str = Field(..., description="Last update timestamp")


class ServiceCostResponse(BaseModel):
    """Service cost response model"""
    service_name: str = Field(..., description="AWS service name")
    category: str = Field(..., description="Service category")
    current_cost: float = Field(..., description="Current cost")
    projected_monthly_cost: float = Field(..., description="Projected monthly cost")
    usage_hours: float = Field(..., description="Usage hours")
    cost_per_hour: float = Field(..., description="Cost per hour")


class CostAlertResponse(BaseModel):
    """Cost alert response model"""
    alert_id: str = Field(..., description="Alert identifier")
    level: str = Field(..., description="Alert level")
    service_name: str = Field(..., description="Service name")
    message: str = Field(..., description="Alert message")
    current_cost: float = Field(..., description="Current cost")
    threshold: float = Field(..., description="Cost threshold")
    recommendations: List[str] = Field(..., description="Recommendations")
    timestamp: str = Field(..., description="Alert timestamp")


class OptimizationRecommendationResponse(BaseModel):
    """Optimization recommendation response model"""
    recommendation_id: str = Field(..., description="Recommendation identifier")
    service_name: str = Field(..., description="Service name")
    category: str = Field(..., description="Service category")
    description: str = Field(..., description="Recommendation description")
    potential_savings: float = Field(..., description="Potential savings amount")
    implementation_effort: str = Field(..., description="Implementation effort level")
    priority: int = Field(..., description="Priority level (1-5)")
    action_items: List[str] = Field(..., description="Action items")


class DataCostAnalysisResponse(BaseModel):
    """Data cost analysis response model"""
    public_data_cost: float = Field(..., description="Public data source costs")
    premium_data_cost: float = Field(..., description="Premium data source costs")
    total_data_cost: float = Field(..., description="Total data costs")
    public_data_percentage: float = Field(..., description="Percentage of public data usage")
    cost_reduction_achieved: float = Field(..., description="Cost reduction achieved")
    meets_public_data_target: bool = Field(..., description="Meets 80% public data target")
    meets_cost_reduction_target: bool = Field(..., description="Meets 80% cost reduction target")
    recommendations: List[str] = Field(..., description="Data cost optimization recommendations")


class EfficiencyMetricsResponse(BaseModel):
    """Auto-scaling efficiency metrics response model"""
    efficiency_score: float = Field(..., description="Overall efficiency score (0-100)")
    average_cpu_utilization: float = Field(..., description="Average CPU utilization percentage")
    average_memory_utilization: float = Field(..., description="Average memory utilization percentage")
    scaling_events_count: int = Field(..., description="Number of scaling events in 24h")
    cost_per_task: float = Field(..., description="Cost per ECS task")
    recommendations: List[str] = Field(..., description="Efficiency optimization recommendations")


class DashboardDataResponse(BaseModel):
    """Complete dashboard data response model"""
    summary: CostSummaryResponse = Field(..., description="Cost summary")
    current_costs: Dict[str, ServiceCostResponse] = Field(..., description="Current service costs")
    data_cost_analysis: DataCostAnalysisResponse = Field(..., description="Data cost analysis")
    efficiency_metrics: EfficiencyMetricsResponse = Field(..., description="Efficiency metrics")
    alerts: List[CostAlertResponse] = Field(..., description="Active cost alerts")
    recommendations: List[OptimizationRecommendationResponse] = Field(..., description="Optimization recommendations")
    cost_trends: Dict[str, List[float]] = Field(..., description="Cost trends over time")
    timestamp: str = Field(..., description="Data timestamp")


class CostThresholdUpdateRequest(BaseModel):
    """Cost threshold update request model"""
    service_name: str = Field(..., description="Service name")
    warning_threshold: Optional[float] = Field(None, description="Warning threshold")
    critical_threshold: Optional[float] = Field(None, description="Critical threshold")
    emergency_threshold: Optional[float] = Field(None, description="Emergency threshold")


# API Endpoints

@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    current_user: dict = Depends(get_current_user)
) -> CostSummaryResponse:
    """
    Get cost summary overview
    
    Returns:
        Cost summary with key metrics
    """
    try:
        cost_monitor = get_cost_monitor()
        dashboard_data = await cost_monitor.get_cost_dashboard_data()
        
        summary = dashboard_data.get("summary", {})
        
        return CostSummaryResponse(
            total_current_cost=summary.get("total_current_cost", 0.0),
            total_projected_monthly_cost=summary.get("total_projected_monthly_cost", 0.0),
            potential_monthly_savings=summary.get("potential_monthly_savings", 0.0),
            cost_reduction_percentage=summary.get("cost_reduction_percentage", 0.0),
            active_alerts_count=summary.get("active_alerts_count", 0),
            high_priority_recommendations=summary.get("high_priority_recommendations", 0),
            last_updated=summary.get("last_updated", datetime.now().isoformat())
        )
        
    except Exception as e:
        logger.error(f"Failed to get cost summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cost summary: {str(e)}")


@router.get("/services", response_model=Dict[str, ServiceCostResponse])
async def get_service_costs(
    days_back: int = Query(7, ge=1, le=30, description="Days to look back for cost data"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, ServiceCostResponse]:
    """
    Get current costs for all AWS services
    
    Args:
        days_back: Number of days to look back for cost data
        
    Returns:
        Dictionary of service costs
    """
    try:
        cost_monitor = get_cost_monitor()
        current_costs = await cost_monitor.get_current_costs(days_back=days_back)
        
        response = {}
        for service_name, cost_metric in current_costs.items():
            response[service_name] = ServiceCostResponse(
                service_name=cost_metric.service_name,
                category=cost_metric.category.value,
                current_cost=cost_metric.current_cost,
                projected_monthly_cost=cost_metric.projected_monthly_cost,
                usage_hours=cost_metric.usage_hours,
                cost_per_hour=cost_metric.cost_per_hour
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get service costs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get service costs: {str(e)}")


@router.get("/alerts", response_model=List[CostAlertResponse])
async def get_cost_alerts(
    level: Optional[str] = Query(None, description="Filter by alert level"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    current_user: dict = Depends(get_current_user)
) -> List[CostAlertResponse]:
    """
    Get active cost alerts
    
    Args:
        level: Filter by alert level (info, warning, critical, emergency)
        service: Filter by service name
        
    Returns:
        List of active cost alerts
    """
    try:
        cost_monitor = get_cost_monitor()
        current_costs = await cost_monitor.get_current_costs()
        alerts = await cost_monitor.generate_cost_alerts(current_costs)
        
        # Filter alerts if requested
        filtered_alerts = alerts
        if level:
            filtered_alerts = [a for a in filtered_alerts if a.level.value == level.lower()]
        if service:
            filtered_alerts = [a for a in filtered_alerts if service.lower() in a.service_name.lower()]
        
        response = []
        for alert in filtered_alerts:
            response.append(CostAlertResponse(
                alert_id=alert.alert_id,
                level=alert.level.value,
                service_name=alert.service_name,
                message=alert.message,
                current_cost=alert.current_cost,
                threshold=alert.threshold,
                recommendations=alert.recommendations,
                timestamp=alert.timestamp.isoformat()
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get cost alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cost alerts: {str(e)}")


@router.get("/recommendations", response_model=List[OptimizationRecommendationResponse])
async def get_optimization_recommendations(
    category: Optional[str] = Query(None, description="Filter by service category"),
    priority: Optional[int] = Query(None, ge=1, le=5, description="Filter by priority level"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of recommendations"),
    current_user: dict = Depends(get_current_user)
) -> List[OptimizationRecommendationResponse]:
    """
    Get cost optimization recommendations
    
    Args:
        category: Filter by service category
        priority: Filter by priority level (1-5)
        limit: Maximum number of recommendations to return
        
    Returns:
        List of optimization recommendations
    """
    try:
        cost_monitor = get_cost_monitor()
        current_costs = await cost_monitor.get_current_costs()
        efficiency_metrics = await cost_monitor.track_auto_scaling_efficiency()
        recommendations = await cost_monitor.generate_optimization_recommendations(
            current_costs, efficiency_metrics
        )
        
        # Filter recommendations if requested
        filtered_recommendations = recommendations
        if category:
            filtered_recommendations = [r for r in filtered_recommendations if r.category.value == category.lower()]
        if priority:
            filtered_recommendations = [r for r in filtered_recommendations if r.priority == priority]
        
        # Sort by priority and potential savings
        filtered_recommendations.sort(key=lambda x: (x.priority, -x.potential_savings))
        
        # Limit results
        filtered_recommendations = filtered_recommendations[:limit]
        
        response = []
        for rec in filtered_recommendations:
            response.append(OptimizationRecommendationResponse(
                recommendation_id=rec.recommendation_id,
                service_name=rec.service_name,
                category=rec.category.value,
                description=rec.description,
                potential_savings=rec.potential_savings,
                implementation_effort=rec.implementation_effort,
                priority=rec.priority,
                action_items=rec.action_items
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get optimization recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimization recommendations: {str(e)}")


@router.get("/data-cost-analysis", response_model=DataCostAnalysisResponse)
async def get_data_cost_analysis(
    current_user: dict = Depends(get_current_user)
) -> DataCostAnalysisResponse:
    """
    Get public vs premium data cost analysis
    
    Returns:
        Data cost analysis showing public data usage efficiency
    """
    try:
        cost_monitor = get_cost_monitor()
        analysis = await cost_monitor.monitor_public_vs_premium_data_costs()
        
        return DataCostAnalysisResponse(
            public_data_cost=analysis.get("public_data_cost", 0.0),
            premium_data_cost=analysis.get("premium_data_cost", 0.0),
            total_data_cost=analysis.get("total_data_cost", 0.0),
            public_data_percentage=analysis.get("public_data_percentage", 0.0),
            cost_reduction_achieved=analysis.get("cost_reduction_achieved", 0.0),
            meets_public_data_target=analysis.get("meets_public_data_target", False),
            meets_cost_reduction_target=analysis.get("meets_cost_reduction_target", False),
            recommendations=analysis.get("recommendations", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to get data cost analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get data cost analysis: {str(e)}")


@router.get("/efficiency-metrics", response_model=EfficiencyMetricsResponse)
async def get_efficiency_metrics(
    current_user: dict = Depends(get_current_user)
) -> EfficiencyMetricsResponse:
    """
    Get auto-scaling efficiency metrics
    
    Returns:
        Auto-scaling efficiency metrics and recommendations
    """
    try:
        cost_monitor = get_cost_monitor()
        metrics = await cost_monitor.track_auto_scaling_efficiency()
        
        return EfficiencyMetricsResponse(
            efficiency_score=metrics.get("efficiency_score", 0.0),
            average_cpu_utilization=metrics.get("average_cpu_utilization", 0.0),
            average_memory_utilization=metrics.get("average_memory_utilization", 0.0),
            scaling_events_count=metrics.get("scaling_events_count", 0),
            cost_per_task=metrics.get("cost_per_task", 0.0),
            recommendations=metrics.get("recommendations", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to get efficiency metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get efficiency metrics: {str(e)}")


@router.get("/dashboard", response_model=DashboardDataResponse)
async def get_dashboard_data(
    force_refresh: bool = Query(False, description="Force refresh of dashboard data"),
    current_user: dict = Depends(get_current_user)
) -> DashboardDataResponse:
    """
    Get complete cost optimization dashboard data
    
    Args:
        force_refresh: Force refresh of cached data
        
    Returns:
        Complete dashboard data including all cost metrics
    """
    try:
        cost_dashboard = get_cost_dashboard()
        dashboard_data = await cost_dashboard.get_dashboard_data(force_refresh=force_refresh)
        
        # Convert to response models
        summary_data = dashboard_data.get("summary", {})
        summary = CostSummaryResponse(
            total_current_cost=summary_data.get("total_current_cost", 0.0),
            total_projected_monthly_cost=summary_data.get("total_projected_monthly_cost", 0.0),
            potential_monthly_savings=summary_data.get("potential_monthly_savings", 0.0),
            cost_reduction_percentage=summary_data.get("cost_reduction_percentage", 0.0),
            active_alerts_count=summary_data.get("active_alerts_count", 0),
            high_priority_recommendations=summary_data.get("high_priority_recommendations", 0),
            last_updated=summary_data.get("last_updated", datetime.now().isoformat())
        )
        
        # Convert current costs
        current_costs = {}
        for service_name, cost_metric in dashboard_data.get("current_costs", {}).items():
            current_costs[service_name] = ServiceCostResponse(
                service_name=cost_metric.service_name,
                category=cost_metric.category.value,
                current_cost=cost_metric.current_cost,
                projected_monthly_cost=cost_metric.projected_monthly_cost,
                usage_hours=cost_metric.usage_hours,
                cost_per_hour=cost_metric.cost_per_hour
            )
        
        # Convert data cost analysis
        data_analysis = dashboard_data.get("data_cost_analysis", {})
        data_cost_analysis = DataCostAnalysisResponse(
            public_data_cost=data_analysis.get("public_data_cost", 0.0),
            premium_data_cost=data_analysis.get("premium_data_cost", 0.0),
            total_data_cost=data_analysis.get("total_data_cost", 0.0),
            public_data_percentage=data_analysis.get("public_data_percentage", 0.0),
            cost_reduction_achieved=data_analysis.get("cost_reduction_achieved", 0.0),
            meets_public_data_target=data_analysis.get("meets_public_data_target", False),
            meets_cost_reduction_target=data_analysis.get("meets_cost_reduction_target", False),
            recommendations=data_analysis.get("recommendations", [])
        )
        
        # Convert efficiency metrics
        efficiency_data = dashboard_data.get("efficiency_metrics", {})
        efficiency_metrics = EfficiencyMetricsResponse(
            efficiency_score=efficiency_data.get("efficiency_score", 0.0),
            average_cpu_utilization=efficiency_data.get("average_cpu_utilization", 0.0),
            average_memory_utilization=efficiency_data.get("average_memory_utilization", 0.0),
            scaling_events_count=efficiency_data.get("scaling_events_count", 0),
            cost_per_task=efficiency_data.get("cost_per_task", 0.0),
            recommendations=efficiency_data.get("recommendations", [])
        )
        
        # Convert alerts
        alerts = []
        for alert in dashboard_data.get("alerts", []):
            alerts.append(CostAlertResponse(
                alert_id=alert.alert_id,
                level=alert.level.value,
                service_name=alert.service_name,
                message=alert.message,
                current_cost=alert.current_cost,
                threshold=alert.threshold,
                recommendations=alert.recommendations,
                timestamp=alert.timestamp.isoformat()
            ))
        
        # Convert recommendations
        recommendations = []
        for rec in dashboard_data.get("recommendations", []):
            recommendations.append(OptimizationRecommendationResponse(
                recommendation_id=rec.recommendation_id,
                service_name=rec.service_name,
                category=rec.category.value,
                description=rec.description,
                potential_savings=rec.potential_savings,
                implementation_effort=rec.implementation_effort,
                priority=rec.priority,
                action_items=rec.action_items
            ))
        
        return DashboardDataResponse(
            summary=summary,
            current_costs=current_costs,
            data_cost_analysis=data_cost_analysis,
            efficiency_metrics=efficiency_metrics,
            alerts=alerts,
            recommendations=recommendations,
            cost_trends=dashboard_data.get("cost_trends", {}),
            timestamp=dashboard_data.get("timestamp", datetime.now().isoformat())
        )
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


@router.get("/trends")
async def get_cost_trends(
    days: int = Query(30, ge=7, le=90, description="Number of days for trend data"),
    services: Optional[str] = Query(None, description="Comma-separated list of services"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, List[float]]:
    """
    Get cost trends over time
    
    Args:
        days: Number of days to get trend data for
        services: Comma-separated list of specific services to include
        
    Returns:
        Dictionary of cost trends by service
    """
    try:
        cost_monitor = get_cost_monitor()
        trends = await cost_monitor._get_cost_trends()
        
        # Filter services if requested
        if services:
            service_list = [s.strip().lower() for s in services.split(",")]
            filtered_trends = {}
            for service, trend_data in trends.items():
                if service.lower() in service_list:
                    filtered_trends[service] = trend_data
            trends = filtered_trends
        
        return trends
        
    except Exception as e:
        logger.error(f"Failed to get cost trends: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cost trends: {str(e)}")


@router.post("/thresholds")
async def update_cost_thresholds(
    threshold_update: CostThresholdUpdateRequest,
    current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    """
    Update cost alert thresholds for a service
    
    Args:
        threshold_update: Threshold update request
        
    Returns:
        Success message
    """
    try:
        cost_monitor = get_cost_monitor()
        
        # Update thresholds in cost monitor
        service_key = cost_monitor._get_service_threshold_key(threshold_update.service_name)
        
        if service_key not in cost_monitor.cost_thresholds:
            cost_monitor.cost_thresholds[service_key] = {}
        
        if threshold_update.warning_threshold is not None:
            cost_monitor.cost_thresholds[service_key]["warning"] = threshold_update.warning_threshold
        
        if threshold_update.critical_threshold is not None:
            cost_monitor.cost_thresholds[service_key]["critical"] = threshold_update.critical_threshold
        
        if threshold_update.emergency_threshold is not None:
            cost_monitor.cost_thresholds[service_key]["emergency"] = threshold_update.emergency_threshold
        
        logger.info(f"Updated cost thresholds for {threshold_update.service_name}")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Cost thresholds updated for {threshold_update.service_name}",
                "service": threshold_update.service_name,
                "thresholds": cost_monitor.cost_thresholds[service_key]
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to update cost thresholds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update cost thresholds: {str(e)}")


@router.post("/refresh")
async def refresh_cost_data(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    """
    Trigger refresh of cost monitoring data
    
    Returns:
        Success message
    """
    try:
        async def refresh_data():
            """Background task to refresh cost data"""
            cost_monitor = get_cost_monitor()
            cost_dashboard = get_cost_dashboard()
            
            # Force refresh of all data
            await cost_monitor.get_current_costs()
            await cost_dashboard.get_dashboard_data(force_refresh=True)
            
            logger.info("Cost data refresh completed")
        
        # Add background task
        background_tasks.add_task(refresh_data)
        
        return JSONResponse(
            status_code=202,
            content={
                "message": "Cost data refresh initiated",
                "status": "processing"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to refresh cost data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh cost data: {str(e)}")


@router.get("/health")
async def health_check() -> JSONResponse:
    """
    Health check endpoint for cost optimization service
    
    Returns:
        Service health status
    """
    try:
        cost_monitor = get_cost_monitor()
        
        # Basic health checks
        health_status = {
            "service": "cost-optimization",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "cost_monitor": "ok",
                "aws_clients": "ok"
            }
        }
        
        # Test AWS client connectivity
        try:
            if cost_monitor.cost_explorer:
                health_status["checks"]["cost_explorer"] = "ok"
            if cost_monitor.cloudwatch:
                health_status["checks"]["cloudwatch"] = "ok"
        except Exception as e:
            health_status["checks"]["aws_clients"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        return JSONResponse(
            status_code=200 if health_status["status"] == "healthy" else 503,
            content=health_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "service": "cost-optimization",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )