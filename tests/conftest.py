"""
Pytest configuration and shared fixtures
"""

import pytest
import requests
from typing import Generator


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test"
    )


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for API testing"""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def demo_credentials() -> dict:
    """Demo user credentials"""
    return {
        "email": "demo@riskintel360.com",
        "password": "demo123"
    }
