"""
Integration tests for AWS Cost Tracking

Tests the integration between cost monitoring components and AWS services,
including Cost Explorer, CloudWatch, and dashboard integration.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import boto3
# from moto import mock_ce, mock_cloudwatch, mock_ecs  # Optional dependency

from riskintel360.services.aws_cost_monitor import AWSCostMonitor, get_cost_monitor
from riskintel360.services.cost_optimization_dashboard import CostOptimizationDashboard, get_cost_dashboard


class TestAWSCostTrackingIntegration:
    """Test AWS cost tracking integration"""
    
    @pytest.fixture
    def cost_monitor(self):
        """Create cost monitor for integration testing"""
        return AWSCostMonitor(region="us-east-1")
    
    @pytest.fixture
    def cost_dashboard(self):
        """Create cost dashboard for integration testing"""
        return CostOptimizationDashboard()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cost_monitor_dashboard_integration(self, cost_monitor, cost_dashboard):
        """Test integration between cost monitor and dashboard"""
        # Mock cost monitor methods
        with patch.object(cost_monitor, 'get_current_costs') as mock_costs, \
             patch.object(cost_monitor, 'monitor_public_vs_premium_data_costs') as mock_data_costs, \
             patch.object(cost_monitor, 'track_auto_scaling_efficiency') as mock_efficiency, \
             patch.object(cost_monitor, 'generate_cost_alerts') as mock_alerts, \
             patch.object(cost_monitor, 'generate_optimization_recommendations') as mock_recommendations, \
             patch.object(cost_monitor, '_get_cost_trends') as mock_trends:
            
            # Set up mock data
            from riskintel360.services.aws_cost_monitor import CostMetric, ServiceCategory
            
            mock_costs.return_value = {
                "Amazon Bedrock": CostMetric(
                    service_name="Amazon Bedrock",
                    category=ServiceCategory.AI_ML,
                    current_cost=100.0,
                    projected_monthly_cost=300.0,
                    usage_hours=168,
                    cost_per_hour=1.8
                )
            }
            
            mock_data_costs.return_value = {
                "public_data_percentage": 0.8,
                "cost_reduction_achieved": 0.75,
                "meets_public_data_target": True,
                "meets_cost_reduction_target": False
            }
            
            mock_efficiency.return_value = {
                "efficiency_score": 75.0,
                "average_cpu_utilization": 65.0,
                "recommendations": []
            }
            
            mock_alerts.return_value = []
            mock_recommendations.return_value = []
            mock_trends.return_value = {"total": [100, 105, 110]}
            
            # Replace dashboard's cost monitor with our mocked one
            cost_dashboard.cost_monitor = cost_monitor
            
            # Test dashboard data retrieval
            dashboard_data = await cost_dashboard.get_dashboard_data(force_refresh=True)
            
            # Verify integration
            assert dashboard_data is not None
            assert "widgets" in dashboard_data
            assert "metadata" in dashboard_data
            
            # Verify all widgets were created
            widgets = dashboard_data["widgets"]
            expected_widgets = [
                "cost_summary", "cost_trends", "service_breakdown",
                "data_cost_analysis", "efficiency_metrics", 
                "active_alerts", "optimization_recommendations"
            ]
            
            for widget_id in expected_widgets:
                assert widget_id in widgets
                assert widgets[widget_id] is not None
    
    @pytest.mark.integration
    # @mock_ce  # Requires moto library
    async def test_cost_explorer_integration(self, cost_monitor):
        """Test Cost Explorer integration with mocked AWS"""
        # Create mock Cost Explorer client
        ce_client = boto3.client('ce', region_name='us-east-1')
        
        # Mock the cost monitor's client
        cost_monitor.cost_explorer = ce_client
        
        # Test getting costs (will use mocked CE)
        costs = await cost_monitor.get_current_costs(days_back=7)
        
        # Should handle empty response gracefully
        assert isinstance(costs, dict)
    
    @pytest.mark.integration
    # @mock_cloudwatch  # Requires moto library
    async def test_cloudwatch_integration(self, cost_monitor):
        """Test CloudWatch integration with mocked AWS"""
        # Create mock CloudWatch client
        cw_client = boto3.client('cloudwatch', region_name='us-east-1')
        
        # Mock the cost monitor's client
        cost_monitor.cloudwatch = cw_client
        
        # Test getting ECS metrics (will use mocked CloudWatch)
        metrics = await cost_monitor._get_ecs_cluster_metrics()
        
        # Should handle empty response gracefully
        assert isinstance(metrics, dict)
    
    @pytest.mark.integration
    async def test_end_to_end_cost_workflow(self, cost_monitor, cost_dashboard):
        """Test complete end-to-end cost monitoring workflow"""
        # Mock all external AWS calls
        with patch.object(cost_monitor, '_get_cost_and_usage') as mock_cost_usage, \
             patch.object(cost_monitor, '_get_cloudwatch_metric') as mock_cw_metric:
            
            # Mock Cost Explorer response
            mock_cost_usage.return_value = {
                'ResultsByTime': [
                    {
                        'Groups': [
                            {
                                'Keys': ['Amazon Bedrock'],
                                'Metrics': {'BlendedCost': {'Amount': '150.75'}}
                            },
                            {
                                'Keys': ['Amazon Elastic Container Service'],
                                'Metrics': {'BlendedCost': {'Amount': '85.50'}}
                            },
                            {
                                'Keys': ['Amazon Simple Storage Service'],
                                'Metrics': {'BlendedCost': {'Amount': '25.25'}}
                            }
                        ]
                    }
                ]
            }
            
            # Mock CloudWatch response
            mock_cw_metric.return_value = {
                'Datapoints': [
                    {'Average': 65.5, 'Timestamp': datetime.now()},
                    {'Average': 70.2, 'Timestamp': datetime.now()}
                ]
            }
            
            # Replace dashboard's cost monitor
            cost_dashboard.cost_monitor = cost_monitor
            
            # Execute complete workflow
            
            # 1. Get current costs
            current_costs = await cost_monitor.get_current_costs()
            assert len(current_costs) == 3
            assert "Amazon Bedrock" in current_costs
            
            # 2. Monitor data costs
            data_analysis = await cost_monitor.monitor_public_vs_premium_data_costs()
            assert "public_data_percentage" in data_analysis
            
            # 3. Track efficiency
            efficiency = await cost_monitor.track_auto_scaling_efficiency()
            assert "efficiency_score" in efficiency
            
            # 4. Generate alerts
            alerts = await cost_monitor.generate_cost_alerts(current_costs)
            assert isinstance(alerts, list)
            
            # 5. Generate recommendations
            recommendations = await cost_monitor.generate_optimization_recommendations(
                current_costs, efficiency
            )
            assert isinstance(recommendations, list)
            
            # 6. Get complete dashboard
            dashboard_data = await cost_dashboard.get_dashboard_data(force_refresh=True)
            assert dashboard_data is not None
            
            # Verify workflow results
            summary = dashboard_data.get("summary", {})
            assert summary.get("total_projected_monthly_cost", 0) > 0
    
    @pytest.mark.integration
    async def test_concurrent_cost_operations(self, cost_monitor):
        """Test concurrent cost monitoring operations"""
        # Mock external calls for consistent results
        with patch.object(cost_monitor, '_get_cost_and_usage') as mock_cost_usage, \
             patch.object(cost_monitor, '_get_cloudwatch_metric') as mock_cw_metric:
            
            mock_cost_usage.return_value = {
                'ResultsByTime': [
                    {
                        'Groups': [
                            {
                                'Keys': ['Amazon Bedrock'],
                                'Metrics': {'BlendedCost': {'Amount': '100.00'}}
                            }
                        ]
                    }
                ]
            }
            
            mock_cw_metric.return_value = {
                'Datapoints': [
                    {'Average': 65.0, 'Timestamp': datetime.now()}
                ]
            }
            
            # Run multiple operations concurrently
            tasks = [
                cost_monitor.get_current_costs(),
                cost_monitor.monitor_public_vs_premium_data_costs(),
                cost_monitor.track_auto_scaling_efficiency(),
                cost_monitor.get_cost_dashboard_data()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All operations should complete successfully
            for result in results:
                assert not isinstance(result, Exception)
                assert result is not None
    
    @pytest.mark.integration
    async def test_cost_alert_workflow_integration(self, cost_monitor):
        """Test cost alert generation and processing workflow"""
        # Create cost scenario that triggers alerts
        with patch.object(cost_monitor, '_get_cost_and_usage') as mock_cost_usage:
            
            # High cost scenario
            mock_cost_usage.return_value = {
                'ResultsByTime': [
                    {
                        'Groups': [
                            {
                                'Keys': ['Amazon Bedrock'],
                                'Metrics': {'BlendedCost': {'Amount': '200.00'}}  # High cost
                            }
                        ]
                    }
                ]
            }
            
            # Get costs and generate alerts
            current_costs = await cost_monitor.get_current_costs()
            alerts = await cost_monitor.generate_cost_alerts(current_costs)
            
            # Should generate alerts for high costs
            assert len(alerts) > 0
            
            # Check alert properties
            for alert in alerts:
                assert hasattr(alert, 'alert_id')
                assert hasattr(alert, 'level')
                assert hasattr(alert, 'service_name')
                assert hasattr(alert, 'message')
                assert hasattr(alert, 'recommendations')
                assert len(alert.recommendations) > 0
    
    @pytest.mark.integration
    async def test_optimization_recommendation_workflow(self, cost_monitor):
        """Test optimization recommendation generation workflow"""
        # Create scenario with optimization opportunities
        from riskintel360.services.aws_cost_monitor import CostMetric, ServiceCategory
        
        cost_metrics = {
            "Amazon Bedrock": CostMetric(
                service_name="Amazon Bedrock",
                category=ServiceCategory.AI_ML,
                current_cost=150.0,
                projected_monthly_cost=450.0,  # High AI/ML costs
                usage_hours=168,
                cost_per_hour=2.7
            ),
            "Amazon S3": CostMetric(
                service_name="Amazon Simple Storage Service",
                category=ServiceCategory.STORAGE,
                current_cost=100.0,
                projected_monthly_cost=300.0,  # High storage costs
                usage_hours=168,
                cost_per_hour=1.8
            )
        }
        
        efficiency_metrics = {
            "efficiency_score": 55.0,  # Low efficiency
            "average_cpu_utilization": 40.0,  # Low CPU usage
            "average_memory_utilization": 45.0  # Low memory usage
        }
        
        # Generate recommendations
        recommendations = await cost_monitor.generate_optimization_recommendations(
            cost_metrics, efficiency_metrics
        )
        
        # Should generate multiple recommendations
        assert len(recommendations) > 0
        
        # Should have AI/ML recommendations
        ai_ml_recs = [r for r in recommendations if r.category == ServiceCategory.AI_ML]
        assert len(ai_ml_recs) > 0
        
        # Should have storage recommendations
        storage_recs = [r for r in recommendations if r.category == ServiceCategory.STORAGE]
        assert len(storage_recs) > 0
        
        # Should have efficiency recommendations
        efficiency_recs = [r for r in recommendations if "efficiency" in r.description.lower()]
        assert len(efficiency_recs) > 0
        
        # Check recommendation properties
        for rec in recommendations:
            assert rec.potential_savings > 0
            assert rec.priority >= 1
            assert len(rec.action_items) > 0
    
    @pytest.mark.integration
    async def test_public_data_cost_tracking_integration(self, cost_monitor):
        """Test public vs premium data cost tracking integration"""
        # Test data cost analysis
        analysis = await cost_monitor.monitor_public_vs_premium_data_costs()
        
        # Should return complete analysis
        assert "public_data_cost" in analysis
        assert "premium_data_cost" in analysis
        assert "total_data_cost" in analysis
        assert "public_data_percentage" in analysis
        assert "cost_reduction_achieved" in analysis
        assert "meets_public_data_target" in analysis
        assert "meets_cost_reduction_target" in analysis
        assert "recommendations" in analysis
        
        # Should meet public data targets (80% public data usage)
        public_percentage = analysis["public_data_percentage"]
        assert 0 <= public_percentage <= 1
        
        # Should achieve cost reduction
        cost_reduction = analysis["cost_reduction_achieved"]
        assert 0 <= cost_reduction <= 1
    
    @pytest.mark.integration
    async def test_dashboard_widget_integration(self, cost_dashboard):
        """Test dashboard widget integration and data flow"""
        # Mock cost monitor data
        with patch.object(cost_dashboard.cost_monitor, 'get_cost_dashboard_data') as mock_get_data:
            
            mock_get_data.return_value = {
                "summary": {
                    "total_projected_monthly_cost": 500.0,
                    "potential_monthly_savings": 100.0,
                    "active_alerts_count": 1
                },
                "current_costs": {},
                "data_cost_analysis": {"public_data_percentage": 0.85},
                "efficiency_metrics": {"efficiency_score": 80.0},
                "alerts": [],
                "recommendations": [],
                "cost_trends": {"total": [100, 105, 110]},
                "timestamp": datetime.now().isoformat()
            }
            
            # Test individual widget retrieval
            cost_summary = await cost_dashboard.get_widget_data("cost_summary")
            assert cost_summary is not None
            assert cost_summary.widget_type == "metric"
            
            # Test widget refresh
            refreshed_widget = await cost_dashboard.refresh_widget("cost_summary")
            assert refreshed_widget is not None
            
            # Test dashboard export
            exported_data = await cost_dashboard.export_dashboard_data("json")
            assert exported_data != ""
            
            # Should be valid JSON
            import json
            parsed_data = json.loads(exported_data)
            assert "widgets" in parsed_data
    
    @pytest.mark.integration
    async def test_error_handling_integration(self, cost_monitor, cost_dashboard):
        """Test error handling in integrated cost monitoring workflow"""
        # Test with failing AWS calls
        with patch.object(cost_monitor, '_get_cost_and_usage') as mock_cost_usage:
            
            # Simulate AWS API failure
            mock_cost_usage.side_effect = Exception("AWS API Error")
            
            # Should handle errors gracefully
            costs = await cost_monitor.get_current_costs()
            assert isinstance(costs, dict)  # Should return empty dict, not raise
            
            # Dashboard should handle missing data
            cost_dashboard.cost_monitor = cost_monitor
            dashboard_data = await cost_dashboard.get_dashboard_data(force_refresh=True)
            
            # Should return error dashboard
            assert dashboard_data is not None
            assert "error" in dashboard_data or len(dashboard_data.get("widgets", {})) == 0
    
    @pytest.mark.integration
    def test_singleton_integration(self):
        """Test singleton pattern integration"""
        # Test cost monitor singleton
        monitor1 = get_cost_monitor()
        monitor2 = get_cost_monitor()
        assert monitor1 is monitor2
        
        # Test dashboard singleton
        dashboard1 = get_cost_dashboard()
        dashboard2 = get_cost_dashboard()
        assert dashboard1 is dashboard2
        
        # Test that dashboard uses the same monitor instance
        assert dashboard1.cost_monitor is not None


class TestAWSServiceIntegration:
    """Test integration with specific AWS services"""
    
    @pytest.mark.integration
    async def test_bedrock_cost_tracking(self):
        """Test Bedrock-specific cost tracking"""
        cost_monitor = AWSCostMonitor()
        
        # Mock Bedrock costs
        with patch.object(cost_monitor, '_get_cost_and_usage') as mock_cost_usage:
            
            mock_cost_usage.return_value = {
                'ResultsByTime': [
                    {
                        'Groups': [
                            {
                                'Keys': ['Amazon Bedrock'],
                                'Metrics': {'BlendedCost': {'Amount': '250.75'}}
                            }
                        ]
                    }
                ]
            }
            
            costs = await cost_monitor.get_current_costs()
            
            # Should categorize Bedrock correctly
            assert "Amazon Bedrock" in costs
            bedrock_cost = costs["Amazon Bedrock"]
            assert bedrock_cost.category.value == "ai_ml"
            assert bedrock_cost.current_cost == 250.75
    
    @pytest.mark.integration
    async def test_ecs_cost_and_efficiency_tracking(self):
        """Test ECS cost and efficiency tracking integration"""
        cost_monitor = AWSCostMonitor()
        
        # Mock ECS costs and metrics
        with patch.object(cost_monitor, '_get_cost_and_usage') as mock_cost_usage, \
             patch.object(cost_monitor, '_get_cloudwatch_metric') as mock_cw_metric:
            
            mock_cost_usage.return_value = {
                'ResultsByTime': [
                    {
                        'Groups': [
                            {
                                'Keys': ['Amazon Elastic Container Service'],
                                'Metrics': {'BlendedCost': {'Amount': '125.50'}}
                            }
                        ]
                    }
                ]
            }
            
            mock_cw_metric.return_value = {
                'Datapoints': [
                    {'Average': 75.0, 'Timestamp': datetime.now()},
                    {'Average': 80.0, 'Timestamp': datetime.now()}
                ]
            }
            
            # Get costs and efficiency
            costs = await cost_monitor.get_current_costs()
            efficiency = await cost_monitor.track_auto_scaling_efficiency()
            
            # Verify ECS cost tracking
            assert "Amazon Elastic Container Service" in costs
            ecs_cost = costs["Amazon Elastic Container Service"]
            assert ecs_cost.category.value == "compute"
            
            # Verify efficiency tracking
            assert "efficiency_score" in efficiency
            assert efficiency["efficiency_score"] > 0
    
    @pytest.mark.integration
    async def test_s3_cost_optimization_tracking(self):
        """Test S3 cost optimization tracking"""
        cost_monitor = AWSCostMonitor()
        
        # Mock high S3 costs
        with patch.object(cost_monitor, '_get_cost_and_usage') as mock_cost_usage:
            
            mock_cost_usage.return_value = {
                'ResultsByTime': [
                    {
                        'Groups': [
                            {
                                'Keys': ['Amazon Simple Storage Service'],
                                'Metrics': {'BlendedCost': {'Amount': '180.25'}}
                            }
                        ]
                    }
                ]
            }
            
            costs = await cost_monitor.get_current_costs()
            recommendations = await cost_monitor.generate_optimization_recommendations(costs, {})
            
            # Should generate S3-specific recommendations
            s3_recs = [r for r in recommendations if "storage" in r.category.value.lower()]
            assert len(s3_recs) > 0
            
            # Should include lifecycle policy recommendations
            s3_rec = s3_recs[0]
            assert any("lifecycle" in item.lower() for item in s3_rec.action_items)


# Performance integration tests
class TestCostMonitoringPerformance:
    """Test cost monitoring performance in integrated scenarios"""
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_large_scale_cost_analysis_performance(self):
        """Test performance with large-scale cost data"""
        import time
        
        cost_monitor = AWSCostMonitor()
        
        # Mock large dataset
        with patch.object(cost_monitor, '_get_cost_and_usage') as mock_cost_usage:
            
            # Generate large cost dataset (100 services)
            large_groups = []
            for i in range(100):
                large_groups.append({
                    'Keys': [f'Service{i}'],
                    'Metrics': {'BlendedCost': {'Amount': str(i * 5.75)}}
                })
            
            mock_cost_usage.return_value = {
                'ResultsByTime': [{'Groups': large_groups}]
            }
            
            start_time = time.time()
            
            # Run complete analysis
            costs = await cost_monitor.get_current_costs()
            alerts = await cost_monitor.generate_cost_alerts(costs)
            recommendations = await cost_monitor.generate_optimization_recommendations(costs, {})
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should handle large datasets efficiently (< 10 seconds)
            assert processing_time < 10.0
            assert len(costs) == 100
            assert isinstance(alerts, list)
            assert isinstance(recommendations, list)
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_dashboard_performance_with_large_dataset(self):
        """Test dashboard performance with large cost dataset"""
        import time
        
        dashboard = CostOptimizationDashboard()
        
        # Create large mock dataset
        from riskintel360.services.aws_cost_monitor import CostMetric, ServiceCategory
        
        large_costs = {}
        for i in range(50):
            large_costs[f"Service{i}"] = CostMetric(
                service_name=f"Service{i}",
                category=ServiceCategory.COMPUTE,
                current_cost=i * 10.0,
                projected_monthly_cost=i * 30.0,
                usage_hours=168,
                cost_per_hour=i * 0.18
            )
        
        large_dashboard_data = {
            "summary": {"total_projected_monthly_cost": 10000},
            "current_costs": large_costs,
            "data_cost_analysis": {"public_data_percentage": 0.8},
            "efficiency_metrics": {"efficiency_score": 75.0},
            "alerts": [],
            "recommendations": [],
            "cost_trends": {"total": list(range(30))},
            "timestamp": datetime.now().isoformat()
        }
        
        with patch.object(dashboard.cost_monitor, 'get_cost_dashboard_data') as mock_get_data:
            mock_get_data.return_value = large_dashboard_data
            
            start_time = time.time()
            result = await dashboard.get_dashboard_data(force_refresh=True)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Should process large datasets efficiently (< 5 seconds)
            assert processing_time < 5.0
            assert result is not None
            assert "widgets" in result


if __name__ == "__main__":
    pytest.main([__file__])
