"""
Performance Regression Testing with Automated Baseline Comparisons

Tests performance metrics against established baselines and detects regressions
automatically with detailed reporting and recommendations.
"""

import pytest
import time
import asyncio
import json
import psutil
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from unittest.mock import Mock, AsyncMock, patch

from riskintel360.models import ValidationRequest, Priority
from riskintel360.services.cost_management import AWSCostManager, CostProfile


@dataclass
class PerformanceMetric:
    """Performance metric with baseline comparison"""
    name: str
    current_value: float
    baseline_value: Optional[float]
    unit: str
    threshold_percentage: float
    regression_percentage: Optional[float] = None
    status: str = "unknown"  # improved, stable, regressed, new


@dataclass
class PerformanceBenchmark:
    """Performance benchmark results"""
    test_name: str
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput_ops_per_sec: Optional[float] = None
    error_rate_percent: float = 0.0
    custom_metrics: Dict[str, float] = None


class PerformanceRegressionTester:
    """Performance regression testing with baseline management"""
    
    def __init__(self, baseline_file: str = "performance-baseline.json"):
        self.baseline_file = Path(baseline_file)
        self.current_results = {}
        self.baseline_data = self._load_baseline()
        self.regression_threshold = 5.0  # 5% regression threshold
    
    def _load_baseline(self) -> Dict[str, float]:
        """Load performance baseline data"""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, 'r') as f:
                    data = json.load(f)
                return data.get('metrics', {})
            except Exception as e:
                print(f"Warning: Could not load baseline data: {e}")
        return {}
    
    def _save_baseline(self, metrics: Dict[str, float]):
        """Save performance baseline data"""
        try:
            baseline_data = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "metrics": metrics
            }
            
            with open(self.baseline_file, 'w') as f:
                json.dump(baseline_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save baseline data: {e}")
    
    def record_metric(self, name: str, value: float, unit: str = "units"):
        """Record a performance metric"""
        self.current_results[name] = {
            "value": value,
            "unit": unit,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def analyze_regression(self) -> List[PerformanceMetric]:
        """Analyze performance regression against baseline"""
        metrics = []
        
        for metric_name, metric_data in self.current_results.items():
            current_value = metric_data["value"]
            unit = metric_data["unit"]
            baseline_value = self.baseline_data.get(metric_name)
            
            regression_percentage = None
            status = "new"
            
            if baseline_value is not None and baseline_value > 0:
                regression_percentage = ((current_value - baseline_value) / baseline_value) * 100
                
                if abs(regression_percentage) <= 2.0:  # Within 2% is stable
                    status = "stable"
                elif regression_percentage > self.regression_threshold:
                    status = "regressed"
                elif regression_percentage < -self.regression_threshold:
                    status = "improved"
                else:
                    status = "stable"
            
            metric = PerformanceMetric(
                name=metric_name,
                current_value=current_value,
                baseline_value=baseline_value,
                unit=unit,
                threshold_percentage=self.regression_threshold,
                regression_percentage=regression_percentage,
                status=status
            )
            
            metrics.append(metric)
        
        return metrics
    
    def update_baseline_if_acceptable(self, metrics: List[PerformanceMetric]):
        """Update baseline if performance is acceptable"""
        regressed_metrics = [m for m in metrics if m.status == "regressed"]
        
        if len(regressed_metrics) == 0:
            # No regressions, safe to update baseline
            new_baseline = {}
            for metric in metrics:
                new_baseline[metric.name] = metric.current_value
            
            self._save_baseline(new_baseline)
            print("??Performance baseline updated")
        else:
            print(f"?â?¡ï? Baseline not updated due to {len(regressed_metrics)} regressions")
    
    def generate_report(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Generate performance regression report"""
        improved = [m for m in metrics if m.status == "improved"]
        stable = [m for m in metrics if m.status == "stable"]
        regressed = [m for m in metrics if m.status == "regressed"]
        new = [m for m in metrics if m.status == "new"]
        
        overall_status = "passed"
        if len(regressed) > 0:
            severe_regressions = [m for m in regressed if m.regression_percentage and m.regression_percentage > 10]
            overall_status = "failed" if severe_regressions else "warning"
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status,
            "summary": {
                "total_metrics": len(metrics),
                "improved": len(improved),
                "stable": len(stable),
                "regressed": len(regressed),
                "new": len(new)
            },
            "regressed_metrics": [
                {
                    "name": m.name,
                    "regression_percentage": m.regression_percentage,
                    "current_value": m.current_value,
                    "baseline_value": m.baseline_value,
                    "unit": m.unit
                }
                for m in regressed
            ],
            "improved_metrics": [
                {
                    "name": m.name,
                    "improvement_percentage": abs(m.regression_percentage) if m.regression_percentage else 0,
                    "current_value": m.current_value,
                    "baseline_value": m.baseline_value,
                    "unit": m.unit
                }
                for m in improved
            ]
        }


class TestPerformanceRegression:
    """Performance regression tests with baseline comparison"""
    
    @pytest.fixture
    def performance_tester(self):
        """Create performance regression tester"""
        return PerformanceRegressionTester("test-performance-baseline.json")
    
    @pytest.fixture
    def cost_manager(self):
        """Create cost manager for performance testing"""
        return AWSCostManager(CostProfile.DEMO)
    
    @pytest.mark.performance
    def test_model_import_performance(self, performance_tester):
        """Test model import performance regression"""
        
        # Measure import time
        start_time = time.time()
        
        from riskintel360.models import ValidationRequest, Priority
        from riskintel360.models.database import ValidationRequestDB
        from riskintel360.models.core import MarketAnalysisResult
        
        import_time = time.time() - start_time
        
        # Record metric
        performance_tester.record_metric("model_import_time", import_time, "seconds")
        
        # Verify reasonable performance
        assert import_time < 5.0, f"Model import took {import_time:.3f}s, should be < 5.0s"
        
        print(f"Model import time: {import_time:.3f}s")
    
    @pytest.mark.performance
    def test_validation_request_creation_performance(self, performance_tester):
        """Test validation request creation performance"""
        
        start_time = time.time()
        memory_start = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Create multiple validation requests
        requests = []
        for i in range(1000):
            request = ValidationRequest(
                user_id=f"perf_user_{i}",
                business_concept=f"Performance test business concept {i}",
                target_market=f"Performance test market {i}",
                analysis_scope=["market", "competitive"],
                priority=Priority.MEDIUM
            )
            requests.append(request)
        
        creation_time = time.time() - start_time
        memory_end = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_end - memory_start
        
        # Record metrics
        performance_tester.record_metric("validation_creation_time_1000", creation_time, "seconds")
        performance_tester.record_metric("validation_creation_memory", memory_used, "MB")
        performance_tester.record_metric("validation_creation_rate", 1000 / creation_time, "requests/second")
        
        # Verify performance requirements
        assert creation_time < 1.0, f"Creating 1000 requests took {creation_time:.3f}s, should be < 1.0s"
        assert memory_used < 50.0, f"Memory usage {memory_used:.1f}MB, should be < 50MB"
        
        print(f"Created 1000 validation requests in {creation_time:.3f}s ({1000/creation_time:.0f} req/s)")
        print(f"Memory usage: {memory_used:.1f}MB")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cost_estimation_performance(self, performance_tester, cost_manager):
        """Test cost estimation performance"""
        
        start_time = time.time()
        cpu_start = psutil.cpu_percent()
        
        # Perform multiple cost estimations
        estimations = []
        for i in range(100):
            estimate = await cost_manager.estimate_validation_cost(
                business_concept=f"Performance test concept {i}",
                analysis_scope=["market", "competitive", "financial"],
                target_market="Performance test market"
            )
            estimations.append(estimate)
        
        estimation_time = time.time() - start_time
        cpu_end = psutil.cpu_percent()
        cpu_used = max(0, cpu_end - cpu_start)
        
        # Record metrics
        performance_tester.record_metric("cost_estimation_time_100", estimation_time, "seconds")
        performance_tester.record_metric("cost_estimation_cpu", cpu_used, "percent")
        performance_tester.record_metric("cost_estimation_rate", 100 / estimation_time, "estimations/second")
        
        # Verify performance
        assert estimation_time < 5.0, f"100 cost estimations took {estimation_time:.3f}s, should be < 5.0s"
        assert all(e.total_cost_usd > 0 for e in estimations), "All estimations should have positive cost"
        
        print(f"100 cost estimations in {estimation_time:.3f}s ({100/estimation_time:.1f} est/s)")
        print(f"CPU usage: {cpu_used:.1f}%")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self, performance_tester, cost_manager):
        """Test concurrent operations performance"""
        
        start_time = time.time()
        memory_start = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Create concurrent cost estimation tasks
        async def estimate_cost(i):
            return await cost_manager.estimate_validation_cost(
                business_concept=f"Concurrent test {i}",
                analysis_scope=["market", "competitive"],
                target_market="Concurrent test market"
            )
        
        # Run 50 concurrent estimations
        tasks = [estimate_cost(i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        
        concurrent_time = time.time() - start_time
        memory_end = psutil.Process().memory_info().rss / 1024 / 1024
        memory_used = memory_end - memory_start
        
        # Record metrics
        performance_tester.record_metric("concurrent_operations_time_50", concurrent_time, "seconds")
        performance_tester.record_metric("concurrent_operations_memory", memory_used, "MB")
        performance_tester.record_metric("concurrent_throughput", 50 / concurrent_time, "operations/second")
        
        # Verify performance
        assert concurrent_time < 10.0, f"50 concurrent operations took {concurrent_time:.3f}s, should be < 10.0s"
        assert len(results) == 50, "All concurrent operations should complete"
        assert all(r.total_cost_usd > 0 for r in results), "All results should be valid"
        
        print(f"50 concurrent operations in {concurrent_time:.3f}s ({50/concurrent_time:.1f} ops/s)")
        print(f"Memory usage: {memory_used:.1f}MB")
    
    @pytest.mark.performance
    def test_data_processing_performance(self, performance_tester):
        """Test data processing performance"""
        
        # Create large dataset
        large_dataset = {
            "validations": [
                {
                    "id": f"validation_{i}",
                    "business_concept": f"Business concept {i}" * 10,  # Make it larger
                    "target_market": f"Market {i}" * 5,
                    "analysis_results": {
                        "market_size": i * 1000000,
                        "competition_level": "high" if i % 2 else "medium",
                        "financial_viability": i * 0.1,
                        "risk_factors": [f"Risk {j}" for j in range(5)]
                    }
                }
                for i in range(1000)
            ]
        }
        
        start_time = time.time()
        memory_start = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Process data (serialize/deserialize)
        json_data = json.dumps(large_dataset)
        parsed_data = json.loads(json_data)
        
        # Perform some processing
        processed_count = 0
        for validation in parsed_data["validations"]:
            if validation["analysis_results"]["market_size"] > 500000:
                processed_count += 1
        
        processing_time = time.time() - start_time
        memory_end = psutil.Process().memory_info().rss / 1024 / 1024
        memory_used = memory_end - memory_start
        
        # Record metrics
        performance_tester.record_metric("data_processing_time_1000", processing_time, "seconds")
        performance_tester.record_metric("data_processing_memory", memory_used, "MB")
        performance_tester.record_metric("data_processing_rate", 1000 / processing_time, "records/second")
        
        # Verify performance
        assert processing_time < 2.0, f"Processing 1000 records took {processing_time:.3f}s, should be < 2.0s"
        assert processed_count > 0, "Should process some records"
        
        print(f"Processed 1000 records in {processing_time:.3f}s ({1000/processing_time:.0f} rec/s)")
        print(f"Memory usage: {memory_used:.1f}MB")
        print(f"Filtered records: {processed_count}")
    
    @pytest.mark.performance
    def test_memory_usage_stability(self, performance_tester):
        """Test memory usage stability over time"""
        
        memory_measurements = []
        
        # Perform operations and measure memory over time
        for iteration in range(10):
            # Create and destroy objects
            temp_objects = []
            for i in range(100):
                obj = ValidationRequest(
                    user_id=f"memory_test_{i}",
                    business_concept=f"Memory test concept {i}" * 20,
                    target_market=f"Memory test market {i}" * 10,
                    analysis_scope=["market", "competitive", "financial", "risk", "customer"],
                    priority=Priority.HIGH
                )
                temp_objects.append(obj)
            
            # Measure memory
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_measurements.append(current_memory)
            
            # Clean up
            del temp_objects
            
            time.sleep(0.1)  # Small delay
        
        # Calculate memory statistics
        min_memory = min(memory_measurements)
        max_memory = max(memory_measurements)
        avg_memory = sum(memory_measurements) / len(memory_measurements)
        memory_variance = max_memory - min_memory
        
        # Record metrics
        performance_tester.record_metric("memory_usage_min", min_memory, "MB")
        performance_tester.record_metric("memory_usage_max", max_memory, "MB")
        performance_tester.record_metric("memory_usage_avg", avg_memory, "MB")
        performance_tester.record_metric("memory_variance", memory_variance, "MB")
        
        # Verify memory stability
        assert memory_variance < 100.0, f"Memory variance {memory_variance:.1f}MB too high, should be < 100MB"
        
        print(f"Memory usage: min={min_memory:.1f}MB, max={max_memory:.1f}MB, avg={avg_memory:.1f}MB")
        print(f"Memory variance: {memory_variance:.1f}MB")
    
    @pytest.mark.performance
    def test_analyze_performance_regression(self, performance_tester):
        """Analyze performance regression against baseline"""
        
        # Analyze regression
        metrics = performance_tester.analyze_regression()
        
        # Generate report
        report = performance_tester.generate_report(metrics)
        
        # Print regression analysis
        print(f"\n?? Performance Regression Analysis:")
        print(f"   Overall Status: {report['overall_status'].upper()}")
        print(f"   Total Metrics: {report['summary']['total_metrics']}")
        print(f"   Improved: {report['summary']['improved']}")
        print(f"   Stable: {report['summary']['stable']}")
        print(f"   Regressed: {report['summary']['regressed']}")
        print(f"   New: {report['summary']['new']}")
        
        # Show regressed metrics
        if report['regressed_metrics']:
            print(f"\n??Regressed Metrics:")
            for metric in report['regressed_metrics']:
                print(f"   - {metric['name']}: {metric['regression_percentage']:+.1f}% "
                      f"({metric['baseline_value']:.3f} ??{metric['current_value']:.3f} {metric['unit']})")
        
        # Show improved metrics
        if report['improved_metrics']:
            print(f"\n??Improved Metrics:")
            for metric in report['improved_metrics'][:3]:  # Show top 3
                print(f"   - {metric['name']}: {metric['improvement_percentage']:+.1f}% "
                      f"({metric['baseline_value']:.3f} ??{metric['current_value']:.3f} {metric['unit']})")
        
        # Update baseline if acceptable
        performance_tester.update_baseline_if_acceptable(metrics)
        
        # Save detailed report
        report_file = Path("test-results/performance-regression-report.json")
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n?? Detailed report saved to: {report_file}")
        
        # Fail test if severe regressions detected
        severe_regressions = [
            m for m in report['regressed_metrics'] 
            if m['regression_percentage'] > 20.0  # 20% regression is severe
        ]
        
        if severe_regressions:
            pytest.fail(f"Severe performance regressions detected: {[m['name'] for m in severe_regressions]}")
        
        return report


@pytest.mark.performance
def test_comprehensive_performance_regression():
    """Comprehensive performance regression test suite"""
    print("\n?? Starting Performance Regression Analysis")
    print("=" * 60)
    
    # Initialize performance tester
    performance_tester = PerformanceRegressionTester("comprehensive-performance-baseline.json")
    
    # Run performance tests
    test_instance = TestPerformanceRegression()
    
    try:
        # Test 1: Model imports
        print("\n1ï¸?â?£ Testing Model Import Performance...")
        test_instance.test_model_import_performance(performance_tester)
        
        # Test 2: Object creation
        print("\n2ï¸?â?£ Testing Object Creation Performance...")
        test_instance.test_validation_request_creation_performance(performance_tester)
        
        # Test 3: Data processing
        print("\n3ï¸?â?£ Testing Data Processing Performance...")
        test_instance.test_data_processing_performance(performance_tester)
        
        # Test 4: Memory stability
        print("\n4ï¸?â?£ Testing Memory Usage Stability...")
        test_instance.test_memory_usage_stability(performance_tester)
        
        # Test 5: Analyze regression
        print("\n5ï¸?â?£ Analyzing Performance Regression...")
        report = test_instance.test_analyze_performance_regression(performance_tester)
        
        print(f"\n?ð??¯¯ Performance Analysis Complete!")
        print(f"   Status: {report['overall_status'].upper()}")
        
        if report['overall_status'] == 'passed':
            print("   ??No significant performance regressions detected")
        elif report['overall_status'] == 'warning':
            print("   ?â?¡ï? Minor performance regressions detected")
        else:
            print("   ??Significant performance regressions detected")
        
    except Exception as e:
        print(f"??Performance regression testing failed: {e}")
        raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "performance"])
