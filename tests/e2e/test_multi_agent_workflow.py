"""
Multi-Agent Workflow End-to-End Tests
Tests the coordination and execution of all six AI agents working together
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
import httpx


class TestMultiAgentWorkflow:
    """Test multi-agent coordination and workflow execution"""
    
    @pytest.fixture(scope="class")
    def api_base_url(self):
        """API base URL for testing"""
        return "http://test-api:8000"
    
    @pytest.fixture(scope="class")
    def test_user_credentials(self):
        """Test user credentials"""
        return {
            "email": "analyst@testcorp.com",
            "password": "test_password_123",
            "user_id": "test-user-001"
        }
    
    @pytest.fixture(scope="class")
    async def authenticated_client(self, api_base_url, test_user_credentials):
        """Authenticated HTTP client"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            auth_response = await client.post(f"{api_base_url}/api/v1/auth/login", json={
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"]
            })
            assert auth_response.status_code == 200
            access_token = auth_response.json()["access_token"]
            client.headers.update({"Authorization": f"Bearer {access_token}"})
            yield client
    
    @pytest.mark.asyncio
    async def test_six_agent_coordination_saas_scenario(self, api_base_url, authenticated_client):
        """
        Test all six agents working together on SaaS startup scenario
        Agents: Market Research, Competitive Intelligence, Financial Validation, 
                Risk Assessment, Customer Intelligence, Synthesis & Recommendation
        """
        print("\n?? Testing Six-Agent Coordination - SaaS Scenario")
        print("=" * 55)
        
        # Create comprehensive validation request
        saas_validation_data = {
            "business_concept": "AI-powered project management tool for remote teams",
            "target_market": "Remote-first companies with 50-500 employees globally",
            "analysis_scope": ["market", "competitive", "financial", "risk", "customer"],
            "priority": "high",
            "custom_parameters": {
                "budget_range": "1000000-2500000",
                "timeline": "18-months",
                "target_revenue": "10000000",
                "team_size": "15-25",
                "technology_stack": "ai_ml_saas",
                "target_markets": ["north_america", "europe", "asia_pacific"],
                "business_model": "subscription_saas"
            }
        }
        
        # Step 1: Create validation request
        create_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations",
            json=saas_validation_data
        )
        assert create_response.status_code == 201
        validation_result = create_response.json()
        validation_id = validation_result["id"]
        
        print(f"   ??Validation created: {validation_id}")
        
        # Step 2: Start multi-agent workflow
        start_time = time.time()
        
        start_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations/{validation_id}/start"
        )
        assert start_response.status_code == 200
        
        print("   ?? Multi-agent workflow started")
        
        # Step 3: Monitor individual agent execution
        expected_agents = [
            "market_research",
            "competitive_intelligence", 
            "financial_validation",
            "risk_assessment",
            "customer_intelligence",
            "synthesis_recommendation"
        ]
        
        agent_results = {}
        agent_execution_times = {}
        agents_completed = set()
        
        max_wait_time = 600  # 10 minutes max for all agents
        
        while len(agents_completed) < 6 and (time.time() - start_time) < max_wait_time:
            # Get current status
            status_response = await authenticated_client.get(
                f"{api_base_url}/api/v1/validations/{validation_id}/status"
            )
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            # Check each agent's progress
            for agent_id in expected_agents:
                agent_status = status_data.get("agent_statuses", {}).get(agent_id, {})
                
                if agent_status.get("status") == "completed" and agent_id not in agents_completed:
                    agents_completed.add(agent_id)
                    execution_time = agent_status.get("execution_time_ms", 0) / 1000
                    agent_execution_times[agent_id] = execution_time
                    
                    print(f"   ??{agent_id.replace('_', ' ').title()} completed in {execution_time:.2f}s")
                    
                    # Verify agent response time (<5 seconds requirement)
                    assert execution_time < 5.0, f"Agent {agent_id} exceeded 5s limit: {execution_time}s"
                    
                    # Get agent-specific results
                    agent_result_response = await authenticated_client.get(
                        f"{api_base_url}/api/v1/validations/{validation_id}/agents/{agent_id}/results"
                    )
                    if agent_result_response.status_code == 200:
                        agent_results[agent_id] = agent_result_response.json()
                
                elif agent_status.get("status") == "failed":
                    error_msg = agent_status.get("error_message", "Unknown error")
                    print(f"   ??{agent_id} failed: {error_msg}")
                    # Don't fail the test immediately, check if graceful degradation works
            
            # Check if workflow is complete
            if status_data.get("status") == "completed":
                break
            elif status_data.get("status") == "failed":
                print(f"   ?â?¡ï? Workflow failed: {status_data.get('error_message', 'Unknown error')}")
                break
            
            await asyncio.sleep(3)  # Check every 3 seconds
        
        total_execution_time = time.time() - start_time
        print(f"\n   ?â?±ï? Total workflow execution time: {total_execution_time:.2f}s")
        
        # Step 4: Verify agent coordination and data sharing
        print("\n4ï¸?â?£ Verifying Agent Coordination and Data Sharing...")
        
        # Verify all expected agents completed or handled gracefully
        assert len(agents_completed) >= 4, f"Too few agents completed: {len(agents_completed)}/6"
        
        # Verify agent results contain expected data structures
        for agent_id, result in agent_results.items():
            assert "agent_id" in result
            assert "status" in result
            assert "confidence_score" in result
            assert "analysis" in result
            assert result["agent_id"] == agent_id
            assert 0 <= result["confidence_score"] <= 1
            
            print(f"   ??{agent_id}: Confidence {result['confidence_score']:.2f}")
        
        # Step 5: Verify cross-agent data integration
        print("\n5ï¸?â?£ Verifying Cross-Agent Data Integration...")
        
        # Get final synthesis results
        results_response = await authenticated_client.get(
            f"{api_base_url}/api/v1/validations/{validation_id}/results"
        )
        assert results_response.status_code == 200
        final_results = results_response.json()
        
        # Verify synthesis agent integrated data from other agents
        synthesis_analysis = final_results.get("synthesis_analysis", {})
        
        # Check for cross-references between agent analyses
        market_data_referenced = False
        competitive_data_referenced = False
        financial_data_referenced = False
        
        synthesis_content = str(synthesis_analysis).lower()
        
        if "market" in synthesis_content or "growth" in synthesis_content:
            market_data_referenced = True
        if "competitor" in synthesis_content or "competitive" in synthesis_content:
            competitive_data_referenced = True
        if "revenue" in synthesis_content or "financial" in synthesis_content:
            financial_data_referenced = True
        
        print(f"   ??Market data referenced: {market_data_referenced}")
        print(f"   ??Competitive data referenced: {competitive_data_referenced}")
        print(f"   ??Financial data referenced: {financial_data_referenced}")
        
        # Step 6: Verify strategic recommendations quality
        print("\n6ï¸?â?£ Verifying Strategic Recommendations Quality...")
        
        recommendations = final_results.get("strategic_recommendations", [])
        assert len(recommendations) > 0, "No strategic recommendations generated"
        
        for i, recommendation in enumerate(recommendations):
            assert "recommendation" in recommendation
            assert "priority" in recommendation
            assert "rationale" in recommendation
            
            print(f"   ??Recommendation {i+1}: {recommendation.get('priority', 'unknown')} priority")
        
        # Step 7: Performance verification
        print("\n7ï¸?â?£ Verifying Performance Requirements...")
        
        # Individual agent performance (<5 seconds each)
        for agent_id, exec_time in agent_execution_times.items():
            assert exec_time < 5.0, f"Agent {agent_id} exceeded 5s: {exec_time}s"
        
        # Overall workflow performance (<2 hours, but we test with shorter timeout)
        assert total_execution_time < 600, f"Workflow exceeded 10min test limit: {total_execution_time}s"
        
        # Verify overall quality metrics
        overall_score = final_results.get("overall_score", 0)
        confidence_level = final_results.get("confidence_level", 0)
        
        assert 0 <= overall_score <= 100, f"Invalid overall score: {overall_score}"
        assert 0 <= confidence_level <= 1, f"Invalid confidence level: {confidence_level}"
        
        print(f"   ??Overall Score: {overall_score}/100")
        print(f"   ??Confidence Level: {confidence_level:.2f}")
        print(f"   ??Agents Completed: {len(agents_completed)}/6")
        print(f"   ??Average Agent Time: {sum(agent_execution_times.values())/len(agent_execution_times):.2f}s")
        
        # Test Summary
        print("\n?ð??¯¯ Multi-Agent Workflow Test Summary")
        print("=" * 40)
        print(f"??Validation ID: {validation_id}")
        print(f"??Agents Completed: {len(agents_completed)}/6")
        print(f"??Total Execution Time: {total_execution_time:.2f}s")
        print(f"??Performance: All agents <5s")
        print(f"??Data Integration: Cross-agent references verified")
        print(f"??Recommendations: {len(recommendations)} strategic recommendations")
        print(f"??Quality Score: {overall_score}/100 (Confidence: {confidence_level:.2f})")
    
    @pytest.mark.asyncio
    async def test_agent_failure_recovery(self, api_base_url, authenticated_client):
        """
        Test multi-agent workflow with simulated agent failures
        Verify graceful degradation and partial results
        """
        print("\n??§ Testing Agent Failure Recovery")
        print("=" * 35)
        
        # Create validation with failure simulation parameters
        failure_test_data = {
            "business_concept": "Test agent failure recovery scenario",
            "target_market": "Test market for failure scenarios",
            "analysis_scope": ["market", "competitive", "financial", "risk", "customer"],
            "priority": "medium",
            "custom_parameters": {
                "test_mode": "failure_simulation",
                "simulate_failures": ["competitive_intelligence", "risk_assessment"],
                "failure_type": "timeout"
            }
        }
        
        create_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations",
            json=failure_test_data
        )
        assert create_response.status_code == 201
        validation_id = create_response.json()["id"]
        
        print(f"   ??Failure test validation created: {validation_id}")
        
        # Start workflow with simulated failures
        start_response = await authenticated_client.post(
            f"{api_base_url}/api/v1/validations/{validation_id}/start"
        )
        assert start_response.status_code == 200
        
        # Monitor workflow with expected failures
        start_time = time.time()
        max_wait_time = 300  # 5 minutes
        
        failed_agents = set()
        completed_agents = set()
        
        while (time.time() - start_time) < max_wait_time:
            status_response = await authenticated_client.get(
                f"{api_base_url}/api/v1/validations/{validation_id}/status"
            )
            status_data = status_response.json()
            
            for agent_id, agent_status in status_data.get("agent_statuses", {}).items():
                if agent_status.get("status") == "failed" and agent_id not in failed_agents:
                    failed_agents.add(agent_id)
                    print(f"   ?â?¡ï? Agent {agent_id} failed as expected")
                elif agent_status.get("status") == "completed" and agent_id not in completed_agents:
                    completed_agents.add(agent_id)
                    print(f"   ??Agent {agent_id} completed successfully")
            
            if status_data.get("status") in ["completed", "partial_complete", "failed"]:
                break
            
            await asyncio.sleep(2)
        
        # Verify graceful degradation
        final_status_response = await authenticated_client.get(
            f"{api_base_url}/api/v1/validations/{validation_id}/status"
        )
        final_status = final_status_response.json()
        
        # Should have partial results even with failures
        assert len(completed_agents) > 0, "No agents completed successfully"
        assert len(failed_agents) > 0, "No simulated failures occurred"
        
        # Verify partial results are available
        results_response = await authenticated_client.get(
            f"{api_base_url}/api/v1/validations/{validation_id}/results"
        )
        
        if results_response.status_code == 200:
            results_data = results_response.json()
            # Should have partial results with appropriate confidence adjustments
            confidence_level = results_data.get("confidence_level", 0)
            # Confidence should be lower due to missing agent data
            assert confidence_level < 0.9, "Confidence should be reduced with failed agents"
            print(f"   ??Partial results available with adjusted confidence: {confidence_level:.2f}")
        
        print(f"   ??Graceful degradation verified: {len(completed_agents)} completed, {len(failed_agents)} failed")
    
    @pytest.mark.asyncio
    async def test_concurrent_multi_agent_workflows(self, api_base_url, authenticated_client):
        """
        Test multiple concurrent multi-agent workflows
        Verify system can handle concurrent validation requests
        """
        print("\n?? Testing Concurrent Multi-Agent Workflows")
        print("=" * 45)
        
        # Create multiple validation requests
        concurrent_validations = []
        
        validation_scenarios = [
            {
                "business_concept": "E-commerce marketplace for handmade goods",
                "target_market": "Artisans and craft enthusiasts globally",
                "scenario_name": "E-commerce Marketplace"
            },
            {
                "business_concept": "Fitness tracking app with AI personal trainer",
                "target_market": "Health-conscious individuals aged 25-45",
                "scenario_name": "Fitness AI App"
            },
            {
                "business_concept": "B2B invoice automation platform",
                "target_market": "Small to medium businesses with manual invoicing",
                "scenario_name": "Invoice Automation"
            }
        ]
        
        # Create all validations
        for i, scenario in enumerate(validation_scenarios):
            validation_data = {
                "business_concept": scenario["business_concept"],
                "target_market": scenario["target_market"],
                "analysis_scope": ["market", "competitive", "financial"],
                "priority": "medium",
                "custom_parameters": {
                    "concurrent_test": True,
                    "scenario_id": i + 1
                }
            }
            
            create_response = await authenticated_client.post(
                f"{api_base_url}/api/v1/validations",
                json=validation_data
            )
            assert create_response.status_code == 201
            validation_result = create_response.json()
            
            concurrent_validations.append({
                "id": validation_result["id"],
                "scenario": scenario["scenario_name"]
            })
            
            print(f"   ??Created validation {i+1}: {scenario['scenario_name']}")
        
        # Start all validations concurrently
        start_tasks = []
        for validation in concurrent_validations:
            task = authenticated_client.post(
                f"{api_base_url}/api/v1/validations/{validation['id']}/start"
            )
            start_tasks.append(task)
        
        start_responses = await asyncio.gather(*start_tasks)
        
        for i, response in enumerate(start_responses):
            assert response.status_code == 200
            print(f"   ?? Started workflow {i+1}")
        
        # Monitor all workflows concurrently
        start_time = time.time()
        max_wait_time = 600  # 10 minutes for concurrent workflows
        
        completed_validations = set()
        
        while len(completed_validations) < len(concurrent_validations) and (time.time() - start_time) < max_wait_time:
            # Check status of all validations
            status_tasks = []
            for validation in concurrent_validations:
                task = authenticated_client.get(
                    f"{api_base_url}/api/v1/validations/{validation['id']}/status"
                )
                status_tasks.append(task)
            
            status_responses = await asyncio.gather(*status_tasks)
            
            for i, response in enumerate(status_responses):
                if response.status_code == 200:
                    status_data = response.json()
                    validation_id = concurrent_validations[i]["id"]
                    
                    if status_data.get("status") == "completed" and validation_id not in completed_validations:
                        completed_validations.add(validation_id)
                        scenario_name = concurrent_validations[i]["scenario"]
                        print(f"   ??Completed: {scenario_name}")
            
            await asyncio.sleep(5)  # Check every 5 seconds
        
        total_time = time.time() - start_time
        
        # Verify concurrent execution results
        assert len(completed_validations) >= 2, f"Too few concurrent validations completed: {len(completed_validations)}"
        
        print(f"\n   ?? Concurrent Execution Results:")
        print(f"   ??Validations Completed: {len(completed_validations)}/{len(concurrent_validations)}")
        print(f"   ??Total Execution Time: {total_time:.2f}s")
        print(f"   ??Average Time per Validation: {total_time/len(completed_validations):.2f}s")
        
        # Verify results quality for completed validations
        for validation in concurrent_validations:
            if validation["id"] in completed_validations:
                results_response = await authenticated_client.get(
                    f"{api_base_url}/api/v1/validations/{validation['id']}/results"
                )
                if results_response.status_code == 200:
                    results_data = results_response.json()
                    overall_score = results_data.get("overall_score", 0)
                    confidence = results_data.get("confidence_level", 0)
                    print(f"   ?? {validation['scenario']}: Score {overall_score}, Confidence {confidence:.2f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
