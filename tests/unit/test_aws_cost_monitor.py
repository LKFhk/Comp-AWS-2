"""
Unit tests for AWS Cost Monitor

Tests the AWS cost monitoring functionality including cost tracking,
optimization recommendations, and alert generation.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import boto3
# from moto import mock_ce, mock_cloudwatch  # Optional dependency

from riskintel360.services.aws_cost_monitor import (
    AWSCostMonitor,
    CostMetric,
    CostAlert,
    CostOptimizationRecommendation,
    CostAlertLevel,
    ServiceCategory,
    get_cost_monitor
)


class TestAWSCostMonitor:
    """Test AWS Cost Monitor functionality"""
    
    @pytest.fixture
    def cost_monitor(self):
        """Create cost monitor instance for testing"""
        return AWSCostMonitor(region="us-east-1")
    
    @pytest.fixture
    def sample_cost_data(self):
        """Sample cost data for testing"""
        return {
            'ResultsByTime': [
                {
                    'Groups': [
                        {
                            'Keys': ['Amazon Bedrock'],
                            'Metrics': {
                                'BlendedCost': {
                                    'Amount': '150.50'
                                }
                            }
                        },
                        {
                            'Keys': ['Amazon Elastic Container Service'],
                            'Metrics': {
                                'BlendedCost': {
                                    'Amount': '75.25'
                                }
                            }
                        }
                    ]
                }
            ]
        }
    
    @pytest.fixture
    def sample_cloudwatch_response(self):
        """Sample CloudWatch response for testing"""
        return {
            'Datapoints': [
                {'Average': 65.5, 'Timestamp': datetime.now()},
                {'Average': 70.2, 'Timestamp': datetime.now()},
                {'Average': 68.8, 'Timestamp': datetime.now()}
            ]
        }
    
    def test_cost_monitor_initialization(self, cost_monitor):
        """Test cost monitor initialization"""
        assert cost_monitor.region == "us-east-1"
        assert cost_monitor.cost_thresholds is not None
        assert cost_monitor.data_cost_targets is not None
        assert "bedrock" in cost_monitor.cost_thresholds
        assert "public_data_percentage" in cost_monitor.data_cost_targets
    
    def test_categorize_service(self, cost_monitor):
        """Test service categorization"""
        assert cost_monitor._categorize_service("Amazon Bedrock") == ServiceCategory.AI_ML
        assert cost_monitor._categorize_service("Amazon Elastic Container Service") == ServiceCategory.COMPUTE
        assert cost_monitor._categorize_service("Amazon Simple Storage Service") == ServiceCategory.STORAGE
        assert cost_monitor._categorize_service("Amazon CloudWatch") == ServiceCategory.MONITORING
        assert cost_monitor._categorize_service("Unknown Service") == ServiceCategory.COMPUTE
    
    @patch('boto3.client')
    @pytest.mark.asyncio
    async def test_get_current_costs(self, mock_boto_client, cost_monitor, sample_cost_data):
        """Test getting current costs"""
        # Mock Cost Explorer client
        mock_ce_client = Mock()
        mock_ce_client.get_cost_and_usage.return_value = sample_cost_data
        mock_boto_client.return_value = mock_ce_client
        
        # Reinitialize with mocked client
        cost_monitor._initialize_clients()
        cost_monitor.cost_explorer = mock_ce_client
        
        costs = await cost_monitor.get_current_costs(days_back=7)
        
        assert len(costs) == 2
        assert "Amazon Bedrock" in costs
        assert "Amazon Elastic Container Service" in costs
        
        bedrock_cost = costs["Amazon Bedrock"]
        assert bedrock_cost.service_name == "Amazon Bedrock"
        assert bedrock_cost.current_cost == 150.50
        assert bedrock_cost.category == ServiceCategory.AI_ML
        assert bedrock_cost.projected_monthly_cost > 0
    
    @pytest.mark.asyncio
    async def test_monitor_public_vs_premium_data_costs(self, cost_monitor):
        """Test public vs premium data cost monitoring"""
        with patch.object(cost_monitor, '_get_data_source_costs') as mock_get_costs:
            # Mock data source costs
            mock_get_costs.side_effect = [50.0, 200.0]  # public, premium
            
            analysis = await cost_monitor.monitor_public_vs_premium_data_costs()
            
            assert analysis is not None
            assert "public_data_cost" in analysis
            assert "premium_data_cost" in analysis
            assert "public_data_percentage" in analysis
            assert "cost_reduction_achieved" in analysis
            
            # Check calculations
            assert analysis["public_data_cost"] == 50.0
            assert analysis["premium_data_cost"] == 200.0
            assert analysis["total_data_cost"] == 250.0
            assert analysis["public_data_percentage"] == 0.2  # 50/250
    
    @pytest.mark.asyncio
    async def test_track_auto_scaling_efficiency(self, cost_monitor):
        """Test auto-scaling efficiency tracking"""
        with patch.object(cost_monitor, '_get_ecs_cluster_metrics') as mock_get_metrics:
            # Mock ECS metrics
            mock_get_metrics.return_value = {
                "avg_cpu": 65.0,
                "avg_memory": 75.0,
                "scaling_events": 8,
                "cost_per_task": 0.05
            }
            
            efficiency = await cost_monitor.track_auto_scaling_efficiency()
            
            assert efficiency is not None
            assert "efficiency_score" in efficiency
            assert "recommendations" in efficiency
            
            # Check efficiency score calculation
            expected_cpu_efficiency = min(65.0 / 70, 1.0)
            expected_memory_efficiency = min(75.0 / 80, 1.0)
            expected_score = (expected_cpu_efficiency + expected_memory_efficiency) / 2 * 100
            
            assert abs(efficiency["efficiency_score"] - expected_score) < 0.1
    
    @pytest.mark.asyncio
    async def test_generate_cost_alerts_warning_level(self, cost_monitor):
        """Test cost alert generation for warning level"""
        # Create cost metrics that exceed warning thresholds
        cost_metrics = {
            "Amazon Bedrock": CostMetric(
                service_name="Amazon Bedrock",
                category=ServiceCategory.AI_ML,
                current_cost=50.0,
                projected_monthly_cost=150.0,  # Exceeds warning threshold of 100
                usage_hours=168,
                cost_per_hour=0.3
            )
        }
        
        alerts = await cost_monitor.generate_cost_alerts(cost_metrics)
        
        assert len(alerts) >= 1
        bedrock_alert = next((a for a in alerts if "bedrock" in a.alert_id.lower()), None)
        assert bedrock_alert is not None
        assert bedrock_alert.level == CostAlertLevel.WARNING
        assert bedrock_alert.service_name == "Amazon Bedrock"
        assert bedrock_alert.current_cost == 150.0
        assert len(bedrock_alert.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_generate_cost_alerts_critical_level(self, cost_monitor):
        """Test cost alert generation for critical level"""
        # Create cost metrics that exceed critical thresholds
        cost_metrics = {
            "Amazon Bedrock": CostMetric(
                service_name="Amazon Bedrock",
                category=ServiceCategory.AI_ML,
                current_cost=200.0,
                projected_monthly_cost=600.0,  # Exceeds critical threshold of 500
                usage_hours=168,
                cost_per_hour=3.6
            )
        }
        
        alerts = await cost_monitor.generate_cost_alerts(cost_metrics)
        
        assert len(alerts) >= 1
        bedrock_alert = next((a for a in alerts if "bedrock" in a.alert_id.lower()), None)
        assert bedrock_alert is not None
        assert bedrock_alert.level == CostAlertLevel.CRITICAL
        assert "Critical" in bedrock_alert.message
    
    @pytest.mark.asyncio
    async def test_generate_cost_alerts_emergency_level(self, cost_monitor):
        """Test cost alert generation for emergency level"""
        # Create cost metrics that exceed emergency thresholds
        cost_metrics = {
            "Amazon Bedrock": CostMetric(
                service_name="Amazon Bedrock",
                category=ServiceCategory.AI_ML,
                current_cost=500.0,
                projected_monthly_cost=1200.0,  # Exceeds emergency threshold of 1000
                usage_hours=168,
                cost_per_hour=7.1
            )
        }
        
        alerts = await cost_monitor.generate_cost_alerts(cost_metrics)
        
        assert len(alerts) >= 1
        bedrock_alert = next((a for a in alerts if "bedrock" in a.alert_id.lower()), None)
        assert bedrock_alert is not None
        assert bedrock_alert.level == CostAlertLevel.EMERGENCY
        assert "Emergency" in bedrock_alert.message
    
    @pytest.mark.asyncio
    async def test_generate_cost_alerts_total_cost(self, cost_monitor):
        """Test total cost alert generation"""
        # Create cost metrics that exceed total cost thresholds
        cost_metrics = {
            "Service1": CostMetric(
                service_name="Service1",
                category=ServiceCategory.COMPUTE,
                current_cost=100.0,
                projected_monthly_cost=400.0,
                usage_hours=168,
                cost_per_hour=2.4
            ),
            "Service2": CostMetric(
                service_name="Service2",
                category=ServiceCategory.STORAGE,
                current_cost=150.0,
                projected_monthly_cost=700.0,  # Total = 1100, exceeds critical threshold
                usage_hours=168,
                cost_per_hour=4.2
            )
        }
        
        alerts = await cost_monitor.generate_cost_alerts(cost_metrics)
        
        # Should have total cost alert
        total_alert = next((a for a in alerts if a.service_name == "Total"), None)
        assert total_alert is not None
        assert total_alert.level == CostAlertLevel.CRITICAL
        assert total_alert.current_cost == 1100.0
    
    @pytest.mark.asyncio
    async def test_generate_optimization_recommendations(self, cost_monitor):
        """Test optimization recommendation generation"""
        cost_metrics = {
            "Amazon Bedrock": CostMetric(
                service_name="Amazon Bedrock",
                category=ServiceCategory.AI_ML,
                current_cost=100.0,
                projected_monthly_cost=300.0,
                usage_hours=168,
                cost_per_hour=1.8
            ),
            "Amazon S3": CostMetric(
                service_name="Amazon Simple Storage Service",
                category=ServiceCategory.STORAGE,
                current_cost=50.0,
                projected_monthly_cost=150.0,
                usage_hours=168,
                cost_per_hour=0.9
            )
        }
        
        efficiency_metrics = {
            "efficiency_score": 60.0,  # Below 70 threshold
            "average_cpu_utilization": 45.0,
            "average_memory_utilization": 55.0
        }
        
        recommendations = await cost_monitor.generate_optimization_recommendations(
            cost_metrics, efficiency_metrics
        )
        
        assert len(recommendations) > 0
        
        # Should have AI/ML optimization recommendation
        ai_ml_rec = next((r for r in recommendations if r.category == ServiceCategory.AI_ML), None)
        assert ai_ml_rec is not None
        assert ai_ml_rec.potential_savings > 0
        assert len(ai_ml_rec.action_items) > 0
        
        # Should have efficiency improvement recommendation
        efficiency_rec = next((r for r in recommendations if "efficiency" in r.description.lower()), None)
        assert efficiency_rec is not None
    
    def test_get_service_threshold_key(self, cost_monitor):
        """Test service threshold key mapping"""
        assert cost_monitor._get_service_threshold_key("Amazon Bedrock") == "bedrock"
        assert cost_monitor._get_service_threshold_key("Amazon Elastic Container Service") == "ecs"
        assert cost_monitor._get_service_threshold_key("Amazon Simple Storage Service") == "s3"
        assert cost_monitor._get_service_threshold_key("Amazon CloudWatch") == "cloudwatch"
        assert cost_monitor._get_service_threshold_key("Unknown Service") == "ecs"
    
    def test_get_service_recommendations(self, cost_monitor):
        """Test service-specific recommendations"""
        bedrock_recs = cost_monitor._get_service_recommendations("Amazon Bedrock", CostAlertLevel.WARNING)
        assert len(bedrock_recs) > 0
        assert any("prompt" in rec.lower() for rec in bedrock_recs)
        
        ecs_recs = cost_monitor._get_service_recommendations("Amazon Elastic Container Service", CostAlertLevel.CRITICAL)
        assert len(ecs_recs) > 0
        assert any("container" in rec.lower() for rec in ecs_recs)
        assert "Urgent" in ecs_recs[0]  # Critical level should add urgent prefix
        
        s3_recs = cost_monitor._get_service_recommendations("Amazon Simple Storage Service", CostAlertLevel.EMERGENCY)
        assert len(s3_recs) > 0
        assert any("lifecycle" in rec.lower() for rec in s3_recs)
        assert "IMMEDIATE ACTION REQUIRED" in s3_recs[0]  # Emergency level should add immediate action
    
    @pytest.mark.asyncio
    async def test_get_cost_dashboard_data(self, cost_monitor):
        """Test getting complete cost dashboard data"""
        with patch.object(cost_monitor, 'get_current_costs') as mock_costs, \
             patch.object(cost_monitor, 'monitor_public_vs_premium_data_costs') as mock_data_costs, \
             patch.object(cost_monitor, 'track_auto_scaling_efficiency') as mock_efficiency, \
             patch.object(cost_monitor, 'generate_cost_alerts') as mock_alerts, \
             patch.object(cost_monitor, 'generate_optimization_recommendations') as mock_recommendations, \
             patch.object(cost_monitor, '_get_cost_trends') as mock_trends:
            
            # Mock all the data
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
                "cost_reduction_achieved": 0.75
            }
            
            mock_efficiency.return_value = {
                "efficiency_score": 75.0
            }
            
            mock_alerts.return_value = []
            mock_recommendations.return_value = []
            mock_trends.return_value = {"total": [100, 105, 110]}
            
            dashboard_data = await cost_monitor.get_cost_dashboard_data()
            
            assert dashboard_data is not None
            assert "summary" in dashboard_data
            assert "current_costs" in dashboard_data
            assert "data_cost_analysis" in dashboard_data
            assert "efficiency_metrics" in dashboard_data
            assert "alerts" in dashboard_data
            assert "recommendations" in dashboard_data
            assert "cost_trends" in dashboard_data
            
            # Check summary calculations
            summary = dashboard_data["summary"]
            assert summary["total_current_cost"] == 100.0
            assert summary["total_projected_monthly_cost"] == 300.0
    
    def test_estimate_traditional_data_costs(self, cost_monitor):
        """Test traditional data cost estimation"""
        traditional_cost = cost_monitor._estimate_traditional_data_costs()
        assert traditional_cost > 0
        assert isinstance(traditional_cost, float)
    
    @pytest.mark.asyncio
    async def test_get_data_source_costs_public(self, cost_monitor):
        """Test public data source cost calculation"""
        public_sources = ["SEC EDGAR", "FINRA", "CFPB"]
        cost = await cost_monitor._get_data_source_costs(public_sources)
        
        assert cost > 0
        assert cost < 100  # Public sources should be relatively cheap
    
    @pytest.mark.asyncio
    async def test_get_data_source_costs_premium(self, cost_monitor):
        """Test premium data source cost calculation"""
        premium_sources = ["Bloomberg API", "Reuters"]
        cost = await cost_monitor._get_data_source_costs(premium_sources)
        
        assert cost > 0
        assert cost > 100  # Premium sources should be more expensive
    
    def test_generate_category_recommendations_ai_ml(self, cost_monitor):
        """Test AI/ML category recommendations"""
        recommendations = cost_monitor._generate_category_recommendations(ServiceCategory.AI_ML, 500.0)
        
        assert len(recommendations) > 0
        ai_ml_rec = recommendations[0]
        assert ai_ml_rec.category == ServiceCategory.AI_ML
        assert ai_ml_rec.potential_savings > 0
        assert "Claude-3" in " ".join(ai_ml_rec.action_items)
    
    def test_generate_category_recommendations_compute(self, cost_monitor):
        """Test compute category recommendations"""
        recommendations = cost_monitor._generate_category_recommendations(ServiceCategory.COMPUTE, 400.0)
        
        assert len(recommendations) > 0
        compute_rec = recommendations[0]
        assert compute_rec.category == ServiceCategory.COMPUTE
        assert "ECS" in " ".join(compute_rec.action_items)
    
    def test_generate_category_recommendations_storage(self, cost_monitor):
        """Test storage category recommendations"""
        recommendations = cost_monitor._generate_category_recommendations(ServiceCategory.STORAGE, 300.0)
        
        assert len(recommendations) > 0
        storage_rec = recommendations[0]
        assert storage_rec.category == ServiceCategory.STORAGE
        assert "lifecycle" in " ".join(storage_rec.action_items)
    
    def test_get_cost_monitor_singleton(self):
        """Test cost monitor singleton pattern"""
        monitor1 = get_cost_monitor()
        monitor2 = get_cost_monitor()
        
        assert monitor1 is monitor2
        assert isinstance(monitor1, AWSCostMonitor)


class TestCostMetric:
    """Test CostMetric data class"""
    
    def test_cost_metric_creation(self):
        """Test cost metric creation"""
        metric = CostMetric(
            service_name="Amazon Bedrock",
            category=ServiceCategory.AI_ML,
            current_cost=100.0,
            projected_monthly_cost=300.0,
            usage_hours=168,
            cost_per_hour=1.8
        )
        
        assert metric.service_name == "Amazon Bedrock"
        assert metric.category == ServiceCategory.AI_ML
        assert metric.current_cost == 100.0
        assert metric.projected_monthly_cost == 300.0
        assert metric.usage_hours == 168
        assert metric.cost_per_hour == 1.8
        assert isinstance(metric.timestamp, datetime)


class TestCostAlert:
    """Test CostAlert data class"""
    
    def test_cost_alert_creation(self):
        """Test cost alert creation"""
        alert = CostAlert(
            alert_id="test_alert_123",
            level=CostAlertLevel.WARNING,
            service_name="Amazon Bedrock",
            message="Cost threshold exceeded",
            current_cost=150.0,
            threshold=100.0,
            recommendations=["Optimize usage", "Review settings"]
        )
        
        assert alert.alert_id == "test_alert_123"
        assert alert.level == CostAlertLevel.WARNING
        assert alert.service_name == "Amazon Bedrock"
        assert alert.message == "Cost threshold exceeded"
        assert alert.current_cost == 150.0
        assert alert.threshold == 100.0
        assert len(alert.recommendations) == 2
        assert isinstance(alert.timestamp, datetime)


class TestCostOptimizationRecommendation:
    """Test CostOptimizationRecommendation data class"""
    
    def test_recommendation_creation(self):
        """Test recommendation creation"""
        recommendation = CostOptimizationRecommendation(
            recommendation_id="rec_123",
            service_name="Amazon Bedrock",
            category=ServiceCategory.AI_ML,
            description="Optimize model usage",
            potential_savings=50.0,
            implementation_effort="low",
            priority=1,
            action_items=["Use Haiku for simple tasks", "Implement caching"]
        )
        
        assert recommendation.recommendation_id == "rec_123"
        assert recommendation.service_name == "Amazon Bedrock"
        assert recommendation.category == ServiceCategory.AI_ML
        assert recommendation.description == "Optimize model usage"
        assert recommendation.potential_savings == 50.0
        assert recommendation.implementation_effort == "low"
        assert recommendation.priority == 1
        assert len(recommendation.action_items) == 2


class TestServiceCategory:
    """Test ServiceCategory enum"""
    
    def test_service_category_values(self):
        """Test service category enum values"""
        assert ServiceCategory.AI_ML.value == "ai_ml"
        assert ServiceCategory.COMPUTE.value == "compute"
        assert ServiceCategory.STORAGE.value == "storage"
        assert ServiceCategory.MONITORING.value == "monitoring"
        assert ServiceCategory.DATA.value == "data"
        assert ServiceCategory.NETWORKING.value == "networking"


class TestCostAlertLevel:
    """Test CostAlertLevel enum"""
    
    def test_cost_alert_level_values(self):
        """Test cost alert level enum values"""
        assert CostAlertLevel.INFO.value == "info"
        assert CostAlertLevel.WARNING.value == "warning"
        assert CostAlertLevel.CRITICAL.value == "critical"
        assert CostAlertLevel.EMERGENCY.value == "emergency"


# Performance tests
class TestCostMonitorPerformance:
    """Test cost monitor performance requirements"""
    
    @pytest.mark.asyncio
    async def test_cost_analysis_performance(self):
        """Test that cost analysis completes within performance requirements"""
        import time
        
        cost_monitor = AWSCostMonitor()
        
        # Mock the external calls to focus on processing performance
        with patch.object(cost_monitor, '_get_cost_and_usage') as mock_cost_usage, \
             patch.object(cost_monitor, '_get_ecs_cluster_metrics') as mock_ecs_metrics:
            
            mock_cost_usage.return_value = {
                'ResultsByTime': [
                    {
                        'Groups': [
                            {
                                'Keys': [f'Service{i}'],
                                'Metrics': {'BlendedCost': {'Amount': str(i * 10.5)}}
                            } for i in range(10)  # 10 services
                        ]
                    }
                ]
            }
            
            mock_ecs_metrics.return_value = {
                "avg_cpu": 65.0,
                "avg_memory": 75.0,
                "scaling_events": 5,
                "cost_per_task": 0.05
            }
            
            start_time = time.time()
            
            # Run cost analysis
            costs = await cost_monitor.get_current_costs()
            data_analysis = await cost_monitor.monitor_public_vs_premium_data_costs()
            efficiency = await cost_monitor.track_auto_scaling_efficiency()
            alerts = await cost_monitor.generate_cost_alerts(costs)
            recommendations = await cost_monitor.generate_optimization_recommendations(costs, efficiency)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should complete within 5 seconds for performance requirement
            assert processing_time < 5.0
            
            # Verify all components completed
            assert len(costs) > 0
            assert data_analysis is not None
            assert efficiency is not None
            assert isinstance(alerts, list)
            assert isinstance(recommendations, list)
    
    @pytest.mark.asyncio
    async def test_concurrent_cost_monitoring(self):
        """Test concurrent cost monitoring operations"""
        cost_monitor = AWSCostMonitor()
        
        # Mock external calls
        with patch.object(cost_monitor, '_get_cost_and_usage') as mock_cost_usage, \
             patch.object(cost_monitor, '_get_ecs_cluster_metrics') as mock_ecs_metrics:
            
            mock_cost_usage.return_value = {'ResultsByTime': []}
            mock_ecs_metrics.return_value = {"avg_cpu": 65.0, "avg_memory": 75.0}
            
            # Run multiple concurrent operations
            tasks = [
                cost_monitor.get_current_costs(),
                cost_monitor.monitor_public_vs_premium_data_costs(),
                cost_monitor.track_auto_scaling_efficiency(),
                cost_monitor.get_cost_dashboard_data()
            ]
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Should handle concurrent operations efficiently
            assert end_time - start_time < 10.0
            
            # All operations should complete successfully
            for result in results:
                assert not isinstance(result, Exception)


if __name__ == "__main__":
    pytest.main([__file__])
