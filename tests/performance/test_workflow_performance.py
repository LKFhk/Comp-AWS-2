"""
Workflow Performance Tests
Tests performance requirements for complete validation workflows
Target: Complete validation in <2 hours, individual agents <5 seconds
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime, timezone
from typing import Dict, Any, List
import httpx
import psutil
import json


class TestWorkflowPerformance:
    """Test performance requirements for validation workflows"""
    
    @pytest.fixture(scope="class")
    def api_base_url(self):
        """API base URL for testing"""
        return "http://test-api:8000"
    
    @pytest.fixture(scope="class")
    def performance_config(self):
        """Performance test configuration"""
        return {
            "max_agent_response_time": 5.0,  # 5 seconds max per agent
            "max_workflow_time": 7200.0,     # 2 hours max for complete workflow
            "test_workflow_time": 600.0,     # 10 minutes for testing
            "concurrent_users": 10,          # Concurrent validation requests
            "memory_limit_mb": 512,          # Memory limit per agent
            "cpu_threshold": 80.0,           # CPU usage threshold
        }
    
    @pytest.fixture(scope="class")
    async def authenticated_client(self, api_base_url):
        """Authenticated HTTP client"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Use test credentials
            auth_response = await client.post(f"{api_base_url}/api/v1/auth/login", json={
                "email": "analyst@testcorp.com",
                "password": "test_password_123"
            })
            assert auth_response.status_code == 200
            access_token = auth_response.json()["access_token"]
            client.headers.update({"Authorization": f"Bearer {access_token}"})
            yield client
    
    @pytest.mark.asyncio
    async def test_individual_agent_performance(self, api_base_url, authenticated_client, performance_config):
        """
        Test individual agent performance requirements
        Each agent must respond within 5 seconds
        """
        print("\n??Testing Individual Agent Performance")
        print("=" * 40)
        
        # Create performance test validation
        performance_validation_data = {
            "business_concept": "Performance test - AI-powered analytics platform",
            "target_market": "Enterprise customers requiring real-time analytics",
            "analysis_scope": ["market", "competitive", "financial", "risk", "customer"],
            "priority": "high",
            "custom_parameters": {
                "performance_test": True,
                "target_response_time": 5.0
            }
        }
        
        create_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations",
            json=performance_validation_data
        )
        assert create_response.status_code == 201
        validation_id = create_response.json()["id"]
        
        print(f"   ??Performance test validation created: {validation_id}")
        
        # Start workflow and monitor individual agent performance
        start_time = time.time()
        
        start_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations/{validation_id}/start"
        )
        assert start_response.status_code == 200
        
        print("   ?? Performance workflow started")
        
        # Monitor each agent's performance
        expected_agents = [
            "market_analysis",
            "risk_assessment",
            "customer_behavior_intelligence"
        ]
        
        agent_performance_data = {}
        agents_completed = set()
        
        max_wait_time = performance_config["test_workflow_time"]
        
        while len(agents_completed) < 6 and (time.time() - start_time) < max_wait_time:
            # Get current status
            status_response = await authenticated_client.get(
                f"{api_base_url}/api/v1/validations/{validation_id}/status"
            )
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            # Check each agent's performance
            for agent_id in expected_agents:
                agent_status = status_data.get("agent_statuses", {}).get(agent_id, {})
                
                if agent_status.get("status") == "completed" and agent_id not in agents_completed:
                    agents_completed.add(agent_id)
                    
                    # Record performance metrics
                    execution_time = agent_status.get("execution_time_ms", 0) / 1000
                    memory_usage = agent_status.get("memory_usage_mb", 0)
                    tokens_used = agent_status.get("tokens_used", 0)
                    
                    agent_performance_data[agent_id] = {
                        "execution_time": execution_time,
                        "memory_usage_mb": memory_usage,
                        "tokens_used": tokens_used,
                        "status": "completed"
                    }
                    
                    # Verify performance requirements
                    max_time = performance_config["max_agent_response_time"]
                    max_memory = performance_config["memory_limit_mb"]
                    
                    print(f"   ?? {agent_id.replace('_', ' ').title()}:")
                    print(f"      ?ï¿½ï¿½?  Execution Time: {execution_time:.2f}s (limit: {max_time}s)")
                    print(f"      ?ï¿½ï¿½ Memory Usage: {memory_usage}MB (limit: {max_memory}MB)")
                    print(f"      ?ï¿½ï¿½ Tokens Used: {tokens_used}")
                    
                    # Assert performance requirements
                    assert execution_time <= max_time, f"Agent {agent_id} exceeded time limit: {execution_time}s > {max_time}s"
                    
                    if memory_usage > 0:  # Only check if memory data is available
                        assert memory_usage <= max_memory, f"Agent {agent_id} exceeded memory limit: {memory_usage}MB > {max_memory}MB"
                    
                    print(f"      ??Performance requirements met")
            
            # Check if workflow is complete
            if status_data.get("status") == "completed":
                break
            
            await asyncio.sleep(2)
        
        total_workflow_time = time.time() - start_time
        
        # Performance summary
        print(f"\n   ?? Performance Test Summary:")
        print(f"   ??Agents Completed: {len(agents_completed)}/6")
        print(f"   ??Total Workflow Time: {total_workflow_time:.2f}s")
        
        if agent_performance_data:
            execution_times = [data["execution_time"] for data in agent_performance_data.values()]
            avg_execution_time = statistics.mean(execution_times)
            max_execution_time = max(execution_times)
            
            print(f"   ??Average Agent Time: {avg_execution_time:.2f}s")
            print(f"   ??Slowest Agent Time: {max_execution_time:.2f}s")
            
            # All agents should meet performance requirements
            assert max_execution_time <= performance_config["max_agent_response_time"]
            assert avg_execution_time <= performance_config["max_agent_response_time"]
        
        # Verify workflow completed within test time limit
        assert total_workflow_time <= performance_config["test_workflow_time"]
        
        print("   ?ï¿½ï¿½ All performance requirements met!")
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_performance(self, api_base_url, authenticated_client, performance_config):
        """
        Test performance under concurrent load
        Multiple validation workflows running simultaneously
        """
        print("\n?? Testing Concurrent Workflow Performance")
        print("=" * 45)
        
        concurrent_count = performance_config["concurrent_users"]
        
        # Create multiple validation requests
        validation_ids = []
        
        for i in range(concurrent_count):
            validation_data = {
                "business_concept": f"Concurrent test {i+1} - SaaS platform for {['healthcare', 'finance', 'education', 'retail', 'manufacturing'][i % 5]}",
                "target_market": f"Target market {i+1} - {['SMB', 'Enterprise', 'Startup', 'Government', 'Non-profit'][i % 5]} sector",
                "analysis_scope": ["market", "competitive", "financial"],
                "priority": "medium",
                "custom_parameters": {
                    "concurrent_test": True,
                    "test_id": i + 1
                }
            }
            
            create_response = await authenticated_client.post(
                f"{api_base_url}/api/v1/validations",
                json=validation_data
            )
            assert create_response.status_code == 201
            validation_ids.append(create_response.json()["id"])
        
        print(f"   ??Created {len(validation_ids)} concurrent validation requests")
        
        # Start all workflows simultaneously
        start_time = time.time()
        
        start_tasks = []
        for validation_id in validation_ids:
            task = authenticated_client.post(
                f"{api_base_url}/api/v1/validations/{validation_id}/start"
            )
            start_tasks.append(task)
        
        start_responses = await asyncio.gather(*start_tasks, return_exceptions=True)
        
        successful_starts = 0
        for i, response in enumerate(start_responses):
            if isinstance(response, Exception):
                print(f"   ?ï¿½ï¿½? Validation {i+1} failed to start: {response}")
            elif response.status_code == 200:
                successful_starts += 1
            else:
                print(f"   ?ï¿½ï¿½? Validation {i+1} start failed with status {response.status_code}")
        
        print(f"   ?? Successfully started {successful_starts}/{len(validation_ids)} workflows")
        
        # Monitor system performance during concurrent execution
        system_metrics = []
        completed_validations = set()
        
        max_wait_time = performance_config["test_workflow_time"]
        
        while len(completed_validations) < successful_starts and (time.time() - start_time) < max_wait_time:
            # Collect system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            
            system_metrics.append({
                "timestamp": time.time() - start_time,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_info.percent,
                "memory_available_mb": memory_info.available / (1024 * 1024)
            })
            
            # Check validation statuses
            status_tasks = []
            for validation_id in validation_ids:
                task = authenticated_client.get(
                    f"{api_base_url}/api/v1/validations/{validation_id}/status"
                )
                status_tasks.append(task)
            
            status_responses = await asyncio.gather(*status_tasks, return_exceptions=True)
            
            for i, response in enumerate(status_responses):
                if not isinstance(response, Exception) and response.status_code == 200:
                    status_data = response.json()
                    validation_id = validation_ids[i]
                    
                    if status_data.get("status") == "completed" and validation_id not in completed_validations:
                        completed_validations.add(validation_id)
                        completion_time = time.time() - start_time
                        print(f"   ??Validation {i+1} completed in {completion_time:.2f}s")
            
            await asyncio.sleep(5)  # Check every 5 seconds
        
        total_concurrent_time = time.time() - start_time
        
        # Analyze performance results
        print(f"\n   ?? Concurrent Performance Results:")
        print(f"   ??Validations Completed: {len(completed_validations)}/{successful_starts}")
        print(f"   ??Total Execution Time: {total_concurrent_time:.2f}s")
        
        if len(completed_validations) > 0:
            avg_time_per_validation = total_concurrent_time / len(completed_validations)
            print(f"   ??Average Time per Validation: {avg_time_per_validation:.2f}s")
        
        # System resource analysis
        if system_metrics:
            avg_cpu = statistics.mean([m["cpu_percent"] for m in system_metrics])
            max_cpu = max([m["cpu_percent"] for m in system_metrics])
            avg_memory = statistics.mean([m["memory_percent"] for m in system_metrics])
            max_memory = max([m["memory_percent"] for m in system_metrics])
            
            print(f"\n   ?ï¿½ï¿½ï¿? System Resource Usage:")
            print(f"   ??Average CPU: {avg_cpu:.1f}%")
            print(f"   ??Peak CPU: {max_cpu:.1f}%")
            print(f"   ??Average Memory: {avg_memory:.1f}%")
            print(f"   ??Peak Memory: {max_memory:.1f}%")
            
            # Verify system didn't exceed thresholds
            cpu_threshold = performance_config["cpu_threshold"]
            assert max_cpu <= cpu_threshold, f"CPU usage exceeded threshold: {max_cpu}% > {cpu_threshold}%"
        
        # Verify acceptable completion rate
        completion_rate = len(completed_validations) / successful_starts if successful_starts > 0 else 0
        assert completion_rate >= 0.8, f"Completion rate too low: {completion_rate:.2f} < 0.8"
        
        print("   ?ï¿½ï¿½ Concurrent performance requirements met!")
    
    @pytest.mark.asyncio
    async def test_memory_usage_performance(self, api_base_url, authenticated_client, performance_config):
        """
        Test memory usage during validation workflows
        Verify memory efficiency and no memory leaks
        """
        print("\n?ï¿½ï¿½ Testing Memory Usage Performance")
        print("=" * 35)
        
        # Record initial memory usage
        initial_memory = psutil.virtual_memory()
        print(f"   ?? Initial Memory Usage: {initial_memory.percent:.1f}%")
        
        # Create memory-intensive validation
        memory_test_data = {
            "business_concept": "Memory performance test - Large-scale data analytics platform",
            "target_market": "Enterprise customers with big data requirements",
            "analysis_scope": ["market", "competitive", "financial", "risk", "customer"],
            "priority": "high",
            "custom_parameters": {
                "memory_test": True,
                "large_dataset": True,
                "complex_analysis": True
            }
        }
        
        create_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations",
            json=memory_test_data
        )
        assert create_response.status_code == 201
        validation_id = create_response.json()["id"]
        
        # Start workflow and monitor memory usage
        start_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations/{validation_id}/start"
        )
        assert start_response.status_code == 200
        
        memory_samples = []
        start_time = time.time()
        max_wait_time = 300  # 5 minutes
        
        while (time.time() - start_time) < max_wait_time:
            # Sample memory usage
            current_memory = psutil.virtual_memory()
            memory_samples.append({
                "timestamp": time.time() - start_time,
                "memory_percent": current_memory.percent,
                "memory_used_mb": (current_memory.total - current_memory.available) / (1024 * 1024)
            })
            
            # Check if workflow completed
            status_response = await authenticated_client.get(
                f"{api_base_url}/api/v1/validations/{validation_id}/status"
            )
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get("status") in ["completed", "failed"]:
                    break
            
            await asyncio.sleep(3)
        
        # Analyze memory usage patterns
        if memory_samples:
            memory_percentages = [sample["memory_percent"] for sample in memory_samples]
            memory_used_mb = [sample["memory_used_mb"] for sample in memory_samples]
            
            avg_memory = statistics.mean(memory_percentages)
            max_memory = max(memory_percentages)
            min_memory = min(memory_percentages)
            
            avg_memory_mb = statistics.mean(memory_used_mb)
            max_memory_mb = max(memory_used_mb)
            
            print(f"\n   ?? Memory Usage Analysis:")
            print(f"   ??Average Memory: {avg_memory:.1f}%")
            print(f"   ??Peak Memory: {max_memory:.1f}%")
            print(f"   ??Memory Range: {min_memory:.1f}% - {max_memory:.1f}%")
            print(f"   ??Average Memory Used: {avg_memory_mb:.0f}MB")
            print(f"   ??Peak Memory Used: {max_memory_mb:.0f}MB")
            
            # Check for memory leaks (memory should not continuously increase)
            if len(memory_samples) >= 10:
                first_half_avg = statistics.mean(memory_percentages[:len(memory_percentages)//2])
                second_half_avg = statistics.mean(memory_percentages[len(memory_percentages)//2:])
                memory_increase = second_half_avg - first_half_avg
                
                print(f"   ?? Memory Trend: {memory_increase:+.1f}% change")
                
                # Memory increase should be reasonable (not a significant leak)
                assert memory_increase < 10.0, f"Potential memory leak detected: {memory_increase:.1f}% increase"
            
            # Verify memory usage stays within reasonable bounds
            assert max_memory < 90.0, f"Memory usage too high: {max_memory:.1f}%"
        
        # Check final memory usage
        final_memory = psutil.virtual_memory()
        memory_change = final_memory.percent - initial_memory.percent
        
        print(f"   ?? Final Memory Usage: {final_memory.percent:.1f}% ({memory_change:+.1f}% change)")
        
        # Memory should return to reasonable levels after workflow
        assert abs(memory_change) < 15.0, f"Excessive memory change: {memory_change:.1f}%"
        
        print("   ?ï¿½ï¿½ Memory performance requirements met!")
    
    @pytest.mark.asyncio
    async def test_api_response_time_performance(self, api_base_url, authenticated_client):
        """
        Test API endpoint response times
        All API calls should respond quickly
        """
        print("\n?? Testing API Response Time Performance")
        print("=" * 40)
        
        api_endpoints = [
            ("GET", "/health", None),
            ("GET", "/api/v1/validations", None),
            ("POST", "/api/v1/validations", {
                "business_concept": "API performance test",
                "target_market": "Test market",
                "analysis_scope": ["market"],
                "priority": "low"
            })
        ]
        
        response_times = {}
        
        for method, endpoint, data in api_endpoints:
            times = []
            
            # Test each endpoint multiple times
            for i in range(5):
                start_time = time.time()
                
                if method == "GET":
                    response = await authenticated_client.get(f"{api_base_url}{endpoint}")
                elif method == "POST":
                    response = await authenticated_client.post(f"{api_base_url}{endpoint}", json=data)
                
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                times.append(response_time)
                
                # Verify successful response
                assert response.status_code in [200, 201], f"API call failed: {method} {endpoint}"
            
            avg_time = statistics.mean(times)
            max_time = max(times)
            min_time = min(times)
            
            response_times[f"{method} {endpoint}"] = {
                "avg": avg_time,
                "max": max_time,
                "min": min_time
            }
            
            print(f"   ?? {method} {endpoint}:")
            print(f"      ?ï¿½ï¿½?  Average: {avg_time:.1f}ms")
            print(f"      ?ï¿½ï¿½?  Range: {min_time:.1f}ms - {max_time:.1f}ms")
            
            # API responses should be fast (<1 second for most endpoints)
            max_allowed_time = 5000 if "validations" in endpoint and method == "POST" else 1000
            assert avg_time < max_allowed_time, f"API response too slow: {avg_time:.1f}ms > {max_allowed_time}ms"
        
        print("   ?ï¿½ï¿½ API response time requirements met!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
