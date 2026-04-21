"""
Pytest configuration for Judge agent tests.

Configures pytest-asyncio mode so that async tests work without
per-test markers.
"""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "asyncio: mark test as async")


@pytest.fixture(autouse=True)
def _reset_state():
    """Ensure clean state between tests."""
    yield
