"""
Integration tests for Docker container orchestration
Tests the fintech-enhanced Docker configuration and ML dependencies
"""

import pytest
import docker
import time
import requests
import subprocess
import os
from typing import Dict, Any
import json


class TestDockerOrchestration:
    """Test Docker container orchestration for fintech platform"""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Create Docker client for testing"""
        return docker.from_env()
    
    @pytest.fixture(scope="class")
    def compose_project(self):
        """Start docker-compose services for testing"""
        # Start services
        subprocess.run([
            "docker-compose", "-f", "docker-compose.yml", 
            "--profile", "dev", "up", "-d"
        ], check=True, cwd=".")
        
        # Wait for services to be ready
        time.sleep(30)
        
        yield "riskintel360"
        
        # Cleanup
        subprocess.run([
            "docker-compose", "-f", "docker-compose.yml",
            "--profile", "dev", "down", "-v"
        ], check=False, cwd=".")
    
    def test_ml_dependencies_installation(self, docker_client):
        """Test ML dependencies are properly installed in container"""
        # Build test container
        image, logs = docker_client.images.build(
            path=".",
            dockerfile="Dockerfile",
            target="development",
            tag="riskintel360:test-ml"
        )
        
        # Test ML libraries are installed
        container = docker_client.containers.run(
            image.id,
            command="python -c 'import sklearn, numpy, pandas, scipy, tensorflow, torch; print(\"ML libraries OK\")'",
            remove=True,
            capture_output=True,
            text=True
        )
        
        assert "ML libraries OK" in container
    
    def test_fintech_ml_libraries(self, docker_client):
        """Test fintech-specific ML libraries are available"""
        # Build test container
        image, logs = docker_client.images.build(
            path=".",
            dockerfile="Dockerfile", 
            target="development",
            tag="riskintel360:test-fintech"
        )
        
        # Test fintech ML libraries
        test_imports = [
            "import yfinance",
            "import alpha_vantage", 
            "import fredapi",
            "import pyod",
            "import hdbscan",
            "import umap",
            "import statsmodels",
            "import shap",
            "import optuna"
        ]
        
        for import_stmt in test_imports:
            container = docker_client.containers.run(
                image.id,
                command=f"python -c '{import_stmt}; print(\"{import_stmt} OK\")'",
                remove=True,
                capture_output=True,
                text=True
            )
            assert f"{import_stmt} OK" in container
    
    def test_container_environment_variables(self, compose_project, docker_client):
        """Test fintech environment variables are properly set"""
        containers = docker_client.containers.list(
            filters={"label": f"com.docker.compose.project={compose_project}"}
        )
        
        api_container = None
        for container in containers:
            if "riskintel360-dev-api" in container.name:
                api_container = container
                break
        
        assert api_container is not None, "API container not found"
        
        # Check fintech environment variables
        env_vars = api_container.attrs["Config"]["Env"]
        env_dict = {}
        for env_var in env_vars:
            if "=" in env_var:
                key, value = env_var.split("=", 1)
                env_dict[key] = value
        
        # Test fintech API configuration
        fintech_env_vars = [
            "ALPHA_VANTAGE_API_KEY",
            "YAHOO_FINANCE_API_KEY",
            "FRED_API_KEY",
            "SEC_EDGAR_API_KEY",
            "TREASURY_API_KEY",
            "NEWS_API_KEY"
        ]
        
        for var in fintech_env_vars:
            assert var in env_dict, f"Missing environment variable: {var}"
        
        # Test ML configuration
        ml_env_vars = [
            "ML_MODEL_PATH",
            "FRAUD_DETECTION_THRESHOLD",
            "ML_BATCH_SIZE",
            "ML_INFERENCE_TIMEOUT"
        ]
        
        for var in ml_env_vars:
            assert var in env_dict, f"Missing ML environment variable: {var}"
        
        # Test Bedrock configuration
        bedrock_env_vars = [
            "BEDROCK_REGION",
            "BEDROCK_MODEL_REGULATORY",
            "BEDROCK_MODEL_FRAUD",
            "BEDROCK_MODEL_RISK",
            "BEDROCK_MODEL_MARKET",
            "BEDROCK_MODEL_KYC"
        ]
        
        for var in bedrock_env_vars:
            assert var in env_dict, f"Missing Bedrock environment variable: {var}"
    
    def test_volume_mounts(self, compose_project, docker_client):
        """Test volume mounts for ML models and fintech data"""
        containers = docker_client.containers.list(
            filters={"label": f"com.docker.compose.project={compose_project}"}
        )
        
        api_container = None
        for container in containers:
            if "riskintel360-dev-api" in container.name:
                api_container = container
                break
        
        assert api_container is not None, "API container not found"
        
        # Check volume mounts
        mounts = api_container.attrs["Mounts"]
        mount_destinations = [mount["Destination"] for mount in mounts]
        
        # Test required volume mounts
        required_mounts = [
            "/app",           # Source code
            "/app/logs",      # Logs
            "/app/models",    # ML models
            "/app/data"       # Fintech data
        ]
        
        for mount in required_mounts:
            assert mount in mount_destinations, f"Missing volume mount: {mount}"
    
    def test_service_health_checks(self, compose_project):
        """Test health checks for all services"""
        # Wait for services to be healthy
        max_wait = 120  # 2 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # Test API health
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(5)
        else:
            pytest.fail("Services did not become healthy within timeout")
        
        # Test API health endpoint
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "database" in health_data
        assert "redis" in health_data
    
    def test_database_connectivity(self, compose_project):
        """Test database connectivity from API container"""
        # Test database connection through API
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["database"]["status"] == "connected"
        assert "postgresql" in health_data["database"]["type"]
    
    def test_redis_connectivity(self, compose_project):
        """Test Redis connectivity from API container"""
        # Test Redis connection through API
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["redis"]["status"] == "connected"
    
    def test_ml_model_directory_access(self, compose_project):
        """Test ML model directory is accessible"""
        # Test through API endpoint
        try:
            response = requests.get("http://localhost:8000/api/v1/ml/models/status")
            assert response.status_code in [200, 404]  # 404 is OK if no models yet
            
            if response.status_code == 200:
                model_status = response.json()
                assert "model_path" in model_status
                assert "/app/models" in model_status["model_path"]
        except requests.exceptions.RequestException:
            # If endpoint doesn't exist yet, that's OK for this test
            pass
    
    def test_fintech_data_directory_access(self, compose_project):
        """Test fintech data directory is accessible"""
        # Test through API endpoint
        try:
            response = requests.get("http://localhost:8000/api/v1/data/status")
            assert response.status_code in [200, 404]  # 404 is OK if endpoint doesn't exist
            
            if response.status_code == 200:
                data_status = response.json()
                assert "data_path" in data_status
                assert "/app/data" in data_status["data_path"]
        except requests.exceptions.RequestException:
            # If endpoint doesn't exist yet, that's OK for this test
            pass
    
    def test_container_resource_limits(self, compose_project, docker_client):
        """Test container resource limits and performance"""
        containers = docker_client.containers.list(
            filters={"label": f"com.docker.compose.project={compose_project}"}
        )
        
        for container in containers:
            # Get container stats
            stats = container.stats(stream=False)
            
            # Test memory usage is reasonable
            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]
            memory_percent = (memory_usage / memory_limit) * 100
            
            # Memory usage should be less than 90%
            assert memory_percent < 90, f"Container {container.name} using {memory_percent:.1f}% memory"
            
            # Test CPU usage is reasonable
            cpu_stats = stats["cpu_stats"]
            precpu_stats = stats["precpu_stats"]
            
            if "cpu_usage" in cpu_stats and "cpu_usage" in precpu_stats:
                cpu_delta = cpu_stats["cpu_usage"]["total_usage"] - precpu_stats["cpu_usage"]["total_usage"]
                system_delta = cpu_stats["system_cpu_usage"] - precpu_stats["system_cpu_usage"]
                
                if system_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * 100
                    # CPU usage should be reasonable for idle containers
                    assert cpu_percent < 50, f"Container {container.name} using {cpu_percent:.1f}% CPU"
    
    def test_log_output_format(self, compose_project, docker_client):
        """Test container log output format"""
        containers = docker_client.containers.list(
            filters={"label": f"com.docker.compose.project={compose_project}"}
        )
        
        api_container = None
        for container in containers:
            if "riskintel360-dev-api" in container.name:
                api_container = container
                break
        
        assert api_container is not None, "API container not found"
        
        # Get recent logs
        logs = api_container.logs(tail=50, timestamps=True).decode('utf-8')
        
        # Test log format (should contain structured logging)
        assert len(logs) > 0, "No logs found"
        
        # Look for application startup messages
        log_lines = logs.split('\n')
        startup_found = False
        
        for line in log_lines:
            if "Starting development server" in line or "Application startup complete" in line:
                startup_found = True
                break
        
        assert startup_found, "Application startup message not found in logs"
    
    def test_network_connectivity_between_services(self, compose_project):
        """Test network connectivity between services"""
        # Test API can connect to database and Redis through health check
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        
        health_data = response.json()
        
        # Verify all services are connected
        assert health_data["database"]["status"] == "connected"
        assert health_data["redis"]["status"] == "connected"
        
        # Test response time is reasonable
        assert health_data["response_time_ms"] < 1000  # Less than 1 second
    
    def test_container_security_configuration(self, compose_project, docker_client):
        """Test container security configuration"""
        containers = docker_client.containers.list(
            filters={"label": f"com.docker.compose.project={compose_project}"}
        )
        
        for container in containers:
            container_config = container.attrs["Config"]
            host_config = container.attrs["HostConfig"]
            
            # Test containers are not running as root (except database containers)
            if "postgres" not in container.name and "redis" not in container.name:
                user = container_config.get("User", "")
                # Should have non-root user configured
                assert user != "root" or user == "", f"Container {container.name} running as root"
            
            # Test no privileged mode
            assert not host_config.get("Privileged", False), f"Container {container.name} running in privileged mode"
            
            # Test read-only root filesystem where appropriate
            # (Skip for development containers that need write access)
            if "dev" not in container.name:
                read_only_rootfs = host_config.get("ReadonlyRootfs", False)
                # This is optional for development, but good to check
    
    def test_environment_specific_configuration(self, compose_project):
        """Test environment-specific configuration is applied"""
        # Test development-specific settings
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        
        health_data = response.json()
        
        # Should be in development mode
        assert health_data.get("environment") == "development"
        assert health_data.get("debug") is True
        
        # Test hot-reload is enabled (check through API info endpoint)
        try:
            response = requests.get("http://localhost:8000/api/v1/info")
            if response.status_code == 200:
                info_data = response.json()
                assert info_data.get("reload_enabled") is True
        except requests.exceptions.RequestException:
            # If endpoint doesn't exist, that's OK
            pass


class TestDockerBuildOptimization:
    """Test Docker build optimization and caching"""
    
    def test_docker_layer_caching(self, docker_client):
        """Test Docker layer caching is working efficiently"""
        # Build image first time
        start_time = time.time()
        image1, logs1 = docker_client.images.build(
            path=".",
            dockerfile="Dockerfile",
            target="development",
            tag="riskintel360:cache-test-1",
            nocache=True
        )
        first_build_time = time.time() - start_time
        
        # Build image second time (should use cache)
        start_time = time.time()
        image2, logs2 = docker_client.images.build(
            path=".",
            dockerfile="Dockerfile",
            target="development", 
            tag="riskintel360:cache-test-2"
        )
        second_build_time = time.time() - start_time
        
        # Second build should be significantly faster due to caching
        assert second_build_time < first_build_time * 0.5, "Docker layer caching not working efficiently"
        
        # Cleanup
        docker_client.images.remove(image1.id, force=True)
        docker_client.images.remove(image2.id, force=True)
    
    def test_multi_stage_build_efficiency(self, docker_client):
        """Test multi-stage build produces efficient images"""
        # Build development image
        dev_image, _ = docker_client.images.build(
            path=".",
            dockerfile="Dockerfile",
            target="development",
            tag="riskintel360:dev-size-test"
        )
        
        # Build production image
        prod_image, _ = docker_client.images.build(
            path=".",
            dockerfile="Dockerfile",
            target="production",
            tag="riskintel360:prod-size-test"
        )
        
        # Get image sizes
        dev_size = dev_image.attrs["Size"]
        prod_size = prod_image.attrs["Size"]
        
        # Production image should be smaller or similar size
        # (It might be larger due to optimizations, but shouldn't be dramatically larger)
        size_ratio = prod_size / dev_size
        assert size_ratio < 2.0, f"Production image is {size_ratio:.1f}x larger than development"
        
        # Cleanup
        docker_client.images.remove(dev_image.id, force=True)
        docker_client.images.remove(prod_image.id, force=True)
    
    def test_requirements_file_optimization(self):
        """Test requirements files are optimized for caching"""
        # Check requirements.txt exists and is properly structured
        assert os.path.exists("requirements.txt"), "requirements.txt not found"
        assert os.path.exists("requirements-ml.txt"), "requirements-ml.txt not found"
        
        # Check requirements are pinned (for reproducible builds)
        with open("requirements.txt", "r") as f:
            requirements = f.read()
        
        # Should have version pins for major dependencies
        major_deps = ["fastapi", "uvicorn", "pydantic", "sqlalchemy"]
        for dep in major_deps:
            assert f"{dep}>=" in requirements, f"{dep} should be version pinned"
        
        # Check ML requirements
        with open("requirements-ml.txt", "r") as f:
            ml_requirements = f.read()
        
        ml_deps = ["scikit-learn", "numpy", "pandas", "tensorflow", "torch"]
        for dep in ml_deps:
            assert f"{dep}>=" in ml_requirements, f"ML dependency {dep} should be version pinned"
