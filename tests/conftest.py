"""
Conftest file for pytest configuration and fixtures.
"""

import pytest

from .test_helpers import TestHelper


@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for the API endpoints."""
    return "http://localhost:7071/api"


@pytest.fixture(scope="session")
def available_probes(api_base_url):
    """Get available probes for testing."""
    response = TestHelper.make_request("GET", "/v1/probes")
    if response.status_code != 200:
        pytest.skip("Could not fetch available probes")

    probes = response.json()["probes"]
    if not probes:
        pytest.skip("No probes available for testing")

    return probes


@pytest.fixture(scope="session")
def test_probe(available_probes):
    """Get the first available probe for testing."""
    return available_probes[0]


@pytest.fixture(scope="session")
def test_layer(test_probe):
    """Get the first available layer for testing."""
    return test_probe["layers"][0]
