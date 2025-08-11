"""
Integration tests for TaskTracker Azure Functions API.

These tests verify the functionality of all three endpoints:
- /health
- /v1/probes
- /v1/predict

Tests can be run against a locally running Azure Functions instance.
"""

import pytest
import requests  # type: ignore

from .test_helpers import BASE_URL, TIMEOUT, TestHelper


class TestHealthEndpoint:
    """Test cases for the /health endpoint."""

    def test_health_check_success(self):
        """Test that health check returns 200 with correct status."""
        response = TestHelper.make_request("GET", "/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert "TaskTracker API is running" in data["message"]

    def test_health_check_response_structure(self):
        """Test that health check response has correct structure."""
        response = TestHelper.make_request("GET", "/health")
        data = response.json()

        required_fields = ["status", "message"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


class TestProbesEndpoint:
    """Test cases for the /v1/probes endpoint."""

    def test_list_probes_success(self):
        """Test that probes list returns 200 with probe information."""
        response = TestHelper.make_request("GET", "/v1/probes")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert "probes" in data
        assert isinstance(data["probes"], list)

    def test_probes_structure(self):
        """Test that each probe has the correct structure."""
        response = TestHelper.make_request("GET", "/v1/probes")
        data = response.json()

        for probe in data["probes"]:
            required_fields = ["model", "probe_type", "layers"]
            for field in required_fields:
                assert field in probe, f"Missing required field: {field}"

            assert isinstance(probe["layers"], list), "layers should be a list"
            assert all(
                isinstance(layer, int) for layer in probe["layers"]
            ), "all layers should be integers"
            assert (
                probe["probe_type"] == "linear_probe"
            ), "probe_type should be 'linear_probe'"

    def test_probes_not_empty(self):
        """Test that at least some probes are available."""
        response = TestHelper.make_request("GET", "/v1/probes")
        data = response.json()

        assert len(data["probes"]) > 0, "Expected at least one probe to be available"


class TestPredictEndpoint:
    """Test cases for the /v1/predict endpoint."""

    def test_predict_success(self):
        """Test successful prediction with valid data."""
        available_probes = TestHelper.get_available_probes()
        if not available_probes:
            pytest.skip("No probes available for testing")

        test_probe = available_probes[0]
        test_layer = test_probe["layers"][0]

        request_data = {
            "model": test_probe["model"],
            "probe_type": test_probe["probe_type"],
            "layer": test_layer,
            "primary_activations": TestHelper.generate_test_activations(4096, seed=42),
            "text_activations": TestHelper.generate_test_activations(4096, seed=43),
        }

        response = TestHelper.make_request("POST", "/v1/predict", request_data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert "predicted_probability" in data
        assert 0.0 <= data["predicted_probability"] <= 1.0
        assert data["model"] == test_probe["model"]
        assert data["layer"] == test_layer

    def test_predict_invalid_model(self):
        """Test prediction with invalid model name."""
        request_data = {
            "model": "nonexistent_model",
            "layer": 0,
            "primary_activations": TestHelper.generate_test_activations(4096),
            "text_activations": TestHelper.generate_test_activations(4096),
        }

        response = TestHelper.make_request("POST", "/v1/predict", request_data)

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "not found" in data["error"].lower()

    def test_predict_invalid_layer(self):
        """Test prediction with invalid layer number."""
        available_probes = TestHelper.get_available_probes()
        if not available_probes:
            pytest.skip("No probes available for testing")

        test_probe = available_probes[0]
        invalid_layer = 9999  # Assuming this layer doesn't exist

        request_data = {
            "model": test_probe["model"],
            "layer": invalid_layer,
            "primary_activations": TestHelper.generate_test_activations(4096),
            "text_activations": TestHelper.generate_test_activations(4096),
        }

        response = TestHelper.make_request("POST", "/v1/predict", request_data)

        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_predict_wrong_activation_size(self):
        """Test prediction with wrong activation array size."""
        available_probes = TestHelper.get_available_probes()
        if not available_probes:
            pytest.skip("No probes available for testing")

        test_probe = available_probes[0]
        test_layer = test_probe["layers"][0]

        request_data = {
            "model": test_probe["model"],
            "layer": test_layer,
            "primary_activations": [0.1, 0.2, 0.3],  # Wrong size
            "text_activations": TestHelper.generate_test_activations(4096),
        }

        response = TestHelper.make_request("POST", "/v1/predict", request_data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "validation" in data["error"].lower()

    def test_predict_missing_fields(self):
        """Test prediction with missing required fields."""
        available_probes = TestHelper.get_available_probes()
        if not available_probes:
            pytest.skip("No probes available for testing")

        test_probe = available_probes[0]

        request_data = {
            "model": test_probe["model"],
            # Missing layer, primary_activations, text_activations
        }

        response = TestHelper.make_request("POST", "/v1/predict", request_data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_predict_invalid_json(self):
        """Test prediction with invalid JSON."""
        # Make request with invalid JSON
        url = f"{BASE_URL}/v1/predict"
        headers = {"Content-Type": "application/json"}

        response = requests.post(
            url, headers=headers, data="invalid json{", timeout=TIMEOUT
        )

        assert response.status_code == 500

    def test_predict_multiple_models(self):
        """Test prediction works with different available models."""
        available_probes = TestHelper.get_available_probes()
        if not available_probes:
            pytest.skip("No probes available for testing")

        for probe in available_probes[:3]:  # Test first 3 probes
            for layer in probe["layers"][:2]:  # Test first 2 layers
                request_data = {
                    "model": probe["model"],
                    "layer": layer,
                    "primary_activations": TestHelper.generate_test_activations(4096),
                    "text_activations": TestHelper.generate_test_activations(4096),
                }

                response = TestHelper.make_request("POST", "/v1/predict", request_data)

                assert (
                    response.status_code == 200
                ), f"Failed for {probe['model']} layer {layer}"
                data = response.json()
                assert 0.0 <= data["predicted_probability"] <= 1.0


class TestIntegration:
    """Integration tests that test multiple endpoints together."""

    def test_end_to_end_workflow(self):
        """Test complete workflow: health -> probes -> predict."""
        # 1. Check health
        health_response = TestHelper.make_request("GET", "/health")
        assert health_response.status_code == 200

        # 2. Get available probes
        probes_response = TestHelper.make_request("GET", "/v1/probes")
        assert probes_response.status_code == 200
        probes_data = probes_response.json()
        assert len(probes_data["probes"]) > 0

        # 3. Make prediction with first available probe
        probe = probes_data["probes"][0]
        layer = probe["layers"][0]

        request_data = {
            "model": probe["model"],
            "layer": layer,
            "primary_activations": TestHelper.generate_test_activations(4096),
            "text_activations": TestHelper.generate_test_activations(4096),
        }

        predict_response = TestHelper.make_request("POST", "/v1/predict", request_data)
        assert predict_response.status_code == 200

        predict_data = predict_response.json()
        assert "predicted_probability" in predict_data
        assert predict_data["model"] == probe["model"]
        assert predict_data["layer"] == layer
