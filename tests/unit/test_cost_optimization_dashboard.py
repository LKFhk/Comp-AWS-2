"""
Unit tests for Cost Optimization Dashboard

Tests the dashboard functionality including widget creation,
data processing, and dashboard management.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

from riskintel360.services.cost_optimization_dashboard import (
    CostOptimizationDashboard,
    DashboardWidget,
    CostDashboardConfig,
    get_cost_dashboard
)
from riskintel360.services.aws_cost_monitor import (
    CostMetric,
    CostAlert,
    CostOptimizationRecommendation,
    CostAlertLevel,
    ServiceCategory
)


class TestCostOptimizationDashboard:
    """Test Cost Optimization Dashboard functionality"""
    
    @pytest.fixture
    def dashboard_config(self):
        """Create dashboard configuration for testing"""
        return CostDashboardConfig(
            refresh_interval=300,
            alert_retention_days=30,
            recommendation_limit=10,
            enable_real_time_alerts=True
        )
    
    @pytest.fixture
    def dashboard(self, dashboard_config):
        """Create dashboard instance for testing"""
        return CostOptimizationDashboard(dashboard_config)
    
    @pytest.fixture
    def sample_dashboard_data(self):
        """Sample dashboard data for testing"""
        return {
            "summary": {
                "total_current_cost": 250.0,
                "total_projected_monthly_cost": 750.0,
                "potential_monthly_savings": 150.0,
                "cost_reduction_percentage": 20.0,
                "active_alerts_count": 2,
                "high_priority_recommendations": 3
            },
            "current_costs": {
                "Amazon Bedrock": CostMetric(
                    service_name="Amazon Bedrock",
                    category=ServiceCategory.AI_ML,
                    current_cost=100.0,
                    projected_monthly_cost=300.0,
                    usage_hours=168,
                    cost_per_hour=1.8
                ),
                "Amazon ECS": CostMetric(
                    service_name="Amazon Elastic Container Service",
                    category=ServiceCategory.COMPUTE,
                    current_cost=75.0,
                    projected_monthly_cost=225.0,
                    usage_hours=168,
                    cost_per_hour=1.3
                )
            },
            "data_cost_analysis": {
                "public_data_percentage": 0.8,
                "cost_reduction_achieved": 0.75,
                "meets_public_data_target": True,
                "meets_cost_reduction_target": False,
                "recommendations": ["Optimize premium data usage"]
            },
            "efficiency_metrics": {
                "efficiency_score": 75.0,
                "average_cpu_utilization": 65.0,
                "average_memory_utilization": 70.0,
                "scaling_events_count": 5,
                "recommendations": ["Adjust scaling policies"]
            },
            "alerts": [
                CostAlert(
                    alert_id="alert_1",
                    level=CostAlertLevel.WARNING,
                    service_name="Amazon Bedrock",
                    message="Cost threshold exceeded",
                    current_cost=300.0,
                    threshold=250.0,
                    recommendations=["Optimize usage"]
                )
            ],
            "recommendations": [
                CostOptimizationRecommendation(
                    recommendation_id="rec_1",
                    service_name="Amazon Bedrock",
                    category=ServiceCategory.AI_ML,
                    description="Optimize model usage",
                    potential_savings=50.0,
                    implementation_effort="low",
                    priority=1,
                    action_items=["Use Haiku for simple tasks"]
                )
            ],
            "cost_trends": {
                "total": [100, 105, 110, 108, 112],
                "bedrock": [40, 42, 45, 43, 46],
                "ecs": [30, 32, 35, 33, 36]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def test_dashboard_initialization(self, dashboard, dashboard_config):
        """Test dashboard initialization"""
        assert dashboard.config == dashboard_config
        assert dashboard.cost_monitor is not None
        assert dashboard.dashboard_cache == {}
        assert dashboard.last_refresh is None
        assert len(dashboard.widget_configs) > 0
    
    def test_dashboard_config_defaults(self):
        """Test dashboard configuration defaults"""
        config = CostDashboardConfig()
        assert config.refresh_interval == 300
        assert config.alert_retention_days == 30
        assert config.recommendation_limit == 10
        assert config.enable_real_time_alerts is True
        assert config.cost_threshold_multiplier == 1.0
    
    def test_is_cache_valid_no_cache(self, dashboard):
        """Test cache validity with no cache"""
        assert not dashboard._is_cache_valid()
    
    def test_is_cache_valid_fresh_cache(self, dashboard):
        """Test cache validity with fresh cache"""
        dashboard.last_refresh = datetime.now()
        dashboard.dashboard_cache = {"test": "data"}
        assert dashboard._is_cache_valid()
    
    def test_is_cache_valid_stale_cache(self, dashboard):
        """Test cache validity with stale cache"""
        dashboard.last_refresh = datetime.now() - timedelta(seconds=400)  # Older than refresh interval
        dashboard.dashboard_cache = {"test": "data"}
        assert not dashboard._is_cache_valid()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_dashboard_data_fresh(self, dashboard, sample_dashboard_data):
        """Test getting fresh dashboard data"""
        with patch.object(dashboard.cost_monitor, 'get_cost_dashboard_data') as mock_get_data:
            mock_get_data.return_value = sample_dashboard_data
            
            result = await dashboard.get_dashboard_data(force_refresh=True)
            
            assert result is not None
            assert "widgets" in result
            assert "metadata" in result
            assert "summary" in result
            
            # Check that cache was updated
            assert dashboard.dashboard_cache == result
            assert dashboard.last_refresh is not None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_dashboard_data_cached(self, dashboard, sample_dashboard_data):
        """Test getting cached dashboard data"""
        # Set up cache
        dashboard.dashboard_cache = {"cached": "data"}
        dashboard.last_refresh = datetime.now()
        
        result = await dashboard.get_dashboard_data(force_refresh=False)
        
        assert result == {"cached": "data"}
    
    @pytest.mark.asyncio
    async def test_create_cost_summary_widget(self, dashboard, sample_dashboard_data):
        """Test cost summary widget creation"""
        widget = await dashboard._create_cost_summary_widget(sample_dashboard_data)
        
        assert isinstance(widget, DashboardWidget)
        assert widget.widget_id == "cost_summary"
        assert widget.title == "Cost Summary"
        assert widget.widget_type == "metric"
        assert widget.priority == 1
        
        # Check widget data
        assert "metrics" in widget.data
        assert len(widget.data["metrics"]) == 4
        
        # Check specific metrics
        metrics = widget.data["metrics"]
        projection_metric = next(m for m in metrics if "Monthly Projection" in m["label"])
        assert projection_metric["value"] == 750.0
        assert projection_metric["format"] == "currency"
    
    @pytest.mark.asyncio
    async def test_create_cost_trends_widget(self, dashboard, sample_dashboard_data):
        """Test cost trends widget creation"""
        widget = await dashboard._create_cost_trends_widget(sample_dashboard_data)
        
        assert isinstance(widget, DashboardWidget)
        assert widget.widget_id == "cost_trends"
        assert widget.widget_type == "chart"
        
        # Check chart data
        chart_data = widget.data["chart_data"]
        assert "labels" in chart_data
        assert "datasets" in chart_data
        assert len(chart_data["datasets"]) > 0
        
        # Check that total costs are included
        total_dataset = next((ds for ds in chart_data["datasets"] if ds["label"] == "Total"), None)
        assert total_dataset is not None
        assert total_dataset["data"] == [100, 105, 110, 108, 112]
    
    @pytest.mark.asyncio
    async def test_create_service_breakdown_widget(self, dashboard, sample_dashboard_data):
        """Test service breakdown widget creation"""
        widget = await dashboard._create_service_breakdown_widget(sample_dashboard_data)
        
        assert isinstance(widget, DashboardWidget)
        assert widget.widget_id == "service_breakdown"
        assert widget.widget_type == "chart"
        
        # Check chart data
        chart_data = widget.data["chart_data"]
        assert "labels" in chart_data
        assert "datasets" in chart_data
        assert len(chart_data["datasets"]) == 1
        
        # Check data values
        dataset = chart_data["datasets"][0]
        assert len(dataset["data"]) == 2  # Two services
        assert sum(dataset["data"]) == widget.data["total_cost"]
    
    @pytest.mark.asyncio
    async def test_create_data_cost_widget(self, dashboard, sample_dashboard_data):
        """Test data cost analysis widget creation"""
        widget = await dashboard._create_data_cost_widget(sample_dashboard_data)
        
        assert isinstance(widget, DashboardWidget)
        assert widget.widget_id == "data_cost_analysis"
        assert widget.widget_type == "metric"
        
        # Check metrics
        metrics = widget.data["metrics"]
        assert len(metrics) == 4
        
        # Check public data usage metric
        public_metric = next(m for m in metrics if "Public Data Usage" in m["label"])
        assert public_metric["value"] == 80.0  # 0.8 * 100
        assert public_metric["format"] == "percentage"
        assert public_metric["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_create_efficiency_widget(self, dashboard, sample_dashboard_data):
        """Test efficiency metrics widget creation"""
        widget = await dashboard._create_efficiency_widget(sample_dashboard_data)
        
        assert isinstance(widget, DashboardWidget)
        assert widget.widget_id == "efficiency_metrics"
        assert widget.widget_type == "metric"
        
        # Check metrics
        metrics = widget.data["metrics"]
        assert len(metrics) == 4
        
        # Check efficiency score
        efficiency_metric = next(m for m in metrics if "Efficiency Score" in m["label"])
        assert efficiency_metric["value"] == 75.0
        assert efficiency_metric["status"] == "success"  # >= 70
    
    @pytest.mark.asyncio
    async def test_create_alerts_widget(self, dashboard, sample_dashboard_data):
        """Test alerts widget creation"""
        widget = await dashboard._create_alerts_widget(sample_dashboard_data)
        
        assert isinstance(widget, DashboardWidget)
        assert widget.widget_id == "active_alerts"
        assert widget.widget_type == "alert"
        
        # Check alert data
        assert "alert_groups" in widget.data
        assert "total_alerts" in widget.data
        assert "severity_counts" in widget.data
        
        # Check alert grouping
        alert_groups = widget.data["alert_groups"]
        assert "warning" in alert_groups
        assert len(alert_groups["warning"]) == 1
        
        # Check most severe level
        assert widget.data["most_severe"] == "warning"
    
    @pytest.mark.asyncio
    async def test_create_recommendations_widget(self, dashboard, sample_dashboard_data):
        """Test recommendations widget creation"""
        widget = await dashboard._create_recommendations_widget(sample_dashboard_data)
        
        assert isinstance(widget, DashboardWidget)
        assert widget.widget_id == "optimization_recommendations"
        assert widget.widget_type == "table"
        
        # Check table data
        assert "recommendations" in widget.data
        assert "columns" in widget.data
        assert "total_potential_savings" in widget.data
        
        # Check recommendations
        recommendations = widget.data["recommendations"]
        assert len(recommendations) == 1
        
        rec = recommendations[0]
        assert rec["service"] == "Amazon Bedrock"
        assert rec["potential_savings"] == 50.0
        assert rec["priority"] == 1
    
    def test_get_cost_status(self, dashboard):
        """Test cost status determination"""
        # Test success status
        summary = {"total_projected_monthly_cost": 200, "active_alerts_count": 0}
        assert dashboard._get_cost_status(summary) == "success"
        
        # Test info status
        summary = {"total_projected_monthly_cost": 600, "active_alerts_count": 0}
        assert dashboard._get_cost_status(summary) == "info"
        
        # Test warning status (high cost)
        summary = {"total_projected_monthly_cost": 1200, "active_alerts_count": 0}
        assert dashboard._get_cost_status(summary) == "warning"
        
        # Test warning status (alerts)
        summary = {"total_projected_monthly_cost": 200, "active_alerts_count": 2}
        assert dashboard._get_cost_status(summary) == "warning"
    
    def test_get_most_severe_level(self, dashboard):
        """Test most severe alert level determination"""
        # Test emergency
        alert_groups = {"emergency": [{"id": "1"}], "critical": [], "warning": [], "info": []}
        assert dashboard._get_most_severe_level(alert_groups) == "emergency"
        
        # Test critical
        alert_groups = {"emergency": [], "critical": [{"id": "1"}], "warning": [], "info": []}
        assert dashboard._get_most_severe_level(alert_groups) == "critical"
        
        # Test warning
        alert_groups = {"emergency": [], "critical": [], "warning": [{"id": "1"}], "info": []}
        assert dashboard._get_most_severe_level(alert_groups) == "warning"
        
        # Test info
        alert_groups = {"emergency": [], "critical": [], "warning": [], "info": [{"id": "1"}]}
        assert dashboard._get_most_severe_level(alert_groups) == "info"
        
        # Test none
        alert_groups = {"emergency": [], "critical": [], "warning": [], "info": []}
        assert dashboard._get_most_severe_level(alert_groups) == "none"
    
    def test_assess_data_quality(self, dashboard, sample_dashboard_data):
        """Test data quality assessment"""
        # Test good quality data
        quality = dashboard._assess_data_quality(sample_dashboard_data)
        assert quality["score"] >= 80
        assert quality["status"] == "good"
        assert len(quality["issues"]) == 0
        
        # Test missing data
        incomplete_data = {"summary": {}}  # Missing most data
        quality = dashboard._assess_data_quality(incomplete_data)
        assert quality["score"] < 80
        assert quality["status"] in ["fair", "poor"]
        assert len(quality["issues"]) > 0
    
    def test_get_empty_dashboard(self, dashboard):
        """Test empty dashboard structure"""
        empty_dashboard = dashboard._get_empty_dashboard()
        
        assert "widgets" in empty_dashboard
        assert "metadata" in empty_dashboard
        assert "summary" in empty_dashboard
        assert "error" in empty_dashboard
        
        assert empty_dashboard["widgets"] == {}
        assert empty_dashboard["metadata"]["data_quality"]["score"] == 0
    
    @pytest.mark.asyncio
    async def test_get_widget_data(self, dashboard, sample_dashboard_data):
        """Test getting specific widget data"""
        with patch.object(dashboard, 'get_dashboard_data') as mock_get_data:
            mock_get_data.return_value = {
                "widgets": {
                    "cost_summary": DashboardWidget(
                        widget_id="cost_summary",
                        title="Cost Summary",
                        widget_type="metric",
                        data={"test": "data"}
                    )
                }
            }
            
            widget = await dashboard.get_widget_data("cost_summary")
            
            assert widget is not None
            assert widget.widget_id == "cost_summary"
            assert widget.data == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_get_widget_data_not_found(self, dashboard):
        """Test getting non-existent widget data"""
        with patch.object(dashboard, 'get_dashboard_data') as mock_get_data:
            mock_get_data.return_value = {"widgets": {}}
            
            widget = await dashboard.get_widget_data("non_existent")
            
            assert widget is None
    
    @pytest.mark.asyncio
    async def test_refresh_widget(self, dashboard, sample_dashboard_data):
        """Test refreshing specific widget"""
        with patch.object(dashboard, 'get_dashboard_data') as mock_get_data:
            mock_get_data.return_value = {
                "widgets": {
                    "cost_summary": DashboardWidget(
                        widget_id="cost_summary",
                        title="Cost Summary",
                        widget_type="metric",
                        data={"refreshed": "data"}
                    )
                }
            }
            
            widget = await dashboard.refresh_widget("cost_summary")
            
            # Should call get_dashboard_data with force_refresh=True
            mock_get_data.assert_called_once_with(force_refresh=True)
            
            assert widget is not None
            assert widget.data == {"refreshed": "data"}
    
    @pytest.mark.asyncio
    async def test_export_dashboard_data_json(self, dashboard, sample_dashboard_data):
        """Test exporting dashboard data as JSON"""
        with patch.object(dashboard, 'get_dashboard_data') as mock_get_data:
            mock_get_data.return_value = {"test": "data", "number": 123}
            
            exported = await dashboard.export_dashboard_data("json")
            
            assert exported != ""
            
            # Should be valid JSON
            parsed = json.loads(exported)
            assert parsed["test"] == "data"
            assert parsed["number"] == 123
    
    @pytest.mark.asyncio
    async def test_export_dashboard_data_unsupported_format(self, dashboard):
        """Test exporting dashboard data with unsupported format"""
        with patch.object(dashboard, 'get_dashboard_data') as mock_get_data:
            mock_get_data.return_value = {"test": "data"}
            
            exported = await dashboard.export_dashboard_data("xml")
            
            assert exported == ""  # Should return empty string on error
    
    def test_get_cost_dashboard_singleton(self):
        """Test cost dashboard singleton pattern"""
        dashboard1 = get_cost_dashboard()
        dashboard2 = get_cost_dashboard()
        
        assert dashboard1 is dashboard2
        assert isinstance(dashboard1, CostOptimizationDashboard)


class TestDashboardWidget:
    """Test DashboardWidget data class"""
    
    def test_dashboard_widget_creation(self):
        """Test dashboard widget creation"""
        widget = DashboardWidget(
            widget_id="test_widget",
            title="Test Widget",
            widget_type="metric",
            data={"value": 100},
            refresh_interval=300,
            priority=1
        )
        
        assert widget.widget_id == "test_widget"
        assert widget.title == "Test Widget"
        assert widget.widget_type == "metric"
        assert widget.data == {"value": 100}
        assert widget.refresh_interval == 300
        assert widget.priority == 1
    
    def test_dashboard_widget_defaults(self):
        """Test dashboard widget default values"""
        widget = DashboardWidget(
            widget_id="test_widget",
            title="Test Widget",
            widget_type="metric",
            data={"value": 100}
        )
        
        assert widget.refresh_interval == 300  # Default
        assert widget.priority == 1  # Default


class TestCostDashboardConfig:
    """Test CostDashboardConfig data class"""
    
    def test_config_creation(self):
        """Test configuration creation"""
        config = CostDashboardConfig(
            refresh_interval=600,
            alert_retention_days=60,
            recommendation_limit=20,
            enable_real_time_alerts=False,
            cost_threshold_multiplier=1.5
        )
        
        assert config.refresh_interval == 600
        assert config.alert_retention_days == 60
        assert config.recommendation_limit == 20
        assert config.enable_real_time_alerts is False
        assert config.cost_threshold_multiplier == 1.5
    
    def test_config_defaults(self):
        """Test configuration default values"""
        config = CostDashboardConfig()
        
        assert config.refresh_interval == 300
        assert config.alert_retention_days == 30
        assert config.recommendation_limit == 10
        assert config.enable_real_time_alerts is True
        assert config.cost_threshold_multiplier == 1.0


# Performance tests
class TestDashboardPerformance:
    """Test dashboard performance requirements"""
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_dashboard_refresh_performance(self):
        """Test dashboard refresh performance"""
        import time
        
        dashboard = CostOptimizationDashboard()
        
        # Mock cost monitor to return data quickly
        with patch.object(dashboard.cost_monitor, 'get_cost_dashboard_data') as mock_get_data:
            mock_get_data.return_value = {
                "summary": {"total_projected_monthly_cost": 500},
                "current_costs": {},
                "data_cost_analysis": {},
                "efficiency_metrics": {},
                "alerts": [],
                "recommendations": [],
                "cost_trends": {},
                "timestamp": datetime.now().isoformat()
            }
            
            start_time = time.time()
            result = await dashboard.get_dashboard_data(force_refresh=True)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Dashboard refresh should be fast (< 2 seconds)
            assert processing_time < 2.0
            assert result is not None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_widget_creation_performance(self):
        """Test widget creation performance"""
        import time
        
        dashboard = CostOptimizationDashboard()
        
        # Create large sample data
        large_sample_data = {
            "summary": {"total_projected_monthly_cost": 1000},
            "current_costs": {
                f"Service{i}": CostMetric(
                    service_name=f"Service{i}",
                    category=ServiceCategory.COMPUTE,
                    current_cost=i * 10.0,
                    projected_monthly_cost=i * 30.0,
                    usage_hours=168,
                    cost_per_hour=i * 0.18
                ) for i in range(50)  # 50 services
            },
            "data_cost_analysis": {"public_data_percentage": 0.8},
            "efficiency_metrics": {"efficiency_score": 75.0},
            "alerts": [
                CostAlert(
                    alert_id=f"alert_{i}",
                    level=CostAlertLevel.WARNING,
                    service_name=f"Service{i}",
                    message=f"Alert {i}",
                    current_cost=i * 100.0,
                    threshold=i * 80.0
                ) for i in range(20)  # 20 alerts
            ],
            "recommendations": [
                CostOptimizationRecommendation(
                    recommendation_id=f"rec_{i}",
                    service_name=f"Service{i}",
                    category=ServiceCategory.COMPUTE,
                    description=f"Recommendation {i}",
                    potential_savings=i * 25.0,
                    implementation_effort="medium",
                    priority=i % 5 + 1
                ) for i in range(30)  # 30 recommendations
            ],
            "cost_trends": {"total": list(range(30))},
            "timestamp": datetime.now().isoformat()
        }
        
        start_time = time.time()
        processed_data = await dashboard._process_dashboard_data(large_sample_data)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Widget processing should handle large datasets efficiently (< 3 seconds)
        assert processing_time < 3.0
        assert "widgets" in processed_data
        assert len(processed_data["widgets"]) > 0


if __name__ == "__main__":
    pytest.main([__file__])
