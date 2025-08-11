"""
Test helpers for TaskTracker integration tests.
"""

import os
from typing import Any, Dict, Optional

import numpy as np
import requests  # type: ignore

# Test configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:7071/api")
TIMEOUT = 30  # seconds


class TestHelper:
    """Helper class for generating test data and making requests."""

    @staticmethod
    def generate_test_activations(size: int = 4096, seed: int = 42) -> list:
        """Generate random activation arrays for testing."""
        np.random.seed(seed)
        return np.random.normal(0.5, 0.2, size).tolist()

    @staticmethod
    def make_request(
        method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Make HTTP request to the API endpoint."""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}

        if method.upper() == "GET":
            return requests.get(url, headers=headers, timeout=TIMEOUT)

        if method.upper() == "POST":
            return requests.post(url, headers=headers, json=data, timeout=TIMEOUT)

        raise ValueError(f"Unsupported HTTP method: {method}")

    @staticmethod
    def get_available_probes():
        """Get list of available probes."""
        response = TestHelper.make_request("GET", "/v1/probes")
        if response.status_code != 200:
            return []
        return response.json()["probes"]
