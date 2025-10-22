"""
Performance tests for Cost Optimization Algorithms

Tests the performance of cost monitoring, optimization algorithms,
and dashboard rendering under various load conditions.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import statistics
from concurrent.futures import ThreadPoolExecutor
import psutil
import gc

from riskintel360.services.aws_cost_monitor import AWSCostMonitor, CostMetric, ServiceCategory
from riskintel360.services.cost_optimization_dashboard import CostOptimizationDashboard


class TestCostOptimizationPerformance:
    """Test cost optimization performance requirements"""
    
    @pytest.fixture
    def cost_monitor(self):
        """Create cost monitor for performance testing"""
        return AWSCostMonitor()
    
    @pytest.fixture
    def cost_dashboard(self):
        """Create cost dashboard for performance testing"""
        return CostOptimizationDashboard()
    
    @pytest.fixture
    def large_cost_dataset(self):
        """Generate large cost dataset for performance testing"""
        costs = {}
        categories = list(ServiceCategory)
        
        for i in range(1000):  # 1000 services
            category = categories[i % len(categories)]
            costs[f"Service{i}"] = CostMetric(
                service_name=f"Service{i}",
                category=category,
                current_cost=i * 2.5,
                projected_monthly_cost=i * 7.5,
                usage_hours=168 + (i % 50),
                cost_per_hour=(i * 2.5) / (168 + (i % 50))
            )
        
        return costs
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cost_analysis_response_time(self, cost_monitor):
        """Test cost analysis meets response time requirements (< 5 seconds)"""
        # Mock external AWS calls for consistent timing
        with patch.object(cost_monitor, '_get_cost_and_usage') as mock_cost_usage, \
             patch.object(cost_monitor, '_get_cloudwatch_metric') as mock_cw_metric:
            
            # Mock realistic AWS responses
            mock_cost_usage.return_value = {
                'ResultsByTime': [
                    {
                        'Groups': [
                            {
                                'Keys': [f'Service{i}'],
                                'Metrics': {'BlendedCost': {'Amount': str(i * 12.5)}}
                            } for i in range(20)  # 20 services
                        ]
                    }
                ]
            }
            
            mock_cw_metric.return_value = {
                'Datapoints': [
                    {'Average': 65.0 + i, 'Timestamp': datetime.now()} 
                    for i in range(24)  # 24 hours of data
                ]
            }
            
            # Measure response time
            start_time = time.time()
            
            costs = await cost_monitor.get_current_costs()
            data_analysis = await cost_monitor.monitor_public_vs_premium_data_costs()
            efficiency = await cost_monitor.track_auto_scaling_efficiency()
            alerts = await cost_monitor.generate_cost_alerts(costs)
            recommendations = await cost_monitor.generate_optimization_recommendations(costs, efficiency)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Performance requirement: < 5 seconds
            assert response_time < 5.0, f"Cost analysis took {response_time:.2f}s, exceeds 5s requirement"
            
            # Verify completeness
            assert len(costs) > 0
            assert data_analysis is not None
            assert efficiency is not None
            assert isinstance(alerts, list)
            assert isinstance(recommendations, list)
    
    @pytest.mark.performance
    async def test_dashboard_refresh_performance(self, cost_dashboard):
        """Test dashboard refresh meets performance requirements"""
        # Mock cost monitor for consistent timing
        with patch.object(cost_dashboard.cost_monitor, 'get_cost_dashboard_data') as mock_get_data:
            
            # Create realistic dashboard data
            mock_get_data.return_value = {
                "summary": {
                    "total_projected_monthly_cost": 1500.0,
                    "potential_monthly_savings": 300.0,
                    "active_alerts_count": 5
                },
                "current_costs": {
                    f"Service{i}": CostMetric(
                        service_name=f"Service{i}",
                        category=ServiceCategory.COMPUTE,
                        current_cost=i * 5.0,
                        projected_monthly_cost=i * 15.0,
                        usage_hours=168,
                        cost_per_hour=i * 0.03
                    ) for i in range(25)  # 25 services
                },
                "data_cost_analysis": {"public_data_percentage": 0.8},
                "efficiency_metrics": {"efficiency_score": 75.0},
                "alerts": [],
                "recommendations": [],
                "cost_trends": {"total": list(range(30))},
                "timestamp": datetime.now().isoformat()
            }
            
            # Measure dashboard refresh time
            start_time = time.time()
            
            dashboard_data = await cost_dashboard.get_dashboard_data(force_refresh=True)
            
            end_time = time.time()
            refresh_time = end_time - start_time
            
            # Performance requirement: < 3 seconds for dashboard refresh
            assert refresh_time < 3.0, f"Dashboard refresh took {refresh_time:.2f}s, exceeds 3s requirement"
            
            # Verify completeness
            assert dashboard_data is not None
            assert "widgets" in dashboard_data
            assert len(dashboard_data["widgets"]) > 0
    
    @pytest.mark.performance
    async def test_large_dataset_processing_performance(self, cost_monitor, large_cost_dataset):
        """Test performance with large cost datasets"""
        # Test alert generation with large dataset
        start_time = time.time()
        
        alerts = await cost_monitor.generate_cost_alerts(large_cost_dataset)
        
        alert_time = time.time() - start_time
        
        # Should handle 1000 services efficiently
        assert alert_time < 10.0, f"Alert generation took {alert_time:.2f}s for 1000 services"
        
        # Test recommendation generation
        start_time = time.time()
        
        efficiency_metrics = {"efficiency_score": 65.0}
        recommendations = await cost_monitor.generate_optimization_recommendations(
            large_cost_dataset, efficiency_metrics
        )
        
        recommendation_time = time.time() - start_time
        
        # Should generate recommendations efficiently
        assert recommendation_time < 15.0, f"Recommendation generation took {recommendation_time:.2f}s"
        
        # Verify results
        assert isinstance(alerts, list)
        assert isinstance(recommendations, list)
    
    @pytest.mark.performance
    async def test_concurrent_cost_operations_performance(self, cost_monitor):
        """Test performance under concurrent load"""
        # Mock external calls
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
                'Datapoints': [{'Average': 65.0, 'Timestamp': datetime.now()}]
            }
            
            # Create multiple concurrent operations
            async def cost_operation():
                costs = await cost_monitor.get_current_costs()
                alerts = await cost_monitor.generate_cost_alerts(costs)
                return len(costs), len(alerts)
            
            # Run 10 concurrent operations
            start_time = time.time()
            
            tasks = [cost_operation() for _ in range(10)]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            concurrent_time = end_time - start_time
            
            # Should handle concurrent operations efficiently
            assert concurrent_time < 8.0, f"10 concurrent operations took {concurrent_time:.2f}s"
            
            # All operations should complete successfully
            assert len(results) == 10
            for result in results:
                assert isinstance(result, tuple)
                assert len(result) == 2
    
    @pytest.mark.performance
    async def test_memory_usage_performance(self, cost_monitor, large_cost_dataset):
        """Test memory usage with large datasets"""
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Force garbage collection
        gc.collect()
        
        # Process large dataset multiple times
        for i in range(5):
            alerts = await cost_monitor.generate_cost_alerts(large_cost_dataset)
            recommendations = await cost_monitor.generate_optimization_recommendations(
                large_cost_dataset, {"efficiency_score": 70.0}
            )
            
            # Clear references
            del alerts, recommendations
            
            # Force garbage collection
            gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB for large dataset processing)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB, exceeds 100MB limit"
    
    @pytest.mark.performance
    async def test_cost_trend_calculation_performance(self, cost_monitor):
        """Test cost trend calculation performance"""
        # Mock large trend dataset
        with patch.object(cost_monitor, '_get_cost_trends') as mock_trends:
            
            # Generate 90 days of trend data for 50 services
            trend_data = {}
            for service in [f"Service{i}" for i in range(50)]:
                trend_data[service] = [i * 2.5 + day * 0.1 for day in range(90)]
            
            mock_trends.return_value = trend_data
            
            start_time = time.time()
            
            # Get trends multiple times
            for _ in range(10):
                trends = await cost_monitor._get_cost_trends()
            
            end_time = time.time()
            trend_time = end_time - start_time
            
            # Should calculate trends efficiently
            assert trend_time < 2.0, f"Trend calculation took {trend_time:.2f}s for 10 iterations"
    
    @pytest.mark.performance
    async def test_widget_rendering_performance(self, cost_dashboard):
        """Test dashboard widget rendering performance"""
        # Create large widget dataset
        large_dashboard_data = {
            "summary": {"total_projected_monthly_cost": 5000.0},
            "current_costs": {
                f"Service{i}": CostMetric(
                    service_name=f"Service{i}",
                    category=ServiceCategory.COMPUTE,
                    current_cost=i * 3.0,
                    projected_monthly_cost=i * 9.0,
                    usage_hours=168,
                    cost_per_hour=i * 0.018
                ) for i in range(100)  # 100 services
            },
            "data_cost_analysis": {"public_data_percentage": 0.8},
            "efficiency_metrics": {"efficiency_score": 75.0},
            "alerts": [],
            "recommendations": [],
            "cost_trends": {
                f"service{i}": list(range(30)) for i in range(20)  # 20 services, 30 days
            },
            "timestamp": datetime.now().isoformat()
        }
        
        start_time = time.time()
        
        # Process dashboard data (widget creation)
        processed_data = await cost_dashboard._process_dashboard_data(large_dashboard_data)
        
        end_time = time.time()
        widget_time = end_time - start_time
        
        # Widget processing should be fast
        assert widget_time < 5.0, f"Widget processing took {widget_time:.2f}s for 100 services"
        
        # Verify all widgets created
        assert "widgets" in processed_data
        assert len(processed_data["widgets"]) > 0
    
    @pytest.mark.performance
    async def test_optimization_algorithm_scalability(self, cost_monitor):
        """Test optimization algorithm scalability"""
        # Test with increasing dataset sizes
        dataset_sizes = [10, 50, 100, 500, 1000]
        processing_times = []
        
        for size in dataset_sizes:
            # Create dataset of specified size
            cost_dataset = {}
            for i in range(size):
                cost_dataset[f"Service{i}"] = CostMetric(
                    service_name=f"Service{i}",
                    category=ServiceCategory.COMPUTE,
                    current_cost=i * 2.0,
                    projected_monthly_cost=i * 6.0,
                    usage_hours=168,
                    cost_per_hour=i * 0.012
                )
            
            # Measure processing time
            start_time = time.time()
            
            recommendations = await cost_monitor.generate_optimization_recommendations(
                cost_dataset, {"efficiency_score": 70.0}
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            processing_times.append(processing_time)
            
            # Verify results
            assert isinstance(recommendations, list)
        
        # Check scalability - processing time should scale reasonably
        # Time per service should not increase dramatically
        time_per_service = [t / s for t, s in zip(processing_times, dataset_sizes)]
        
        # Average time per service should be reasonable (< 0.01s per service)
        avg_time_per_service = statistics.mean(time_per_service)
        assert avg_time_per_service < 0.01, f"Average time per service: {avg_time_per_service:.4f}s"
    
    @pytest.mark.performance
    async def test_alert_generation_performance_under_load(self, cost_monitor):
        """Test alert generation performance under high load"""
        # Create high-cost scenario that triggers many alerts
        high_cost_dataset = {}
        for i in range(200):  # 200 services with high costs
            high_cost_dataset[f"Service{i}"] = CostMetric(
                service_name=f"Service{i}",
                category=ServiceCategory.COMPUTE,
                current_cost=500 + i * 10,  # High costs to trigger alerts
                projected_monthly_cost=1500 + i * 30,
                usage_hours=168,
                cost_per_hour=(500 + i * 10) / 168
            )
        
        start_time = time.time()
        
        # Generate alerts (should trigger many due to high costs)
        alerts = await cost_monitor.generate_cost_alerts(high_cost_dataset)
        
        end_time = time.time()
        alert_generation_time = end_time - start_time
        
        # Should handle high-alert scenarios efficiently
        assert alert_generation_time < 8.0, f"Alert generation took {alert_generation_time:.2f}s"
        
        # Should generate multiple alerts
        assert len(alerts) > 0
        
        # Verify alert quality
        for alert in alerts[:10]:  # Check first 10 alerts
            assert hasattr(alert, 'alert_id')
            assert hasattr(alert, 'level')
            assert hasattr(alert, 'recommendations')
    
    @pytest.mark.performance
    async def test_data_export_performance(self, cost_dashboard):
        """Test dashboard data export performance"""
        # Create large dashboard data
        with patch.object(cost_dashboard, 'get_dashboard_data') as mock_get_data:
            
            large_data = {
                "widgets": {
                    f"widget_{i}": {
                        "data": {f"metric_{j}": j * 1.5 for j in range(100)}
                    } for i in range(50)  # 50 widgets with 100 metrics each
                },
                "metadata": {"timestamp": datetime.now().isoformat()},
                "summary": {f"metric_{i}": i * 2.5 for i in range(100)}
            }
            
            mock_get_data.return_value = large_data
            
            start_time = time.time()
            
            # Export large dataset
            exported_json = await cost_dashboard.export_dashboard_data("json")
            
            end_time = time.time()
            export_time = end_time - start_time
            
            # Export should be fast even for large datasets
            assert export_time < 3.0, f"Data export took {export_time:.2f}s"
            
            # Verify export completeness
            assert exported_json != ""
            assert len(exported_json) > 1000  # Should be substantial data
    
    @pytest.mark.performance
    async def test_cache_performance(self, cost_dashboard):
        """Test dashboard cache performance"""
        # Mock cost monitor data
        with patch.object(cost_dashboard.cost_monitor, 'get_cost_dashboard_data') as mock_get_data:
            
            mock_get_data.return_value = {
                "summary": {"total_projected_monthly_cost": 1000.0},
                "current_costs": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # First call (cache miss)
            start_time = time.time()
            data1 = await cost_dashboard.get_dashboard_data(force_refresh=True)
            first_call_time = time.time() - start_time
            
            # Second call (cache hit)
            start_time = time.time()
            data2 = await cost_dashboard.get_dashboard_data(force_refresh=False)
            second_call_time = time.time() - start_time
            
            # Cache hit should be much faster
            assert second_call_time < first_call_time / 10, "Cache hit not significantly faster"
            assert second_call_time < 0.1, f"Cache hit took {second_call_time:.4f}s, should be < 0.1s"
            
            # Data should be identical
            assert data1 == data2


class TestCostOptimizationBenchmarks:
    """Benchmark tests for cost optimization performance"""
    
    @pytest.mark.performance
    @pytest.mark.benchmark
    async def test_end_to_end_performance_benchmark(self):
        """Benchmark complete end-to-end cost optimization workflow"""
        cost_monitor = AWSCostMonitor()
        cost_dashboard = CostOptimizationDashboard()
        
        # Mock all external calls for consistent benchmarking
        with patch.object(cost_monitor, '_get_cost_and_usage') as mock_cost_usage, \
             patch.object(cost_monitor, '_get_cloudwatch_metric') as mock_cw_metric:
            
            # Realistic AWS response simulation
            mock_cost_usage.return_value = {
                'ResultsByTime': [
                    {
                        'Groups': [
                            {
                                'Keys': [f'Service{i}'],
                                'Metrics': {'BlendedCost': {'Amount': str(i * 15.75)}}
                            } for i in range(50)  # 50 services
                        ]
                    }
                ]
            }
            
            mock_cw_metric.return_value = {
                'Datapoints': [
                    {'Average': 65.0 + (i % 20), 'Timestamp': datetime.now()} 
                    for i in range(48)  # 48 hours of data
                ]
            }
            
            # Replace dashboard's cost monitor
            cost_dashboard.cost_monitor = cost_monitor
            
            # Benchmark complete workflow
            start_time = time.time()
            
            # Step 1: Get current costs
            costs = await cost_monitor.get_current_costs()
            
            # Step 2: Analyze data costs
            data_analysis = await cost_monitor.monitor_public_vs_premium_data_costs()
            
            # Step 3: Track efficiency
            efficiency = await cost_monitor.track_auto_scaling_efficiency()
            
            # Step 4: Generate alerts
            alerts = await cost_monitor.generate_cost_alerts(costs)
            
            # Step 5: Generate recommendations
            recommendations = await cost_monitor.generate_optimization_recommendations(costs, efficiency)
            
            # Step 6: Create dashboard
            dashboard_data = await cost_dashboard.get_dashboard_data(force_refresh=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Complete workflow benchmark: < 10 seconds
            assert total_time < 10.0, f"Complete workflow took {total_time:.2f}s, exceeds 10s benchmark"
            
            # Verify all components completed
            assert len(costs) > 0
            assert data_analysis is not None
            assert efficiency is not None
            assert isinstance(alerts, list)
            assert isinstance(recommendations, list)
            assert dashboard_data is not None
            
            # Performance metrics
            print(f"\n=== Cost Optimization Performance Benchmark ===")
            print(f"Total workflow time: {total_time:.2f}s")
            print(f"Services processed: {len(costs)}")
            print(f"Alerts generated: {len(alerts)}")
            print(f"Recommendations generated: {len(recommendations)}")
            print(f"Time per service: {total_time / len(costs):.4f}s")
    
    @pytest.mark.performance
    @pytest.mark.benchmark
    async def test_scalability_benchmark(self):
        """Benchmark scalability across different dataset sizes"""
        cost_monitor = AWSCostMonitor()
        
        print(f"\n=== Cost Optimization Scalability Benchmark ===")
        
        for size in [10, 50, 100, 500]:
            # Create dataset
            cost_dataset = {}
            for i in range(size):
                cost_dataset[f"Service{i}"] = CostMetric(
                    service_name=f"Service{i}",
                    category=ServiceCategory.COMPUTE,
                    current_cost=i * 3.5,
                    projected_monthly_cost=i * 10.5,
                    usage_hours=168,
                    cost_per_hour=i * 0.021
                )
            
            # Benchmark processing
            start_time = time.time()
            
            alerts = await cost_monitor.generate_cost_alerts(cost_dataset)
            recommendations = await cost_monitor.generate_optimization_recommendations(
                cost_dataset, {"efficiency_score": 70.0}
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"Size {size:3d}: {processing_time:.3f}s ({processing_time/size:.5f}s per service)")
            
            # Scalability requirement: should scale linearly
            time_per_service = processing_time / size
            assert time_per_service < 0.02, f"Time per service {time_per_service:.5f}s exceeds 0.02s limit"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
