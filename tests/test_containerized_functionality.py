"""
Test containerized functionality for RiskIntel360 Platform
Tests that verify the application works correctly in containerized environments.
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock

from riskintel360.api.main import create_app
from riskintel360.config.environment import get_environment_manager
from riskintel360.services.agent_runtime import get_session_manager, shutdown_session_manager


class TestContainerizedFunctionality:
    """Test cases for containerized functionality"""
    
    @pytest.mark.asyncio
    async def test_app_creation(self):
        """Test that the FastAPI app can be created successfully"""
        app = create_app()
        assert app is not None
        assert app.title == "RiskIntel360 Platform API"
    
    @pytest.mark.asyncio
    async def test_environment_detection(self):
        """Test environment detection works correctly"""
        env_manager = get_environment_manager()
        
        # Should detect local_docker by default
        assert env_manager._deployment_target.value == "local_docker"
        assert env_manager._environment.value == "development"
    
    @pytest.mark.asyncio
    async def test_configuration_validation(self):
        """Test configuration validation"""
        env_manager = get_environment_manager()
        
        # Should validate successfully in test environment
        is_valid = env_manager.validate_configuration()
        assert is_valid
    
    @pytest.mark.asyncio
    async def test_session_manager_in_container_context(self):
        """Test session manager works in container-like context"""
        # Simulate container environment
        with patch.dict('os.environ', {
            'ENVIRONMENT': 'development',
            'DEPLOYMENT_TARGET': 'local_docker',
        }):
            session_manager = await get_session_manager()
            assert session_manager._running
            
            # Test basic functionality
            session = await session_manager.create_session("test_agent", "test_user")
            assert session is not None
            assert session.session_id is not None
            
            # Cleanup
            await session_manager.cleanup_session(session.session_id)
            await shutdown_session_manager()
    
    @pytest.mark.asyncio
    async def test_health_endpoint_functionality(self):
        """Test health endpoint works correctly"""
        from riskintel360.api.health import health_check
        
        # Test health check function
        health_status = await health_check()
        assert health_status.status in ["healthy", "degraded", "unhealthy"]
        assert health_status.environment == "development"
        assert health_status.deployment_target == "local_docker"
        assert "session_manager" in health_status.components
    
    @pytest.mark.asyncio
    async def test_ecs_environment_simulation(self):
        """Test ECS environment detection and configuration"""
        # Simulate ECS environment
        with patch.dict('os.environ', {
            'ECS_CONTAINER_METADATA_URI_V4': 'http://169.254.170.2/v4/metadata',
            'ENVIRONMENT': 'production',
            'AWS_DEFAULT_REGION': 'us-east-1',
        }):
            # Create new environment manager to pick up changes
            from riskintel360.config.environment import EnvironmentManager
            ecs_env_manager = EnvironmentManager()
            
            assert ecs_env_manager._deployment_target.value == "aws_ecs"
            assert ecs_env_manager._environment.value == "production"
            
            config = ecs_env_manager.get_config()
            assert config.deployment_target.value == "aws_ecs"
            assert config.environment.value == "production"
    
    @pytest.mark.asyncio
    async def test_concurrent_session_handling(self):
        """Test concurrent session handling in container context"""
        session_manager = await get_session_manager()
        
        # Create multiple sessions concurrently
        async def create_test_session(i):
            return await session_manager.create_session(f"agent_{i}", f"user_{i}")
        
        # Create 5 sessions concurrently
        tasks = [create_test_session(i) for i in range(5)]
        sessions = await asyncio.gather(*tasks)
        
        assert len(sessions) == 5
        assert len(set(s.session_id for s in sessions)) == 5  # All unique
        
        # Cleanup
        for session in sessions:
            await session_manager.cleanup_session(session.session_id)
        
        await shutdown_session_manager()
    
    @pytest.mark.asyncio
    async def test_memory_limits_simulation(self):
        """Test memory limits handling in container context"""
        session_manager = await get_session_manager()
        
        # Test with limited sessions (simulating container memory limits)
        original_max = session_manager.max_sessions
        session_manager.max_sessions = 3
        
        try:
            # Create sessions up to limit
            sessions = []
            for i in range(3):
                session = await session_manager.create_session(f"agent_{i}", f"user_{i}")
                await session_manager.update_session_status(session.session_id, session_manager.SessionStatus.RUNNING)
                sessions.append(session)
            
            # Try to create one more (should fail)
            with pytest.raises(RuntimeError, match="Maximum concurrent sessions"):
                await session_manager.create_session("overflow_agent", "overflow_user")
            
            # Cleanup
            for session in sessions:
                await session_manager.cleanup_session(session.session_id)
        
        finally:
            session_manager.max_sessions = original_max
            await shutdown_session_manager()
    
    def test_docker_build_configuration(self):
        """Test Docker build configuration is valid"""
        # Test that Dockerfile targets are properly configured
        with open("Dockerfile", "r") as f:
            dockerfile_content = f.read()
        
        # Check for multi-stage build targets
        assert "FROM base as development" in dockerfile_content
        assert "FROM base as production" in dockerfile_content
        
        # Check for proper environment variables
        assert "ENV ENVIRONMENT=development" in dockerfile_content
        assert "ENV ENVIRONMENT=production" in dockerfile_content
        
        # Check for health checks
        assert "HEALTHCHECK" in dockerfile_content
    
    def test_ecs_task_definition_validity(self):
        """Test ECS task definitions are valid"""
        from infrastructure.ecs_config import generate_task_definition_json
        
        # Test development task definition
        dev_task_def = generate_task_definition_json("development")
        assert dev_task_def["family"] == "RiskIntel360-development"
        assert dev_task_def["cpu"] == "512"
        assert dev_task_def["memory"] == "1024"
        assert len(dev_task_def["containerDefinitions"]) == 1
        
        container = dev_task_def["containerDefinitions"][0]
        assert container["name"] == "RiskIntel360-agent"
        assert any(env["name"] == "ENVIRONMENT" and env["value"] == "development" 
                  for env in container["environment"])
        
        # Test production task definition
        prod_task_def = generate_task_definition_json("production")
        assert prod_task_def["family"] == "RiskIntel360-production"
        assert prod_task_def["cpu"] == "1024"
        assert prod_task_def["memory"] == "2048"
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown_handling(self):
        """Test graceful shutdown in container context"""
        session_manager = await get_session_manager()
        
        # Create some sessions
        session1 = await session_manager.create_session("agent1", "user1")
        session2 = await session_manager.create_session("agent2", "user2")
        
        # Verify sessions exist
        assert await session_manager.get_session(session1.session_id) is not None
        assert await session_manager.get_session(session2.session_id) is not None
        
        # Simulate graceful shutdown
        await shutdown_session_manager()
        
        # Verify shutdown completed without errors
        assert not session_manager._running


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
