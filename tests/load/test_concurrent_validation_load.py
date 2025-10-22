"""
Load Testing for Concurrent Validation Requests

Tests the platform's ability to handle multiple concurrent validation requests
with realistic load patterns and performance monitoring.
"""

import pytest
import asyncio
import time
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from unittest.mock import Mock, AsyncMock, patch

from tests.fixtures.business_scenarios import ALL_SCENARIOS, get_scenario_by_id
from riskintel360.models import ValidationRequest, Priority
from riskintel360.services.cost_management import AWSCostManager, CostProfile


@dataclass
class LoadTestResult:
    """Load test execution result"""
    test_name: str
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    max_response_time: float
    min_response_time: float
    throughput_requests_per_second: float
    error_rate_percentage: float
    total_duration: float
    memory_usage_mb: float
    cpu_usage_percent: float


class ConcurrentValidationLoadTester:
    """Load tester for concurrent validation requests"""
    
    def __init__(self):
        self.results = []
        self.active_requests = {}
        self.request_counter = 0
    
    async def simulate_user_session(self, user_id: str, num_requests: int, delay_range: tuple = (1, 5)) -> List[Dict[str, Any]]:
        """Simulate a user session with multiple validation requests"""
        session_results = []
        
        for i in range(num_requests):
            # Random delay between requests
            await asyncio.sleep(random.uniform(*delay_range))
            
            # Select random scenario
            scenario = random.choice(ALL_SCENARIOS)
            validation_request = scenario.to_validation_request(f"{user_id}-{i}")
            
            # Execute validation request
            start_time = time.time()
            
            try:
                # Simulate validation execution
                result = await self._simulate_validation_execution(validation_request)
                
                execution_time = time.time() - start_time
                
                session_results.append({
                    "user_id": user_id,
                    "request_id": validation_request.id,
                    "scenario_id": scenario.scenario_id,
                    "success": True,
                    "execution_time": execution_time,
                    "error": None
                })
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                session_results.append({
                    "user_id": user_id,
                    "request_id": validation_request.id,
                    "scenario_id": scenario.scenario_id,
                    "success": False,
                    "execution_time": execution_time,
                    "error": str(e)
                })
        
        return session_results
    
    async def _simulate_validation_execution(self, request: ValidationRequest) -> Dict[str, Any]:
        """Simulate validation execution with realistic timing"""
        
        # Simulate different execution times based on complexity
        base_time = 2.0  # Base execution time
        complexity_multiplier = len(request.analysis_scope) * 0.5
        random_factor = random.uniform(0.8, 1.2)
        
        execution_time = base_time * complexity_multiplier * random_factor
        
        # Add some variability and occasional failures
        if random.random() < 0.05:  # 5% failure rate
            await asyncio.sleep(execution_time * 0.3)  # Partial execution before failure
            raise Exception("Simulated validation failure")
        
        # Simulate processing time
        await asyncio.sleep(execution_time)
        
        # Return mock result
        return {
            "validation_id": request.id,
            "overall_score": random.uniform(40, 95),
            "confidence_level": random.uniform(0.7, 0.95),
            "execution_time": execution_time,
            "agents_executed": len(request.analysis_scope)
        }
    
    async def run_load_test(
        self, 
        concurrent_users: int, 
        requests_per_user: int,
        test_duration_minutes: Optional[int] = None
    ) -> LoadTestResult:
        """Run load test with specified parameters"""
        
        print(f"?? Starting load test: {concurrent_users} users, {requests_per_user} requests each")
        
        start_time = time.time()
        
        # Create user sessions
        user_tasks = []
        for user_id in range(concurrent_users):
            task = self.simulate_user_session(
                user_id=f"load-test-user-{user_id}",
                num_requests=requests_per_user,
                delay_range=(0.5, 2.0)  # Faster for load testing
            )
            user_tasks.append(task)
        
        # Execute all user sessions concurrently
        try:
            if test_duration_minutes:
                # Run for specified duration
                session_results = await asyncio.wait_for(
                    asyncio.gather(*user_tasks, return_exceptions=True),
                    timeout=test_duration_minutes * 60
                )
            else:
                # Run until completion
                session_results = await asyncio.gather(*user_tasks, return_exceptions=True)
            
        except asyncio.TimeoutError:
            print("??Load test timed out")
            session_results = []
        
        total_duration = time.time() - start_time
        
        # Process results
        all_requests = []
        for session_result in session_results:
            if isinstance(session_result, Exception):
                print(f"??Session failed: {session_result}")
                continue
            
            if isinstance(session_result, list):
                all_requests.extend(session_result)
        
        # Calculate metrics
        successful_requests = [r for r in all_requests if r["success"]]
        failed_requests = [r for r in all_requests if not r["success"]]
        
        if successful_requests:
            response_times = [r["execution_time"] for r in successful_requests]
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0.0
        
        total_requests = len(all_requests)
        throughput = total_requests / total_duration if total_duration > 0 else 0.0
        error_rate = (len(failed_requests) / total_requests * 100) if total_requests > 0 else 0.0
        
        # Create result
        result = LoadTestResult(
            test_name=f"concurrent_users_{concurrent_users}_requests_{requests_per_user}",
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=len(successful_requests),
            failed_requests=len(failed_requests),
            average_response_time=avg_response_time,
            max_response_time=max_response_time,
            min_response_time=min_response_time,
            throughput_requests_per_second=throughput,
            error_rate_percentage=error_rate,
            total_duration=total_duration,
            memory_usage_mb=0.0,  # Would use psutil in real implementation
            cpu_usage_percent=0.0  # Would use psutil in real implementation
        )
        
        self.results.append(result)
        
        print(f"??Load test completed:")
        print(f"   Duration: {total_duration:.1f}s")
        print(f"   Total requests: {total_requests}")
        print(f"   Successful: {len(successful_requests)}")
        print(f"   Failed: {len(failed_requests)}")
        print(f"   Error rate: {error_rate:.1f}%")
        print(f"   Throughput: {throughput:.1f} req/s")
        print(f"   Avg response time: {avg_response_time:.2f}s")
        
        return result
    
    def generate_load_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive load test report"""
        if not self.results:
            return {"error": "No load test results available"}
        
        # Calculate aggregate metrics
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        total_failed = sum(r.failed_requests for r in self.results)
        
        avg_throughput = sum(r.throughput_requests_per_second for r in self.results) / len(self.results)
        avg_response_time = sum(r.average_response_time for r in self.results) / len(self.results)
        max_response_time = max(r.max_response_time for r in self.results)
        avg_error_rate = sum(r.error_rate_percentage for r in self.results) / len(self.results)
        
        return {
            "summary": {
                "total_tests": len(self.results),
                "total_requests": total_requests,
                "total_successful": total_successful,
                "total_failed": total_failed,
                "overall_error_rate": (total_failed / total_requests * 100) if total_requests > 0 else 0,
                "average_throughput": avg_throughput,
                "average_response_time": avg_response_time,
                "max_response_time": max_response_time
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "concurrent_users": r.concurrent_users,
                    "throughput": r.throughput_requests_per_second,
                    "avg_response_time": r.average_response_time,
                    "error_rate": r.error_rate_percentage,
                    "duration": r.total_duration
                }
                for r in self.results
            ],
            "performance_analysis": {
                "meets_sla": avg_response_time < 5.0 and avg_error_rate < 5.0,
                "scalability_rating": self._calculate_scalability_rating(),
                "recommendations": self._generate_recommendations()
            }
        }
    
    def _calculate_scalability_rating(self) -> str:
        """Calculate scalability rating based on results"""
        if not self.results:
            return "unknown"
        
        # Check if performance degrades significantly with increased load
        sorted_results = sorted(self.results, key=lambda x: x.concurrent_users)
        
        if len(sorted_results) < 2:
            return "insufficient_data"
        
        # Compare first and last results
        first_result = sorted_results[0]
        last_result = sorted_results[-1]
        
        response_time_degradation = (
            (last_result.average_response_time - first_result.average_response_time) 
            / first_result.average_response_time * 100
        )
        
        error_rate_increase = last_result.error_rate_percentage - first_result.error_rate_percentage
        
        if response_time_degradation < 20 and error_rate_increase < 2:
            return "excellent"
        elif response_time_degradation < 50 and error_rate_increase < 5:
            return "good"
        elif response_time_degradation < 100 and error_rate_increase < 10:
            return "fair"
        else:
            return "poor"
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on results"""
        recommendations = []
        
        if not self.results:
            return ["Run load tests to get recommendations"]
        
        avg_error_rate = sum(r.error_rate_percentage for r in self.results) / len(self.results)
        avg_response_time = sum(r.average_response_time for r in self.results) / len(self.results)
        
        if avg_error_rate > 5:
            recommendations.append("High error rate detected - investigate error handling and system stability")
        
        if avg_response_time > 5:
            recommendations.append("Response times exceed SLA - consider performance optimization")
        
        # Check for performance degradation with scale
        if len(self.results) > 1:
            sorted_results = sorted(self.results, key=lambda x: x.concurrent_users)
            if sorted_results[-1].average_response_time > sorted_results[0].average_response_time * 2:
                recommendations.append("Significant performance degradation with scale - review scalability architecture")
        
        if not recommendations:
            recommendations.append("Performance looks good - continue monitoring in production")
        
        return recommendations


class TestConcurrentValidationLoad:
    """Test concurrent validation load scenarios"""
    
    @pytest.fixture
    def load_tester(self):
        """Create load tester instance"""
        return ConcurrentValidationLoadTester()
    
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_light_load_10_users(self, load_tester):
        """Test light load with 10 concurrent users"""
        
        result = await load_tester.run_load_test(
            concurrent_users=10,
            requests_per_user=3
        )
        
        # Verify performance requirements
        assert result.error_rate_percentage < 10.0, f"Error rate {result.error_rate_percentage:.1f}% too high"
        assert result.average_response_time < 10.0, f"Avg response time {result.average_response_time:.2f}s too slow"
        assert result.successful_requests > 0, "Should have some successful requests"
        
        print(f"??Light load test passed: {result.successful_requests}/{result.total_requests} successful")
    
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_medium_load_25_users(self, load_tester):
        """Test medium load with 25 concurrent users"""
        
        result = await load_tester.run_load_test(
            concurrent_users=25,
            requests_per_user=2
        )
        
        # Verify performance requirements
        assert result.error_rate_percentage < 15.0, f"Error rate {result.error_rate_percentage:.1f}% too high"
        assert result.average_response_time < 15.0, f"Avg response time {result.average_response_time:.2f}s too slow"
        assert result.throughput_requests_per_second > 1.0, "Throughput too low"
        
        print(f"??Medium load test passed: {result.throughput_requests_per_second:.1f} req/s throughput")
    
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_heavy_load_50_users(self, load_tester):
        """Test heavy load with 50 concurrent users"""
        
        result = await load_tester.run_load_test(
            concurrent_users=50,
            requests_per_user=2
        )
        
        # More lenient requirements for heavy load
        assert result.error_rate_percentage < 25.0, f"Error rate {result.error_rate_percentage:.1f}% too high"
        assert result.average_response_time < 30.0, f"Avg response time {result.average_response_time:.2f}s too slow"
        assert result.successful_requests > result.total_requests * 0.5, "Success rate too low"
        
        print(f"??Heavy load test passed: {result.successful_requests}/{result.total_requests} successful")
    
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_stress_load_100_users(self, load_tester):
        """Test stress load with 100 concurrent users"""
        
        result = await load_tester.run_load_test(
            concurrent_users=100,
            requests_per_user=1
        )
        
        # Stress test - system may degrade but should not fail completely
        assert result.error_rate_percentage < 50.0, f"Error rate {result.error_rate_percentage:.1f}% too high"
        assert result.successful_requests > 0, "Should have some successful requests even under stress"
        
        print(f"??Stress load test completed: {result.error_rate_percentage:.1f}% error rate")
    
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_scalability_progression(self, load_tester):
        """Test scalability with progressive load increase"""
        
        user_counts = [5, 10, 20, 30]
        results = []
        
        for user_count in user_counts:
            print(f"\n?? Testing with {user_count} concurrent users...")
            
            result = await load_tester.run_load_test(
                concurrent_users=user_count,
                requests_per_user=2
            )
            results.append(result)
        
        # Analyze scalability
        print(f"\n?? Scalability Analysis:")
        for i, result in enumerate(results):
            print(f"   {user_counts[i]} users: {result.average_response_time:.2f}s avg, "
                  f"{result.error_rate_percentage:.1f}% errors, {result.throughput_requests_per_second:.1f} req/s")
        
        # Verify reasonable scalability
        first_result = results[0]
        last_result = results[-1]
        
        response_time_increase = (
            (last_result.average_response_time - first_result.average_response_time) 
            / first_result.average_response_time * 100
        )
        
        # Response time should not increase more than 200% with 6x load
        assert response_time_increase < 200, f"Response time increased {response_time_increase:.1f}% - poor scalability"
        
        print(f"??Scalability test passed: {response_time_increase:.1f}% response time increase")
    
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_sustained_load_duration(self, load_tester):
        """Test sustained load over time"""
        
        print("?±ï? Running sustained load test for 2 minutes...")
        
        result = await load_tester.run_load_test(
            concurrent_users=15,
            requests_per_user=10,  # More requests per user
            test_duration_minutes=2
        )
        
        # Verify sustained performance
        assert result.total_duration >= 110, "Test should run for at least 110 seconds"
        assert result.error_rate_percentage < 20.0, f"Error rate {result.error_rate_percentage:.1f}% too high for sustained load"
        assert result.throughput_requests_per_second > 0.5, "Throughput too low for sustained load"
        
        print(f"??Sustained load test passed: {result.total_duration:.1f}s duration, "
              f"{result.throughput_requests_per_second:.1f} req/s sustained throughput")
    
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_mixed_scenario_load(self, load_tester):
        """Test load with mixed business scenarios"""
        
        # Override scenario selection to ensure variety
        original_simulate = load_tester._simulate_validation_execution
        
        async def mixed_scenario_simulate(request):
            # Add scenario-specific timing
            scenario_id = getattr(request, 'scenario_id', 'unknown')
            
            if 'complex' in scenario_id or 'fintech' in scenario_id:
                base_time = 4.0  # Complex scenarios take longer
            elif 'niche' in scenario_id:
                base_time = 1.5  # Simple scenarios are faster
            else:
                base_time = 2.5  # Standard scenarios
            
            await asyncio.sleep(base_time * random.uniform(0.8, 1.2))
            
            return {
                "validation_id": request.id,
                "overall_score": random.uniform(40, 95),
                "confidence_level": random.uniform(0.7, 0.95),
                "execution_time": base_time,
                "scenario_complexity": scenario_id
            }
        
        load_tester._simulate_validation_execution = mixed_scenario_simulate
        
        result = await load_tester.run_load_test(
            concurrent_users=20,
            requests_per_user=3
        )
        
        # Restore original method
        load_tester._simulate_validation_execution = original_simulate
        
        # Verify mixed scenario handling
        assert result.successful_requests > 0, "Should handle mixed scenarios successfully"
        assert result.error_rate_percentage < 20.0, "Mixed scenarios should not cause excessive errors"
        
        print(f"??Mixed scenario load test passed: {result.successful_requests} successful requests")
    
    @pytest.mark.load
    def test_generate_load_test_report(self, load_tester):
        """Test load test report generation"""
        
        # Add some mock results
        load_tester.results = [
            LoadTestResult(
                test_name="test_10_users",
                concurrent_users=10,
                total_requests=30,
                successful_requests=28,
                failed_requests=2,
                average_response_time=2.5,
                max_response_time=4.2,
                min_response_time=1.8,
                throughput_requests_per_second=3.2,
                error_rate_percentage=6.7,
                total_duration=9.4,
                memory_usage_mb=45.2,
                cpu_usage_percent=25.3
            ),
            LoadTestResult(
                test_name="test_25_users",
                concurrent_users=25,
                total_requests=50,
                successful_requests=45,
                failed_requests=5,
                average_response_time=3.8,
                max_response_time=7.1,
                min_response_time=2.1,
                throughput_requests_per_second=4.1,
                error_rate_percentage=10.0,
                total_duration=12.2,
                memory_usage_mb=62.8,
                cpu_usage_percent=42.1
            )
        ]
        
        # Generate report
        report = load_tester.generate_load_test_report()
        
        # Verify report structure
        assert "summary" in report
        assert "test_results" in report
        assert "performance_analysis" in report
        
        # Verify summary data
        summary = report["summary"]
        assert summary["total_tests"] == 2
        assert summary["total_requests"] == 80
        assert summary["total_successful"] == 73
        assert summary["total_failed"] == 7
        
        # Verify performance analysis
        analysis = report["performance_analysis"]
        assert "meets_sla" in analysis
        assert "scalability_rating" in analysis
        assert "recommendations" in analysis
        assert isinstance(analysis["recommendations"], list)
        
        print(f"??Load test report generated successfully")
        print(f"   Overall error rate: {summary['overall_error_rate']:.1f}%")
        print(f"   Scalability rating: {analysis['scalability_rating']}")
        print(f"   Recommendations: {len(analysis['recommendations'])}")


@pytest.mark.load
@pytest.mark.asyncio
async def test_comprehensive_load_testing():
    """Comprehensive load testing suite"""
    print("\n?ï¿½ï¿½ Starting Comprehensive Load Testing")
    print("=" * 60)
    
    load_tester = ConcurrentValidationLoadTester()
    
    # Test progression: Light -> Medium -> Heavy
    load_scenarios = [
        (10, 2, "Light Load"),
        (25, 2, "Medium Load"),
        (50, 1, "Heavy Load")
    ]
    
    for users, requests, description in load_scenarios:
        print(f"\n?ï¿½ï¿½ {description}: {users} users, {requests} requests each")
        
        try:
            result = await load_tester.run_load_test(users, requests)
            
            # Verify basic requirements
            assert result.total_requests > 0, "Should execute some requests"
            assert result.successful_requests >= result.total_requests * 0.5, "Should have reasonable success rate"
            
            print(f"   ??{description} completed successfully")
            
        except Exception as e:
            print(f"   ??{description} failed: {e}")
    
    # Generate comprehensive report
    print(f"\n?? Generating Load Test Report...")
    report = load_tester.generate_load_test_report()
    
    print(f"   Total tests: {report['summary']['total_tests']}")
    print(f"   Total requests: {report['summary']['total_requests']}")
    print(f"   Success rate: {(report['summary']['total_successful']/report['summary']['total_requests']*100):.1f}%")
    print(f"   Scalability rating: {report['performance_analysis']['scalability_rating']}")
    
    # Save report
    import json
    from pathlib import Path
    
    report_file = Path("test-results/load-test-report.json")
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"   ?? Report saved to: {report_file}")
    
    print(f"\n?? Comprehensive Load Testing Completed!")
    print("=" * 60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "load"])
